"""Starts pyathy when you run `python pyathy` from the folder that holds this one.

Python runs this file when it is given the folder. It puts the folder's own code
(pyathy/) and the libraries pyathy uses (lib/) first on the import path, then starts
pyathy. Stdlib only, so it runs on any Python before anything else is found.
"""

import os
import shutil
import sys

sys.dont_write_bytecode = True  # never write __pycache__ into this folder

HERE = os.path.dirname(os.path.abspath(__file__))
# Python caches this very file before it runs, too early for the line above: remove it.
shutil.rmtree(os.path.join(HERE, "__pycache__"), ignore_errors=True)
sys.path[:0] = [HERE, os.path.join(HERE, "lib")]

from pyathy.cli import main  # noqa: E402

main()
