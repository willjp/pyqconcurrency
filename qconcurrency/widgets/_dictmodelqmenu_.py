#!/usr/bin/env python
"""
Name :          qconcurrency.widgets._dictmodelqmenu_.py
Created :       Apr 16, 2017
Author :        Will Pittman
Contact :       willjpittman@gmail.com
________________________________________________________________________________
Description :   A QMenu, designed to work with a `DictModel`

                Supports nested-tables, and is kept up-to-date
                with changes from the model it is representing.
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

#!TODO: test updates to model update qmenu

class DictModelQMenu( QtWidgets.QMenu ):
    """
    QMenu, that dynamically gets rebuilt every time it is called.
    It's contents are determined by a :py:obj:`DictModel`.

    :py:obj:`DictModel` sub-tables are represented as sub-menus.
    """
    triggered_row = QtCore.Signal( object, dict)   # ( modelitem.level(), modelitem.columnvals() )  emits the entire row of columnvals when an item is clicked
    def __init__(self, dictmodel, indexinfo={'id':'_id','name':'name'} ):
        """
        dictmodel (DictModel):
            The model whose contents we are using to generate
            the popup menu contents. Nested tables will appear
            in sub-menus.

        indexinfo (dict, optional):  ``(ex:  {'id':'_id', 'name': 'name'} )``
            A dictionary containing the keys `id` and `name`.
            The value of these keys represent the name (appears in qmenu)
            and it's corresponding databaseId.

            The values of these keys are column-names from the dictmodel.
            See :py:meth:`DictModel.__init__`
        """

        QtWidgets.QMenu.__init__(self)

        if not isinstance( dictmodel, DictModel ):
            raise TypeError(
                '`dictmodel` argument expects a DictModel object. Received: %s' % repr(self)
            )
        self._dictmodel = dictmodel
        self._indexinfo = indexinfo

        # Connections
        self._dictmodel.itemChanged.connect( self._handle_modelchange )

        # Load
        self._create_actions()

    def _create_actions(self, baseitem=None, submenu_of=None ):
        if baseitem is None:
            self.clear()
            baseitem = self._dictmodel


        for key in baseitem.keys():
            modelitem = baseitem[ key ]
            _id  = modelitem.columnval( self._indexinfo['id']   )
            name = modelitem.columnval( self._indexinfo['name'] )


            # if modelitem has children, create menu
            # instead of action
            menu = None
            if modelitem.rowCount():
                menu = QtWidgets.QMenu( title=name )
            if menu:
                if submenu_of:
                    submenu_of.addMenu( menu )
                else:
                    self.addMenu( menu )


            # if modelitem does not have children,
            # add to menu as an action
            else:
                if submenu_of:
                    submenu_of.addAction( name, functools.partial( self._emit_triggered_row, modelitem ) )
                else:
                    self.addAction( name, functools.partial( self._emit_triggered_row, modelitem ) )


            # if modelitem has children,
            # recurse through children, adding
            # them this item's menu
            if modelitem.rowCount():
                self._create_actions( baseitem=modelitem, submenu_of=menu )

    def _emit_triggered_row(self, modelitem ):
        """
        We cannot meaningfully bind actions to the menu from a Model,
        but we can emit a signal with information about what was just selected.
        """

        if modelitem:
            self.triggered_row.emit( modelitem.level(), modelitem.columnvals() )

    def _handle_modelchange(self, *args, **kwds):
        """
        Whenever the model changes, recreate the
        QMenu actions/submenus.
        """
        self._create_actions()




if __name__ == '__main__':
    #external
    from Qt import QtWidgets
    #internal
    from qconcurrency        import QApplication
    from qconcurrency.models import DictModel

    def printargs(*args,**kwds):
        print( args )
        print( kwds )


    with QApplication():
        model = DictModel( columns=['name'] )
        model.add_row( 1, {'name':'one'} )
        model.add_row( 2, {'name':'two'} )
        model.add_row( 3, {'name':'three'} )

        model[1].add_child( '1a', {'name':'one-a'} )
        model[1].add_child( '1b', {'name':'one-b'} )

        menu   = DictModelQMenu( model, indexinfo={'id':'_id','name':'name'} )
        button = QtWidgets.QPushButton('press me')
        button.setMenu( menu )

        menu.triggered_row.connect( printargs )

        button.show()



