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
from __future__    import unicode_literals
from __future__    import absolute_import
from __future__    import division
from __future__    import print_function
#external
from   Qt import QtCore, QtWidgets
import six
#internal
from   qconcurrency.exceptions_  import *
from   qconcurrency.threading    import ThreadedTask, SoloThreadedTask
from   qconcurrency.widgets      import ProgressBar

#!TODO: handle request-abort

class QBaseWindow( QtWidgets.QWidget ):
    def __init__(self, title=None ):
        QtWidgets.QWidget.__init__(self)
        self._title  = title
        self._layout = None

        self._initui()

    def _initui(self):
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

    def new_solotask(self, callback, signals=None, mutex_expiry=5000):
        solotask = self._progressbar.new_solotask(
            callback     = callback,
            signals      = signals,
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

