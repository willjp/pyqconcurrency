
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
            model.item(0,0).child(0,0).text(),
            '10'
        )

    def test_consistenthier__toplevelitems(self):
        model = DictModel(
            columns = ['A','B','C'],
        )
        row = model.add_row( 1, {'A':2,'B':3,'C':4} )

        # 3x ways of accessing info
        self.assertEqual( model.item(0,0).text(), '1' )
        self.assertEqual( model.item(0,1).text(), '2' )
        self.assertEqual( model.item(0,2).text(), '3' )
        self.assertEqual( model.item(0,3).text(), '4' )

        self.assertEqual( model[1].columnval('A'), '2' )
        self.assertEqual( model[1].columnval('B'), '3' )
        self.assertEqual( model[1].columnval('C'), '4' )

        self.assertEqual( row.columnval('A'), '2' )
        self.assertEqual( row.columnval('B'), '3' )
        self.assertEqual( row.columnval('C'), '4' )

    def test_consistenthier__nesteditems(self):
        model = DictModel(
            columns = ['A','B','C'],
        )
        row = model.add_row( 1, {'A':2,'B':3} )
        row.add_child( 11, {'A':12,'B':13})

        index = model.item(0,0).child(0,0).index()

        self.assertEqual( model.itemFromIndex(index).text(), '11' )
        self.assertEqual( model.itemFromIndex(index.sibling(0,1)).text(), '12' )
        self.assertEqual( model.itemFromIndex(index.sibling(0,2)).text(), '13' )

        self.assertEqual( model[1][11].text(), '11' )
        self.assertEqual( model[1][11].columnval('A'), '12' )
        self.assertEqual( model[1][11].columnval('B'), '13' )

