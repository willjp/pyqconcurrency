#!/usr/bin/env python
"""
Name :          qconcurrency._threadifaces_.py
Created :       Apr 08, 2017
Author :        Will Pittman
Contact :       willjpittman@gmail.com
________________________________________________________________________________
Description :
________________________________________________________________________________
"""
#builtin
from __future__    import unicode_literals
from __future__    import absolute_import
from __future__    import division
from __future__    import print_function
from   collections import MutableMapping, Iterable, OrderedDict
import logging
import sys
import os
import uuid
#package
#external
from   Qt import QtCore, QtWidgets
import six
#internal
from   qconcurrency.exceptions_  import *

logger = logging.getLogger(__name__)
loc    = locals


def SignalManagerFactory( signals, queue_stop=None ):
    """
    Dynamically creates a :py:obj:`SignalManager` class
    with all required signals.
    """

    if not isinstance( signals, MutableMapping ):
        raise RuntimeError(
            'Expected `signals` argument to be a dictionary of \n'
            'signal-names, and emit-datatypes \n'
        )

    class_ = (
        'from Qt import QtCore \n'
        #'class SignalManager( SignalManager ):\n'
        'class SignalManager( QtCore.QObject ):\n'
    )


    for signal in signals:

        # signals without a returntype
        if not signals[signal]:
            class_ += '    {signal} = QtCore.Signal() \n'.format(signal=signal)

        # signals with multiple returns
        elif isinstance( signals[signal], Iterable ):
            class_ += '    {signal} = QtCore.Signal({signal_datatypes})\n'.format(
                signal           = signal,
                signal_datatypes = ','.join([ str(datatype.__name__) for datatype in signals[signal] ]),
            )
        else:
            class_ += '    {signal} = QtCore.Signal({datatype})\n'.format(
                signal   = signal,
                datatype = signals[signal].__name__,
            )

    # self._signals
    class_ += (
        '    def __init__(self, _id=None, queue_stop=None ): \n'
        '        QtCore.QObject.__init__(self)               \n'
        '                                                    \n'
        '        self._id              = _id                 \n'
        '        self._queue_stop      = queue_stop          \n'
        '        self._abort_requested = False               \n'
        '        self._signals         = {                   \n'
    )
    for signal in signals:
        class_ += '            "{signal}": self.{signal},\n'.format(signal=signal)
    class_ += '        }\n'

    # methods
    class_ += (
        '    def _request_abort(self):                                      \n'
        '        """                                                        \n'
        '        Private method that sets attr :py:attr:`_abort_requested`. \n'
        '        Designed to be connected to a signal.                      \n'
        '        """                                                        \n'
        '        self._abort_requested = True                               \n'
        '                                                                   \n'
        '    def handle_if_abort(self):                                     \n'
        '        """                                                        \n'
        '        Checks if an abort has been requested. If so,              \n'
        '        raises :py:obj:`UserCancelledOperation`                    \n'
        '                                                                   \n'
        '        Raises:                                                    \n'
        '            :py:obj:`UserCancelledOperation`                       \n'
        '        """                                                        \n'
        '                                                                   \n'
        '        # if self._request_abort() has been called                 \n'
        '        if self._abort_requested:                                  \n'
        '            raise UserCancelledOperation()                         \n'
        '                                                                   \n'
        '                                                                   \n'
        '        # for SoloThreadedTask                                     \n'
        '        if self._queue_stop and self._id:                          \n'
        '            while not self._queue_stop.empty():                    \n'
        '               stop_id = self._queue_stop.get()                    \n'
        '               if stop_id == self._id:                             \n'
        '                   raise UserCancelledOperation()                  \n'
        '                                                                   \n'
        '    def signals(self):                                             \n'
        '        """                                                        \n'
        '        Returns a dictionary of signal-names, and the signal       \n'
        '        they represent.                                            \n'
        '                                                                   \n'
        '        Returns:                                                   \n'
        '                                                                   \n'
        '            .. code-block:: python                                 \n'
        '                                                                   \n'
        '                {                                                  \n'
        '                    "returned":  QtCore.Signal(),                  \n'
        '                    "exception": QtCore.Signal(tuple)              \n'
        '                    ...                                            \n'
        '                }                                                  \n'
        '        """                                                        \n'
        '        return self._signals                                       \n'
    )



    _locals = locals()
    exec( class_, globals(), _locals )

    return _locals['SignalManager']()



