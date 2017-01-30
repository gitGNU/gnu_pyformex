.. $Id$

..
  This file is part of pyFormex 1.0.2  (Thu Jun 18 15:35:31 CEST 2015)
  pyFormex is a tool for generating, manipulating and transforming 3D
  geometrical models by sequences of mathematical operations.
  Home page: http://pyformex.org
  Project page:  http://savannah.nongnu.org/projects/pyformex/
  Copyright 2004-2015 (C) Benedict Verhegghe (benedict.verhegghe@feops.com)
  Distributed under the GNU General Public License version 3 or later.

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see http://www.gnu.org/licenses/.


.. include:: defines.inc
.. include:: links.inc


.. _cha:importing:

******************
Importing pyFormex
******************

.. warning:: This document contains very preliminary information of a new
	     feature under development. Use at your own risk!

.. topic:: Abstract

	   This document gives some guidelines about how to import pyFormex
	   into a Python application (instead of running the Python application
	   from pyFormex).


Background
==========

Traditionally, pyFormex is launched with the 'pyformex' command, and
pyFormex (or Python) scripts are executed from the pyFormex environment
(whether GUI or non-GUI).

Sometimes however it may be more suitable to import pyFormex into another
Python script or environment. Therefore some modifications are underway
to allow this.


How to proceed
==============

In commit bd27925 of the git repositories the basic necessary changes were
made to allow a basic pyFormex to be imported into normal Python workflow.
These changes are currently only available when using pyFormex from the
git sources. You may have to do a pull first.


Running non-GUI scripts
=======================

If you do not need the pyFormex GUI, the following is required to import
pyFormex and make its scripting language usable just like in a pyFormex
script/application:

- make sure Python finds the path from which to import pyFormex,
- import pyFormex (this is done implicitely when importing one of
  the modules or subpackages from pyFormex),
- import the pyFormex scripting language, if you want to use it. You
  probably want to, since you have imported pyFormex, but you would
  not need it if you just want to use some pyFormex classes or modules.

While there are many ways to do this, we present hereafter a few typical
examples of how it can be done. Suppose we have a (partial) directory
layout as follows::

  /
  |-- home
  |   |-- user
  |   |   |-- pyformex
  |   |   |   |-- pyformex
  |   |   |   |   |-- main.py
  |   |   |   |   |-- gui
  |   |   |   |   |-- opengl
  |   |   |   |   |-- plugins
  |   |   |-- apps
  |   |   |   |   |-- example1.py
  |   |   |   |   |-- example2.py

Thus, the path of the pyFormex package (i.e. the 'pyformex' directory containing
the pyFormex 'main.py' source file and having at least subdirectories
'gui', 'opengl', 'plugins') is '/home/user/pyformex/pyformex'.
We have to add its parent path ('/home/user/pyformex')
to the front of the Python paths to search for packages and modules.
Furthermore, suppose we have our Python scripts in a directory '/home/user/apps/example1.py'.


Example1
--------
The contents of 'example1.py' looks like this::

  # Set path to import pyFormex
  import sys
  sys.path.insert(0,'/home/user/pyformex')

  # Import the pyFormex with its full scripting language
  from pyformex.script import *

  # Show that we can do some pyFormex operations
  a = array([[1,2,3],[4,5,6]])
  print(a)
  b = growAxis(a,2)
  print(b)

It can be run with the command::

  python example1.py

and produces the result::

  [[1 2 3]
   [4 5 6]]
  [[1 2 3 0 0]
   [4 5 6 0 0]]

Example2
--------
Instead of hardcoding the pyFormex package path inside the script, you can
set it in the PYTHONPATH environment variable. Also, in this example we do
not import everything from the pyFormex scripting language, only the few
things we need::

  # Import some required modules
  import numpy
  from pyformex import arraytools

  # Show that we can do some pyFormex operations
  a = numpy.array([[1,2,3],[4,5,6]])
  print(a)
  b = arraytools.growAxis(a,2,axis=0)
  print(b)

This script can now be run with a command::

  PYTHONPATH=/home/user/pyformex python example2.py

and produces the results::

  [[1 2 3]
   [4 5 6]]
  [[1 2 3]
   [4 5 6]
   [0 0 0]
   [0 0 0]]


Caveats
=======

- It is possible to use relative paths for the pyFormex package path. Be aware
  though that these may not work if you execute the python command from a
  directory that is actually a symlink.


Limitations
===========

Currently you can not set the pyFormex command line options when not
using the pyformex command.

Loading user preferences has not been tested yet. There is a function
'loadUserConfig' in pyformex.main (untested).

Using (parts of) pyFormex other than through the pyformex command has not
been thoroughly tested yet. While the basic functionality should likely
work, the use of some complex classes and modules may raise some problems.

Warnings can not be silenced (unless you load the user preferences and
disable the warnings from the GUI first).

.. End
