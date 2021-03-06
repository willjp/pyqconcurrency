#!/usr/bin/env python
"""
Name :          qconcurrency.widgets._progressbar_.py
Created :       Apr 17, 2017
Author :        Will Pittman
Contact :       willjpittman@gmail.com
________________________________________________________________________________
Description :   ProgressBar, that can be updated from a separate thread.
________________________________________________________________________________
"""
#builtin
from __future__    import unicode_literals
from __future__    import absolute_import
from __future__    import division
from __future__    import print_function
from   collections import Iterable
import functools
import uuid
import copy
import logging
import threading
#external
from Qt            import QtWidgets
#internal
from qconcurrency.threading_  import ThreadedTask, SoloThreadedTask

#!TODO: http://stackoverflow.com/questions/7108715/how-to-show-hide-a-child-qwidget-with-a-motion-animation

logger = logging.getLogger(__name__)


class _ProgressSoloThreadedTask( SoloThreadedTask ):
    """
    customized :py:obj:`qconcurrency.threading_.SoloThreadedTask` that
    assigns a new jobid for each thread it starts, and each thread's progress
    is measured entirely independently.

    This way, there is no race-condition where cancelling one thread can knock out
    progress on *all* threads.
    """
    def __init__(self, progressbar, callback, signals=None, connections=None, mutex_expiry=5000 ):
        self._progressbar = progressbar
        SoloThreadedTask.__init__(self,
            callback     = callback,
            signals      = signals,
            connections  = connections,
            mutex_expiry = mutex_expiry,
        )

    def start(self, expiryTimeout=-1, threadpool=None, wait=False, *args, **kwds ):
        """
        Wraps :py:meth:`qconcurrency.threading_.SoloThreadedTask.start` ,
        adding signal-connections so that they update a progressbar.

        See Also:

            * :py:meth:`qconcurrency.threading_.SoloThreadedTask.start`
        """

        jobid = uuid.uuid4().hex

        connections = self._connections.copy()
        if not connections:
            connections = {}

        progbar_connections = {
            'incr_progress' : functools.partial( self._progressbar.incr_progress, jobid=jobid ),
            'add_progress'  : functools.partial( self._progressbar.add_progress,  jobid=jobid ),
            'returned'      : functools.partial( self._progressbar._handle_return_or_abort, jobid=jobid ),
            'exception'     : functools.partial( self._progressbar._handle_return_or_abort, jobid=jobid ),
        }

        for signal in progbar_connections:
            if signal in connections:
                connections[ signal ].append( progbar_connections[signal] )
            else:
                connections[ signal ] = [ progbar_connections[signal] ]


        SoloThreadedTask.start(self,
                           expiryTimeout = expiryTimeout,
                           threadpool    = threadpool,
                           wait          = wait,
                           _connections  = connections,
                           *args,**kwds
                       )



