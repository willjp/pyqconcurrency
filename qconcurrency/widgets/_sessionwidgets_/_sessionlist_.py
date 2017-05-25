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
#external
from Qt import QtWidgets, QtCore, QtGui
#internal


#!TODO: _SessionListWidget should update SessionList by signals
#!       * when `setText` is called
#!       * when `change_id` is called

#!TODO: each item should have `is_changed` method

class SessionList( QtWidgets.QWidget ):
    save_requested = QtCore.Signal()
    def __init__(self):
        QtWidgets.QListWidget.__init__(self)

        # Attributes
        self._newitems     = set()
        self._delitems     = set()
        self._changeditems = set()

        self._list         = None  # QListWidget instance
        self._items        = {}    # { id : listwidgetitem }

        self._initui()

    def _initui(self):
        # Create Widgets
        layout     = QtWidgets.QVBoxLayout()
        self._list = QtWidgets.QListWidget()

        # Position Widgets
        self.setLayout(layout)
        layout.addWidget( self._list )

        # Widget Attributes
        layout.setContentsMargins( 0,0,0,0 )

    def addItem(self, text, _id=None, is_new=False ):
        """
        Adds a single item to the list.

        Args:
            text (str):
                The text you would like to add to the list.

            _id (int, str, optional):
                The databaseId, uuid, or other identifier
                that is unique at least to this list.

                If this item is new, and no `_id` value is provided,
                a uuid will be assigned to the item.

            is_new (bool, optional):
                If True, this item will be tracked as a new item.
                If False, this item will be tracked as an item that
                already exists in long-term-storage (database, config, ...)
        """

        if not _id:
            if is_new:
                _id = uuid.uuid4().hex
            else:
                raise RuntimeError(
                    '`SessionList.addItem()` expects you to provide a value for `_id` '
                    'when you are addint an item that is not new'
                )

        widget = _SessionListWidget( _id, text, is_new )
        self._list.addItem( widget )
        self._items[ _id ] = widget

        if is_new:
            self._newitems.add( _id )

    def addItems(self, items):
        """
        Args:
            items (dict, list):
                If items already exist in the database, provide an OrderedDict
                with the id as the key.

                .. code-block:: python

                    OrderedDict([ (123,'A)',(124,'B'),(125,'C') ])

                If items do not yet exist in the database (or other long-term storage),
                simply provide a list, and ids will be assigned to items.


                .. code-block:: python

                    [ 'A','B','C' ]

        """
        pass

    def items_and_ids(self):
        """
        Returns a dictionary of all widgets contained within the listwidget
        in the form of ``{ id : listwidgetitem }``.

        Returns:

            .. code-block::

                {
                    12345                             : <_SessionListWidget instance>,   # non new-items generally use database-ids
                    12346                             : <_SessionListWidget instance>,
                    'a87a8dd6e62f4a53a268afb43cac1d96': <_SessionListWidget instance>,   # new-items generally use uuids
                }

        """
        return self._items



class _SessionListWidget( QtWidgets.QListWidgetItem ):
    """
    Custom QListWidgetItem, stores additional info
    """
    def __init__(self, _id, text, is_new=False ):
        QtWidgets.QListWidgetItem.__init__(self, str(text) )

        if not isinstance( is_new, bool ):
            raise TypeError(
                'Expected bool for argument `is_new`, received type %s' % type(is_new)
            )

        self._id     = _id
        self._is_new = is_new

    def is_new(self):
        """
        Returns True/False depending on whether the data this
        widget represents is marked as being stored in long-term-storage.
        """
        return bool(self._is_new)

    def id(self):
        """
        Returns the id of the current object (either long-term-storage id, or
        an assigned :py:obj:`uuid`)
        """
        return self._id

    def change_id(self, _id, is_new=None ):
        """
        Allows you to modify the Id of the current item,
        in addition to allowing you to change the item's `new`
        status (whether or not the item is marked as existing
        in long-term-storage with this id).

        Args:
            _id (int, str):
                The databaseId, uuid, or other identifier
                that is unique at least to this list.

            is_new (bool, optional): ``(ex:  None, True, False )``
                By default, the `new` status is left untouched,
                but you may set it to ``True`` or ``False``.
        """

        self._id = _id

        if is_new != None:
            self._is_new == is_new




if __name__ == '__main__':
    from qconcurrency import QApplication

    with QApplication():

        slist = SessionList()
        slist.show()

        slist.addItem( 'A', is_new=True )
        slist.addItem( 'B', is_new=True )

        print( slist.items_and_ids() )

