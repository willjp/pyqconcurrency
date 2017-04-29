
#builtin
from functools import partial
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
            signals  = {'returned':bool},
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


    def test_job_runs(self):
        pass

    def test_job_abort(self):
        pass


    def test_signal_returned_noval(self):
        pass

    def test_signal_returned_val(self):
        pass

    def test_signal_exception(self):
        pass



    def test_custom_signals(self):
        pass

    def test_custom_signal_nodata(self):
        pass

    def test_custom_signal_single(self):
        pass

    def test_custom_signal_multi(self):
        pass

    def test_custom_signal_non_builtin(self):
        pass

    def test_async_signals(self):
        pass




