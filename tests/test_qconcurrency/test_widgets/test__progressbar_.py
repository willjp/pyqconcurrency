
#builtin
from   functools import partial
import time
#external
import unittest
from   Qt                      import QtCore, QtWidgets
import six
#internal
from   qconcurrency.testutils             import mock
from   qconcurrency.widgets._progressbar_ import *
from   qconcurrency                       import QApplication

qapplication = QApplication()


class Test_ProgressBar(unittest.TestCase):
    def test_progress_arithmetic(self):

        with mock.patch.object( ProgressBar, 'setHidden' ) as _setHidden:
            bar = ProgressBar()
            bar.add_progress(  5, jobid='aaa' )
            bar.add_progress(  5, jobid='aaa' )
            bar.incr_progress( 2, jobid='aaa' )
            bar.incr_progress( 2, jobid='aaa' )

            total   = bar._progress['aaa']['total']
            current = bar._progress['aaa']['current']

            self.assertEqual( current, 4 )
            self.assertEqual( total,  10 )

    def test_progress_total(self):

        with mock.patch.object( ProgressBar, 'setHidden' ) as _setHidden:
            bar = ProgressBar()
            bar.add_progress( 5, jobid='aaa')
            bar.add_progress( 5, jobid='bbb')
            bar.incr_progress( 1, jobid='aaa')
            bar.incr_progress( 1, jobid='bbb')

            self.assertEqual( bar._progressbar.maximum(), 10 )
            self.assertEqual( bar._progressbar.value(),   2  )

    def test_premature_completion(self):

        with mock.patch.object( ProgressBar, 'setHidden' ) as _setHidden:
            bar = ProgressBar()
            bar.add_progress( 5, jobid='aaa')
            bar.add_progress( 5, jobid='bbb')
            bar.incr_progress( 1, jobid='aaa')
            bar.incr_progress( 1, jobid='bbb')
            bar.reset( 'bbb' )

            self.assertEqual( bar._progressbar.maximum(), 5 )
            self.assertEqual( bar._progressbar.value(),   1  )

    def test_new_task(self):

        with mock.patch.object( ProgressBar, 'setHidden' ) as _setHidden:
            with mock.patch.object( ProgressBar, 'reset' ) as _reset:
                def set_progress( signalmgr=None,*args,**kwds ):
                    signalmgr.add_progress.emit(5)
                    signalmgr.incr_progress.emit(1)

                threadpool = QtCore.QThreadPool()

                bar  = ProgressBar()
                task = bar.new_task(
                    callback = set_progress,
                )
                task.start( threadpool=threadpool )
                threadpool.waitForDone()

                while qapplication.hasPendingEvents():
                    qapplication.processEvents()

                self.assertEqual( bar._progressbar.value(), 1 )
                self.assertEqual( bar._progressbar.maximum(), 5 )


    def test_new_solotask(self):

        with mock.patch.object( ProgressBar, 'setHidden' ) as _setHidden:
            with mock.patch.object( ProgressBar, 'reset' ) as _reset:
                def set_progress( signalmgr=None, *args, **kwds ):
                    signalmgr.add_progress.emit(5)
                    signalmgr.incr_progress.emit(1)

                threadpool = QtCore.QThreadPool()

                bar  = ProgressBar()
                task = bar.new_solotask(
                    callback = set_progress,
                )
                task.start( threadpool=threadpool )
                threadpool.waitForDone()

                while qapplication.hasPendingEvents():
                    qapplication.processEvents()

                self.assertEqual( bar._progressbar.value(), 1 )
                self.assertEqual( bar._progressbar.maximum(), 5 )






