#!/usr/bin/env python
"""
Name :          qconcurrency/models.py
Created :       Apr 14, 2017
Author :        Will Pittman
Contact :       willjpittman@gmail.com
________________________________________________________________________________
Description :   Generic models, and interfaces for models to be used
                in various Qt `View` widgets (ex: QTableView, QListView, QTableView, QComboBox, ...)
________________________________________________________________________________
"""
#builtin
from __future__          import unicode_literals
from __future__          import absolute_import
from __future__          import division
from __future__          import print_function
from collections         import Iterable, MutableMapping
#external
from Qt                  import QtGui, QtCore
#internal

__all__ = [
    'DictModel',
    'DictModelRow',
]


#!TODO: test using delattr unecessary, (and potentially harmful)
#!      QStandardItemModel methods (like appendRow, setItem, ...)

#!TODO: validation based on `hierarchy`, preventing nesting below defined
#!TODO: validation of column-names when setting columnvals

class DictModel( QtGui.QStandardItemModel ):
    """
    Customized python interface for :py:obj:`QtGui.QStandardItemModel` so that it's
    values, and nested tables can be accessed like a python dictionary.

    Example:


        Simple Example:


        .. code-block:: bash

            | _id | firstname | lastname  | username |
            |========================================|
            | 101 | luke      | skywalker | lukes    |
            | 102 | leia      | skywalker | leias    |
            |========================================|

        .. code-block:: python

            model = DictModel( columns=('firstname','lastname','username') )

            model.add_row( 101, columnvals = {
                    'firstname':'luke'      ,
                    'lastname' :'skywalker' ,
                    'username' :'lukes'     ,
                }
            )

            userId = 101
            print( model[userId].column('firstname') )
            >>> 'luke'

            print( model[userId].columnvals() )
            >>> {'_id':101, 'firstname':'luke', 'lastname':'skywalker', 'username':'lukes'}



        Nested-Table Example:

        .. code-block:: bash

            |=============|
            | _id | class |  # level: 'jedi_class'
            |=============|
            | 101 | sith  |
            |  |===========================================|
            |  | _id | firstname  | lastname   | username  | # level: 'user'
            |  |===========================================|
            |  | 56  | Darth      | Vader      | anakins   |
            |  | 57  | Darth      | Maul       | darthm    |
            |  |===========================================|
            |             |
            | 102 | jedi  |
            |  |===========================================|
            |  | _id | firstname  | lastname   | username  | # level: 'user'
            |  |===========================================|
            |  | 58  | Mace       | Windu      | macew     |
            |  | 59  | Ben        | Kenobi     | benk      |
            |  |===========================================|
            |             |
            |=============|

        .. code-block:: python

            model = DictModel(
                    hierarchy = ('jedi_class','user'),
                    columns   = {
                        'jedi_class':  ('class'),
                        'user':        ('firstname','lastname','username')
                    },
                )

            sith_row = model.add_row( 101, {'class':'sith'} )
            jedi_row = model.add_row( 102, {'class':'jedi'} )
            sith_row.add_child( 56, {'firstname':'Darth', 'lastname':'Vader', 'username':'anakins'} )
            sith_row.add_child( 57, {'firstname':'Darth', 'lastname':'Maul',  'username':'darthm'} )

            jediclassId = 101
            userId      =  56
            print( model[jediclassId][userId].column('username') )
            >>> 'anakins'

            print( model[jediclassId].level() )
            >>> 'jedi_class'

            print( model[jediclassId][userId].level() )
            >>> 'user'


        :py:obj:`qconcurrency.models.DictModel`  column datatypes

        .. code-block:: bash

            |===============================================|
            | _id          | columnA        | columnB       |
            |===============================================|
            | DictModelRow |  QStandardItem | QStandardItem |
            |   |===============================================|
            |   | _id          | columnA        | columnB       |
            |   |===============================================|
            |   | DictModelRow |  QStandardItem | QStandardItem |
            |   |===============================================|
            |                                               |
            |===============================================|

    """
    def __init__(self, columns, hierarchy=None ):
        """

        Args:
            columns (list, dict):
                Defines the available columns for the table/tree this :py:obj:`QtGui.QStandardItemModel`
                (the `key`, generally referring to the databaseId, is always the first column)

                If `hierarchy` argument is set, you have two options:

                    * This can be a list of column-names, that will be
                      created in all levels of nested table.

                    * This can be a dictionary in the form of ``{'level_name':(column,column,column,...), ...}``
                      that indicates specific-columns for each level of table-nesting.

                If `hierarchy` is not set, this must be a list of column-names,
                and they will be applicable to any level of table-nesting.


            hierarchy (list, optional):  ``(ex:  ('department_type','department')  )``
                A list that labels what type of data is stored at each
                level of table-nesting in this :py:obj:`qconcurrency.models.DictModel`. Each item
                indicates another level of nesting.

        """
        QtGui.QStandardItemModel.__init__(self)

        # Attributes
        self._defaultcolumnvals = {}      # all columns for new rows are initialized as ``None``
        self._columns           = None    # either a list of columns, or a dict of hierarchy-keys and their columns
        self._hierarchy         = None    # either ``None``, or a list, indicating the level of each


        # Validation
        # ==========

        # If imposing hierarchy restrictions
        if hierarchy:
            self._hierarchy = hierarchy

            if isinstance( columns, MutableMapping ):
                if not set(hierarchy).issubset( set(columns.keys()) ):
                    raise RuntimeError((
                        '`columns` argument is missing keys represented in`hierarchy` \n'
                        'columns:   %s \n'
                        'hierarchy: %s \n'
                        ) % (repr(columns.keys()), repr(hierarchy))
                    )

            # so that hierarchy can always be handled the same,
            # create `columns` as a dict, if a list was passed
            elif hasattr( columns, Iterable ):
                new_columns = {}
                for level in hierarchy:
                    new_columns[ level ] = columns[:]

                columns = new_columns
            else:
                raise RuntimeError(
                    'When `hierarchy` argument is set, `columns` must be either: \n'
                    '   * a list of columns (applicable to all hierarchy levels) \n'
                    '   * a dict of hierarchy-keys, and the columns associated with them \n'
                )

            for level in hierarchy:
                self._defaultcolumnvals[ level ] = {}
                for key in columns:
                    self._defaultcolumnvals[ level ][ key ] = None


        # If not imposing hierarchy restrictions
        else:
            if isinstance( columns, MutableMapping ):
                raise RuntimeError(
                    'When `hierarchy` argument is *not* set, `columns` should always \n'
                    'be a list of column-names. This set of columns will be reused by all \n'
                    'levels of nested tables. '
                )
            for key in columns:
                self._defaultcolumnvals[ key ] = None


        self._columns   = columns
        self._hierarchy = hierarchy

    def __getitem__(self, key):
        """
        Returns a :py:obj:`qconcurrency.models.DictModelRow` object representing
        a row from this :py:obj:`qconcurrency.models.DictModel`.
        """
        return self._get_rowitem(key)

    def add_row(self, key, columnvals=None ):
        """
        Adds a new (toplevel) row to this DictModel, henceforth referred to by the key `key`.

        Args:
            key (obj):
                Key is the id you will use to refer to this object.
                Generally it will be a databaseId. This object must be
                hashable.

            columnvals (dict, optional):
                Optionally, you may provide a dictionary of column-val assignments
                (appropriate to this item's table-level). All columns, not
                assigned in `columnvals` will be initialized with a value of ''.


        Returns:
            :py:obj:`qconcurrency.models.DictModelRow`
        """

        set_columnvals = self._defaultcolumnvals.copy()
        set_columnvals.update( columnvals )
        item = DictModelRow( parent=self, key=key, columnvals=set_columnvals)

        # NOTE: this step should not be necessary,
        #       but it seems to be...
        self.setItem( self.rowCount()-1, 0, item )

        return item

    def columns(self, level=None ):
        """
        Returns the columns for a particular level of nested-table
        within this :py:obj:`qconcurrency.models.DictModel`.

        Args:
            level (obj):
                If a `hierarchy` was assigned to this :py:obj:`qconcurrency.models.DictModel`,
                this will be a label from it. Otherwise, this will be an integer
                indicating the level-of-nesting (and it will be ignored).

        Returns:

            .. code-block:: python

                ('firstname','lastname','username', ...)
        """

        if self._hierarchy:
            if level == None:
                raise RuntimeError(
                    'This `qconcurrency.models.DictModel` was created with different columns at '
                    'different levels. You\'ll need to provide the `level` you are '
                    'interested in to get the column-list '
                )
            return self._columns[ level ]
        else:
            return self._columns

    def column_index(self, level=None, column=None ):
        """
        Returns the column-index for a specific columnname
        at a specific level.

        Returns:

            .. code-block:: python

                3   # a column-index
        """
        if self._hierarchy:
            return self._columns[ level ].index( column )
        else:
            return self._columns.index( column )

    def default_columnvals(self, level=None ):
        """
        Returns the default-columnvals for a particular level of nested-table.
        See :py:meth:`qconcurrency.models.DictModelRow.level`

        Args:
            level (obj):
                If a `hierarchy` was assigned to this :py:obj:`qconcurrency.models.DictModel`,
                this will be a label from it. Otherwise, this will be an integer
                indicating the level-of-nesting (and it will be ignored).

        Returns:

            .. code-block:: python

                {
                    'firstname': None,
                    'lastname':  None,
                    ...
                }
        """

        if self._hierarchy:
            return self._defaultcolumnvals[ level ]
        else:
            return self._defaultcolumnvals

    def hierarchy(self):
        """
        Returns the model's hierarchy tuple
        (if one has been assigned in :py:obj:`qconcurrency.models.DictModel.__init__`)

        Returns:

            .. code-block:: python

                ('jedi_class', 'user') # if assigned a hierarchy
                None                   # if no hierarchy is assigned
        """
        return self._hierarchy

    def _get_rowitem(self, key):
        """
        Returns the item in the first column of this :py:obj:`QtGui.QStandardItemModel`
        for the row with the key indicated by `key`.

        Args:
            key (obj):
                A key assigned to a row within this Model. Generally,
                this would be a database-Id.

        Returns:
            QtGui.QStandardItem
        """
        for i in range(self.rowCount()):
            if self.item(i,0).text() == str(key):
                return self.item(i,0)

    def _get_colindex(self, column):
        """
        Returns the column-index for a column within this :py:obj:`QtGui.QStandardItemModel`
        by it's name.

        Args:
            column (str):  ``(ex: 'name' )``
                Any item from the :py:meth:`__init__` argument `columns`.

        Returns:

            .. code-block:: python

                4   # integer, representing the 0-based index of this column
                    # in the table

        Raises:
            KeyError: if column does not exist in table
        """
        if column in self._columns:
            return self._columns.index(column) +1

        raise KeyError(
            'Column "%s" does not exist in this `qconcurrency.models.DictModel` columns: %s' % (
                column, str(self._columns)
            )
        )

    def keys(self):
        """
        Returns list containing keys for every
        row that has been added to this :py:obj:`qconcurrency.models.DictModel` s root

        Returns:

            .. code-block:: python

                [ 1, 2, 3, 5, 8, ... ]

        """
        keys = []
        for i in range(self.rowCount()):
            keys.append( self.item(i,0).id() )
        return keys