class ThreadedTask( QtCore.QRunnable ):
    """
    Bundles a callback method, it's arguments, and a variable
    number of signals (with variable return-types) into a :py:obj:`QtCore.QRunnable`
    that can be safely queued in a :py:obj:`QtCore.QThreadPool`.

    Threads can be easily cancelled (if for instance a user
    changes their mind, and wants to do something else).



    Args:
        callback (callable):
            A function, method, or class that you would like to run in
            a separate thread.

        signals (dict, optional):
            Dictionary of signal-names, and the datatypes they will emit.
            Signals defined here will override any default signals.

            .. code-block:: python

                {
                    # signal-name #  # datatype #   # equivalent-to #

                    'add_item':       (int,str),    #: QtCore.Signal(int,str)
                    'add_progress':   int,          #: QtCore.Signal(int)
                    'returned':       None,         #: QtCore.Signal()
                }

        *args/**kwds:
            Any additional arguments/keyword-arguments are passed
            to the callback in :py:meth:`run`

    """
    def __init__(self, callback, signals=None, *args, **kwds ):
        QtCore.QRunnable.__init__(self)

        # Arguments
        self._callback = callback
        self._args     = args
        self._kwds     = kwds
        self._id       = None # used by SoloThreadedTask

        if signals == None:
            signals = {}

        # Attributes
        self._signals  = {
            'returned':        None,
            'exception':       tuple,
            'abort_requested': None,
            'add_progress':    int,
            'incr_progress':   int,
        }
        self._signals.update( signals )


        self._signalmgr = SignalManagerFactory( self._signals )

    def run(self):
        """
        Runs ``callback( *args, **kwds )`` in a separate thread. This method
        will be called automatically by the :py:obj:`QtCore.QThreadPool`
        when queued (see :py:meth:`start`)

        If an unhandled exception is raised during the callback's execution,
        the signal *exception* is called. Otherwise the signal *returned*
        is emitted when the method completes.

        If you desire to catch the return-value of the callback, simply define
        the expected return-value for it in the argument `signals`.

        .. code-block:: python

            task = ThreadedTask(
                callback = mycallback,
                signals  = {'returned': (int,int)},  #: mycallback is now expected to return 2x integers
            )
        """
        try:
            retval = self._callback( signalmgr=self._signalmgr, *self._args, **self._kwds )

            if not self._signals['returned']:
                self._signalmgr.returned.emit()
            else:
                self._signalmgr.returned.emit( retval )

        except:
            exc_info = sys.exc_info()
            self._signalmgr.exception.emit( exc_info )
            six.reraise( *exc_info )

    def start(self, expiryTimeout=-1, threadpool=None ):
        """
        Queues this thread in a :py:obj:`QtCore.QThreadPool`
        (by default :py:obj:`QtCore.QThreadPool.globalInstance()` )

        Args:
            expiryTimeout (int, optional):
                Thread that unused for N milliseconds are considered expired
                and will exit. By default, no exipiryTimeout is set ``(-1)``.

            threadpool (QtCore.QThreadPool, optional):
                By default, this :py:obj:`ThreadedTask` will be queued in the
                QCoreApplication's global threadpool. If you would prefer to assign
                another, you may specify it here.
        """
        if not threadpool:
            threadpool = QtCore.QThreadPool.globalInstance()

        threadpool.start( self, expiryTimeout )

    def signalmgr(self):
        """
        Returns :py:obj:`SignalManager` instance (QObject that will be
        passed to separate thread, and stores all signals the thread will
        use to communicate back to the UI thread.)
        """
        return self._signalmgr

    def signal(self, signal_name):
        """
        Returns one of the :py:obj:`QtCore.Signal` s defined in `signals`.
        See documentation in :py:meth:`__init__`.
        """
        return getattr( self._signalmgr, signal_name )

    def request_abort(self,*args,**kwds):
        """
        Runs :py:meth:`SignalManager._request_abort` .
        (your callback will still need to periodically run
        :py:meth:`SignalManager.handle_if_abort` at safe points
        to exit).
        """
        logger.warning('Abort Requested for `ThreadedTask`: %s' % repr(self))
        self._signalmgr._request_abort()



