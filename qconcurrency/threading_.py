#!/usr/bin/env python
"""
Name :          qconcurrency.threading_..py
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
from   numbers     import Number
import logging
import sys
import os
import uuid
import time
import importlib
#package
#external
from   Qt import QtCore, QtWidgets
import six
#internal
from   qconcurrency.exceptions_  import *

logger = logging.getLogger(__name__)
loc    = locals

__all__ = [
    'SignalManagerFactory',
    'ThreadedTask',
    'SoloThreadedTask',
]

def SignalManagerFactory( signals, queue_stop=None ):
    """
    Dynamically creates a :py:obj:`SignalManager` class
    with all requested signals.


    :py:obj:`SignalManager` objects are dynamically
    created :py:obj:`QtCore.QObject` designed to be handed
    off to a separate thread. They contain a variable
    number of signals, and the method `handle_if_abort`
    which checks the value of `self._abort_requested`

    Example:

        .. code-block:: python

            class SignalManager( QtCore.QObject ):
                returned  = QtCore.Signal()
                exception = QtCore.Signal()

                def handle_if_abort(self):
                    if self._abort_requested:
                        raise UserCancelledOperation()

    Args:
        signals (dict, optional): ``(ex: {signal_name:emitted datatype(s)} )``

            A dictionary of signal-names, and the datatypes
            they will emit.

            .. code-block:: python

                {
                    'update_status': None,        # update_status = QtCore.Signal()
                    'log_message':  str,          # log_message   = QtCore.Signal(str)
                    'add_item':     (int, str),   # add_item      = QtCore.Signal(int, str)
                }

        queue_stop (queue.Queue, optional):
            A queue that handles request-aborts. When
            :py:obj:`SignalManager.handle_if_abort` is run,
            if the queue contains this thread's assigned id,
            then this thread will be stopped.

    """

    if not isinstance( signals, MutableMapping ):
        raise RuntimeError(
            'Expected `signals` argument to be a dictionary of \n'
            'signal-names, and emit-datatypes \n'
        )


    # extend globals to include all types needed for signals
    def import_signal_datatype( _globals, datatype ):
        """
        Args:
            _globals (dict):
                A modified version of `globals` builtin, that will be used
                when defining class

            datatype (object):
                A python object, emitted by a signal.

        Returns:

            .. code-block:: python

                (
                    _globals, # globals() with datatype pkg imported
                    pkgname , # full importpath of datatype
                )

        """
        str_datatype = datatype.__name__

        if datatype.__module__ != '__builtin__':
            _globals[ datatype.__module__.split('.')[-1] ] = (
                importlib.import_module( datatype.__module__ )
            )
            str_datatype = '%s.%s' % (
                datatype.__module__.split('.')[-1],
                datatype.__name__,
            )
        return _globals, str_datatype




    _globals = globals()
    class_   = (
        'from Qt import QtCore \n'
        'class SignalManager( QtCore.QObject ):\n'
    )


    for signal in signals:

        # signals without a returntype
        if not signals[signal]:
            class_ += '    {signal} = QtCore.Signal() \n'.format(signal=signal)

        # signals with multiple returns
        elif isinstance( signals[signal], Iterable ):
            str_datatypes = []
            for datatype in signals[signal]:
                (_globals, str_datatype) = import_signal_datatype( _globals, datatype )
                str_datatypes.append( str_datatype )

            class_ += '    {signal} = QtCore.Signal({signal_datatypes})\n'.format(
                signal           = signal,
                signal_datatypes = ','.join(str_datatypes)
            )

        # single signal datatype
        else:
            (_globals, str_datatype) = import_signal_datatype( _globals, signals[signal] )
            class_ += '    {signal} = QtCore.Signal({datatype})\n'.format(
                signal   = signal,
                datatype = str_datatype,
            )

    # self._signals
    class_ += (
        '    def __init__(self, _id=None, signals=None, queue_stop=None ): \n'
        '        QtCore.QObject.__init__(self)               \n'
        '                                                    \n'
        '        self._id              = _id                 \n'
        '        self._queue_stop      = queue_stop          \n'
        '        self._abort_requested = False               \n'
        '        self._signals_arg     = signals             \n'
        '        self._signals         = {                   \n'
    )
    for signal in signals:
        class_ += '            "{signal}": self.{signal},\n'.format(signal=signal)
    class_ += '        }\n'

    # methods
    class_ += (
        '    def _request_abort(self):                                              \n'
        '        """                                                                \n'
        '        Private method that sets attr :py:attr:`_abort_requested`.         \n'
        '        Designed to be connected to a signal.                              \n'
        '        """                                                                \n'
        '        self._abort_requested = True                                       \n'
        '                                                                           \n'
        '    def handle_if_abort(self, msg=None):                                   \n'
        '        """                                                                \n'
        '        Checks if an abort has been requested. If so,                      \n'
        '        raises :py:obj:`UserCancelledOperation`                            \n'
        '                                                                           \n'
        '        Raises:                                                            \n'
        '            :py:obj:`UserCancelledOperation`                               \n'
        '        """                                                                \n'
        '        if not msg:                                                        \n'
        '            msg = ""                                                       \n'
        '                                                                           \n'
        '        # if self._request_abort() has been called                         \n'
        '        if self._abort_requested:                                          \n'
        '            raise UserCancelledOperation( msg )                            \n'
        '                                                                           \n'
        '                                                                           \n'
        '    def signals(self):                                                     \n'
        '        """                                                                \n'
        '        Returns a dictionary of signal-names, and the signal               \n'
        '        they represent.                                                    \n'
        '                                                                           \n'
        '        Returns:                                                           \n'
        '                                                                           \n'
        '            .. code-block:: python                                         \n'
        '                                                                           \n'
        '                {                                                          \n'
        '                    "returned":  QtCore.Signal(),                          \n'
        '                    "exception": QtCore.Signal(tuple)                      \n'
        '                    ...                                                    \n'
        '                }                                                          \n'
        '        """                                                                \n'
        '        return self._signals                                               \n'
    )



    _locals = locals()
    exec( class_, _globals, _locals )

    return _locals['SignalManager']()



