from   qconcurrency.threading import SoloThreadedTask
from   Qt                     import QtCore, QtWidgets
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
            # ( signals have no priority, once emitted,  )
            # ( you must wait for all them to be handled )
            # ( before you can cancel the job            )
            self._sem_rendering.tryAcquire(1,5000)
            signalmgr.add_item.emit( str(i) )  # add an item to the list

    def addItem(self, item):
        time.sleep(0.01)
        try:
            QtWidgets.QListWidget.addItem(self, item )
        except:
            self._mutex_rendering.unlock()
            six.reraise( *sys.exc_info() )

        self._sem_rendering.release(1)




if __name__ == '__main__':
    from   qconcurrency           import QApplication
    from   qconcurrency.threading import ThreadedTask
    import time

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

