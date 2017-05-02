
#builtin
from   functools import partial
import time
#external
import unittest
from   Qt                      import QtCore, QtWidgets
import six
#internal
from   qconcurrency.testutils  import mock
from   qconcurrency.threading_ import *
from   qconcurrency            import QApplication

qapplication = QApplication()



class Test_ThreadedTask( unittest.TestCase ):
    def test_running_in_thread(self):

        hasrun_queue = six.moves.queue.Queue()
        threadpool   = QtCore.QThreadPool()


        def check_thread( ui_thread, hasrun_queue, signalmgr=None ):
            if QtCore.QThread.currentThread() == ui_thread:
                hasrun_queue.put(True)
            hasrun_queue.put(False)


        ui_thread = QtCore.QThread.currentThread()
        task = ThreadedTask(
            callback = check_thread,
            # args/kwds
            ui_thread    = QtCore.QThread.currentThread(),
            hasrun_queue = hasrun_queue,
        )
        task.start( threadpool=threadpool )


        # verify thread-test has run,
        # and that `check_thread` actually ran from a different thread
        threadpool.waitForDone()
        self.assertEqual( hasrun_queue.empty(), False )
        self.assertEqual( hasrun_queue.get(),   False )


    def test_job_abort(self):

        queue      = six.moves.queue.Queue()
        threadpool = QtCore.QThreadPool()

        def try_abort( signalmgr ):
            for i in range(100):
                signalmgr.handle_if_abort()
                time.sleep(0.01)

        def queue_put( queue, *args, **kwds ):
            queue.put( True )

        task = ThreadedTask( callback=try_abort )

        # (direct connection is unecessary when running within eventloop)
        task.signal('exception').connect( partial( queue_put, queue=queue ), QtCore.Qt.DirectConnection )
        task.start( threadpool=threadpool )
        task.request_abort()

        threadpool.waitForDone()
        self.assertEqual( queue.empty(), False )

    def test_signal_returned_noval(self):

        queue       = six.moves.queue.Queue()
        threadpool  = QtCore.QThreadPool()
        recv_signal = mock.Mock()

        def mycallback( signalmgr ):
            pass

        task = ThreadedTask(
            callback = mycallback,
        )

        # (direct connection is unecessary when running within eventloop)
        task.signal('returned').connect( recv_signal, QtCore.Qt.DirectConnection )
        task.start( threadpool=threadpool )

        threadpool.waitForDone()
        self.assertEqual( recv_signal.called, True )

    def test_signal_returned_val(self):

        queue       = six.moves.queue.Queue()
        threadpool  = QtCore.QThreadPool()
        recv_signal = mock.Mock()

        def mycallback( signalmgr ):
            return 'aaa'

        task = ThreadedTask(
            callback = mycallback,
            signals  = {'returned':str}
        )

        # (direct connection is unecessary when running within eventloop)
        task.signal('returned').connect( recv_signal, QtCore.Qt.DirectConnection )
        task.start( threadpool=threadpool )

        threadpool.waitForDone()
        recv_signal.assert_called_with( 'aaa' )


    def test_custom_signal_nodata(self):

        queue       = six.moves.queue.Queue()
        threadpool  = QtCore.QThreadPool()
        recv_signal = mock.Mock()

        def try_abort( signalmgr ):
            signalmgr.test.emit()

        task = ThreadedTask(
            callback = try_abort ,
            signals  = {'test':None},
        )

        # (direct connection is unecessary when running within eventloop)
        task.signal('test').connect( recv_signal, QtCore.Qt.DirectConnection )
        task.start( threadpool=threadpool )

        threadpool.waitForDone()
        recv_signal.assert_called()

    def test_custom_signal_single(self):

        queue       = six.moves.queue.Queue()
        threadpool  = QtCore.QThreadPool()
        recv_signal = mock.Mock()

        def try_abort( signalmgr ):
            signalmgr.test.emit('aaa')

        task = ThreadedTask(
            callback = try_abort ,
            signals  = {'test':str},
        )

        # (direct connection is unecessary when running within eventloop)
        task.signal('test').connect( recv_signal, QtCore.Qt.DirectConnection )
        task.start( threadpool=threadpool )

        threadpool.waitForDone()
        recv_signal.assert_called_with('aaa')

    def test_custom_signal_multi(self):

        queue       = six.moves.queue.Queue()
        threadpool  = QtCore.QThreadPool()
        recv_signal = mock.Mock()

        def try_abort( signalmgr ):
            signalmgr.test.emit('aaa','bbb')

        task = ThreadedTask(
            callback = try_abort ,
            signals  = {'test':(str,str)},
        )

        # (direct connection is unecessary when running within eventloop)
        task.signal('test').connect( recv_signal, QtCore.Qt.DirectConnection )
        task.start( threadpool=threadpool )

        threadpool.waitForDone()
        recv_signal.assert_called_with('aaa','bbb')

    def test_custom_signal_non_builtin(self):

        queue       = six.moves.queue.Queue()
        threadpool  = QtCore.QThreadPool()
        recv_signal = mock.Mock()

        def mycallback( signalmgr ):
            mutex = QtCore.QMutex()
            signalmgr.test.emit( mutex )

        def is_mutex( queue, mutex ):
            if isinstance( mutex, QtCore.QMutex ):
                queue.put(True)
                return
            queue.put(False)


        task = ThreadedTask(
            callback = mycallback,
            signals  = {'test': QtCore.QMutex}
        )

        # (direct connection is unecessary when running within eventloop)
        task.signal('test').connect( partial( is_mutex, queue ), QtCore.Qt.DirectConnection )
        task.start( threadpool=threadpool )

        threadpool.waitForDone()
        self.assertEqual( queue.empty(), False )
        self.assertEqual( queue.get(),   True )

    def test_async_signals(self):
        """
        verify slots are being fired as signals are emitted from other thread.
        difficult to test, since not in eventloop.
        """

        self.fail()



