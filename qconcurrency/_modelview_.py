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
from Qt            import QtGui
#internal

class DictModel( QtGui.QAbstractItemModel ):
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
        self._columns = columns

    def __getattribute__(self, key, attr):
        """
        Returns one of the column-values
        """
        index = self._column_index(key)
        if attr not in self._columns:
            raise KeyError(
                'attr "%s" not in :py:meth:`__init__` argument `columns`' % attr
            )
        return self.item( index.row(), self._columns.index(i)+1 )


    def __getitem__(self, key):
        pass

    def __setitem__(self, key, model=None ):
        pass

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

        for key in item_keys:
            widget               = index.sibling(
                index.row(), self._columns.index(key)
            )
            columnvals[ colkey ] = widget.text()

        return columnvals

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




if __name__ == '__main__':
    pass

