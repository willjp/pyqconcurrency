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

## keep track of all tasks with uuids.
## as each uuid is finished, or burned, remove it's
## remaining steps

class ProgressBar( QtWidgets.QProgressBar ):
    def __init__(self):
        QtWidgets.QProgressBar.__init__(self)

        self._progress = {}  # { jobid: {'total':10, 'current':3} }

    def add_progress(self, jobid, amount):
        """
        Adds to the total number of required steps
        required to complete.
        """
        if jobid not in self._progress:
            self._progress[ jobid ] = {'total':amount, 'current':0}
        else:
            self._progress[ jobid ]['total'] += amount

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

    def incr_progress(self, jobid, amount=1):
        """
        Completes a particular number of steps for
        a particular jobid.
        """
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

    def new_task(self, callback, signals, *args, **kwds ):
        """
        Creates a new :py:obj:`ThreadedTask` object, adding
        signals to it so that it can update this :py:obj:`ProgressBar`.
        """
        pass

    def new_solotask(self, callback, signals, mutex_expiry=5000 ):
        """
        Creates a new :py:obj:`SoloThreadedTask` object, adding
        signals to it so that it can update this :py:obj:`ProgressBar`.
        """
        pass




if __name__ == '__main__':
    pass

