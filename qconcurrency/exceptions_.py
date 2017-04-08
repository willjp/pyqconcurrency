#!/usr/bin/env python
"""
Name :          qconcurrency.exceptions_.py
Created :       Apr 08, 2017
Author :        Will Pittman
Contact :       willjpittman@gmail.com
________________________________________________________________________________
Description :   All exceptions used by qconcurrency package.
________________________________________________________________________________
"""
#builtin
from __future__    import unicode_literals
from __future__    import absolute_import
from __future__    import division
from __future__    import print_function



class UserCancelledOperation( Exception ):
    """
    If a user cancels an operation.
    """
    pass


