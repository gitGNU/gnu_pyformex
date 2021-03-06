.. $Id$  -*- rst -*-

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


.. pyFormex documentation reference manual master file

.. include:: defines.inc
.. include:: links.inc



.. _cha:reference:

##########################
 pyFormex reference manual
##########################

.. topic:: Abstract

   This is the reference manual for pyFormex |release|.
   It describes most of the classes and functions
   defined in the pyFormex modules. It was built automatically from
   the pyFormex sources and is therefore the ultimate reference
   document if you want to look up the precise arguments (and their meaning)
   of any class constructor or function in pyFormex. The :ref:`genindex`
   and :ref:`modindex` may be helpful in navigating through this
   document.


This reference manual describes the classes in functions defined in
most of the pyFormex modules. It was built automatically from the docstrings in
the pyFormex sources. The pyFormex modules are placed in three paths:

- ``pyformex`` contains the core functionality, with most of the
  geometrical transformations, the pyFormex scripting language and utilities,
- ``pyformex/gui`` contains all the modules that form the interactive
  graphical user interface,
- ``pyformex/plugins`` contains extensions that are not considered to
  be essential parts of pyFormex. They usually provide additional
  functionality for specific applications.

Some of the modules are loaded automatically when pyFormex is
started. Currently this is the case with the modules
:mod:`coords`, :mod:`formex`, :mod:`arraytools`, :mod:`script` and, if the GUI is used, :mod:`draw` and :mod:`colors`.
All the public definitions in these modules are available to pyFormex
scripts without explicitly importing them. Also available is the complete
:mod:`numpy` namespace, because it is imported by :mod:`arraytools`.

The definitions in the other modules can only be accessed using the
normal Python ``import`` statements.

.. _sec:autoloaded-modules:

Autoloaded modules
==================

The definitions in these modules are always available to your scripts, without
the need to explicitely import them.

.. mytoctree::
   :maxdepth: 1
   :numbered:
   :numberedfrom: -1

   ref/coords
   ref/formex
   ref/arraytools
   ref/script
   ref/gui.draw
   ref/opengl.colors


.. _sec:core-modules:

Other pyFormex core modules
===========================

Together with the autoloaded modules, the following modules located under the
main pyformex path are considered to belong to the pyformex core functionality.

.. mytoctree::
   :maxdepth: 1
   :numbered:
   :numberedfrom: -1

   ref/mesh
   ref/geometry
   ref/connectivity
   ref/elements
   ref/trisurface
   ref/utils
   ref/varray
   ref/adjacency
   ref/simple
   ref/project
   ref/geomfile
   ref/geomtools
   ref/inertia
   ref/fileread
   ref/filewrite
   ref/coordsys
   ref/field
   ref/multi
   ref/software


.. _sec:gui-modules:

pyFormex GUI modules
====================

These modules create the components of the pyFormex GUI. They are located under pyformex/gui. They depend on the Qt4 framework.

.. mytoctree::
   :maxdepth: 1
   :numbered:
   :numberedfrom: -1

   ref/gui.widgets
   ref/gui.menu
   ref/gui.colorscale
   ref/gui.viewport
   ref/gui.image
   ref/gui.imageViewer
   ref/gui.appMenu
   ref/gui.toolbar


.. _sec:plugins-modules:

pyFormex plugins
================

Plugin modules extend the basic pyFormex functions to variety of
specific applications. Apart from being located under the pyformex/plugins
path, these modules are in no way different from other pyFormex modules.

.. mytoctree::
   :maxdepth: 1
   :numbered:
   :numberedfrom: -1

   ref/plugins.bifmesh
   ref/plugins.cameratools
   ref/plugins.ccxdat
   ref/plugins.ccxinp
   ref/plugins.curve
   ref/plugins.datareader
   ref/plugins.dxf
   ref/plugins.export
   ref/plugins.fe
   ref/plugins.fe_abq
   ref/plugins.fe_post
   ref/plugins.flavia
   ref/plugins.imagearray
   ref/plugins.isopar
   ref/plugins.isosurface
   ref/plugins.lima
   ref/plugins.neu_exp
   ref/plugins.nurbs
   ref/plugins.objects
   ref/plugins.partition
   ref/plugins.plot2d
   ref/plugins.polygon
   ref/plugins.polynomial
   ref/plugins.postproc
   ref/plugins.properties
   ref/plugins.pyformex_gts
   ref/plugins.section2d
   ref/plugins.sectionize
   ref/plugins.tetgen
   ref/plugins.tools
   ref/plugins.turtle
   ref/plugins.units
   ref/plugins.web
   ref/plugins.webgl

   ref/plugins.calpy_itf

..   ref/centerline  still relevant?
..   ref/draw2d   gives errors on py2rst
..   ref/fe_ast  needs work
..   ref/f2flu  still relevant?
..   ref/formian
..   ref/mesh_ext
..   ref/meshlist  still relevant?
..   ref/partition  still relevant?
..   ref/surface_abq  still relevant?
..   ref/wrl    gives errors on py2rst

.. _sec:opengl-modules:

pyFormex OpenGL modules
=======================

These modules are responsible for rendering the 3D models and depend on OpenGL. Currently, pyFormex contains two rendering engines. The new engine's modules are located under pyformex/opengl.

.. mytoctree::
   :maxdepth: 1
   :numbered:
   :numberedfrom: -1

   ref/opengl.camera
   ref/opengl.canvas
   ref/opengl.decors
   ref/opengl.drawable
   ref/opengl.matrix
   ref/opengl.objectdialog
   ref/opengl.renderer
   ref/opengl.sanitize
   ref/opengl.scene
   ref/opengl.shader
   ref/opengl.textext
   ref/opengl.texture

.. _sec:menu-modules:

pyFormex plugin menus
=====================

Plugin menus are optionally loadable menus for the pyFormex GUI, providing
specialized interactive functionality. Because these are still under heavy
development, they are currently not documented. Look to the source code or
try them out in the GUI. They can be loaded from the File menu option and
switched on permanently from the Settings menu.

Currently avaliable:

- geometry_menu
- formex_menu
- surface_menu
- tools_menu
- draw2d_menu
- nurbs_menu
- dxf_tools
- jobs menu
- postproc_menu
- bifmesh_menu

.. - fe_menu     used?

.. _sec:tools-modules:

pyFormex tools
==============

The main pyformex path contains a number of modules that are not
considered to be part of the pyFormex core, but are rather tools that
were used in the implementation of other modules, but can also be useful
elsewhere.

.. mytoctree::
   :maxdepth: 1
   :numbered:
   :numberedfrom: -1

   ref/olist
   ref/mydict
   ref/odict
   ref/attributes
   ref/collection
   ref/config
   ref/flatkeydb
   ref/sendmail
   ref/timer

.. ref/track    errors on py2rst

.. End
