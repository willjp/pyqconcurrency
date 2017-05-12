
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

        def queue_put( *args, **kwds):
            queue.put( True )

        task = ThreadedTask( callback=try_abort )

        # (direct connection is unecessary when running within eventloop)
        task.signal('exception').connect( queue_put, QtCore.Qt.DirectConnection )
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



class Test_SoloThreadedTask( unittest.TestCase ):
    def test_stop_method(self):
        """
        task should be interrupted before `_callback`
        completes - so queue should be empty.
        """

        queue_finished = six.moves.queue.Queue()

        def _callback( queue_finished, signalmgr=None ):
            for i in range(15):
                signalmgr.handle_if_abort()
                time.sleep(0.1)
            queue_finished.put(True)


        task = SoloThreadedTask(
            callback = _callback,
        )
        task.start( queue_finished=queue_finished )

        task.stop()
        self.assertEqual( queue_finished.empty(), True )

    def test_interrupted(self):
        """
        Despite that 3x tasks are started at essentially
        the same time, only the last task completes, so the
        queue should only contain a single item.
        """

        queue_finished = six.moves.queue.Queue()
        threadpool     = QtCore.QThreadPool()

        def _callback( queue_finished, signalmgr=None ):
            for i in range(10):
                signalmgr.handle_if_abort()
                time.sleep(0.05)
            queue_finished.put(True)


        task = SoloThreadedTask(
            callback = _callback,
        )
        task.start( queue_finished=queue_finished, threadpool=threadpool )
        task.start( queue_finished=queue_finished, threadpool=threadpool )
        task.start( queue_finished=queue_finished, threadpool=threadpool )


        threadpool.waitForDone()
        self.assertEqual( queue_finished.qsize(), 1 )

    def test_interrupted_with_wait(self):
        """
        Despite that 20x tasks are started at essentially
        the same time, with wait=True, they should all complete.
        """

        queue_finished = six.moves.queue.Queue()
        threadpool     = QtCore.QThreadPool()

        def _callback( queue_finished, signalmgr=None ):
            for i in range(1):
                signalmgr.handle_if_abort()
                time.sleep(0.005)
            queue_finished.put(True)


        task = SoloThreadedTask(
            callback = _callback,
        )
        for i in range(10):
            task.start(
                queue_finished = queue_finished,
                threadpool     = threadpool,
                wait           = True,
            )

        threadpool.waitForDone()
        self.assertEqual( queue_finished.qsize(), 10 )

    def test_start_wait__false(self):
        """
        Run SoloThreadedTask in separate thread, do not wait
        in main UI thread for completion.

        NOTE: This test is technically a race-condition.
        """
        queue_finished = six.moves.queue.Queue()
        threadpool     = QtCore.QThreadPool()

        def _callback( queue_finished, signalmgr=None ):
            for i in range(3):
                signalmgr.handle_if_abort()
                time.sleep(0.05)
            queue_finished.put(True)


        task = SoloThreadedTask(
            callback = _callback,
        )
        task.start(
            queue_finished = queue_finished,
            threadpool     = threadpool,
            wait           = False,
        )
        self.assertEqual( queue_finished.qsize(), 0 )
        threadpool.waitForDone()

    def test_start_wait__true(self):
        """
        wait for task to finish in UI thread.
        """
        queue_finished = six.moves.queue.Queue()
        threadpool     = QtCore.QThreadPool()

        def _callback( queue_finished, signalmgr=None ):
            for i in range(3):
                signalmgr.handle_if_abort()
                time.sleep(0.05)
            queue_finished.put(True)


        task = SoloThreadedTask(
            callback = _callback,
        )
        task.start(
            queue_finished = queue_finished,
            threadpool     = threadpool,
            wait           = True,
        )
        self.assertEqual( queue_finished.qsize(), 1 )
        threadpool.waitForDone()

    def test_isactive(self):
        queue_finished = six.moves.queue.Queue()
        threadpool     = QtCore.QThreadPool()

        def _callback( queue_finished, signalmgr=None ):
            for i in range(3):
                signalmgr.handle_if_abort()
                time.sleep(0.05)
            queue_finished.put(True)


        task = SoloThreadedTask(
            callback = _callback,
        )
        task.start(
            queue_finished = queue_finished,
            threadpool     = threadpool,
        )
        self.assertEqual( task.is_active(), True )
        threadpool.waitForDone()

    def test_isinactive(self):
        queue_finished = six.moves.queue.Queue()
        threadpool     = QtCore.QThreadPool()

        def _callback( queue_finished, signalmgr=None ):
            for i in range(3):
                signalmgr.handle_if_abort()
                time.sleep(0.05)
            queue_finished.put(True)


        task = SoloThreadedTask(
            callback = _callback,
        )
        task.start(
            queue_finished = queue_finished,
            threadpool     = threadpool,
        )
        threadpool.waitForDone()
        self.assertEqual( task.is_active(), False )



class Test_QSemaphoreLocker( unittest.TestCase ):
    def test_lose_scope_lock(self):
        """
        when `locked` var loses scope, semaphore is unlocked.
        """
        semaphore = QtCore.QSemaphore(1)

        def testlock( semaphore ):
            locked = QSemaphoreLocker( semaphore, 1 )
            self.assertEqual( semaphore.tryAcquire(1,0), False )

        testlock( semaphore )
        self.assertEqual( semaphore.tryAcquire(1,0), True )
        semaphore.release(1)

    def test_with_exit_lock(self):
        """
        when context-manager ends, lock is released.
        """
        semaphore = QtCore.QSemaphore(1)

        with QSemaphoreLocker( semaphore ):
            self.assertEqual( semaphore.tryAcquire(1,0), False )

        self.assertEqual( semaphore.tryAcquire(1,0), True )
        semaphore.release(1)



