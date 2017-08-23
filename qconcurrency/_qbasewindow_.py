#!/usr/bin/env python
"""
Name :          qconcurrency._qbasewindow_.py
Created :       Apr 17, 2017
Author :        Will Pittman
Contact :       willjpittman@gmail.com
________________________________________________________________________________
Description :   Window that comes packaged with a progressbar,
                and a way of creating ThreadedTasks.
________________________________________________________________________________
"""
#builtin
from   __future__    import unicode_literals
from   __future__    import absolute_import
from   __future__    import division
from   __future__    import print_function
from   collections   import Iterable
import uuid
import functools
import logging
import threading
#external
from   Qt import QtCore, QtWidgets
import six
#internal
from   qconcurrency.exceptions_   import *
from   qconcurrency.threading_    import ThreadedTask, SoloThreadedTask
from   qconcurrency.widgets       import ProgressBar
from   qconcurrency._fake_        import Fake

logger = logging.getLogger(__name__)


class QBaseWindow( QtWidgets.QWidget ):
    def __init__(self, title=None ):
        QtWidgets.QWidget.__init__(self)
        self._title  = title
        self._layout = None


        # Build Widgets
        # =============
        layout = QtWidgets.QVBoxLayout()
        self._mainlayout_container = QtWidgets.QVBoxLayout()
        self._mainwidget           = QtWidgets.QWidget()
        self._progressbar          = ProgressBar()


        # Position Widgets
        # ================
        QtWidgets.QWidget.setLayout(self, layout)
        layout.addLayout( self._mainlayout_container )
        self._mainlayout_container.addWidget( self._mainwidget )
        layout.addWidget( self._progressbar )

        # Widget Attrs
        # ============
        if self._title:
            self.setWindowTitle(self._title)

    def setLayout(self, layout):
        self._mainwidget.setLayout( layout )

    def new_task(self, callback, signals=None, *args, **kwds):
        task = self._progressbar.new_task(
            callback = callback,
            signals  = signals,
            *args, **kwds
        )
        return task

    def new_solotask(self, callback, signals=None, connections=None, mutex_expiry=5000):

        solotask = self._progressbar.new_solotask(
            callback     = callback,
            signals      = signals,
            connections  = connections,
            mutex_expiry = mutex_expiry,
        )
        return solotask



class _ProgressSoloThreadedTask_QBaseObject( SoloThreadedTask ):
    """
    SoloThreadedTask subclass that fakes an interface to a progressbar
    for a QBaseObject. If a progressbar is not available in the parent-widget-hierarchy
    of the QBaseObject (if it is even a widget), then the signals will not be
    connected to anything.


    QBaseObjects do not necessarily become widgets, and even
    if they do they are not necessarily always going to be parented to
    a :py:obj:`QBaseWindow`.

    Whenever a SoloThreadedTask is started from here, it checks
    to see if the :py:obj:`QBaseObject` has a parent, and if that parent
    has a `progressbar` method. If all of the stars line up, that window's
    progressbar will be used by the `add_progress` and `incr_progress` signals
    available on the :py:obj:`SoloThreadedTask` s :py:obj:`SignalManager`.

    """
    def __init__(self, qbaseobject, callback, signals=None, connections=None, mutex_expiry=5000):
        """
        Args:
            qbaseobject (QBaseObject):
                The QBaseObject instance this is attached to. Whenever the task
                is started, it will be checked for a parent window/progressbar.
        """
        self._qbaseobject = qbaseobject
        SoloThreadedTask.__init__(self,
            callback     = callback,
            signals      = signals,
            connections  = connections,
            mutex_expiry = mutex_expiry,
        )

    def start(self, expiryTimeout=-1, threadpool=None, wait=False, *args, **kwds ):
        """
        Looks for/connects the progressbar.
        """

        jobid = uuid.uuid4().hex

        # check if this QBaseObject has a parent window,
        # and if that window has a method called `progressbar`
        # (presumably yielding a progressbar)
        progressbar = None
        if hasattr( self._qbaseobject, 'window' ):
            if hasattr( self._qbaseobject.window(), 'progressbar' ):
                progressbar = self._qbaseobject.window().progressbar()


        # default arguments
        connections = self._connections.copy()
        if not connections:
            connections = {}

        if progressbar:
            progbar_connections = {
                'incr_progress' : functools.partial( progressbar.incr_progress, jobid=jobid ),
                'add_progress'  : functools.partial( progressbar.add_progress,  jobid=jobid ),
                'returned'      : functools.partial( progressbar._handle_return_or_abort, jobid=jobid ),
                'exception'     : functools.partial( progressbar._handle_return_or_abort, jobid=jobid ),
            }
        else:
            progbar_connections = {}


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



class QBaseObject( object ):
    def new_task(self, callback, signals=None, *args, **kwds):

        # assign signals
        default_signals = {
            'incr_progress': int,
            'add_progress':  int,
        }

        if signals:
            default_signals.update( signals )

        task = ThreadedTask(
            callback = callback,
            signals  = default_signals,
            *args, **kwds
        )

        return task

    def new_solotask(self, callback, signals=None, connections=None, mutex_expiry=5000):

        # assign signals
        default_signals = {
            'incr_progress': int,
            'add_progress':  int,
        }
        default_connections = {}

        if signals:
            default_signals.update( signals )

        if connections:
            for signal in connections:
                if signal in default_connections:
                    if isinstance( connections[signal], Iterable ):
                        default_connections[ signal ].extend( connections[signal] )
                    else:
                        default_connections[ signal ].append( connections[signal] )
                else:
                    default_connections[ signal ] = connections[signal]


        solotask = _ProgressSoloThreadedTask_QBaseObject(
            qbaseobject  = self,
            callback     = callback,
            signals      = default_signals,
            connections  = default_connections,
            mutex_expiry = mutex_expiry,
        )

        return solotask





if __name__ == '__main__':
    #internal
    import functools
    import time
    #external
    from   Qt    import QtWidgets
    import supercli.logging
    #internal
    from   qconcurrency import QApplication, Fake
    supercli.logging.SetLog(lv=10)

    def test_qbasewindow():

        def long_job( signalmgr=None ):
            if not signalmgr:
                signalmgr = Fake()

            signalmgr.add_progress.emit(5)

            for i in range(5):
                signalmgr.handle_if_abort()
                time.sleep(0.3)
                signalmgr.incr_progress.emit(1)



        with QApplication():
            win = QBaseWindow(title='test title')

            # add arbitrary widget
            layout = QtWidgets.QVBoxLayout()
            btn    = QtWidgets.QPushButton('test button')
            win.setLayout(layout)
            layout.addWidget(btn)

            def run_long_job(win):
                task = win.new_task( long_job )
                task.start()

            win.show()

            # connections
            btn.clicked.connect( functools.partial( run_long_job, win ) )

    def runtests():
        test_qbasewindow()

    runtests()

