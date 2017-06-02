#!/usr/bin/env python
"""
Name :          qconcurrency.widgets._updaterwidgets_.updaterlist_.py
Created :       May 25, 2017
Author :        Will Pittman
Contact :       willjpittman@gmail.com
________________________________________________________________________________
Description :   Widgets to use as baseclasses for other widgets within this
                system.
________________________________________________________________________________
"""
#builtin
from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import uuid
import sys
import os
#package
#external
from Qt import QtWidgets, QtCore, QtGui
#internal


class SessionWidgetBase( object ):
    """
    BaseWidget for SessionWidgets.

    SessionWidgets are collection-widgets that are designed to
    allow the user to perform several operations, and then save
    them all at once.
    """
    save_requested = QtCore.Signal( dict ) #: output of :py:meth:`get_changes`
    def __init__(self):

        self._items        = {}
        self._newitems     = set()
        self._delitems     = set()
        self._changeditems = set()

    def has_changes(self):
        """
        Returns True if this widget has any unsaved changes.
        """
        if any([ self._newitems, self._delitems, self._changeditems ]):
            return True
        return False

    def get_changes(self):
        """
        Returns a dict of unsaved changes that this
        widget contains.

        Returns:

            .. code-block:: python

                {
                    'new':     { _id : widget, ... },
                    'deleted': set([ _id, _id, ... ]),
                    'changed': { _id : widget, ... },
                }
        """

        newitems     = {}
        delitems     = {}
        changeditems = {}

        for _id in self._newitems:
            newitems[_id] = self._items[_id]

        for _id in self._changeditems:
            changeditems[_id] = self._items[_id]

        return {
            'new':     newitems,
            'deleted': self._delitems,
            'changed': changeditems,
        }

    def save_changes(self):
        """
        If checks for unsaved new,changed, or deleted items,
        and if changes exist, emits :py:attr:`save_requested` signal.

        It is up to the calling class/method to handle
        the actual saving of the information, and as items
        are saved, this widget can be updated using the method
        :py:meth:`SessionWidgetItemBase.set_saved`.
        """
        if not self.has_changes():
            return

        self.save_requested.emit( self.get_changes() )

    def items(self):
        """
        Returns a dictionary in the format of ``{ _id:item }``
        """
        return self._items



class SessionWidgetItemBase( object ):
    """
    Parent class for all SessionWidgetItems
    (items that get added a :py:obj:`SessionWidget`

    Establishes consistent variables for subclasses,
    and provides convenience methods.
    """
    status_changed = QtCore.Signal( object, bool, bool, bool )  # (self, is_new, is_changed, is_editable )
    def __init__(self, val, _id=None, saved_val=None ):
        """
        Args:
            val (object):
                The value assigned to your object.
                This will be displayed in the widget.

            _id (str, int, optional):
                An id, unique to the collection of items the main.
                If this is a new item (no saved_val is provided)
                this argument is optional, and a uuid will be assigned
                in it's place.

            saved_val (object, optional):
                The value stored in long-term-storage.
                (database, json, etc). The presence of this
        """

        if saved_val == None:
            is_new    = True
            saved_val = uuid.uuid4().hex
        else:
            is_new = False

        ## Attributes
        self._saved_val   = saved_val                   # value saved in database
        self._is_new      = is_new                      # True/False if item is entirely untracked in database
        self._is_changed  = bool( val != saved_val )
        self._is_editable = False
        self._id          = self._get_id( _id, is_new ) # databaseId, or uuid for new items
        self._val         = val                         # the current value of the widget

    def _get_id(self, _id, is_new):
        """
        Returns a value for `_id`.

            * if the item is new and an id has been assigned to it, use that.
            * if the item is new, and no Id has been assigned to it, a uuid is assigned.
            * if the item is not new, and an id has been assigned to it, use that.

            * if the item is not new, and no id has been assigned, error.

        Args:
            _id (str, int, optional):
                An id, unique to the collection of items the main.
                If this is a new item (no saved_val is provided)
                this argument is optional, and a uuid will be assigned
                in it's place.

            is_new (bool):
                True/False indicating if this object represents an item
                that is not saved in long-term-storage.
        """

        if not _id and not is_new:
            raise RuntimeError(
                'Non New items are expected to already be assigned a value for `_id`'
                'and ``__init__`` should be provided with it'
            )

        if not _id:  _id = uuid.uuid4().hex
        else:        _id = _id

        return _id

    def get_savedval(self):
        """
        Returns the value that is currently saved in the database.

        .. note::

            If this is a new item, ``None`` will be returned.
        """
        if self._is_new:
            return None
        return self._saved_val

        self.refresh_status()

    def set_saved(self, _id=None ):
        """
        Marks the information represented by this widget as
        correct, and saved into long-term storage.

            * Changes the item's id *(if _id is specified )*
            * sets the current val to ``self._saved_val``
            * calls ``self.refresh_status()``

        Args:
            _id (object, optional):
                If the long-term-storage id has changed as
                a result of this widget's info being saved,
                you may provide a new value for ``self._id``
        """

        if _id != None:
            self._id = _id

        self._saved_val  = self.get_value()

        if self._is_new or self._is_changed:
            self._is_new     = False
            self._is_changed = False
            self.status_changed.emit(
                self,
                self._is_new,
                self._is_changed,
                self.is_editable(),
            )

    def get_value(self):
        """
        A dummy method that should be re-implemented in
        subclasses of :py:obj:`SessionWidgetItemBase`.

        This method should retrieve the current value from
        the widget.
        """
        raise NotImplementedError(
            '%s has not implemented the method `refresh_status`' % (
                self.__class__.__name__
            )
        )

    def refresh_status(self):
        """
        Re-Checks all status information, refreshing it's
        internal status, and emitting :py:attr:`status_changed`
        if it has changed.
        """

        # Check for changes
        self._val = self.get_value()

        if self._val == self._saved_val:   is_changed = False
        else:                              is_changed = True

        is_new      = self.is_new()

        is_editable = self.is_editable()

        # (is_new only changes in `self.set_saved`)
        if any([
                is_changed    != self._is_changed,
                self.is_new() != self._is_new,
                is_editable   != self._is_editable,
            ]):

            self._is_changed  = is_changed
            self._is_editable = is_editable
            self._is_new      = is_new

            self.status_changed.emit(
                self,
                self._is_new,
                self._is_changed,
                self.is_editable(),
            )

    def is_changed(self):
        """
        Returns True/False if the widget's current value is different
        than it's saved-value.
        """
        if self._is_new:
            return True

        if self.get_value() == self._saved_val:
            return False

        return True

    def is_new(self):
        """
        Returns True/False if the widget is new or not.
        """
        return self._is_new

    def is_editable(self):
        """
        Returns ``True`` if the widget is currently editable.
        Otherwise returns ``False``.
        """

        if self.flags() & QtCore.Qt.ItemIsEditable:
            self._is_editable = True
            return True

        self._is_editable = False
        return False

    def setFlags(self,*args,**kwds):
        """
        Sets the widget's flags, then checks if there is a change
        to the editable status (emitting :py:attr:`status_changed`
        if there is a change).
        """
        orig_status = self.is_editable()
        QtWidgets.QListWidgetItem.setFlags(self,*args,**kwds)

        is_editable = self.is_editable()

        if is_editable != orig_status:
            self.status_changed.emit(
                self,
                self._is_new,
                self._is_changed,
                is_editable,
            )

    def id(self):
        """
        Returns the item's Id
        """
        return self._id




if __name__ == '__main__':
    pass