class SoloThreadedTask( QtCore.QObject ):
    """
    :py:obj:`ThreadedTask` that cancels all of it's running/pending threads (started by
    this :py:obj:`SoloThreadedTask`) whenever a new thread is requested.

    This might be useful for loading tasks such as a method that loads or filters
    a widget's contents.
    """
    def __init__(self, callback, signals=None, mutex_expiry=5000 ):
        QtCore.QObject.__init__(self)

        # Args
        self._callback = callback
        self._mutex_expiry       = mutex_expiry
        self._active_threads     = OrderedDict()  # { uuid : request_abort(method) }

        self._thread_with_mutex = None # uuid.uuid4().hex of thread holding `self._mutex_loading`
                                       # ( continues to hold Id after thread  exits        )
                                       # ( to prevent race-conditions                      )
                                       # ( (who handled `returned/exception` signal first) )

        self._signals = {
            'thread_acquired_mutex': str,         # emits uuid assigned to thread holding mutex
            '_thread_exit_'        : str,         # uuid
        }
        if signals:
            self._signals.update( signals )


        # locks
        self._mutex_loading    = QtCore.QMutex()

    def start(self, expiryTimeout=-1, threadpool=None, *args,**kwds):
        """
        Creates/starts a new :py:obj:`ThreadedTask`, and cancels
        all other pending/running threads started by this
        :py:obj:`SoloThreadedTask` instance.
        """

        threadId = uuid.uuid4().hex

        task = ThreadedTask(
            callback = self._run,
            signals  = self._signals,

            # args/kwds
            threadId = threadId,
            *args, **kwds
        )
        task.signal('thread_acquired_mutex').connect( self._set_active_threadId,   QtCore.Qt.DirectConnection )
        task.signal('_thread_exit_').connect(         self._set_complete_threadId, QtCore.Qt.DirectConnection )

        self._active_threads[ threadId ] = task.request_abort

        task.start( expiryTimeout=expiryTimeout, threadpool=threadpool )

    def _run(self, threadId=None, signalmgr=None, *args, **kwds ):
        """
        This is the method that is run in a separate thread.

            * manages/waits for `self._mutex_loading`
            * cancels all pending threads
            * calls your callback method
        """

        if not self._mutex_loading.tryLock():
            logger.debug('Waiting for loading mutex to be released: %s' % threadId )
            self.stop( until_threadId=threadId )
            self._mutex_loading.tryLock( self._mutex_expiry )


        logger.debug('mutex acquired by threadId: %s' % threadId)
        signalmgr.thread_acquired_mutex.emit( threadId )

        retval = None

        try:
            retval = self._callback(
                signalmgr = signalmgr,
                *args, **kwds
            )
        except:
            signalmgr._thread_exit_.emit( threadId )
            self._mutex_loading.unlock()
            six.reraise( *sys.exc_info() )

        signalmgr._thread_exit_.emit( threadId )
        self._mutex_loading.unlock()
        return retval

    def stop(self, until_threadId=None ):
        """
        Emits `request_abort` signal on all threads up-to (but not including)
        the target `until_threadId`. If `until_threadId` is not provided, all
        pending threads are killed.

        (threadIds will be automatically removed from attr :py:attr:`_active_threads`
        as they return, or raise unhandled exceptions).
        """

        for active_threadId in self._active_threads:
            if active_threadId == until_threadId:
                return
            else:
                logger.debug('requesting abort on threadId: %s' % active_threadId )
                self._active_threads[ active_threadId ]()

    def _set_active_threadId(self, threadId):
        """
        Reports back the UI thread, informing it which thread was
        last to hold the :py:attr:`_mutex_loading`.

        Args:
            threadId (str)
                A string containing a UUID (:py:attr:`uuid.uuid4.hex`)
        """
        self._thread_with_mutex = threadId

    def _set_complete_threadId(self, threadId):
        """
        Remove all threadIds from `active_threadIds` up until
        the thread that signaled indicating it was finished.
        (removing discontinued will remove a lot of clutter)
        """

        if threadId in self._active_threads:
            self._active_threads.pop( threadId )




if __name__ == '__main__':
    import time
    import supercli.logging
    supercli.logging.SetLog(lv=10)

    def test_threadedtask():

        def long_running_job( thread_num, signalmgr=None ):
            print( 'thread started (%s)' % thread_num )
            for i in range(3):
                signalmgr.handle_if_abort()
                time.sleep(1)
            print( 'job finished (%s)' % thread_num )


        for i in range(5):
            task = ThreadedTask(
                callback   = long_running_job,
                # args/kwds
                thread_num = i,
            )
            task.start()

    def test_solo_threadedtask():
        def long_running_job( thread_num, signalmgr=None ):
            print( '[%s] thread started'  % thread_num )
            for i in range(3):
                print( '[%s] thread step %s/3' % (thread_num, i+1) )
                signalmgr.handle_if_abort()
                time.sleep(1)
            print( '[%s] thread finished' % thread_num )


        solotask = SoloThreadedTask(
            callback = long_running_job,
        )

        # every 1s, cancel current job with
        # a new job.
        for i in range(5):
            solotask.start( thread_num=i+1 )
            time.sleep(1)

    def runtests():
        #test_threadedtask()
        test_solo_threadedtask()

    runtests()

