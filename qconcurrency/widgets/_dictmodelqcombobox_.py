#!/usr/bin/env python
"""
Name :          qconcurrency.widgets._dictmodelqcombobox_.py
Created :       Apr 16, 2017
Author :        Will Pittman
Contact :       willjpittman@gmail.com
________________________________________________________________________________
Description :   A QComboBox designed to work with a `DictModel`.

                Builtin QComboBoxes do not support nested items,
                this combobox is built to address this issue, in addition
                to being kept up to date with a Model as it is changed.
________________________________________________________________________________
"""
#builtin
from   __future__        import unicode_literals
from   __future__        import absolute_import
from   __future__        import division
from   __future__        import print_function
from   collections       import OrderedDict, MutableMapping
import functools
import uuid
#external
from   Qt                import QtWidgets, QtGui, QtCore
from   Qt.QtWidgets      import QSizePolicy
#internal
from qconcurrency.models import DictModel

__all__ = 'DictModelQComboBox'


#!TODO: test updates to model update qcombobox
#!TODO: allow different column for name/id for each different level

class DictModelQComboBox( QtWidgets.QComboBox ):
    """
    ComboBox  whose contents are determined by the contents of a
    :py:obj:`qconcurrency.models.DictModel`. The widget's contents are
    updated whenever the modelchanges.


    Example:

        .. image:: ../media/qconcurrency.widgets.DictModelQComboBox.png

    """
    def __init__(self, dictmodel, indexinfo={'id':'_id','name':'name'} ):
        """

        Args:
            dictmodel (DictModel):
                The model you want this QComboBox to display.

            indexinfo (dict, optional):
                Stores information on where the following information
                from the model:

                    * `name`: the name, as it appears in the QComboBox
                    * `id`:   the id, generally a databaseId that corresponds with the name


                This can either be a single dict, if the id/name
                will be the same column for every level of the dictmodel,
                or it can be a dictionary with the level, and a dict of id/name
                for that specific level.

                .. code-block:: python

                    # example 1:
                    #    applies to all levels of table
                    indexinfo = { 'id':'_id',  'name':'name' }


                    # example 2:
                    #    level-specific columns
                    indexinfo = {
                        'departmenttype':{'id':'_id', 'name':'departmenttype_name'},
                        'department'    :{'id':'_id', 'name':'department_name'},
                    }

        """
        QtWidgets.QComboBox.__init__(self)

        if not isinstance( dictmodel, DictModel ):
            raise TypeError(
                '`dictmodel` argument expected to be of type DictModel. Received %s' % type(dictmodel)
            )

        self._dictmodel    = dictmodel
        self._indexinfo    = indexinfo
        self._modelindexes = {}               # {combobox_index : QModelIndex} QModelIndex of each item in QComboBox
        self._level_specific_columns = False  # True    if self._indexinfo is in the format of  { level : {'_id':..., 'name':,..}, level : {...} }
                                              # False   if self._indexinfo is in the format of  {'_id':..., 'name':...}



        if len(dictmodel.keys()):
            if isinstance( dictmodel[ dictmodel.keys()[0] ], MutableMapping ):
                self._level_specific_columns = True


        # Connections (update combobox every time model changes )
        self._dictmodel.itemChanged.connect( self._handle_modelchange )
        self.currentIndexChanged.connect(self.get_selected)

        # Load
        self._populate_combo()

    def _handle_modelchange(self,*args,**kwds):
        self._populate_combo()

    def _populate_combo(self, _baseitem=None, _indent_lv=0):
        """
        Rebuilds the available options
        """

        if _baseitem is None:
            _baseitem = self._dictmodel
            selitem   = self.get_selected()
            self.clear()

        for key in _baseitem.keys():
            modelitem = _baseitem[ key ]

            self._modelindexes[ self.count() ] = modelitem.index()

            if self._level_specific_columns:
                name = self._indexinfo[ modelitem.level() ]['name']
            else:
                name = self._indexinfo['name']


            self.addItem(
                  ' '*(3*_indent_lv)
                + modelitem.columnval( name )
            )


            # if modelitem has children
            if modelitem.rowCount():
                self._populate_combo( _baseitem=modelitem, _indent_lv=_indent_lv+1 )


        # TODO:
        # if this was the first item
        # restore the user's selection if possible
        if _baseitem is self._dictmodel:
            pass

    def get_selected(self):
        """
        Returns the modelitem corresponding to the user's selection.
        From this object, you can find any information from the model.

        Returns:

            The corresponding :py:obj:`DictModelRow` to the selected item.


        See Also:

            * :py:meth:`DictModelRow.columnvals`
            * :py:meth:`DictModelRow.columnval`
            * :py:meth:`DictModelRow.id`
        """

        # if there are items in the list
        if self.currentIndex() != -1:
            modelitem = self._dictmodel.itemFromIndex(
                self._modelindexes[ self.currentIndex() ]
            )
            return modelitem

    def set_selected(self, modelindex):
        """
        Sets the selected item in the QComboBox
        """

        for combo_index in self._modelindexes:
            if self._modelindexes[ combo_index ] == modelindex:
                self.setCurrentIndex( combo_index )
                return


        raise KeyError(
            'Cannot find item in model with a modelindex of %s' % repr(_id)
        )

    def get_item_indexinfo(self, modelitem):
        """
        Returns all keys from `indexinfo` for a particular item.
        (taking into account item's nested-table-level, if `indexinfo` requires it)

        Returns:

            .. code-block:: python

                # if modelitem exists in model
                {
                    'id':    123,
                    'name': 'test name',
                }

                # if modelitem does not exist in model
                {}
        """
        indexinfo = {}

        if self._level_specific_columns:
            for key in self._indexinfo[ modelitem.level() ]:
                indexinfo[ key ] = modelitem.columnval( self._indexinfo[ modelitem.level() ][ key ] )
        else:
            for key in self._indexinfo:
                indexinfo[ key ] = modelitem.columnval( self._indexinfo[ key ] )

        return indexinfo

    def get_modelindex_from_index(self, index):
        """
        Returns the :py:obj:`QtCore.QModelIndex` corresponding
        to the item with a :py:obj:`QtWidgets.QComboBox` index.
        """
        return self._modelindexes[ index ]



if __name__ == '__main__':
    #external
    from Qt import QtWidgets
    #internal
    from qconcurrency        import QApplication
    from qconcurrency.models import DictModel


    with QApplication():
        model = DictModel( columns=['name'] )
        model.add_row( 1, {'name':'one'} )
        model.add_row( 2, {'name':'two'} )
        model.add_row( 3, {'name':'three'} )

        model[1].add_child( 10, {'name':'one-a'} )
        model[1].add_child( 11, {'name':'one-b'} )


        # This QComboBox can display a hierarchy (with indentation)
        combo = DictModelQComboBox( model, indexinfo={'id':'_id', 'name':'name'} )
        combo.show()

        combo.set_selected( model[1][11].index() )
        print( combo.get_selected().columnvals() )




