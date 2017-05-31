#!/usr/bin/env python
"""
Name :          qconcurrency.widgets._updaterwidgets_._updaterlist_.py
Created :       May 24, 2017
Author :        Will Pittman
Contact :       willjpittman@gmail.com
________________________________________________________________________________
Description :   List that manages creation,updates,deletion in a consistent
                manner.
________________________________________________________________________________
"""
#builtin
from   __future__    import unicode_literals
from   __future__    import absolute_import
from   __future__    import division
from   __future__    import print_function
import uuid
import sys
import os
#package
from qconcurrency.widgets._sessionwidgets_._basewidgets_ import (
    SessionWidgetBase, SessionWidgetItemBase
)
#external
from Qt import QtWidgets, QtCore, QtGui
#internal


#!TODO: SessionListItem should be editable on double-click
#!TODO: Enter toggles confirm/edit selected item
#!TODO: colour for Editable

class SessionList( SessionWidgetBase, QtWidgets.QWidget ):
    def __init__(self, colours=None):
        """
        Args:
            colours (dict, optional):
                An optional dictionary, indicating colours to use
                for QListWidgetItems based on their status.

                Any key that is not set in the dictionary
                uses the stylesheet's default colours for
                :py:obj:`QListWidgetItems`

                .. code-block:: python

                    {
                        'normal':  {'fg':QColor(255,255,255), 'bg':QColor(255,255,255)},
                        'changed': {'fg':QColor(255,255,255), 'bg':QColor(255,255,255)},
                        'new':     {'fg':QColor(255,255,255), 'bg':QColor(255,255,255)},
                    }

        """
        SessionWidgetBase.__init__(self)
        QtWidgets.QWidget.__init__(self)

        # Attributes
        if not colours:
            self._colours = {}
        else:
            self._colours = colours

        # Widgets
        self._list = None  # the QListWidget managed by this class

        self._initui()

    def _initui(self):

        # Create Widgets
        layout     = QtWidgets.QVBoxLayout()
        self._list = QtWidgets.QListWidget()

        # Position Widgets
        self.setLayout( layout )
        layout.addWidget( self._list )

        # Widget Attrs
        layout.setContentsMargins(0,0,0,0)

        # Connections
        self._list.itemChanged.connect( self._handle_item_changed )

    def add_item(self, val, _id=None, saved_val=None ):
        """
        Adds a new item to the list.

        Args:
            val (object): ``(ex:  'itemA' )``
                The item you'd like to add to the widget

            _id (object, optional):
                If the item exists and has already been assigned an Id
                provide it here.

                Or, if the item is new, but you want to assign a specific
                Id, you may also provide an Id here.

            saved_val (object, optional):
                If this argument is assigned a value, the item
                will tracked as being an item that is already saved
                to the database (or other long-term-storage).

                You can test whether or not a widget's current value
                is different from this saved value using the method
                :py:meth:`SessionListItem.is_changed`
        """

        if _id in self._items:
            raise KeyError(
                'Another item with the _id(%s) already exists in ``self._items``'
            )

        # Create/Colour/Add Widget
        # ========================
        widget = SessionListItem( val, _id, saved_val )

        # if no normal-colour is set, create it based on default
        if 'default_brush' not in self._colours:
            self._colours['default_brush'] = {
                'fg': widget.foreground(),
                'bg': widget.background(),
            }

        self._list.addItem( widget )

        # set colour
        self._handle_item_statuschanged( widget, widget.is_new(), widget.is_changed() )


        # internal data
        # =============
        if widget.is_new():
            self._newitems.add( widget.id() )
        elif val != saved_val:
            self._changeditems.add( widget.id() )

        self._items[ widget.id() ] = widget

        # connections
        widget.status_changed.connect( self._handle_item_statuschanged )

    def remove_item(self, _id ):
        """
        Removes a single item from the list.

        Args:
            _id (object, optional):
                The `_id` of the item that you want to delete.
        """

        if _id not in self._items:
            return

        # manage internal data
        widget = self._items[_id]

        if widget.is_new():
            self._newitems.remove(_id)

        elif widget.is_changed():
            self._changeditems.remove(_id)
            self._delitems.add(_id)
        else:
            self._delitems.add(_id)

        # remove widget from list
        row  = self._list.row(widget)
        item = self._list.takeItem(row)

        # remove item from tracked items
        self._items.pop(_id)

    def clear(self):
        """
        Clears the list, and all internal data.
        """
        self._list.clear()

        self._items        = {}
        self._newitems     = set()
        self._delitems     = set()
        self._changeditems = set()

    def _handle_item_changed(self, item):
        """
        Handles whenever an item's text is changed.
        """
        item.refresh_status()

    def _handle_item_statuschanged(self, item, is_new, is_changed):
        """
        Handles contextual colour-changes, etc.
        """

        _id = item.id()

        if is_new:
            if 'new' in self._colours:
                item.setForeground( QtGui.QBrush(self._colours['new']['fg']) )
                item.setBackground( QtGui.QBrush(self._colours['new']['bg']) )

            # new-items will already be tracked


        elif is_changed:
            if 'changed' in self._colours:
                item.setForeground( QtGui.QBrush(self._colours['changed']['fg']) )
                item.setBackground( QtGui.QBrush(self._colours['changed']['bg']) )

            self._changeditems.add( _id )


        else:
            if 'normal' in self._colours:
                item.setForeground( QtGui.QBrush(self._colours['normal']['fg']) )
                item.setBackground( QtGui.QBrush(self._colours['normal']['bg']) )
            else:
                item.setForeground( self._colours['default_brush']['fg'] )
                item.setBackground( self._colours['default_brush']['bg'] )

            if _id in self._newitems:
                self._newitems.remove( _id )

            elif _id in self._changeditems:
                self._changeditems.remove( _id )

            # deleted items have no widgets!

    def selectedItems(self):
        """
        Wraps :py:meth:`QtWidgets.QListWidget.selectedItems` , and returns
        all selected :py:obj:`SessionListItems` .
        """
        return self._list.selectedItems()


    def _handle_itemDoubleClicked(self, item):
        """
        When an item is double-clicked, toggle
        widget edit/save mode.
        """

        if QtCore.Qt.ItemIsEditable in item.flags():
            item.setFlags( item.flags() ^ QtCore.Qt.ItemIsEditable )
        else:
            item.setFlags( item.flags() | QtCore.Qt.ItemIsEditable )



class SessionListItem( SessionWidgetItemBase, QtCore.QObject, QtWidgets.QListWidgetItem ):
    def __init__(self, val, _id, saved_val=None ):
        SessionWidgetItemBase.__init__(self, val, _id, saved_val )
        QtCore.QObject.__init__(self)
        QtWidgets.QListWidgetItem.__init__(self)
        self.setText( str(val) )

    def get_value(self):
        """
        Returns the QListWidget's text.
        """
        return self.text()



if __name__ == '__main__':
    from qconcurrency import QApplication
    from Qt import QtGui

    with QApplication():

        colours = {
            'changed':{
                'fg':QtGui.QColor(30,30,30),
                'bg':QtGui.QColor(170,70,50),
            },
            'new':{
                'fg':QtGui.QColor(30,30,30),
                'bg':QtGui.QColor(180,140,50),
            },
        }

        slist = SessionList( colours )
        slist.show()

        slist.add_item( 'A' )
        slist.add_item( 'B' )
        slist.add_item( 'C',  _id=3, saved_val='C' )
        slist.add_item( 'D1', _id=4, saved_val='D' )

