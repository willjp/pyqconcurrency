#!/usr/bin/env python
"""
Name :          qconcurrency.widgets._dictcombobox_.py
Created :       Apr 08, 2017
Author :        Will Pittman
Contact :       willjpittman@gmail.com
________________________________________________________________________________
Description :   Custom QComboBox that stores a key/value pair instead
                of a list.
________________________________________________________________________________
"""
#builtin
from __future__    import unicode_literals
from __future__    import absolute_import
from __future__    import division
from __future__    import print_function
from   collections import MutableMapping, OrderedDict
#external
from   Qt          import QtWidgets


#!TODO: setModel( model, columns = {'id': 1, 'name':2, ...} )
#!      (then you could retrieve very contextual info about the item)

#!TODO: when the selection changes, should we emit the entire row
#!      as a signal? or just the index?

#!TODO: models should always be updated in the UI thread,
#!      but we can update them just like I have been updating
#!      the widgets (only it is a model instead of the widget)

class ModelComboBox( QtWidgets.QComboBox ):
    def __init__(self):

    def __getitem__(self, key):
        """
        This :py:obj:`QComboBox` can be used as if it were
        a dictionary
        """
        return self.data[ key ]

    def keys(self):
        return self.data.keys()

    def values(self):
        return self.data.values()




if __name__ == '__main__':
    pass