class QSemaphoreLocker( QtCore.QObject ):
    """
    Mirrors the behaviour of :py:obj:`QtCore.QMutexLocker`, but instead of a mutex
    manages a :py:obj:`QtCore.QSemaphore` .


    Example:

        .. code-block:: python

            class MyClass( QtCore.QObject ):
                def __init__(self):
                    self._semaphore = QtCore.QSemaphore(5)

                def load(self):
                    locked = QSemaphoreLocker( self._semaphore, 3, 500 )

                    # ...
                    # when locked goes out of scope, 3x resource is released
                    # ...

                def load_again(self):

                    with QSemaphoreLocker( self._semaphore ):
                        # ...
                        # do these actions while 1x semaphore is locked
                        # ...

                    # .. semaphore resources no longer in use ..

    """
    def __init__(self, semaphore, n=1, timeout=-1 ):
        """

        Args:
            semaphore (QtCore.QSemaphore):
                The semaphore that you'd like to lock

            n (int, optional):
                The number of resources you would like to lock
                in the semaphore.

            timeout (int, optional):
                milliseconds you would like to wait for `n` resources
                to become available before failing :py:meth:`QtCore.QSemaphore.acquire`
                A :py:obj:`RuntimeError` will be raised.
        """
        QtCore.QObject.__init__(self)

        if not isinstance( semaphore, QtCore.QSemaphore ):
            raise TypeError((
                'expected `semaphore` argument to be of type `QtCore.QSemaphore` \n'
                'received type: %s'
                ) % str(type(semaphore))
            )


        self._semaphore = semaphore
        self._resources = n

        self.destroyed.connect(
            functools.partial(
                self._semaphore.unlock,
                self._resources,
            )
        )

        success = self._semaphore.tryAcquire( n, timeout )
        if not success:
            raise TimedOut(
                'waited timeout of %sms to acquire %s QSemaphore resources' % (
                    timeout, n)
            )

    def __enter__(self):
        pass

    def __exit__(self, err_type, err_msg, err_tb ):
        """
        On exit, releases all resources that were acquired
        """
        if all([ err_type, err_msg, err_tb ]):
            self._semaphore.release( self._resources )
            six.reraise( err_type, err_msg, err_tb )

        self._semaphore.release( self._resources )



