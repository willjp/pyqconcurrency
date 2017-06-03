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
from   __future__           import unicode_literals
from   __future__           import absolute_import
from   __future__           import division
from   __future__           import print_function
from   collections          import OrderedDict
import functools
import uuid
#external
from   Qt                   import QtWidgets, QtGui, QtCore
from   Qt.QtWidgets         import QSizePolicy
#internal
from   qconcurrency.models  import DictModel



class DictModelQMenu( QtWidgets.QMenu ):
    """
    QMenu, whose actions/submenus are based/rebuilt from
    a :py:obj:`DictModel`. There are 2x display methods:

        * `indented`: every :py:obj:`DictModelRow` in the model is
                      a action. Items in nested-tables are indented,
                      and positioned under their parent.

        * `submenu`:  :py:obj:`DictModelRow` s that contain
                      child-tables are presented as submenus.
                      Only bottom-level :py:obj:`DictModelRow`
                      items are actions.


    Example:

        .. figure:: ../media/qconcurrency.widgets.DictModelQMenu_indented.png

            ``menustyle='indented'``


        .. figure:: ../media/qconcurrency.widgets.DictModelQMenu_submenu.png

            ``menustyle='submenu'``

    """
    triggered_row = QtCore.Signal( QtCore.QModelIndex )
    def __init__(self, dictmodel, menustyle='submenu', indexinfo={'id':'_id','name':'name'} ):
        """
        dictmodel (DictModel):
            The model whose contents we are using to generate
            the popup menu contents. Nested tables will appear
            in sub-menus.

        menustyle (str, optional): ``(ex: 'submenu', 'indented' )``
            This argument determines how to handle nested tables
            in the DictModel.

            * `submenu`: each item containing children will be implemented
                         in the menu as a submenu. Only the items from
                         the bottom-most nested-table can be selected.

            * `indented`: every item is selectable, child items are merely
                          indented to indicate that they are children
                          of their parent.

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

        if menustyle not in ('submenu','indented'):
            raise RuntimeError((
                'the only available menustyles are "submenu", "indented". '
                'Received "%s"') % menustyle
            )

        self._dictmodel = dictmodel
        self._indexinfo = indexinfo
        self._menustyle = menustyle
        self._submenus  = {}         # { uuid : submenu-widget }
                                     # (simply keeps references to qmenus so
                                     # they are note deleted when scope ends)

        # Connections
        self._dictmodel.itemChanged.connect( self._handle_modelchange )

        # Load
        self._create_actions()

    def _create_actions(self):
        if self._menustyle == 'submenu':
            return self._create_submenu_actions()
        elif self._menustyle == 'indented':
            return self._create_indented_actions()
        else:
            raise RuntimeError((
                'the only available menustyles are "submenu", "indented". '
                'Received "%s"') % menustyle
            )

    def _create_submenu_actions(self, baseitem=None, submenu_of=None ):

        if baseitem is None:
            self.clear()
            self._submenus = {}
            baseitem       = self._dictmodel


        for key in baseitem.keys():
            modelitem = baseitem[ key ]
            _id  = modelitem.columnval( self._indexinfo['id']   )
            name = modelitem.columnval( self._indexinfo['name'] )


            # if modelitem has children, create menu
            # instead of action
            menu = None
            if modelitem.rowCount():
                menu = QtWidgets.QMenu( title=name )
                self._submenus[ uuid.uuid4().hex ] = menu # keep reference on object, so not
                                                          # deleted when method scope ends
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
                self._create_submenu_actions( baseitem=modelitem, submenu_of=menu )

    def _create_indented_actions(self, baseitem=None, indent_lv=0 ):

        if baseitem is None:
            self.clear()
            baseitem = self._dictmodel


        for key in baseitem.keys():
            modelitem = baseitem[ key ]
            _id  = modelitem.columnval( self._indexinfo['id']   )
            name = modelitem.columnval( self._indexinfo['name'] )

            indent = ' '*  (3*indent_lv)

            self.addAction( indent+name, functools.partial( self._emit_triggered_row, modelitem ) )


            # if modelitem has children,
            # recurse through children, adding
            # them this item's menu
            if modelitem.rowCount():
                self._create_indented_actions( baseitem=modelitem, indent_lv=indent_lv+1 )

    def _emit_triggered_row(self, modelitem ):
        """
        We cannot meaningfully bind actions to the menu from a Model,
        but we can emit a signal with information about what was just selected.
        """

        if modelitem:
            self.triggered_row.emit( modelitem.index() )

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


    def test_submenu_style():

        with QApplication():
            model = DictModel( columns=['name'] )
            model.add_row( 1, {'name':'one'} )
            model.add_row( 2, {'name':'two'} )
            model.add_row( 3, {'name':'three'} )

            model[1].add_child( '1a', {'name':'one-a'} )
            model[1].add_child( '1b', {'name':'one-b'} )

            menu   = DictModelQMenu( model, menustyle='submenu', indexinfo={'id':'_id','name':'name'} )
            button = QtWidgets.QPushButton('press me')
            button.setMenu( menu )

            menu.triggered_row.connect( printargs )

            button.show()

    def test_indented_style():

        with QApplication():
            model = DictModel( columns=['name'] )
            model.add_row( 1, {'name':'one'} )
            model.add_row( 2, {'name':'two'} )
            model.add_row( 3, {'name':'three'} )

            model[1].add_child( '1a', {'name':'one-a'} )
            model[1].add_child( '1b', {'name':'one-b'} )

            menu   = DictModelQMenu( model, menustyle='indented', indexinfo={'id':'_id','name':'name'} )
            button = QtWidgets.QPushButton('press me')
            button.setMenu( menu )

            menu.triggered_row.connect( printargs )

            button.show()



    test_submenu_style()
    #test_indented_style()


