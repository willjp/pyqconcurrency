
from   qconcurrency import Fake
from   Qt           import QtWidgets
import unittest


# NOTE: QApplication is very hard to test, it basically lives for the duration
#       of the tests once it has been initialized.


class Test_Fake( unittest.TestCase ):
    def test_attr(self):
        fake = Fake()
        fake.fake.fake

    def test_callable_attr(self):
        fake = Fake()
        fake.fake.fake('a','b',c='c')

    def test_callable_then_attr(self):
        fake = Fake()
        fake.fake.fake('a',b='b').fake


