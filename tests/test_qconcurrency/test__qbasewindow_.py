
#builtin
from   functools import partial
import time
#external
import unittest
from   Qt                      import QtCore, QtWidgets
import six
#internal
from   qconcurrency.testutils     import mock
from   qconcurrency._qbasewindow_ import *
from   qconcurrency               import QApplication

qapplication = QApplication()


class Test_QBaseWindow( unittest.TestCase ):
    def test_assignlayout(self):
        """
        If unhandled exception, this is broken.
        """
        class MyWin( QBaseWindow ):
            pass

        win = MyWin()
        win.setLayout( QtWidgets.QVBoxLayout() )

    def test_new_task__customsignal(self):

        class MyWin( QBaseWindow ):
            def __init__(self):
                QBaseWindow.__init__(self)
                self.threadpool          = QtCore.QThreadPool()
                self.custom_signal_fired = False

            def start_task(self):
                task = self.new_task(
                    callback = self.run_task,
                    signals  = {'test_sig':None},
                )
                task.signal('test_sig').connect(self.check_custom_signal )
                task.start( threadpool=self.threadpool )

            def run_task(self, signalmgr=None ):
                signalmgr.test_sig.emit()

            def check_custom_signal(self):
                self.custom_signal_fired = True

        win = MyWin()
        win.start_task()
        win.threadpool.waitForDone()

        while qapplication.hasPendingEvents():
            qapplication.processEvents()

        self.assertEqual( win.custom_signal_fired, True )

    def test_new_task__progressbar(self):

        class MyWin( QBaseWindow ):
            def __init__(self):
                QBaseWindow.__init__(self)
                self.custom_signal_fired = False
                self.threadpool   = QtCore.QThreadPool()
                self._progressbar.incr_progress = mock.Mock()
                self._progressbar.add_progress = mock.Mock()

            def start_task(self):
                task = self.window().new_task(
                    callback = self.run_task,
                )
                task.start( threadpool=self.threadpool )

            def run_task(self, signalmgr=None ):
                signalmgr.add_progress.emit(1)
                signalmgr.incr_progress.emit(1)

        win = MyWin()
        win.start_task()
        win.threadpool.waitForDone()
        while qapplication.hasPendingEvents():
            qapplication.processEvents()

        self.assertEqual( win._progressbar.add_progress.called, True )
        self.assertEqual( win._progressbar.incr_progress.called, True )

    def test_new_task__kwds(self):
        class MyWin( QBaseWindow ):
            def __init__(self):
                QBaseWindow.__init__(self)
                self.custom_signal_fired = False
                self.threadpool   = QtCore.QThreadPool()

                self.a = None
                self.b = None
                self.c = None

            def start_task(self):
                task = self.window().new_task(
                    callback = self.run_task,

                    # test args/kwds
                    arg_a=1,
                    arg_b=2,
                    arg_c=3,
                )
                task.start( threadpool=self.threadpool )

            def run_task(self, arg_a, arg_b, arg_c, signalmgr=None ):
                if not any([ arg_a, arg_b, arg_c ]):
                    raise RuntimeError(
                        'args not submitted'
                    )

        win = MyWin()
        win.start_task()
        win.threadpool.waitForDone()
        while qapplication.hasPendingEvents():
            qapplication.processEvents()

    def test_new_solotask__customsignal(self):

        class MyWin( QBaseWindow ):
            def __init__(self):
                QBaseWindow.__init__(self)
                self.threadpool          = QtCore.QThreadPool()
                self.custom_signal_fired = False

                self._thread_load = self.new_solotask(
                    callback    = self.run_task,
                    signals     = {'test_sig':None},
                    connections = {'test_sig':[self.check_custom_signal]},
                )

            def start_task(self):
                self._thread_load.start( threadpool=self.threadpool )

            def run_task(self, signalmgr=None ):
                signalmgr.test_sig.emit()

            def check_custom_signal(self):
                self.custom_signal_fired = True

        win = MyWin()
        win.start_task()
        win.threadpool.waitForDone()

        while qapplication.hasPendingEvents():
            qapplication.processEvents()

        self.assertEqual( win.custom_signal_fired, True )

    def test_new_solotask__progressbar(self):

        class MyWin( QBaseWindow ):
            def __init__(self):
                QBaseWindow.__init__(self)
                self._progressbar.incr_progress = mock.Mock()
                self._progressbar.add_progress = mock.Mock()

                self._thread_load = self.new_solotask(
                    callback    = self.run_task,
                )

            def start_task(self, threadpool ):
                self._thread_load.start( threadpool=threadpool )

            def run_task(self, signalmgr=None, *args, **kwds ):
                signalmgr.add_progress.emit(1)
                signalmgr.incr_progress.emit(1)


        threadpool = QtCore.QThreadPool()
        win = MyWin()
        win.start_task( threadpool=threadpool )
        threadpool.waitForDone()

        while qapplication.hasPendingEvents():
            qapplication.processEvents()

        self.assertEqual( win._progressbar.add_progress.called, True )
        self.assertEqual( win._progressbar.incr_progress.called, True )

    def test_new_solotask__kwds(self):

        class MyWin( QBaseWindow ):
            def __init__(self):
                QBaseWindow.__init__(self)
                self.threadpool   = QtCore.QThreadPool()

                self._thread_load = self.new_solotask(
                    callback    = self.run_task,
                )

            def start_task(self):
                self._thread_load.start(
                    arg_a      = 1,
                    arg_b      = 2,
                    threadpool = self.threadpool
                )

            def run_task(self, arg_a, arg_b, signalmgr=None ):
                if not any([ arg_a, arg_b ]):
                    raise RuntimeError(
                        'missing arguments!'
                    )


        win = MyWin()
        win.start_task()
        win.threadpool.waitForDone()

        while qapplication.hasPendingEvents():
            qapplication.processEvents()




