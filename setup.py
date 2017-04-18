#!/usr/bin/env python
from   distutils.core import setup, Extension, Command
import setuptools

setup(
    name         = 'qconcurrency',
    version      = '0.0.a1',
    author       = 'Will Pittman',
    author_email = 'willjpittman@gmail.com',
    url          = 'https://github.com/willjp/supercli',
    license      = 'BSD',

    description      = 'A collection of tools to simplify Concurrency in Qt',
    #long_description = cfg.read('README.rst'),

    keywords         = 'Qt PySide PyQt',
    install_requires = ['supercli','six','Qt.py'],
    packages         = setuptools.find_packages(),
    zip_safe         = False,
    include_package_data = True,


    classifiers      = [
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',

        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: POSIX :: BSD',
    ],
)
