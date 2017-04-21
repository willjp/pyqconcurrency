#!/usr/bin/env python
"""
Name :          docs/apigen.py
Created :       Apr 19, 2017
Author :        Will Pittman
Contact :       willjpittman@gmail.com
________________________________________________________________________________
Description :   Alternative to `sphinx-apidoc`, that walks sourcetree,
                presents a single page per-callable, and adds a summary
                of all methods on pages displaying classes.
________________________________________________________________________________
"""
#builtin
from   __future__    import unicode_literals
from   __future__    import absolute_import
from   __future__    import division
from   __future__    import print_function
import logging
import inspect
import importlib
import sys
import os
#package
#external
import six
#internal

loc    = locals
logger = logging.getLogger(__name__)


class GenerateAPI( object ):
    """
    Alternative to `sphinx-apidoc` that presents one-class/function per-page,
    and pairs it with a summary of all methods, with their descriptions.

    Before running, you will need to make sure that the package being
    documented is on the ``$PYTHONPATH``.
    """
    def __init__(self, projectroot, docroot, exclude_types=('special','private','mangled','inherited'), include_types=None, ignore_dirs=['/.tox/','/docs/','/tests/'] ):
        """
        Args:
            projectroot (str): ``(ex: '/path/to/srctree' )``
                Path to the directory immediately above the
                package(s) you are documenting.

            docroot (str):     ``(ex: '/path/to/srctree/docs' )``
                Path to directory that your sphinx-docs are stored.
                ReStructuredText documentation will be rendered to
                subdirectory of it ``{docroot}/source/_api/``.

            exclude_types (list, optional):  ``(ex: ('private','mangled','public','special','inherited') )``
                Determines what types of callables, and modules
                will be visible in the documentation.

            ignore_dirs (list, optional): ``(ex: ['/.tox','/docs/','/tests/'] )``
                Any module-path containing any item in this list
                will not be documented.

        """

        # Arguments
        self._projectroot     = projectroot
        self._docroot         = docroot
        self._ignore_dirs     = ignore_dirs
        self._exclude_types   = exclude_types

        self._init()

    def _init(self):
        logger.info((
            '\n'
            'generating API using:\n'
            'projectroot: "%s" \n'
            'docroot:     "%s" \n'
            ) % (self._projectroot, self._docroot)
        )


        pymodules = self.find_modules()
        self.write_root_modules_page( pymodules )


        for pymodule in pymodules:
            try:
                self.write_module_page( pymodule )
            except:
                logger.error('Error occurred while working on module: %s' % pymodule)
                six.reraise( *sys.exc_info() )

    def find_modules(self):
        """

        Returns:

            set(['proj.module', 'proj.module.other'])
        """

        pymodules = set() # ['file.doc', 'file.doc.something']
        logger.info('gathering python modules...')

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
                    if any([ x in self._exclude_types for x in ('private','special','mangled') ]):
                        if filename[0] == '_':
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

        logger.info((
            'writing %s/source/_api/modules.rst \n'
            'modules: %s'
            ) % (self._docroot, repr(root_modules))
        )

    def write_module_page(self, pymodule):
        """
        writes a page for each pymodule.
        (listing each class/function in the class)
        """

        module = importlib.import_module( pymodule )


        _classes   = set([item[0] for item in inspect.getmembers( module, inspect.isclass    )])
        _functions = set([item[0] for item in inspect.getmembers( module, inspect.isfunction )])


        # remove all types that user wanted hidden
        for exclude_type in self._exclude_types:
            _classes = _classes.difference(
                set([ _class
                     for _class in _classes
                        if self.get_callable_type(_class) == exclude_type ])
            )
            _functions = _functions.difference(
                set([ _function
                     for _function in _functions
                        if self.get_callable_type(_function) == exclude_type ])
            )


        # respect __all__
        if hasattr( module, '__all__' ):
            module_all = set(getattr( module, '__all__' ))
            _classes   = _classes.intersection( module_all )
            _functions = _functions.intersection( module_all )


        self._write_module( pymodule, module, _classes, _functions )

    def _write_module(self, pymodule, module, classes, functions):
        """
        Args:
            pymodule (str):  ``(ex:  'os.path' )``
                The importpath of the module being documented.

            module (obj):
                The imported module at the above path

            classes (list(str)):
                List of classes contained in the module

            functions (list(str)):
                List of functions contained in the module
        """
        rstpath = '%s/source/_api/%s.rst' % (
            self._docroot, pymodule )
        logger.info( 'writing: %s' % rstpath)


        # Write Module
        # ============

        conts  = '\n'
        conts += pymodule +'\n'
        conts += '='* len(pymodule)
        conts += '\n'
        conts += '\n'

        conts += '.. module:: %s' % pymodule
        conts += '\n'


        if classes:
            conts += (
                'classes\n'
                '-------\n'
                '\n'
            )
            for _class in sorted(classes):
                conts+='   * :doc:`{pymodule}.{_class}`\n'.format(**loc())
            conts +='\n\n'

        if functions:
            conts += (
                'functions\n'
                '---------\n'
                '\n'
            )
            for _func in sorted(functions):
                conts+='   * :doc:`{pymodule}.{_func}`\n'.format(**loc())
            conts +='\n\n'

        with open( rstpath, 'w' ) as fw:
            fw.write( conts )



        # Write Indv Callable rstfiles
        # ============================
        if classes:
            for _class in classes:
                self._write_callable( pymodule, module, _class )

        if functions:
            for _func in functions:
                self._write_callable( pymodule, module, _func )

    def _write_callable(self, pymodule, module, callable_):
        """

        """

        callable_importpath = '%s.%s' % (pymodule,callable_)

        rstpath = '%s/source/_api/%s.rst' % (
            self._docroot, callable_importpath)
        logger.info( 'writing: %s' % rstpath)


        # Writing Callable file
        conts  = '\n'
        conts += callable_ +'\n'
        conts += '='*len(callable_)
        conts += '\n\n'



        if inspect.isfunction( getattr(module, callable_) ):
            conts += (
                'Documentation\n'
                '-------------\n'
                '\n\n'
                '.. autofunction:: %s\n'
                '\n\n'
            ) % callable_importpath


        elif inspect.isclass( getattr(module, callable_) ):

            conts += self._get_callable_toc( pymodule, module, callable_ )

            conts += (
                'Documentation\n'
                '-------------\n'
                '\n\n'
            )

            # autoclass
            # =========

            conts += (
                '.. autoclass:: %s\n'
                '   :members:\n'          # documented methods
                '   :undoc-members:\n'    # undocumented methods
                '   :show-inheritance:\n' # show base-classes
            ) %  callable_importpath

            if 'private' not in self._exclude_types:
                conts +='   :private-members:\n'

            if 'special' not in self._exclude_types:
                conts +='   :special-members:\n'

            if 'inherited' not in self._exclude_types:
                conts +='   :inherited-members:\n'

            conts += '\n\n'


            with open( rstpath, 'w' ) as fw:
                fw.write( conts )

    def _get_callable_toc(self, pymodule, module, callable_ ):
        """
        creates an autosummary directive at the top of
        """

        conts     = ''
        class_obj = getattr(module,callable_)

        if not inspect.isclass( class_obj ):
            return conts


        # Collect Info
        # ============

        # dynamically define a class, and retrieve a list
        # of it's attributes (so we can filter them out)
        builtin_attrs = dir(type('dummy', (object,), {}))

        methods    = set([ item for item in class_obj.__dict__  ])

        if '__dict__' in methods:
            methods.remove('__dict__')

        user_attrs = set([ item for item in methods
                                if not callable( getattr(class_obj,item) )  and item not in builtin_attrs ])




        # Attribute List
        # ==============

        if user_attrs:
            conts +=(
                'Attributes\n'
                '----------\n'
                '\n'
                '.. autosummary::\n'
                '\n'
            )
            for user_attr in sorted(list(user_attrs)):
                conts +='   {pymodule}.{callable_}.{user_attr}\n'.format(**loc())
            conts +='\n\n'


        # Method List
        # ===========



        conts +=(
            'Methods\n'
            '-------\n'
            '\n'
            '.. autosummary::\n'
            '\n'
        )


        # these are both involved in class initialization
        # and should always be documented
        # (in case they change how intialization works)
        # (for example, identifying singleton classes!)
        init_methods    = methods.intersection( set(['__init__','__new__']) )


        # organize methods by their type (private,public,special,mangled)
        methods_by_class = {}
        for method in methods:
            method_type = self.get_callable_type( method )

            if method_type not in methods_by_class:
                methods_by_class[ method_type ] = set()

            methods_by_class[ method_type ].add( method )


        # document methods in order (__init__, special, public, private, mangled )
        if init_methods:
            for method in init_methods:
                conts += '   {pymodule}.{callable_}.{method}\n'.format(**loc())

        for method_type in ('special','public','private','mangled'):
            if method_type not in self._exclude_types  and  method_type in methods_by_class:
                for method in sorted(list(methods_by_class[ method_type ])):
                    conts += '   {pymodule}.{callable_}.{method}\n'.format(**loc())
        conts+='\n\n'

        return conts

    def get_callable_type(self, callable_ ):
        """
        returns public/private/special/mangled
        based on the namig-conventions used in the name
        """
        if callable_[0] == '_':

            if callable_[1] == '_':
                if callable_[-2:] != '__':
                    return 'special'
                else:
                    return 'mangled'
            else:
                return 'private'
        else:
            return 'public'




if __name__ == '__main__':
    import os
    import supercli.logging
    supercli.logging.SetLog(lv=20)

    print( os.path.realpath('..')  )
    GenerateAPI( projectroot=os.path.realpath('..'), docroot=os.path.realpath('.') )