class Test_QBaseObject( unittest.TestCase ):
    def test_inherit_w_qwidget(self):
        """
        If QBaseObject is a QObject, it interferes
        in multi-inheritance situations with another
        child of QtCore.QObject.
        """
        class MyClass( QBaseObject, QtWidgets.QWidget ):
            def __init__(self):
                QBaseObject.__init__(self)
                QtWidgets.QWidget.__init__(self)
                self.threadpool      = QtCore.QThreadPool()
                self.signal_received = False

            def issue_signal(self):
                task = self.new_task(
                    callback = self._issue_signal,
                    signals  = {'my_signal':None},
                )
                task.signal('my_signal').connect( self._recv_signal )
                task.start( threadpool=self.threadpool )

            def _issue_signal(self, signalmgr=None ):
                signalmgr.my_signal.emit()

            def _recv_signal(self):
                self.signal_received = True


        myclass = MyClass()
        myclass.issue_signal()
        myclass.threadpool.waitForDone()

        while qapplication.hasPendingEvents():
            qapplication.processEvents()

        self.assertEqual( myclass.signal_received, True )

    def test_new_task__customsignal(self):

        class MyWin( QBaseObject, QtWidgets.QWidget ):
            def __init__(self):
                QBaseObject.__init__(self)
                QtWidgets.QWidget.__init__(self)
                self.threadpool          = QtCore.QThreadPool()
                self.custom_signal_fired = False

            def start_task(self):
                task = self.new_task(
                    callback = self.run_task,
                    signals  = {'test_sig':None},
                )
                task.signal('test_sig').connect(self.check_custom_signal )
                task.start( threadpool=self.threadpool )

            def run_task(self, signalmgr=None ):
                signalmgr.test_sig.emit()

            def check_custom_signal(self):
                self.custom_signal_fired = True

        win = MyWin()
        win.start_task()
        win.threadpool.waitForDone()

        while qapplication.hasPendingEvents():
            qapplication.processEvents()

        self.assertEqual( win.custom_signal_fired, True )

    def test_new_task__progressbar(self):

        class MyWin( QBaseWindow ):
            def __init__(self):
                QBaseWindow.__init__(self)
                self.custom_signal_fired = False
                self.threadpool   = QtCore.QThreadPool()

            def start_task(self):
                task = self.window().new_task(
                    callback = self.run_task,
                )
                task.start( threadpool=self.threadpool )

            def run_task(self, signalmgr=None ):
                signalmgr.add_progress.emit(1)
                signalmgr.incr_progress.emit(1)

        win = MyWin()
        win.start_task()
        win.threadpool.waitForDone()
        while qapplication.hasPendingEvents():
            qapplication.processEvents()

        # this will fail by unhandled exception if
        # the progress signals (unconnected to anything)
        # are not present

    def test_new_task__kwds(self):
        class MyWin( QBaseObject, QtWidgets.QWidget ):
            def __init__(self):
                QBaseObject.__init__(self)
                QtWidgets.QWidget.__init__(self)

                self.custom_signal_fired = False
                self.threadpool   = QtCore.QThreadPool()

                self.a = None
                self.b = None
                self.c = None

            def start_task(self):
                task = self.window().new_task(
                    callback = self.run_task,

                    # test args/kwds
                    arg_a=1,
                    arg_b=2,
                    arg_c=3,
                )
                task.start( threadpool=self.threadpool )

            def run_task(self, arg_a, arg_b, arg_c, signalmgr=None ):
                if not any([ arg_a, arg_b, arg_c ]):
                    raise RuntimeError(
                        'args not submitted'
                    )

        win = MyWin()
        win.start_task()
        win.threadpool.waitForDone()
        while qapplication.hasPendingEvents():
            qapplication.processEvents()

    def test_new_solotask__customsignal(self):

        class MyWin( QBaseObject, QtWidgets.QWidget ):
            def __init__(self):
                QBaseObject.__init__(self)
                QtWidgets.QWidget.__init__(self)
                self.threadpool          = QtCore.QThreadPool()
                self.custom_signal_fired = False

                self._thread_load = self.new_solotask(
                    callback    = self.run_task,
                    signals     = {'test_sig':None},
                    connections = {'test_sig':[self.check_custom_signal]},
                )

            def start_task(self):
                self._thread_load.start( threadpool=self.threadpool )

            def run_task(self, signalmgr=None ):
                signalmgr.test_sig.emit()

            def check_custom_signal(self):
                self.custom_signal_fired = True

        win = MyWin()
        win.start_task()
        win.threadpool.waitForDone()

        while qapplication.hasPendingEvents():
            qapplication.processEvents()

        self.assertEqual( win.custom_signal_fired, True )

    def test_new_solotask__progressbar(self):

        class MyWin( QBaseWindow ):
            def __init__(self):
                QBaseWindow.__init__(self)
                self.threadpool   = QtCore.QThreadPool()

                self._thread_load = self.new_solotask(
                    callback    = self.run_task,
                )

            def start_task(self):
                self._thread_load.start( threadpool=self.threadpool )

            def run_task(self, signalmgr=None ):
                signalmgr.add_progress.emit(1)
                signalmgr.incr_progress.emit(1)


        win = MyWin()
        win.start_task()
        win.threadpool.waitForDone()

        while qapplication.hasPendingEvents():
            qapplication.processEvents()

        # this will fail by unhandled exception if
        # the progress signals (unconnected to anything)
        # are not present

    def test_new_solotask__kwds(self):

        class MyWin( QBaseObject, QtWidgets.QWidget ):
            def __init__(self):
                QBaseObject.__init__(self)
                QtWidgets.QWidget.__init__(self)

                self.threadpool   = QtCore.QThreadPool()

                self._thread_load = self.new_solotask(
                    callback    = self.run_task,
                )

            def start_task(self):
                self._thread_load.start(
                    arg_a      = 1,
                    arg_b      = 2,
                    threadpool = self.threadpool
                )

            def run_task(self, arg_a, arg_b, signalmgr=None ):
                if not any([ arg_a, arg_b ]):
                    raise RuntimeError(
                        'missing arguments!'
                    )


        win = MyWin()
        win.start_task()
        win.threadpool.waitForDone()

        while qapplication.hasPendingEvents():
            qapplication.processEvents()



