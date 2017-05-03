from   qconcurrency.threading_ import ThreadedTask, SoloThreadedTask
from   Qt                      import QtCore, QtWidgets
import sys
import six
import time

class MyThreadedList( QtWidgets.QListWidget ):
    def __init__(self):
        QtWidgets.QListWidget.__init__(self)

        self._sem_rendering  = QtCore.QSemaphore(1)

        self._thread_loading = SoloThreadedTask(
            callback    = self._find_list_items,
            signals     = {
                'add_item': str,
                'clear':    None,
            },
            connections = {
                'add_item':[self.addItem],
                'clear':   [self.clear],
            },
        )

    def load(self):
        """
        Loads list with items from a separate thread.
        If load is already in progress, it will be cancelled
        before the new load request starts.
        """
        self._thread_loading.start()

    def _find_list_items(self, signalmgr=None ):
        """
        Adds 100 items to the list-widget,
        """
        signalmgr.clear.emit()

        for i in range(100):
            signalmgr.handle_if_abort()   # check for a request-abort, and exit early

            # slow signals down, emitting one object at a time
            # so that job can be cancelled.
            # ( signals have no priority, once emitted,  )
            # ( you must wait for them all to be handled )
            self._sem_rendering.tryAcquire(1,5000)
            signalmgr.add_item.emit( str(i) )  # add an item to the list

    def addItem(self, item):
        """
        Unecessarily waits .01 seconds (so you can see widget updating live),
        then adds the item to the list.
        """
        time.sleep(0.01)
        try:
            QtWidgets.QListWidget.addItem(self, item )
        except:
            self._mutex_rendering.unlock()
            six.reraise( *sys.exc_info() )


        if not self._sem_rendering.available():
            self._sem_rendering.release(1)

        # in this example, the wait is performed
        # in the UI thread - it never has a chance to process
        # QApp events (causing item to be rendered) until it runs
        # out of signals to fire. It is unlikely you will
        # need the following line in your production code.
        #
        QtCore.QCoreApplication.instance().processEvents()




if __name__ == '__main__':
    from   qconcurrency            import QApplication
    from   qconcurrency.threading_ import ThreadedTask
    import supercli.logging
    import time

    supercli.logging.SetLog( lv=20 )


    with QApplication():
        # create/load the list
        mylist = MyThreadedList()
        mylist.show()
        mylist.load()


        # from a separate thread (so that it is visible)
        # continuously reload the list

        def multiload_list( listwidget, signalmgr=None ):
            for i in range(3):
                time.sleep(0.5)
                listwidget.load()

        task = ThreadedTask( multiload_list, listwidget=mylist )
        task.start()

