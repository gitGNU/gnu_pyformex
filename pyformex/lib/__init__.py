# $Id$
##
##  This file is part of pyFormex 1.0.2  (Thu Jun 18 15:35:31 CEST 2015)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2015 (C) Benedict Verhegghe (benedict.verhegghe@feops.com)
##  Distributed under the GNU General Public License version 3 or later.
##
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see http://www.gnu.org/licenses/.
##
"""pyFormex C library module initialisation.

This tries to load the compiled libraries, and replaces those that failed
to load with the (slower) Python versions.
"""
from __future__ import print_function


import pyformex as pf
__all__ = [ 'misc', 'nurbs', 'drawgl', 'accelerated' ]

misc = nurbs = drawgl = None
accelerated = []


def checkVersion(lib):
    pf.debug("Succesfully loaded the pyFormex compiled library %s" % lib.__name__, pf.DEBUG.LIB)
    pf.debug("  Library version is %s" % lib.__version__, pf.DEBUG.LIB)
    if not lib.__version__ == pf.__version__:
        raise RuntimeError("Incorrect acceleration library version (have %s, required %s)\nIf you are running pyFormex directly from sources, this might mean you have to run 'make lib' in the top directory of your pyFormex source tree.\nElse, this probably means pyFormex was not correctly installed.")
    accelerated.append(lib)


accelerate = gui = False
if pf.options:
    # testing for not False makes other values than T/F (like None) pass
    # test for existence of these is for sphinx
    accelerate = pf.cfg.get('uselib',False) is not False
    gui = hasattr(pf.options,'gui') and pf.options.gui


if accelerate:

    try:
        from pyformex.lib import misc_ as misc
        checkVersion(misc)
    except ImportError:
        pf.debug("Error while loading the pyFormex compiled misc library", pf.DEBUG.LIB)

    try:
        from pyformex.lib import nurbs_ as nurbs
        checkVersion(nurbs)
    except ImportError:
        pf.debug("Error while loading the pyFormex compiled nurbs library", pf.DEBUG.LIB)

    if gui:
        # !! We need to import GL before drawgl, to define the GL calls !
        from OpenGL import GL
        try:
            from pyformex.lib import drawgl_ as drawgl
            checkVersion(drawgl)
        except ImportError:
            pf.debug("Error while loading the pyFormex compiled drawgl library", pf.DEBUG.LIB)

# Load Python libraries if acceleration libraries failed

if misc is None:
    pf.debug("Using the (slower) Python misc functions", pf.DEBUG.LIB)
    from pyformex.lib import misc

if nurbs is None:
    pf.debug("Using the (slower) Python nurbs functions", pf.DEBUG.LIB)
    from pyformex.lib import nurbs

if gui and drawgl is None:
    pf.debug("Using the (slower) Python draw functions", pf.DEBUG.LIB)
    from pyformex.lib import drawgl


pf.debug("Accelerated: %s" % accelerated, pf.DEBUG.LIB|pf.DEBUG.INFO)
pf.debug(misc, pf.DEBUG.LIB)
pf.debug(nurbs, pf.DEBUG.LIB)
pf.debug(drawgl, pf.DEBUG.LIB)

# End
