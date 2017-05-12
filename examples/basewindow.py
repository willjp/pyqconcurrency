"""
Another example usage of `SoloThreadedTask`,
identical to ``examples/threadedlist.py``, but this
time it is created-by/used within a `QBaseWindow` so that
it's builtin progressbar can be updated.

Now, the signals `add_progress` and `incr_progress`
are used to update the `QBaseWindow`'s builtin progressbar.
"""
import os
import sys
qconcurrency_path = '/'.join(os.path.realpath(__file__).replace('\\','/').split('/')[:-2])
sys.path.insert(0, qconcurrency_path )

from   qconcurrency            import QBaseWindow
from   qconcurrency.threading_ import ThreadedTask, SoloThreadedTask
from   Qt                      import QtCore, QtWidgets
import six
import time



class MyMainWindow( QBaseWindow ):
    def __init__(self):
        QBaseWindow.__init__(self, title='My Window')

        self._sem_rendering = QtCore.QSemaphore(1)

        # using self.new_solotask() instead of
        # SoloThreadedTask adds the signals:
        #
        #    * add_progress
        #    * incr_progress
        #
        # which update this window's builtin progressbar
        #
        self._thread_loading = self.new_solotask(
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

        self._initui()

    def _initui(self):

        # Build Widgets
        layout     = QtWidgets.QVBoxLayout()
        self._list = QtWidgets.QListWidget()
        load_btn   = QtWidgets.QPushButton('load')

        # Position Widgets
        self.setLayout( layout )
        layout.addWidget( self._list )
        layout.addWidget( load_btn )

    def load(self):
        """
        Loads list with items from a separate thread.
        If load is already in progress, it will be cancelled
        before the new load request starts.
        """
        self._thread_loading.start()

    def clear(self):
        """
        Clears the QListWidget
        """
        self._list.clear()

    def _find_list_items(self, signalmgr=None ):
        """
        Adds 100 items to the list-widget,
        """
        signalmgr.add_progress.emit(101)

        signalmgr.clear.emit()
        signalmgr.incr_progress.emit(1)

        for i in range(100):
            signalmgr.handle_if_abort()   # check for a request-abort, and exit early

            # slow signals down, emitting one object at a time
            # so that job can be cancelled.
            # ( signals have no priority, once emitted,  )
            # ( you must wait for them all to be handled )
            self._sem_rendering.tryAcquire(1,5000)
            signalmgr.add_item.emit( str(i) )  # add an item to the list
            signalmgr.incr_progress.emit(1)

    def addItem(self, item):
        """
        Unecessarily waits .01 seconds (so you can see widget updating live),
        then adds the item to the list.
        """
        time.sleep(0.01)
        self._list.addItem(item)
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
        mylist = MyMainWindow()
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

