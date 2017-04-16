#!/usr/bin/env python
"""
Name :          qconcurrency/_modelview_.py
Created :       Apr 14, 2017
Author :        Will Pittman
Contact :       willjpittman@gmail.com
________________________________________________________________________________
Description :   A collection of utilities to help working with modelviews
________________________________________________________________________________
"""
#builtin
from __future__    import unicode_literals
from __future__    import absolute_import
from __future__    import division
from __future__    import print_function
#external
from Qt            import QtGui, QtCore
#internal

#!NOTE: this idea will not work, because you cannot nest
#!      QAbstractItemModels. There is one QAbstractItemModel at the top,
#!      and then everything under it is a QAbstractItem.
#!
#!      It is then the items that should have this interface?

#! items by the model itself

class DictModel( QtGui.QStandardItemModel ):
    """
    A TreeModel, to facilitate nesting TreeModels.

    Rows are reffered to as dictionary keys (database Ids).
    They provide access to other child :py:obj:`DictModel` s.

    Each :py:obj:`DictModel` can also refer to it's column-values
    by name.


    Example:

        .. code-block:: python

            (id)  | name   | path              | code  |
            '201' | 'test' | '/path/to/file1'  | 'AAA' |
            '202' | 'test2'| '/path/to/file2'  | 'BBB' |

               (id) | subitem   | code  |
               300  | 'subtest' | '111' |


        .. code-block:: python

            ## Build DictModel
            model = DictModel(['name','path','code'])
            model.set_columns( 201, {'name':'test',  'path':'/path/to/file1', 'code':'AAA'} )
            model.set_columns( 202, {'name':'test2', 'path':'/path/to/file2', 'code':'BBB'} )

            model[ 202 ] = DictModel(['subitem','code'])


            ## Access items on model
            model.name( 201 )
            >>> 'test'

            model.path( 202 )
            >>> '/path/to/file2'

            model[ 202 ].subitem( 300 )
            >>> 'subtest'

    """
    def __init__(self, columns ):
        """
        Args:
            columns (tuple):
                A tuple of column-names. The order of columns
                determines the rows that items will be assigned
                in the Model.
        """
        QtGui.QStandardItemModel.__init__(self)
        self._columns           = columns
        self._defaultcolumnvals = {}      # all columns for new rows are initialized as ``None``

        for key in self._columns:
            self._defaultcolumnvals[ key ] = None

    def __getitem__(self, key):
        pass

    def __setitem__(self, key, model=None ):
        try:
            index = self.item( self._column_index(key), 0 ).index()
        except:
            self.appendRow([key])
            index = self.set_columns( key, self._default_columnvals )

    def columns(self, key):
        """
        Returns a dictionary with each of this key's row's  keys/values
        (skipping the first, which is always the Id `key`)
        """
        index = self._column_index(key)

        columnvals = {}
        for i in range(len(self._columns)):
            columnvals[ self._columns[i] ] = self.item( index.row(), i+1 )

        return columnvals

    def set_columns(self, key, items):
        """
        Edits the columns for a particular row
        in the modelview.

        Args:
            key:
                A hashable item, likely your database-id

            items (dict):
                A dict of items to assign to the DictModel.
                This dict may only contain items that were
                defined in :py:meth:`__init__` s argument
                `columns`, but does not need to contain every
                key from `columns`.

        Returns:
            Model-Index of the row we just added columns to
        """
        index = self._column_index(key)

        columnvals = {}
        item_keys  = set(items.keys())
        col_keys   = set(self._columns)

        if not item_keys.issubset( col_keys ):
            bad_keys = item_keys.difference( col_keys )
            raise KeyError(
                'Keys %s do not exist in `columns` set in __init__' % ','.join(bad_keys)
            )

        for colkey in item_keys:
            column_index = self._columns.index( colkey )
            widget       = QtGui.QStandardItem( str(items[colkey] ) )
            self.setItem( index, column_index, widget )

        return self.item(index,0).index()

    def _column_index(self,key):
        """
        Returns Model Index for row containing key
        """
        for i in range(self.columnCount()):
            if self.itemAt(i).text() == str(key):
                return self.itemAt(i).index()
        raise KeyError(
            'key "%s" does not exist in DictModel' % key
        )

    def appendItem(self, key):
        item = DictModelItem( key=key )
        QtGui.QStandardItemModel.appendItem( item )
        item.set_columns( self._defaultcolumnvals )
        return item

    def set_child_columns(self, item, columnvals):

        columnvals = {}
        val_keys  = set(columnvals.keys())
        col_keys   = set(self._columns)

        if not val_keys.issubset( col_keys ):
            bad_keys = val_keys.difference( col_keys )
            raise KeyError(
                'Keys %s do not exist in `columns` set in __init__' % ','.join(bad_keys)
            )

        for colkey in val_keys:
            column_index = self._columns.index( colkey ) +1
            widget       = QtGui.QStandardItem( str(columnvals[colkey] ) )
            item.setChild(
            self.setItem( index, column_index, widget )

        return self.item(index,0).index()


class Dummy(object):
    def __getattribute__(self, attr):
        """
        Returns one of the column-values
        """

        index = self._column_index(key)
        if attr not in self._columns:
            raise KeyError(
                'attr "%s" not in :py:meth:`__init__` argument `columns`' % attr
            )
        return self.item( index.row(), self._columns.index(i)+1 )



class DictModelItem( QtGui.QStandardItem ):
    """
    :py:obj:`QtGui.QAbstractItem` whose table is expressed
    as a dictionary (using the first column as the Id).
    """
    def __init__(self, key):
        QtGui.QStandardItem.__init__(self)
        self._key = key

    def __getitem__(self,key):
        """
        Returns another :py:obj:`DictModelItem`
        """
        index = self._column_index(key)
        self.child(index)

    def __setitem__(self, key, columnvals=None ):
        """
        Assign a :py:obj:`DictModelItem` to be a child of this
        :py:obj:`DictModelItem`.
        """
        ## If key exists in table, replace the model it corresponds to
        try:
            index = self._column_index(key)
            #self.setChild( index.row(), 0, modelitem )
            #! update columns

        ## If key does not exist in table, create a new row
        except:
            self.appendRow([key])
            modelitem = DictModelItem(key)
            self.setChild( self.columnCount()-1, 0, modelitem )

    def __getattribute__(self, key, attr):
        pass

    def __setattribute__(self, key, attr, val):
        pass

    def _column_index(self,key):
        """
        Returns Model Index for row containing key
        """
        for i in range(self.columnCount()):
            if self.child(i,0).text() == str(key):
                return self.child(i,0).index()
        raise KeyError(
            'key "%s" does not exist in DictModel' % key
        )

    def set_columns(self, columnvals ):

        if self.model() == None:
            raise RuntimeError(
                'Cannot set columns until `DictModelIem` has been '
                'added to a `DictModel` '
            )





if __name__ == '__main__':
    from   qconcurrency import QApplication
    import sys

    with QApplication():
        #model = QtGui.QStandardItemModel()
        model = DictModel( ('a','b','c') )
        #item  = DictModelItem( key=1)
        #subitem = DictModelItem( key=2 )

        #model.setItem( 0,0,  )
        #item[ 2 ] =



