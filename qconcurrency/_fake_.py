#!/usr/bin/env python
"""
Name :          qconcurrency._fake_.py
Created :       May 24, 2017
Author :        Will Pittman
Contact :       willjpittman@gmail.com
________________________________________________________________________________
Description :   A fake object, allowing the use of arbitrary attributes/methods
                without exceptions.
________________________________________________________________________________
"""
#builtin
from   __future__    import unicode_literals
from   __future__    import absolute_import
from   __future__    import division
from   __future__    import print_function
import sys
import os
#package
#external
#internal


class Fake( object ):
    """
    A fake standin object, that allows you to get/call non-existant
    attributes on it. Like :py:obj:`mock.Mock`, but more portable
    and less utilitarian (this will work, for example in cx_freeze_).

    .. _cx_freeze: https://anthony-tuininga.github.io/cx_Freeze/

    This exists in this library so that you may define
    methods that can be used within :py:obj:`ThreadedTask` ,
    but can also be called outside of a thread (simply ignoring all signals)

    Example:

    .. code-block:: python

        Fake()
        >>> <qconcurrency.Fake object at 0x7fef27891c10>

        Fake().fake.fake.fake
        >>> <qconcurrency.Fake object at 0x7fef27774450>

        Fake().fake.fake.fake( 'cool', 'you get the point' )
        >>> <qconcurrency.Fake object at 0x7fef277123c0>

        """
    def __init__(self, *args, **kwds ):
        """
        Accepts/ignores any number of parameters
        """
        object.__init__(self)

    def __call__(self,*args,**kwds):
        return Fake()

    def __iter__(self):
        yield Fake()

    def __getattribute__(self, attr):
        """
        Accepts/ignores any request for an attribute
        """
        return Fake()



if __name__ == '__main__':
    import time
    import supercli.logging
    supercli.logging.SetLog(lv=10)

    def test_fake():
        fake = Fake()
        print( fake.fake.fake )


    def runtests():
        test_fake()

    runtests()
