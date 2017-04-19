#!/usr/bin/env bash

export QT_API=pyside
export QT_PREFERRED_BINDING=PySide


rm -rf source/_api
rm -rf build
#env PYTHONPATH=../ sphinx-apidoc --separate -d 5 -o source/_api  ../
env PYTHONPATH=../ python apigen.py
env PYTHONPATH=../ make html

