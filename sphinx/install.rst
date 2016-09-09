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


.. _cha:install:

*******************
Installing pyFormex
*******************

.. warning:: This document is under construction

.. topic:: Abstract

   This document explains the different ways for obtaining a running
   pyFormex installation. You will learn how to obtain pyFormex, how
   to install it, and how to get it running.


.. _sec:choose_installation:

Installing pyFormex-1.0.x
=========================

This installation manual is for the pyFormex 1.0 series. Installation instructions for pyFormex-0.9 can be found `here <http:///pyformex.nongnu.org/doc-0.9/install.html>`_.

pyFormex is being developed on GNU/Linux systems, and currently only runs on Linux. On other systems you have the option of running Linux in a virtual machine, or you can boot your machine from a USB stick with a Linux Live system.

As there has not been an official release yet of pyFormex-1.0, this manual only deals with how to run pyFormex from source, and how to install one of the alpha releases.

Whether you are running pyFormex from source or from a packaged release, there are some required packages that you need to have on your Linux system. pyFormex will not run without them. Then, there are also some recommended pacakges: these are only necessary for some applications, but not for basic pyFormex.


.. _sec:dependencies:

Dependencies
============

In order to run pyFormex, you need at least the following installed (and working) on your computer:

**Python** (http://www.python.org) Version 2.7 is required. Lower
versions are no longer supported. Development is ongoing to make
pyFormex run on Python 3.x, but is not ready yet.  Nearly all Linux
distributions come with Python 2.7 installed by default (or as an
option), so this should be no problem.

**FreeType** (https://www.freetype.org/) Used for rendering text. All
   Linux distributions come with FreeType installed, so again here's
   no problem.

**NumPy** (http://www.numpy.org)
   Version 1.0 or higher. NumPy is the package used for efficient
   numerical array operations in Python and is essential for pyFormex.

**Qt4** (http://www.trolltech.com/products/qt)
   The widget toolkit on which the pyFormex Graphical User Interface (GUI) was built.

**PySide** (http://www.pyside.org)
   The Python bindings for Qt4. There is an alternative set of Python bindings
   for Qt4: PyQt4 (http://www.riverbankcomputing.co.uk/pyqt/index.php), and you
   can use this instead. pyFormex will detect the installed one. If you have
   both, you can select either.

**PyOpenGL** (http://pyopengl.sourceforge.net/)
   Python bindings for OpenGL, used for drawing and manipulating the
   3D-structures.

If you only want to use the Formex data model and transformation methods and
do not need the GUI, then NumPy is all you need. This could e.g. suffice for a
non-interactive machine that only does the numerical processing. The install
procedure however does not provide this option yet, so you will have to do the
install by hand.
Currently we recommend to install the whole package including the GUI.
Most probably you will want to visualize your structures and for that you need the GUI anyway.

In order to speed up some time-critical tasks, pyFormex has an acceleration library containing some compiled C functions. In order to install and compile these, you will need a C development environment and the required header files:

- GNU make
- gcc: GNU C compiler
- header files for Python and OpenGL (e.g. from mesa)

We highly recommend that you install these to allow the acceleration library to be compiled.



.. _`install dependencies`:

Installing dependencies on `Debian GNU/Linux`
.............................................
Debian/Ubuntu users can install the pyFormex dependencies from their distribution's repositories. Installing the following packages should suffice:
``python-numpy``, ``python-opengl``, ``python-qt4``, ``python-pyside``.

Also, for compiling the acceleration library, you should install
``python-dev`` and ``libglu1-mesa-dev``. This command will do it all::

  apt-get install python-numpy python-opengl python-qt4 python-pyside python-qt4-gl python-dev libglu1-mesa-dev libfreetype6-dev


Recommends
==========

Additionally, we recommend you to also install the Python and OpenGL header files. The install procedure needs these to compile the pyFormex acceleration library. While pyFormex can run without the library (Python versions will be substituted for all functions in the library), using the library will dramatically speed up some low level operations such as drawing, especially when working with large structures .


Other optional packages that might be useful are ``admesh``, ``python-scipy``,
 ``units``.




.. End