class ThreadedTask( QtCore.QRunnable ):
    """
    Bundles a callback method, it's arguments, and a variable
    number of signals (with variable return-types) into a :py:obj:`QtCore.QRunnable`
    that can be safely queued in a :py:obj:`QtCore.QThreadPool`.

    Every callback method  must accept the keyword argument
    `signalmgr`. `signalmgr` is a :py:obj:`QtCore.QObject`
    that is instantiated with signals to communicate back with the UI
    thread, and the method :py:meth:`SignalManager.handle_if_abort`
    which should be run periodically in your `callback` method
    to handle user-abort requests (issued by :py:meth:`request_abort` ).



    Example:

        *Run function in QCoreApplication's :py:obj:`QtCore.QThreadPool`*

        Handling early-exit by periodically (at safe points)
        checking if :py:meth:`task.request_abort` has been run.

        .. code-block:: python

            def long_running_job( jobid, signalmgr=None ):
                for i in range(5):
                    signalmgr.handle_if_abort()   # exit early, if user-abort requested
                    time.sleep(1)
                print('finished job %s' % jobid )

            task = ThreadedTask(
                callable = long_running_job,
                jobid    = 1
            )
            task.start()


        *Create signals that can be used within the thread.*

        :py:obj:`QtCore.QRunnable` objects (which get used in a
        :py:obj:`QtCore.QThreadPool` ) cannot have signals attached to them.
        In order for this to work you must create a :py:obj:`QtCore.QObject`
        with the signals that can be passed to the thread. This all gets
        done behind the scenes with a :py:obj:`ThreadedTask` .

        .. code-block:: python

            def long_running_job( signalmgr=None ):
                signalmgr.log_message.emit('started job...')
                signalmgr.set_title.emit('My Title', 'my description')
                signalmgr.status_changed.emit()

            def printargs(*args):
                print( args )


            task = ThreadedTask(                      ### Roughly Equivalent to:
                callback = long_running_job,          #
                signals  = {                          #  class SignalManager( QtCore.QObject ):
                    'status_changed': None,           #      status_changed = QtCore.Signal()
                    'log_message':    str,            #      log_message    = QtCore.Signal(str)
                    'set_title':     (str,str),       #      set_title      = QtCore.Signal(str,str)
                },                                    #
            )                                         #
            task.signal('set_title').connect(   printargs )
            task.signal('log_message').connect( printargs )
            task.start()


        *Handle successful returns, and unhandled exceptions*

        :py:obj:`ThreadedTask` have builtin signals
        `returned`, and `exception`, that are emitted
        automatically. You may emit the output of your callback
        in `returned`, only if you  override the `returned`
        signal in the `signals` argument.

        .. code-blocK:: python

            def long_running_job( signalmgr=None ):
                pass

            def run_on_exit(*args,**kwds):
                pass


            task = ThreadedTask(
                callback = long_running_job,
            )
            task.signal('returned').connect(run_on_exit)
            task.signal('exception').connect(run_on_exit)
            task.start()

    See Also:

        * :py:obj:`qconcurrency.threading_.SignalManagerFactory`
        * :py:obj:`qconcurrency.threading_.SoloThreadedTask`

    """
    def __init__(self, callback, signals=None, *args, **kwds ):
        """
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
        QtCore.QRunnable.__init__(self)

        # Arguments
        self._callback = callback
        self._args     = args
        self._kwds     = kwds
        self._id       = None # used by SoloThreadedTask


        # Attributes
        self._signals  = {
            'returned':        None,
            'exception':       tuple,
            'abort_requested': None,
        }
        if signals:
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
            logger.error( 'Unhandled Exception occurred in thread: %s' % repr(exc_info) )
            self._signalmgr.exception.emit( tuple(exc_info) )

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
    this :py:obj:`SoloThreadedTask`) whenever a new thread is requested (and all must exit
    before the latest requested task is allowed to start ).

    This might be useful for methods that load or filter the contents
    of a widget.


    .. warning::

        If slot connected to one of this task's signals does not update
        UI until this thread exits, add the following line to the end of your slot.

        .. code-block:: python

            QtCore.QCoreApplication.instance().processEvents()


    Example:

        .. code-block:: python

            class MyList( QtWidgets.QListWidget ):
                def __init__(self):
                    self._thread_loading = SoloThreadedTask(
                        callback    = self._find_list_items,
                        signals     = {'add_item': str},
                        connections = {'add_item': [self.addItem] },
                    )

                def load(self):
                    #
                    # whenever `self.load` is called
                    # the last load will be cancelled,
                    # after which a new load process will start
                    #
                    self._thread_loading.start()

                def _find_list_items(self, signalmgr=None ):
                    for i in range(100):
                        signalmgr.handle_if_abort()   # check for a request-abort, and exit early
                        time.sleep(1)
                        signalmgr.add_item.emit( i )  # add an item to the list




    See Also:
        * :py:obj:`qconcurrency.threading_.ThreadedTask`

    """
    def __init__(self, callback, signals=None, connections=None, mutex_expiry=5000 ):
        """
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

            connections (dict, optional):
                Dictionary of signal-names, and a list of python-collables you
                would like to connect to the signal.

                .. code-block:: python

                    {
                        'add_item':     [ printargs, mylist.addItem ],
                        'add_progress': [ progbar.add_progress, ],
                        ...
                    }

            *args/**kwds:
                Any additional arguments/keyword-arguments are passed
                to the callback in :py:meth:`run`
        """
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

        self._connections = connections


        # locks
        self._mutex_loading    = QtCore.QMutex()

    def start(self, expiryTimeout=-1, threadpool=None, wait=False, *args,**kwds):
        """
        Creates/starts a new :py:obj:`ThreadedTask`, and cancels
        all other pending/running threads started by this
        :py:obj:`SoloThreadedTask` instance.
        """

        threadId = uuid.uuid4().hex

        task = ThreadedTask(
            callback = self._run,
            signals = self._signals,

            # args/kwds
            threadId = threadId,
            *args, **kwds
        )
        self._active_threads[ threadId ] = task.request_abort


        # setup all user-defined connections
        if self._connections:
            for signal_name in self._connections:
                for callback in self._connections[ signal_name ]:
                    task.signal( signal_name ).connect( callback )


        task.signal('thread_acquired_mutex').connect( self._set_active_threadId )
        task.signal('_thread_exit_').connect(         self._set_complete_threadId )

        task.start( expiryTimeout=expiryTimeout, threadpool=threadpool )


        if wait:
            elapsed = 0
            # wait for thread to lock
            while self._mutex_loading.tryLock(0):
                self._mutex_loading.unlock()
                time.sleep(0.05)
                elapsed += 0.05
            print( 'locked by thread' )


            # wait for thread to unlock
            while not self._mutex_loading.tryLock(0):
                if wait not in (True,False):
                    if elapsed >= wait:
                        raise TimedOut(
                            'waited %ss for job to complete without success' % elapsed
                        )

                time.sleep(0.05)
                elapsed += 0.05
                QtCore.QCoreApplication.instance().processEvents()

            self._mutex_loading.unlock()


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

    def stop(self, until_threadId=None, wait=None ):
        """
        Emits `request_abort` signal on all threads up-to (but not including)
        the target `until_threadId`. If `until_threadId` is not provided, all
        pending threads are killed.

        (threadIds will be automatically removed from attr :py:attr:`_active_threads`
        as they return, or raise unhandled exceptions).


        Args:
            wait (numbers.Number, optional):  ``(ex: None, -1, 100)``
                Optionally, wait *N* seconds for job to complete
                after requesting abort. If negative number, waits
                indefinitely. Waiting in the main UI thread will
                result in a deadlock.

        Raises
            * :py:obj:`TimedOut` if user set a wait time.
        """

        for active_threadId in self._active_threads:
            if active_threadId == until_threadId:
                return
            else:
                logger.debug('requesting abort on threadId: %s' % active_threadId )
                self._active_threads[ active_threadId ]()

        if wait:
            elapsed = 0
            while True:
                locked = self._mutex_loading.tryLock(0)

                # if lock is free, exit
                if locked:
                    self._mutex_loading.unlock()
                    break

                # if waited user-requested time, exit
                if elapsed > 0  and  elapsed >= wait:
                    raise TimedOut('waited %ss for thread to end' % elapsed)
                    break

                time.sleep(0.05)
                elapsed += 0.05

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

    def is_active(self):
        if self._active_threads:
            return True
        return False



if __name__ == '__main__':
    from qconcurrency import QApplication
    from Qt           import QtWidgets
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

        with QApplication():
            label = QtWidgets.QLabel('watch progress in terminal window..')
            label.show()
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
            signalmgr.print_txt.emit('test signal')
            for i in range(3):
                print( '[%s] thread step %s/3' % (thread_num, i+1) )
                signalmgr.handle_if_abort()
                time.sleep(1)
            print( '[%s] thread finished' % thread_num )

        def printtxt(msg):
            print(msg)


        with QApplication():
            label = QtWidgets.QLabel('watch progress in terminal window..')
            label.show()

            solotask = SoloThreadedTask(
                callback    = long_running_job,
                signals     = {'print_txt':str},
                connections = {'print_txt':[printtxt]},
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