class ProgressBar( QtWidgets.QWidget ):
    """
    A ProgressBar designed to track progress of several threads,
    that is hidden automatically whenever all threads have exited
    (by unhandled exception, or return).

    Each thread is assigned it's own `jobid`, so that it's progress
    is tracked entirely independently of all other pending tasks.
    (my hope is that if errors appear in total-calculated progress in the
    codebase, this will lessen the appearance of an error for the user - each
    thread's progress being set to 100% once it exits).
    """
    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        self._progress = {}         # { jobid: {'total':10, 'current':3} }
        self._cancelled_jobids = [] # rolling log of cancelled jobids (so later unhandled progress is ignored)

        self._progressbar = None    # the ProgressBar Widget
        self.setHidden(True)

        self._initui()

    def _initui(self):

        # Create Widgets
        layout = QtWidgets.QHBoxLayout()
        self._progressbar = QtWidgets.QProgressBar()
        self._reset_btn   = QtWidgets.QPushButton('reset progress')

        # Position Widgets
        self.setLayout( layout )
        layout.addWidget( self._progressbar )
        layout.addWidget( self._reset_btn )

        # Connections
        self._reset_btn.clicked.connect( self.reset )

    def add_progress(self, amount, jobid=None):
        """
        Adds to the total number of required steps
        required to complete.
        """

        with threading.Lock():
            if jobid in self._cancelled_jobids:
                return

            if jobid not in self._progress:
                self._progress[ jobid ] = {'total':amount, 'current':0}
            else:
                self._progress[ jobid ]['total'] += amount

            self.refresh_progress()
            self.setHidden(False)

    def refresh_progress(self):
        """
        ReCalculates current/total progress, and updates the progressbar
        """

        with threading.Lock():
            total_progress   = 0
            current_progress = 0
            for jobid in list(self._progress.keys()):
                job_progress = self._progress[ jobid ]

                if   jobid in self._cancelled_jobids:
                    self._progress.pop(jobid)

                elif job_progress['current'] == job_progress['total']:
                    self._progress.pop(jobid)

                else:
                    total_progress   += self._progress[ jobid ]['total']
                    current_progress += self._progress[ jobid ]['current']

            self._progressbar.setMaximum( total_progress   )
            self._progressbar.setValue(   current_progress )

            if total_progress <= current_progress:
                self.setHidden(True)

    def incr_progress(self, amount, jobid):
        """
        Completes a particular number of steps for
        a particular jobid.
        """

        with threading.Lock():
            if jobid in self._cancelled_jobids:
                return

            if amount == None:
                amount = 1

            if jobid not in self._progress:
                return

            self._progress[ jobid ]['current'] += amount
            self.refresh_progress()

    def reset(self, jobid=None ):
        """
        If not `jobid`, sets all required progress-steps back to 0.
        Otherwise, removes all required progress associated with that
        jobid.
        """

        with threading.Lock():
            if not jobid:
                self._progress = {}
                self._progressbar.reset()

            elif jobid in self._progress:
                self._progress.pop( jobid )

            self.refresh_progress()

    def new_task(self, callback, signals=None, *args, **kwds ):
        """
        Creates a new :py:obj:`ThreadedTask` object, adding
        signals to it so that it can update this :py:obj:`ProgressBar`.

        :py:obj:`ThreadedTask` objects are most suitable for
        producer/consumer patterns (multiple threads running at once),
        and no thread depends on another.

        See also:
            * :py:obj:`ThreadedTask`
            * :py:obj:`SoloThreadedTask`
            * :py:meth:`ProgressBar.new_solotask`
        """

        jobid = uuid.uuid4().hex

        # assign signals
        default_signals = {
            'incr_progress': int,
            'add_progress':  int,
        }

        if signals:
            default_signals.update( signals )


        # create task
        task = ThreadedTask(
            callback = callback,
            signals  = default_signals,
            *args, **kwds
        )


        # Connections
        task.signal('incr_progress').connect(
            functools.partial( self.incr_progress, jobid=jobid )
        )
        task.signal('add_progress').connect(
            functools.partial( self.add_progress, jobid=jobid )
        )
        task.signal('returned').connect(
            functools.partial( self._handle_return_or_abort, jobid=jobid )
        )
        task.signal('exception').connect(
            functools.partial( self._handle_return_or_abort, jobid=jobid )
        )

        return task

    def new_solotask(self, callback, signals=None, connections=None, mutex_expiry=5000 ):
        """
        Creates a new :py:obj:`SoloThreadedTask` object, adding
        signals to it so that it can update this :py:obj:`ProgressBar`.
        """

        jobid = uuid.uuid4().hex

        # assign signals
        default_signals = {
            'incr_progress': int,
            'add_progress':  int,
        }
        if signals:
            default_signals.update( signals )

        # assign connections
        default_connections = {}
        if connections:
            for signal in connections:
                if signal in default_connections:
                    if isinstance( connections[ signal ], Iterable ):
                        for _callable in connections[ signal ]:
                            default_connections[ signal ].append( _callable )
                    else:
                        _callable = connections[ signal ]
                        default_connections[ signal ].append( _callable )
                else:
                    default_connections[ signal ] = connections[ signal ]

        # create task
        solotask = _ProgressSoloThreadedTask(
            progressbar  = self,
            callback     = callback,
            signals      = default_signals,
            connections  = default_connections,
            mutex_expiry = mutex_expiry,
        )

        return solotask

    def _handle_return_or_abort(self, *args,**kwds):
        with threading.Lock():

            if 'jobid' in kwds:

                if kwds['jobid']:
                    self.reset( jobid=kwds['jobid'] )

                self._cancelled_jobids.append( kwds['jobid'] )

                # when there are more than 50x entries,
                # prune the tracked jobids
                if len(self._cancelled_jobids) > 50:
                    self._cancelled_jobids.pop(0)

            self.refresh_progress()




if __name__ == '__main__':
    from   qconcurrency import QApplication, Fake
    from   Qt           import QtWidgets, QtCore, QtGui
    import supercli.logging
    import time
    supercli.logging.SetLog(lv=20)


    def update_progbar( start_wait=0, signalmgr=None ):
        if not signalmgr:
            signalmgr = Fake()

        signalmgr.add_progress.emit(5)
        time.sleep( start_wait )

        for i in range(5):
            signalmgr.handle_if_abort()
            time.sleep(0.2)
            signalmgr.incr_progress.emit(1)
        print('done')


    with QApplication():
        win = QtWidgets.QWidget()
        lyt = QtWidgets.QVBoxLayout()
        bar = ProgressBar()
        win.setLayout(lyt)
        lyt.addWidget(bar)

        win.show()

        solotask = bar.new_solotask(
            callback = update_progbar,
        )
        solotask.start( start_wait=0   )

        # wait before starting next job,
        # keeping eventloop alive so progress can be seen
        for i in range(2):
            time.sleep(0.2)
            QtCore.QCoreApplication.instance().processEvents()

        solotask.start( start_wait=0.5 )
        solotask.start()
        solotask.start()


