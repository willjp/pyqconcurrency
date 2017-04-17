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
from   __future__    import unicode_literals
from   __future__    import absolute_import
from   __future__    import division
from   __future__    import print_function
from   collections   import OrderedDict
import functools
import uuid
#external
from   Qt            import QtWidgets, QtGui, QtCore
from   Qt.QtWidgets  import QSizePolicy
#internal


#!TODO: test updates to model update qcombobox

class DictModelQComboBox( QtWidgets.QComboBox ):
    """
    ComboBox that displays nested-model structures.

    This widget does not directly use the modelview,
    but it does get updated when the model changes.

    .. warning::

        In order to select an item in the combobox, you must
        provide the model-index to the item you want, which is
        a bit ackward.
    """
    def __init__(self, dictmodel, indexinfo={'id':'_id','name':'name'} ):
        """

        Args:
            dictmodel (DictModel):
                The model you want this QComboBox to display.

            indexinfo (dict, optional):
                Stores information on where the following information
                from thte model:

                    * `name`: the name, as it appears in the QComboBox
                    * `id`:   the id, generally a databaseId that corresponds with the name
        """
        QtWidgets.QComboBox.__init__(self)

        self._dictmodel   = dictmodel
        self._indexinfo   = indexinfo
        self._modelindexes = {}       # QModelIndex of each item in QComboBox

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
            self.addItem(
                  ' '*(3*_indent_lv)
                + modelitem.columnval(  self._indexinfo['name'])
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



