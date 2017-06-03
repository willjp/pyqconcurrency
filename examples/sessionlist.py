"""
An example of `qconcurrency.widgets.SessionList`


"""
import os
import sys
qconcurrency_path = '/'.join(os.path.realpath(__file__).replace('\\','/').split('/')[:-2])
sys.path.insert(0, qconcurrency_path )

from   qconcurrency            import QBaseWindow
from   qconcurrency.widgets    import SessionList
from   Qt                      import QtCore, QtWidgets, QtGui

import time

class FakeDBCursor( object ):
    """
    A fake database cursor, for the sake of this example
    """
    def __init__(self):
        self.lastrowid = 100

    def execute(self, sql, **kwds ):
        print( sql.format(**kwds) )
        self.lastrowid +=1



class GroceryList( QtWidgets.QWidget ):
    """
    An example of a SessionWidget.
    """
    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        self._initui()

    def _initui(self):
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

        # Create Widgets
        layout     = QtWidgets.QVBoxLayout()
        actionbar  = QtWidgets.QHBoxLayout()
        self._list = SessionList( colours )
        add_btn    = QtWidgets.QPushButton('+ Add Item')
        del_btn    = QtWidgets.QPushButton('- Del Item')
        self._save_btn = QtWidgets.QPushButton('Save')

        # Position Widgets
        self.setLayout( layout )
        layout.addWidget( self._list )
        layout.addLayout( actionbar )

        actionbar.addStretch(1)
        actionbar.addWidget( del_btn )
        actionbar.addWidget( add_btn )
        actionbar.addWidget( self._save_btn )

        # Widget Attrs
        self._list.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )

        # Connections
        self._list.save_requested.connect(
            self._handle_save_changes
        )
        del_btn.clicked.connect(
            self._handle_delete_item
        )
        add_btn.clicked.connect(
            self._handle_add_item
        )
        self._save_btn.clicked.connect(
            self._handle_save
        )

    def load(self):
        """
        Loads 3x items, representing saved data
        """
        self._list.clear()

        fake_database_items = {
            1 : 'Rice',
            2 : 'Chicken',
            3 : 'Soup Stock',
        }

        for _id in fake_database_items:
            text = fake_database_items[ _id ]
            self._list.add_item( text, _id=_id, saved_val=text )

    def _handle_save_changes(self, changes):
        """
        Called when :py:meth:`save_changes` is emitted.

        This example will:
            * update our fake SQL database
            * update widget colours
            * update self._delitems, self._newitems, self._changeditems
              as information is `saved` to our fake database
        """

        # a fake database cursor
        cursor = FakeDBCursor()


        # Saved Items
        # ===========
        for _id in changes['new'].keys():
            widget = changes['new'][_id]
            cursor.execute((
                'INSERT INTO groceryTable \n'
                '       ( food_type )     \n'
                'VALUES ({food_type})     \n'),
                food_type = widget.text()
            )

            # update internaldata, UI colours
            widget.set_saved( _id=cursor.lastrowid )


        # Changed Items
        # =============
        for _id in changes['changed'].keys():
            widget = changes['changed'][_id]
            cursor.execute((
                'UPDATE groceryTable            \n'
                'SET    food_type = {food_type} \n'
                'WHERE  food_Id   = {food_Id}   \n'),
                food_type = widget.text(),
                food_Id   = _id,
            )

            # update internaldata, UI colours
            widget.set_saved( _id=cursor.lastrowid )

        # Deleted Items
        # =============
        if changes['deleted']:
            cursor.execute((
                    'DELETE FROM groceryTable      \n'
                    'WHERE       food_Id IN ( %s ) \n'
                ) % ','.join([str(_id) for _id in changes['deleted'] ])
            )

        self._delitems = set()

    def _handle_delete_item(self):
        selitems = self._list.selectedItems()

        if not selitems:
            return

        for widget in selitems:
            self._list.remove_item( widget.id() )

    def _handle_add_item(self):
        self._list.add_item( '' )

    def _handle_save(self):
        self._list.save_changes()



if __name__ == '__main__':
    from qconcurrency import QApplication


    with QApplication():
        glist = GroceryList()
        glist.load() # load some bogus saved-data
        glist.show()


