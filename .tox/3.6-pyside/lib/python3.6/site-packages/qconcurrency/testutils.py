#builtin
from __future__    import unicode_literals
from __future__    import absolute_import
from __future__    import division
from __future__    import print_function
import sys

__all__ = [
    'mock',
]

_major = sys.version_info[0]
_minor = sys.version_info[1]

if   _major <= 2:
    import mock
else:
    from unittest import mock




if __name__ == '__main__':
    pass
