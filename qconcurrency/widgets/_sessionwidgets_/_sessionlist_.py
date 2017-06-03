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
import copy
#package
from qconcurrency.widgets._sessionwidgets_._basewidgets_ import (
    SessionWidgetBase, SessionWidgetItemBase
)
#external
from Qt import QtWidgets, QtCore, QtGui
#internal


#!NOTE: cannot create item-specific highlight colours.
#!      ex:  lighter variation of 'new', or 'changed'
#!
#!      using transparency in QColor also does not work.
#!      the colour is overlaid on top of the window, not
#!      the QListWidgetItem's background.
#!
#!      In order to have per-listwidgetitem colours,
#!      We would need to implement our own custom delegates,
#!      with customized paintEvent() methods.
#!

class SessionList( SessionWidgetBase, QtWidgets.QWidget ):
    changes_exist = QtCore.Signal(bool) #: True/False if unsaved changes exist
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
                        'editable': {'fg':QColor(255,255,255), 'bg':QColor(255,255,255)},
                    }

        """
        SessionWidgetBase.__init__(self)
        QtWidgets.QWidget.__init__(self)

        # Attributes
        if not colours:   self._colours = {}
        else:             self._colours = colours

        self._default_palette  = copy.copy( self.palette() )  #: the default QlistWidget palette
        self._editable_widgets = set() #: every widget that is currently editable


        # Widgets
        self._list = None  # the QListWidget managed by this class

        self._initui()

    def _initui(self):

        # Create Widgets
        layout     = QtWidgets.QVBoxLayout()
        self._list = _DeselectableListWidget()

        # Position Widgets
        self.setLayout( layout )
        layout.addWidget( self._list )

        # Widget Attrs
        layout.setContentsMargins(0,0,0,0)

        # Connections
        self._list.itemChanged.connect( self._handle_item_changed )
        self._list.itemDoubleClicked.connect( self._handle_itemDoubleClicked )
        self._list.itemSelectionChanged.connect( self._handle_itemSelectionChanged )
        self._list.itemDelegate().closeEditor.connect( self._handle_itemeditfinished )

    def clear(self):
        """
        Clears the list, and all internal data.
        """
        self._list.clear()

        self._items        = {}
        self._newitems     = set()
        self._delitems     = set()
        self._changeditems = set()

        self._last_selected = None

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
        self._handle_item_statuschanged(
            widget,
            widget.is_new(),
            widget.is_changed(),
            widget.is_editable()
        )


        # internal data
        # =============
        if widget.is_new():
            self._newitems.add( widget.id() )
        elif val != saved_val:
            self._changeditems.add( widget.id() )

        self._items[ widget.id() ] = widget

        # connections
        widget.status_changed.connect( self._handle_item_statuschanged )

        # emit changes
        self.changes_exist.emit( self.has_changes() )

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


        # notify any widgets if we have any unsaved changes
        self.changes_exist.emit( self.has_changes() )


    def setSelectionMode(self, selectionMode):
        """
        Wraps :py:meth:`QListWidget.setSelectionMode`
        """
        return self._list.setSelectionMode( selectionMode )

    def setSelectionModel(self, selectionModel):
        """
        Wraps :py:meth:`QListWidget.setSelectionModel`
        """
        return self._list.setSelectionModel( selectionModel )

    def selectedItems(self):
        """
        Wraps :py:meth:`QtWidgets.QListWidget.selectedItems` , and returns
        all selected :py:obj:`SessionListItems` .
        """
        return self._list.selectedItems()

    def keyPressEvent(self, event):
        """
        If an item is selected in the list, the last-item in the selection
        is toggled between editable and normal modes.
        """
        selected_items = self._list.selectedItems()
        if selected_items:

            if event.key() == QtCore.Qt.Key_Enter  or  event.key() == QtCore.Qt.Key_Return:

                # deselect all items except for the last selected
                for i in range(len(selected_items) -1):
                    selected_items[i].set_editable(False)
                    selected_items[i].setSelected(False)

                # toggle editability of last item
                selected_items[-1].toggle_editable()

        QtWidgets.QWidget.keyPressEvent(self,event)


    def _handle_item_changed(self, item):
        """
        Handles whenever an item's text is changed.
        """
        item.refresh_status()

    def _handle_item_statuschanged(self, item, is_new, is_changed, is_editable ):
        """
        Runs whenever an item's status changes.

        Status changes include new, changed, or editable.

            * widgets colours are modified (if colours were set for the current status)
            * internal-data is updated, keeping track of new/changed items.
        """

        _id = item.id()

        # Update Internal Data
        # ====================
        if is_new:
            # new-items will already be tracked,
            pass

        elif is_changed:
            self._changeditems.add( _id )


        else:
            # if item is not new, but it is still tracked
            # internally under self._newitems,
            # (it's saved-data has been updated),
            # update internal-data so that it looks like a
            # normal item.
            if _id in self._newitems:
                self._newitems.remove( _id )

            elif _id in self._changeditems:
                self._changeditems.remove( _id )

        # emit changes_exist
        if self.has_changes():   self.changes_exist.emit(True)
        else:                    self.changes_exist.emit(False)


        # Set Colours
        # ===========
        if is_editable:
            if 'editable' in self._colours:
                item.setForeground( QtGui.QBrush(self._colours['editable']['fg'] ) )
                item.setBackground( QtGui.QBrush(self._colours['editable']['bg'] ) )

                # highlight should match editable colour
                highlight_palette = copy.copy( self._default_palette )

                highlight_palette.setColor(
                    QtGui.QPalette.Highlight,
                    self._colours['editable']['bg']
                )
                highlight_palette.setColor(
                    QtGui.QPalette.HighlightedText,
                    self._colours['editable']['fg'],
                )
                self.setPalette( highlight_palette )
                self._editable_widgets.add( item )
                return

        self.setPalette( self._default_palette )
        if is_new:
            if 'new' in self._colours:
                item.setForeground( QtGui.QBrush(self._colours['new']['fg']) )
                item.setBackground( QtGui.QBrush(self._colours['new']['bg']) )
                return

        if is_changed:
            if 'changed' in self._colours:
                item.setForeground( QtGui.QBrush(self._colours['changed']['fg']) )
                item.setBackground( QtGui.QBrush(self._colours['changed']['bg']) )
                return


        # normal colours
        if 'normal' in self._colours:
            item.setForeground( QtGui.QBrush(self._colours['normal']['fg']) )
            item.setBackground( QtGui.QBrush(self._colours['normal']['bg']) )
        else:
            item.setForeground( self._colours['default_brush']['fg'] )
            item.setBackground( self._colours['default_brush']['bg'] )

    def _handle_itemDoubleClicked(self, item):
        """
        When an item is double-clicked, toggle
        widget edit/normal mode.
        """
        item.toggle_editable()

    def _handle_itemSelectionChanged(self):
        """
        Whenever the selection changes in the listwidget,
        makes all un-selected widgets *not* editable.

        (this also has the effect of restoring their `normal` colour).
        """
        selected_items = self.selectedItems()

        # unset editable on all unselected widgets
        for widget in self._editable_widgets.copy():
            if not any([ widget is selwidget   for selwidget in selected_items ]):
                widget.setFlags( widget.flags() ^ QtCore.Qt.ItemIsEditable )
                self._editable_widgets.remove( widget )

    def _handle_itemeditfinished(self, widget, modelcache ):
        """
        When the user finishes editing an item, refreshes it's status.
        """
        self._editable_widgets = set()

        for widget in self.selectedItems():
            widget.set_editable(False)



class _DeselectableListWidget( QtWidgets.QListWidget ):
    """
    Customized :py:obj:`QListWidget` that deselects
    all widgets whenever the user clicks empty space
    in the list.
    """
    def __init__(self,*args,**kwds):
        QtWidgets.QListWidget.__init__(self,*args,**kwds)

    def mousePressEvent(self, event):
        """
        If no :py:obj:`QListWidgetItem` is under the cursor,
        then clear the selection before handling the mousePressEvent.
        """
        # if LMB, and no widget is under cursor,
        # deselect all widgets.
        if event.button() is QtCore.Qt.LeftButton:
            if not self.itemAt( event.pos() ):
                self.clearSelection()

        return QtWidgets.QListWidget.mousePressEvent(self,event)



class SessionListItem( SessionWidgetItemBase, QtCore.QObject, QtWidgets.QListWidgetItem ):
    def __init__(self, val, _id, saved_val=None ):
        SessionWidgetItemBase.__init__(self, val, _id, saved_val )
        QtCore.QObject.__init__(self)
        QtWidgets.QListWidgetItem.__init__(self)

        # load
        self.setText( str(val) )

    def get_value(self):
        """
        Returns the QListWidget's text.
        """
        return self.text()

    def toggle_editable(self):
        """
        If the widget is currently editable,
        it's value is stored, otherwise makes editable.

        The status is refreshed on the widget.
        """

        # toggle widget editability
        if self.is_editable():
            self.set_editable(False)
        else:
            self.set_editable(True)

    def set_editable(self, status):
        """
        Sets the widget editable/not editable,
        and enters edit-mode.
        """
        if status:
            self.setFlags( self.flags() | QtCore.Qt.ItemIsEditable )
            self.listWidget().editItem(self)
        else:
            self.setFlags( self.flags() ^ QtCore.Qt.ItemIsEditable )



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
            'editable':{
                'fg':QtGui.QColor(30,30,30),
                'bg':QtGui.QColor(60,120,140),
            },
        }

        slist = SessionList( colours )
        slist.show()

        slist.add_item( 'A' )
        slist.add_item( 'B' )
        slist.add_item( 'C',  _id=3, saved_val='C' )
        slist.add_item( 'D1', _id=4, saved_val='D' )


