#!/usr/bin/env python
"""
Name :          mfw_osTest.py
Created :       February 28 2015
Author :        Will Pittman
Contact :       willjpittman@gmail.com
________________________________________________________________________________
Description :   checks operating system running maya so adjustments can be made to paths and
                environment
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

loc = locals

#!TODO: instead of using toctree,
#!      just use :doc: references.

class GenerateAPI( object ):
    def __init__(self, projectroot, docroot, exclude_private=True, ignore_dirs=['/.tox/','/docs/','/tests/'] ):

        # Arguments
        self._projectroot = projectroot
        self._docroot     = docroot
        self._ignore_dirs = ignore_dirs
        self._exclude_private = exclude_private


        pymodules = self.find_modules()

        self.write_root_modules_page( pymodules )

    def find_modules(self):
        """

        Returns:

            set(['proj.module', 'proj.module.other'])
        """

        pymodules = set() # ['file.doc', 'file.doc.something']

        for (root,dirnames,filenames) in os.walk( self._projectroot ):

            # early exit
            if any([ x in root for x in self._ignore_dirs ]):
                continue

            for filename in filenames:
                if filename[-3:] == '.py':

                    # exclude __init__
                    if filename == '__init__.py':
                        continue

                    # exclude private
                    if filename[0] == '_' and self._exclude_private:
                        continue

                    # exclude setup.py
                    if '{root}/{filename}'.format(**loc()) == '%s/setup.py' % self._projectroot:
                        continue

                    filepath = '{root}/{filename}'.format(**loc())
                    modpath  = filepath.replace( self._projectroot, '' )[1:]
                    modpath  = modpath.replace('.py','').replace('/','.')
                    pymodules.add( modpath )

            for dirname in dirnames:
                package = '{root}/{dirname}/__init__.py'.format(**loc())
                if os.path.isfile( package ):
                    module = '{root}/{dirname}'.format(**loc())
                    module = module.replace( self._projectroot, '' )[1:]
                    module = module.replace('/','.')
                    pymodules.add( module )

        return pymodules

    def write_root_modules_page(self, pymodules):
        """
        writes ``_api/modules.rst``

        (the root page that modules are accessed from)
        """
        root_modules = set()

        for pymodule in pymodules:
            if '.' not in pymodule:
                root_modules.add( pymodule )

        projectname = self._projectroot.split('/')[-1]

        fileconts  = projectname +'\n'
        fileconts += '=' *len(projectname) +'\n'
        fileconts += '\n'

        fileconts += (
            '.. toctree::\n'
            '   :maxdepth: 5\n'
            '\n'
            '   '
        )
        fileconts += '\n   '.join(root_modules)
        fileconts += '\n\n'


        if not os.path.isdir( '%s/source/_api' % self._docroot ):
            os.makedirs( '%s/source/_api' % self._docroot )

        with open( '%s/source/_api/modules.rst' % self._docroot, 'w' ) as fw:
            fw.write( fileconts )

    def write_module_page(self, pymodule):
        """
        writes a page for each pymodule.
        (listing each class/function in the class)
        """
        pass



#.. autoclass:: qconcurrency.widgets.DictModelQMenu
#    :members:
#    :undoc-members:
#    :show-inheritance:


if __name__ == '__main__':
    import os

    print( os.path.realpath('..')  )
    GenerateAPI( projectroot=os.path.realpath('..'), docroot=os.path.realpath('.') )

