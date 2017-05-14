from qconcurrency import QApplication
from qconcurrency.threading_ import SoloThreadedTask
from Qt import QtWidgets, QtCore
import six
import supercli.logging
import time
supercli.logging.SetLog(lv=10)


with QApplication():
    wid = QtWidgets.QPushButton('close me')
    wid.show()

    queue_finished = six.moves.queue.Queue()
    threadpool     = QtCore.QThreadPool()
    threadpool.setMaxThreadCount(3)

    def _callback( queue_finished, signalmgr=None ):
        for i in range(30):
            signalmgr.handle_if_abort()
            time.sleep(0.05)
        queue_finished.put(True)
        print('finished')


    task = SoloThreadedTask(
        callback = _callback,
    )
    task.start( queue_finished=queue_finished, threadpool=threadpool )
    task.start( queue_finished=queue_finished, threadpool=threadpool )
    task.start( queue_finished=queue_finished, threadpool=threadpool )



