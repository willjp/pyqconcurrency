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
#internal

class SessionWidgetBase( object ):
    pass


class SessionWidgetItemBase( object ):
    def __init__(self, val, _id=None, *args, **kwds ):
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

        (is_new, saved_val) = self._get_savedval( args, kwds )


        ## Attributes
        self._saved_val = saved_val                   # value saved in database
        self._is_new    = is_new                      # True/False if item is entirely untracked in database
        self._id        = self._get_id( _id, is_new ) # databaseId, or uuid for new items
        self._val       = val                         # the current value of the widget

    def _get_savedval(self, args, kwds):
        """
        Assigns any of the following to be the saved-val,
        otherwise defaults to a uuid:

            * the 3rd positional argument
            * a keyword called `saved_val`
        """

        # by default, saved_val will be set to to
        # a uuid (to prevent unintended clashing)
        saved_val = uuid.uuid4().hex
        is_new    = True

        if len(args) and len(kwds):
            raise TypeError(
                '%s expects a maximum of 3x arguments. received %s' % (
                    self.__class__.__name__, (2+len(args)+len(kwds)) )
            )

        if kwds:
            for kwd in kwds:
                if kwd == 'saved_val':
                    saved_val = kwds['saved_val']
                    is_new    = False
                else:
                    raise TypeError(
                        '%s got an unexpected keyword argument \'%s\'' % (
                            self._class__.__name__, kwd)
                    )

        elif args:
            if len(args) == 1:
                saved_val = args[0]
                is_new    = False
            else:
                raise TypeError(
                    '%s expects a maximum of 3x arguments. received %s' % (
                        self.__class__.__name__, (2+len(args)+len(kwds)) )
                )

        return (is_new,saved_val)

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

        self._is_new    = False
        self._saved_val = self.get_value()

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
        A dummy method, that should be re-implmented
        in subclasses of :py:obj:`SessionWidgetItemBase`.

        This method should examine `self._is_new`, `self._saved_val`, and
        the output of `self.get_value`, and make any required adjustments
        to the widget (ex: perhaps a different colour is used to indicate
        a widget that is new/changed).
        """
        raise NotImplementedError(
            '%s has not implemented the method `refresh_status`' % (
                self.__class__.__name__
            )
        )

    def is_changed(self):
        """
        Returns True/False if the widget's current value is different
        than it's saved-value.
        """
        if self._is_new:
            return True

        if self.get_value() == self._saved_value:
            return False

        return True



if __name__ == '__main__':
    pass
