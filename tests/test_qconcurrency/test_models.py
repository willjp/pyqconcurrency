
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

    def test_consistenthier__columns_lv0(self):
        model = DictModel(
            columns = ['A','B'],
        )
        row = model.add_row( 1, {'A':2,'B':3})
        self.assertEqual( model.columns( level=0 ), ['id','A','B'] )
        self.assertEqual( row.level(), 0 )

    def test_consistenthier__columns_lv1(self):
        model = DictModel(
            columns = ['A','B'],
        )
        row   = model.add_row( 1, {'A':2,'B':3})
        child = row.add_child( 10, {'A':4,'B':5})

        self.assertEqual( model.columns( level=1 ), ['id','A','B'] )
        self.assertEqual( child.level(), 1 )

    def test_consistenthier__columnindex_lv0(self):
        model = DictModel(['A','B'])
        row   = model.add_row( 1, {'A':2,'B':3})

        # id is always 0
        self.assertEqual( model.column_index( level=0, column='A'),  1 )
        self.assertEqual( model.column_index( level=0, column='B'),  2 )

    def test_consistenthier__columnindex_lv1(self):
        model = DictModel(['A','B'])
        row   = model.add_row( 1,  {'A':2,'B':3})
        child = row.add_child( 10, {'A':20,'B':30})

        # id is always 0
        self.assertEqual( model.column_index( level=1, column='A'),  1 )
        self.assertEqual( model.column_index( level=1, column='B'),  2 )


    def test_nestedhier__defaultcolumns(self):

        model = DictModel(
            columns   = {'root':('A','B'), 'sub':('C','D')},
            hierarchy = ('root','sub'),
        )
        model.add_row( 1 )

        self.assertEqual( model.item(0,0).text(), '1',)
        for i in range(1,2):
            self.assertEqual( model.item( 0,i ).text(), '')

    def test_nestedhier__defaultcolumns_nested(self):

        model = DictModel(
            columns   = {'root':('A','B'), 'sub':('C','D')},
            hierarchy = ('root','sub')
        )
        root  = model.add_row( 1 )
        sub   = root.add_child( 10 )

        self.assertEqual( model.item(0,0).child(0,0).text(), '10' )
        for i in range(1,2):
            self.assertEqual( model.item(0,0).child(0,i).text(), '')

    def test_nestedhier__toplevelitems(self):
        model = DictModel(
            columns   = {'root':('A','B'), 'sub':('C','D')},
            hierarchy = ('root','sub')
        )
        root = model.add_row(   1, {'A':2,'B':3} )

        # 3x ways of accessing info (root)
        self.assertEqual( model.item(0,0).text(), '1' )
        self.assertEqual( model.item(0,1).text(), '2' )
        self.assertEqual( model.item(0,2).text(), '3' )

        self.assertEqual( model[1].columnval('A'), '2' )
        self.assertEqual( model[1].columnval('B'), '3' )

        self.assertEqual( root.columnval('A'), '2' )
        self.assertEqual( root.columnval('B'), '3' )

    def test_nestedhier__nesteditems(self):
        model = DictModel(
            columns   = {'root':('A','B'), 'sub':('C','D')},
            hierarchy = ('root','sub')
        )
        root = model.add_row(   1, {'A':2,'B':3} )
        sub  = root.add_child( 10, {'C':20,'D':30})

        # 3x ways of accessing info (child)
        self.assertEqual( model.item(0,0).child(0,0).text(), '10' )
        self.assertEqual( model.item(0,0).child(0,1).text(), '20' )
        self.assertEqual( model.item(0,0).child(0,2).text(), '30' )

        self.assertEqual( model[1][10].columnval('C'), '20' )
        self.assertEqual( model[1][10].columnval('D'), '30' )

        self.assertEqual( sub.columnval('C'), '20' )
        self.assertEqual( sub.columnval('D'), '30' )

    def test_nestedhier__columns_lv0(self):

        model = DictModel(
            columns   = {'root':('A','B'), 'sub':('C','D')},
            hierarchy = ('root','sub'),
        )
        root = model.add_row( 1 )

        # test as int
        self.assertEqual( model.columns(level=0),            ['id','A','B'] )
        # test as str
        self.assertEqual( model.columns(level='root'),       ['id','A','B'] )
        # test from row
        self.assertEqual( model.columns(level=root.level()), ['id','A','B'] )

    def test_nestedhier__columns_lv1(self):

        model = DictModel(
            columns   = {'root':('A','B'), 'sub':('C','D')},
            hierarchy = ('root','sub'),
        )
        root = model.add_row( 1 )
        sub  = root.add_child( 10 )

        # test as int
        self.assertEqual( model.columns(level=1),            ['id','C','D'] )
        # test as str
        self.assertEqual( model.columns(level='sub'),        ['id','C','D'] )
        # test from row
        self.assertEqual( model.columns(level=sub.level()),  ['id','C','D'] )

    def test_nestedhier__columnindex_lv0(self):
        model = DictModel(
            columns   = {'root':('A','B'), 'sub':('C','D')},
            hierarchy = ('root','sub'),
        )
        root  = model.add_row(   1, {'A':2, 'B':3}  )

        # id is always 0
        self.assertEqual( model.column_index( level=0, column='A'),  1 )
        self.assertEqual( model.column_index( level=0, column='B'),  2 )

        self.assertEqual( model.column_index( level='root', column='A'),  1 )
        self.assertEqual( model.column_index( level='root', column='B'),  2 )

        self.assertEqual( model.column_index( level=root.level(), column='A'),  1 )
        self.assertEqual( model.column_index( level=root.level(), column='B'),  2 )

    def test_nestedhier__columnindex_lv1(self):
        model = DictModel(
            columns   = {'root':('A','B'), 'sub':('C','D')},
            hierarchy = ('root','sub'),
        )
        root  = model.add_row(   1, {'A':2, 'B':3}  )
        sub   = root.add_child( 10, {'C':20,'D':30})

        # id is always 0
        self.assertEqual( model.column_index( level=1, column='C'),  1 )
        self.assertEqual( model.column_index( level=1, column='D'),  2 )

        self.assertEqual( model.column_index( level='sub', column='C'),  1 )
        self.assertEqual( model.column_index( level='sub', column='D'),  2 )

        self.assertEqual( model.column_index( level=sub.level(), column='C'),  1 )
        self.assertEqual( model.column_index( level=sub.level(), column='D'),  2 )


    def test_removerow(self):
        model = DictModel(['A','B'])
        row1  = model.add_row( 1, {'A':21,'B':31})
        row2  = model.add_row( 2, {'A':22,'B':32})
        row3  = model.add_row( 3, {'A':23,'B':33})
        row4  = model.add_row( 4, {'A':24,'B':34})

        model.removeRow( 3 )

        removed_rowitem = model.item(3,0)
        self.assertEqual( removed_rowitem, None )
        self.assertEqual( model.rowCount(), 3 )
        self.assertEqual( set(model.keys()), set(['1','2','4']) )

    def test_clear(self):
        model = DictModel(['A','B'])
        row   = model.add_row(    1,{'A':2 ,'B':3 })
        child = row.add_child( 10,{'A':20,'B':30})
        model.clear()

        self.assertEqual( model.rowCount(), 0 )