class DictModelRow( QtGui.QStandardItem ):
    """
    A DictModelRow is a :py:obj:`QtGui.QStandardItem` that holds
    an item's key (usually database-Id) within a :py:obj:`qconcurrency.models.DictModel`.
    It is always added to a :py:obj:`qconcurrency.models.DictModel` at the column-index ``0``.
    When setting columnvals, they are added to the same parent :py:obj:`qconcurrency.models.DictModel`
    or :py:obj:`qconcurrency.models.DictModelRow`, but at different column-indexes.


    Example:

        .. code-block:: bash

                            ===== ========|
            DictModelRow     _id  | class |  # level: 'jedi_class'
                 |          ===== ========|
                 +---------> 101  | sith  |
                 |            |============================================|
                 |            |  _id | firstname  | lastname   | username  | # level: 'user'
                 |            |============================================|
                 +-------------> 56  | Darth      | Vader      | anakins   |
                 +-------------> 57  | Darth      | Maul       | darthm    |
                              |============================================|
                                        /\\           /\\            /\\
                                        |            |             |
               QtGui.QStandardItem  ----+------------+-------------+

    """
    def __init__(self, parent, key, columnvals=None ):
        """
        Args:
            parent (QtGui.QStandardItem, QtGui.QStandardItemModel ):
                Another QStandardItem that has already
                been added to the model, or a model itself.

                It will be used to access the model's info,
                and this widget will be added to it.

            key (obj):
                A hashable python object that will be
                used to represent this object's databaseId.

            columnvals (dict, optional):
                A dictionary of columns, and assignments to store
                in the view.
        """

        QtGui.QStandardItem.__init__(self, str(key))

        if not isinstance( parent, QtGui.QStandardItemModel ):
            if not parent.model():
                raise RuntimeError(
                    '`parent` %s QStandardItem must have already been added to a QStandardItemModel' % repr(parent)
                )

        self._key   = key
        self._level = None  # if `hierarchy` argument was set in `DictModel`, this will be
                            # a label indicating the type of information this
                            # table represents.
                            #
                            # otherwise, this will be an incremented integer
                            # (starting from 0)



        # append this item to the parent's list of children
        if isinstance( parent, QtGui.QStandardItemModel ):
            if parent.hierarchy():
                self._level = parent.hierarchy()[0]
            else:
                self._level = 0
            parent.setItem( parent.rowCount(), 0, self )

        else:
            hierarchy = parent.model().hierarchy()
            if hierarchy:
                index = hierarchy.index( parent.level() ) +1
                self._level = hierarchy[ index ]
            else:
                self._level = parent.level() +1

            parent.setChild( parent.rowCount(), 0, self )

        self.setText( str(key) )
        self.set_columnvals( self.model().default_columnvals(self._level) )
        if columnvals:
            self.set_columnvals( columnvals )

    def __getitem__(self, key):
        return self._get_child_row(key)

    def add_child(self, key, columnvals=None ):
        """
        Adds a new row to this DictModel, at a new level of nesting
        henceforth referred to by the key `key`.

        Example:

            .. code-block:: bash

                |==============|
                | _id | column |
                |==============|
                | 100 | 'A'    |     # add_child( 102, {'column':'A1'} )
                |   |==============|
                |   | _id | column | # added child:  model[100][102]
                |   |==============|
                |   | 102 | 'A1'   |
                |   |==============|
                |              |
                | 101 | 'B'    |
                |==============|

        Args:
            key (obj):
                Key is the id you will use to refer to this object.
                Generally it will be a databaseId. This object must be
                hashable.

            columnvals (dict, optional):
                Optionally, you may provide a dictionary of column-val assignments
                (appropriate to this item's table-level) as determined by the `columns`
                argument to :py:meth:`qconcurrency.models.DictModel.__init__`


        Returns:
            :py:obj:`qconcurrency.models.DictModelRow`

        See Also:
            * :py:meth:`qconcurrency.models.DictModelRow.add_row`
            * :py:meth:`qconcurrency.models.DictModel.add_row`

        """
        item = DictModelRow( parent=self, key=key, columnvals=columnvals )
        return item

    def add_row(self, key, columnvals=None ):
        """
        Adds a new row to this DictModel, at the same level of nesting
        henceforth referred to by the key `key`.

        Example:

            .. code-block:: bash

                |==============|
                | _id | column |
                |==============|
                | 100 | 'A'    | # add_row( 102, {'column':'C'} )
                | 101 | 'B'    |
                | 102 | 'C'    | # added row: model[102]
                |==============|


        Args:
            key (obj):
                Key is the id you will use to refer to this object.
                Generally it will be a databaseId. This object must be
                hashable.

            columnvals (dict, optional):
                Optionally, you may provide a dictionary of column-val assignments
                (appropriate to this item's table-level) as determined by the `columns`
                argument to :py:meth:`qconcurrency.models.DictModel.__init__`


        Returns:
            :py:obj:`qconcurrency.models.DictModelRow`

        See Also:
            * :py:meth:`qconcurrency.models.DictModelRow.add_row`
            * :py:meth:`qconcurrency.models.DictModel.add_row`

        """
        if self.parent():
            item = DictModelRow( parent=self.parent(), key=key, columnvals=columnvals )
        else:
            item = DictModelRow( parent=self.model(), key=key, columnvals=columnvals )

        return item

    def set_columnvals(self, columnvals ):
        """
        Set columnvals on a key of this :py:obj:`qconcurrency.models.DictModel`
        """

        # validation
        if self.model() == None:
            raise RuntimeError('Cannot set columnvals until item has been added to a model')

        columns = self.model().columns( self._level )

        # set columnvals
        for i in range(len(columns)):
            column = columns[i]

            if column in columnvals:
                if self.parent() is not None:
                    self.parent().setChild(
                        self.index().row(),                       # row
                        i+1,                                      # column
                        QtGui.QStandardItem( columnvals[column] ) # item
                    )
                else:
                    self.model().setItem(
                        self.index().row(),                       # row
                        i+1,                                      # column
                        QtGui.QStandardItem( columnvals[column] ) # item
                    )

    def columnvals(self):
        """
        Returns a dictionary of this item's columnvals from the Model.
        A column `_id` will be added to the list of columns, which will
        be the `key` value of this row.
        """
        columnvals = {}
        columns    = self.model().columns(self._level)

        for i in range(len(columns)):
            column = columns[i]
            if self.parent() is not None:
                columnvals[ column ] = self.parent().child( self.row(), i+1 ).text()
            else:
                columnvals[ column ] = self.model().item( self.row(), i+1 ).text()
        columnvals['_id'] = self._key

        return columnvals

    def columnval(self, name):
        """
        Retrieve a single column-value only.
        """

        if name == '_id':
            if self.parent() is not None:
                return self.parent().child( self.row(), 0 ).text()
            else:
                return self.model().item( self.row(), 0 ).text()

        columns = self.model().columns(self._level)
        for i in range(len(columns)):
            column = columns[i]
            if column == name:
                if self.parent() is not None:
                    return self.parent().child( self.row(), i+1 ).text()
                else:
                    return self.model().item( self.row(), i+1 ).text()

        raise KeyError(
            'Unable to find a column named: "%s" in %s' % (name, repr(columns))
        )

    def level(self):
        """
        Returns either a label (if :py:meth:`qconcurrency.models.DictModel.__init__` was passed a
        `hierarchy` argument), or an integer representing the nesting-depth.
        Either way, level is used to indicate the level-of-nesting of the table
        that this item is in.
        """
        return self._level

    def delete(self):
        """
        Removes this *row* from the model.
        """
        if self.parent() is not None:
            self.parent().removeRow( self.index().row() )
        else:
            self.model().removeRow( self.index().row() )

    def _get_sibling_row(self, key):
        """
        Returns a sibling with a different key at the same level.

        Example:

            .. code-block:: bash

                ----------------------------------------------------
                key          | name            | path              |
                ----------------------------------------------------
                100          | 'mnt'           | '/mnt'            |
                   100.1     | 'mntusb'        | '/mnt/usb'        |
                     100.1.a | 'mntusbbackup'  | '/mnt/usb/backup' |
                   100.2     | 'mntcd'         | '/mnt/cd'         |
                             |                 |                   |
                200          | 'home'          | '/home'           |
                   200.1     | 'will'          | '/home/will'      |

            In the above diagram representing the :py:obj:`QStandardItemModel`,
            from `100.1` you would be able retrieve `100.2`.
        """
        if self.parent() == None:
            for i in range(self.model().rowCount()):
                if self.model().item(i,0).text() == str(key):
                    return self.model().item(i,0)
        else:
            for i in range(self.parent().rowCount()):
                if self.parent().child(i,0).text() == str(key):
                    return self.parent().child(i,0)

        raise KeyError(
            'Unable to find key %s in table containing %s' % (key, repr(self))
        )

    def _get_child_row(self, key):
        """
        Returns a child with a particular key.


        Example:

            .. code-block:: bash

                ----------------------------------------------------
                key          | name            | path              |
                ----------------------------------------------------
                100          | 'mnt'           | '/mnt'            |
                   100.1     | 'mntusb'        | '/mnt/usb'        |
                     100.1.a | 'mntusbbackup'  | '/mnt/usb/backup' |
                   100.2     | 'mntcd'         | '/mnt/cd'         |
                             |                 |                   |
                200          | 'home'          | '/home'           |
                   200.1     | 'will'          | '/home/will'      |

            In the above diagram representing the :py:obj:`QStandardItemModel`,
            from `100.1` you would be able retrieve `100.1.a`.
        """
        if not self.rowCount():
            raise RuntimeError(
                '%s has no children. Cannot retrieve child at key %s' % (repr(self), key)
            )

        for i in range(self.rowCount()):
            if self.child(i,0).text() == str(key):
                return self.child(i,0)

        raise KeyError(
            'Cannot find child identified by key "%s" in %s' % (key,repr(self))
        )

    def _get_colindex(self, column):
        return self.model()._get_colindex(column)

    def keys(self):
        """
        Returns list containig keys for every
        child-row that has been added to this :py:obj:`qconcurrency.models.DictModelRow`
        """
        keys = []
        for i in range(self.rowCount()):
            keys.append( self.child(i,0).text() )
        return keys

    def id(self):
        """
        Returns the `key` this row represents.
        (It's value depends on the value passed to :py:meth:`qconcurrency.models.DictModelRow.add_row`
        or :py:meth:`qconcurrency.models.DictModelRow.add_child` ).
        """
        return self._key



