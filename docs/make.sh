#!/usr/bin/env bash

export QT_API=pyside
export QT_PREFERRED_BINDING=PySide


rm -rf source/_api
rm -rf build
mkdir -p              build/html/media
cp -Ra source/media/* build/html/media
#env PYTHONPATH=../ sphinx-apidoc --separate -d 5 -o source/_api  ../
env PYTHONPATH=../ python apigen.py
env PYTHONPATH=../ make html

