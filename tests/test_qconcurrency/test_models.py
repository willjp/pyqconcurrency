
#builtin
from   functools import partial
import time
#external
import unittest
from   Qt                      import QtCore, QtWidgets
import six
#internal
from   qconcurrency.testutils     import mock
from   qconcurrency.models        import *
from   qconcurrency               import QApplication

qapplication = QApplication()


class Test_DictModel( unittest.TestCase ):
    def test_consistenthier__defaultcolumns(self):

        model = DictModel(
            columns = ['A','B','C']
        )
        model.add_row( 1 )

        self.assertEqual( model.item(0,0).text(), '1',)
        for i in range(1,3):
            self.assertEqual( model.item( 0,i ).text(), '')


    def test_consistenthier__defaultcolumns_nested(self):
        model = DictModel(
            columns = ['A','B','C'],
        )
        row = model.add_row( 1 )
        row.add_child( 10 )

        self.assertEqual(
            model.itemFromIndex( QtCore.QModelIndex(0,0, model.item(0,0)) ).text(),
            '10'
        )

