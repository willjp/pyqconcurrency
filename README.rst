
qconcurrency
============

This is simply a collection of tools for python bindings
of the Qt_ GUI library, that simplify running concurrent jobs.
I have built them specifically to address issues I commonly
run into (like needing to stop a *loading* thread automatically
when the user wants to interrupt it witha new load operation).

I am building this with the intention of it being a personal library,
but if you find it useful, please feel free to use and modify :).


See Sphinx documentation_ for more details.

.. _documentation: https://willjp.github.io/pyqconcurrency/





Notes
-----

* make sure to run tests using nose2_ -- using green_, or nose_ causes
  PyQt4/PyQt5 (and not PySide) to inconsistently crash (on different tests) with 
  ``SystemError: Objects/tupleobject.c:54: bad argument to internal function``



.. _Qt:    https://www.qt.io/
.. _nose2: https://github.com/nose-devs/nose2
.. _nose:  https://github.com/nose-devs/nose
.. _green: https://github.com/CleanCut/green


