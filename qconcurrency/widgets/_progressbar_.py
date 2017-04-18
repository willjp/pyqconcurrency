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
import functools
import uuid
#external
from Qt            import QtWidgets
#internal
from qconcurrency.threading  import ThreadedTask, SoloThreadedTask

#!TODO: http://stackoverflow.com/questions/7108715/how-to-show-hide-a-child-qwidget-with-a-motion-animation

## keep track of all tasks with uuids.
## as each uuid is finished, or burned, remove it's
## remaining steps

class ProgressBar( QtWidgets.QProgressBar ):
    def __init__(self):
        QtWidgets.QProgressBar.__init__(self)

        self._progress = {}  # { jobid: {'total':10, 'current':3} }
        self.setHidden(True)

    def add_progress(self, amount, jobid=None):
        """
        Adds to the total number of required steps
        required to complete.
        """

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

        total_progress   = 0
        current_progress = 0
        for jobid in self._progress.keys():
            total_progress   += self._progress[ jobid ]['total']
            current_progress += self._progress[ jobid ]['current']

            if current_progress == total_progress:
                self._progress.pop(jobid)

        self.setMaximum( total_progress   )
        self.setValue(   current_progress )

        if total_progress <= current_progress:
            self.setHidden(True)

    def incr_progress(self, amount, jobid):
        """
        Completes a particular number of steps for
        a particular jobid.
        """

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

        if not jobid:
            self._progress = {}
            QtWidgets.QProgressBar.reset(self)

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
            signals  = signals,
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

    def new_solotask(self, callback, signals=None, mutex_expiry=5000 ):
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


        # create task
        task = SoloThreadedTask(
            callback     = callback,
            signals      = signals,
            mutex_expiry = mutex_expiry,
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

    def _handle_return_or_abort(self, jobid=None, *args,**kwds):
        self.reset( jobid=jobid )



if __name__ == '__main__':
    pass

