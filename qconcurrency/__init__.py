#!/usr/bin/env python
"""
Name :          qconcurrency.__init__.py
Created :       Apr 08, 2017
Author :        Will Pittman
Contact :       willjpittman@gmail.com
________________________________________________________________________________
Description :   Tools to facilitate threading_ locks, mutexes, semaphores, etc.
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
from   qconcurrency.exceptions_   import *
from   qconcurrency._qbasewindow_ import QBaseWindow, QBaseObject
from   qconcurrency._fake_        import *

logger = logging.getLogger(__name__)
loc    = locals

__all__ = [
    'Fake',
    'QApplication',
    'QBaseWindow',
    'QBaseObject',
]



class QApplication( QtWidgets.QApplication ):
    """
    QApplication that can be used in a `with` statement, automatically
    exits when the last widget is deleted, or at the occurrence of an unhandled
    exception.

    Does nothing if a QApplication already exists
    ( Such as from within programs like Autodesk_Maya_, that will have already
    created a QApplication for you )

    .. _Autodesk_Maya: http://www.autodesk.com/products/maya/overview

    Example:

        .. code-block:: python

            with QApplication():
                btn = QtWidgets.QPushButton('boo')
                btn.show()

            # ...
            # when window is closed by user, QApplication exits
    """
    def __init__(self, PySequence=None, *args, **kwds):
        """
        Args:
            PySequence (tuple, optional):
                An optional tuple of arguments to pass to your
                QApplication's `__init__` method. ( uses :py:obj:`sys.argv`
                by default. )
        """
        qapp               = QtWidgets.QApplication.instance()
        self._created_qapp = False

        if not qapp:
            if not PySequence:
                PySequence = sys.argv
            super( QApplication, self ).__init__( PySequence, *args, **kwds )
            self._created_qapp = True

        else:
            self = qapp

    def __enter__(self):
        return self

    def __exit__(self, err_type, err_val, err_tb ):
        """
        If this is not python running in mayagui,
        kill the QApplication on error or close.

        (killing maya's QApplication crashes maya!)
        """
        if err_type or err_val or err_tb:
            #if not _is_mayagui():
            #    self.exit()
            six.reraise( err_type, err_val, err_tb )

        if self._created_qapp:
            sys.exit( self.exec_() )




if __name__ == '__main__':
    import time
    import supercli.logging
    supercli.logging.SetLog(lv=10)

