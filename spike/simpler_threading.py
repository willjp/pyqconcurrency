#!/usr/bin/env python
"""
Name :          simpler_threading.py
Created :       Aug 23, 2017
Author :        Will Pittman
Contact :       willjpittman@gmail.com
________________________________________________________________________________
Description :   Very quickly restarting threads using this library
                has been causing crashes. I'm looking for a more
                normal way of using threads.
________________________________________________________________________________
"""
#builtin
from   __future__    import unicode_literals
from   __future__    import absolute_import
from   __future__    import division
from   __future__    import print_function
import sys
import os
#package
#external
#internal
from qconcurrency.exceptions_ import *

#!TODO: need a means of connecting the ThreadManager's set_stoprequest
#!      to a window - it would probably make the most sense for the
#!      current widget.window() to be connected to the ThreadWorker's
#!      stoprequest - ideally paired with a jobid so only the intended
#!      job is stopped.

class ThreadWorker( QtCore.QObject ):
    """
    This object is designed to be a base-class for classes managing
    related jobs to be run within QThreads.

    It has builtin methods to cancel jobs, or update a
    progressbar in a parent widget.
    """
    progress_added       = QtCore.Signal( int, object )
    progress_incremented = QtCore.Signal( int, object )
    progress_cleared     = QtCore.Signal( object )
    def __init__(self):
        QtCore.QObject.__init__(self)

        self._stoprequest       = True

        self._mutex_working     = QtCore.QMutex()
        self._mutex_stoprequest = QtCore.QMutex()

    def mutex_working(self):
        """
        Returns the `working` mutex.
        """
        return self._mutex_working


    def set_stoprequest(self, message=None):
        """
        Issues a stoprequest. Your threaded jobs should peridically run
        :py:meth:`handle_stoprequest`, to check for, and handle a stoprequest
        (exiting the job with the exception
        :py:obj:`qconcurrency.exceptions_.UserCancelledOperation` )

        Args:
            message (str, optional): ``(ex: 'Process Exit' )``
                Sets the message that will be displayed in the
                raised :py:obj:`qconcurrency.exceptions_.UserCancelledOperation`.
                If not set, 'User Cancelled Operation' will be printed.

        """
        lock = QtCore.QMutexLocker( self._mutex_stoprequest )
        if not message:
            message = 'User Cancelled Operation'
        self._stoprequest = message

    def clear_stoprequest(self):
        """
        Removes any current stoprequests.
        """
        lock = QtCore.QMutexLocker( self._mutex_stoprequest )
        self._stoprequest = False

    def handle_stoprequest(self):
        """
        Checks for a stoprequest, raising
        :py:obj:`qconcurrency.exceptions_.UserCancelledOperation`
        if one exists.

        Side Effect:
            raises :py:obj:`qconcurrency.exceptions_.UserCancelledOperation`
        """
        if self._stoprequest:
            lock = QtCore.QMutexLocker( self._mutex_stoprequest )
            raise UserCancelledOperation('User Cancelled Operation)


    def add_progress(self, amount, jobid=None):
        self.progress_added.emit( amount, jobid )

    def incr_progress(self):
        self.progress_incremented.emit( amount, jobid )

    def clear_progress(self):
        self.progress_cleared.emit( jobid )



class TheadManager( object ):
    """
    Can be used standalone, or as base-class for widgets.
    This object is an interface for a single :py:obj:`QtCore.QThread` ,
    and it's :py:obj:`qconcurrency.threading_.ThreadWorker` s.
    """
    def __init__(self, reference_widget=None, thread=None ):
        """
        Args:
            thread (QtCore.QThread, optional):
                Optionally, you may reuse an existing QThread
                rather than creating one for this object.

                I find this useful if I am wrapping one widget in another
                but their jobs are heavily related, sequential, or otherwise
                do not merit having a new thread of their own.

                If a thread is not provided, one will be created.
        """

        if thread:
            if not isinstance( thread, QtCore.QThread ):
                raise TypeError(
                    ('Expected `thread` argument to be of type QThread.'
                    'Received %s') % str(type(thread))
                )

        self._workers          = [] # keeps workers
        self._reference_widget = None


    def add_worker(self, worker):
        if not isinstance( worker, ThreadWorker ):
            raise TypeError(
                ('Expected `worker` to be of type '
                'qconcurrency.threading_.ThreadWorker. Received %s') % str(type(worker))
            )
        worker.progress_added.connect(       self._handle_progress_added   )
        worker.progress_incremented.connect( self._handle_progress_incremented  )
        worker.progress_cleared.connect(     self._handle_clear_progress )
        self._workers.append( worker )

    def set_reference_widget(self, widget):
        """
        If this widget has the method :py:obj:`window` ,
        it will be used to find the following items, and
        create the appropriate connections on the worker.

            * main-window's `progressbar`
            * main-window's `set_stoprequest`

        Setting a new reference-widget clears the last.
        If the reference-widget is ``None`` , this object
        will be used as the reference-widget.
        """
        self._reference_widget = widget

    def set_stoprequest(self, message=None):
        """
        Requests that all workers be stopped.
        See :py:meth:`qconcurrency.threading_.ThreadWorker.set_stoprequest`
        for more details.

        Args:
            message (str, optional): ``(ex: 'Process Exit' )``
                Sets the message that will be displayed in the
                raised :py:obj:`qconcurrency.exceptions_.UserCancelledOperation`.
                If not set, 'User Cancelled Operation' will be printed.
        """
        for worker in self._workers:
            worker.set_stoprequest( message )


    def _handle_progress_incremented(self, amount, jobid=None):
        pass

    def _handle_progress_added(self, amount, jobid=None):
        pass

    def _handle_progress_cleared(self, amount, jobid=None):
        pass



if __name__ == '__main__':
    pass


