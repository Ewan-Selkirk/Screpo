#!/bin/bash

source venv/bin/activate

if [ -f src/resources.qrc ]; then
  pyside6-rcc --no-compress src/resources.qrc -o src/resources.py
  echo "Compiled qrc file to Python file"

  echo "Working bullshit to make compiled file work on Windows..."
  sed -i '7 i import PySide.QtSvg' src/resources.py

  echo "Finished!"
else
  echo "Could not find 'resources.qrc' in directory 'src'..."
  echo "Aborting..."
fi