if __name__ == '__main__':
    from   qconcurrency import QApplication
    from   Qt           import QtWidgets
    import sys

    def test_simple():

        with QApplication():
            model = DictModel( columns=('a','b','c') )

            # add toplevel rows
            model.add_row( 100, columnvals={'a':'AAA', 'b':'BBB'} )
            model.add_row( 200, columnvals={'a':'ZZZ', 'b':'XXX'} )
            print( model[100].columnvals() )
            print( model[200].columnvals() )

            # add child-rows (and nested children)
            model[100].add_child(     10, columnvals={'c':'CCC'}    )
            model[100][10].add_row( 11 )
            model[100][10].add_row( 12 )
            model[100][10].add_child( 1 , columnvals={'c':'DDD'} )
            print( model[100][10].columnvals() )
            print( model[100][10][1].columnvals() )

            # add model to tree (so it is visible)
            tree = QtWidgets.QTreeView()
            tree.setModel( model )
            tree.show()

    def test_hierarchy_fixedcols():
        with QApplication():

            model = QtGui.QStandardItemModel()
            model = DictModel(
                hierarchy = ('jedi_class','user'),
                columns   = {'jedi_class':['class'],  'user':('username','firstname','lastname')}
            )

            model.add_row(10, columnvals={'class':'sith'} )
            model.add_row(11, columnvals={'class':'jedi'} )

            model[10].add_child( 101, columnvals={'username':'anakins', 'firstname':'anakin', 'lastname':'skywalker'} )
            model[10].add_child( 102, columnvals={'username':'epalpatine'} )
            model[10].add_row( 12, columnvals={'class':'other'} )

            jediclassId = 10
            userId      = 101
            print( model[jediclassId][userId].columnvals() )

            # add model to tree (so it is visible)
            tree = QtWidgets.QTreeView()
            tree.setModel( model )
            tree.show()

    def runtests():
        #test_simple()
        test_hierarchy_fixedcols()


    runtests()

