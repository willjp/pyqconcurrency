
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



!!Warning!!
------------

**This library was founded on a bad idea**. Instead, I've been reusing `QThread` s with worker `QObject` s. It is simpler,
more predictable, and better communicates what code is executing where. 

Note that when working this way, calling a worker method directly will cause the job to run in a separate thread, 
but the UI thread will hang while waiting for it to complete. If you call it with a signal instead, 
it will run truly asynchronously.


Here is an example:

.. code-block:: python

    from Qt import QtWidgets, QtCore

    class MyWorker(QtCore.QObject):
        """ any method on this worker-object will run in a separate thread """
        success = QtCore.Signal(str)
        fail = QtCore.Signal(str)

        def download(self, url):
            pass
        def upload(self, filepath, url):
            pass

    class MyWidget(QtWidgets.QWidget):
        """ our widget, which starts a qthread, and moves our worker to the thread """
        def __init__(self):
            super(MyWidget, self).__init__()

            self.thread = QtCore.QThread()
            self.worker = MyWorker()
            self.worker.moveToThread(self.thread)

            self.worker.success.connect(self.print_message)
            self.worker.fail.connect(self.print_message)

            self._initui()

        def _initui(self):
            # create widgets
            layout = QtWidgets.QVBoxLayout()
            download_btn = QtWidgets.QPushButton('download')
            upload_btn = QtWidgets.QPushButton('upload')

            # position widgets
            self.setLayout(layout)
            layout.addWidget(download_btn)
            layout.addWidget(upload_btn)

        def print_message(self, message):
            print(message)


Notes
-----

* make sure to run tests using nose2_ -- using green_, or nose_ causes
  PyQt4/PyQt5 (and not PySide) to inconsistently crash (on different tests) with 
  ``SystemError: Objects/tupleobject.c:54: bad argument to internal function``



.. _Qt:    https://www.qt.io/
.. _nose2: https://github.com/nose-devs/nose2
.. _nose:  https://github.com/nose-devs/nose
.. _green: https://github.com/CleanCut/green