class Test_DictModelRow( unittest.TestCase ):
    def test_id(self):
        model = DictModel(['A','B'])
        row   = model.add_row( 1, {'A':10,'B':20})

        # ids are returned as their original datatype
        self.assertEqual( row.id(), 1 )

    def test_keys(self):
        model = DictModel(['A','B'])
        row   = model.add_row( 111, {'A':111,'B':2222})

        child = row.add_child( 1, {'A':11,'B':12})
        child = row.add_child( 2, {'A':21,'B':22})
        child = row.add_child( 3, {'A':31,'B':32})

        self.assertEqual( row.keys(), ['1','2','3'] )

    def test_consistenthier__level(self):
        model = DictModel(['A','B'])
        row   = model.add_row( 111, {'A':111,'B':2222})
        child = row.add_child( 1, {'A':11,'B':12})

        self.assertEqual( row.level(), 0 )
        self.assertEqual( child.level(), 1 )

    def test_nestedhier__level(self):
        model = DictModel(
            columns   = {'root':('A','B'), 'sub':('C','D')},
            hierarchy = ('root','sub'),
        )
        root  = model.add_row( 111, {'A':111,'B':2222})
        sub   = root.add_child( 1,   {'C':11,'D':12})

        self.assertEqual( root.level(), 'root' )
        self.assertEqual( sub.level(),  'sub'  )

    def test_delete(self):
        model = DictModel(['A','B'])

        root1  = model.add_row( 1, {'A':111,'B':2222})
        root2  = model.add_row( 2, {'A':111,'B':2222})
        root3  = model.add_row( 3, {'A':111,'B':2222})
        model[2].delete()

        self.assertEqual( model.keys(),  ['1','3'] )


