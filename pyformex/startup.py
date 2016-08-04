#!/usr/bin/python
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
"""pyFormex, a free program for creating and manipulating 3D geometry.

pyFormex is a powerful tool for generating, manipulating, transforming and
displaying large structural models of 3D geometry.
Based on a powerful scripting language, pyFormex is exceptionally suited for
generating parametric models and for the automization of tedious and recurring
tasks in the handling of geometrical models.
Built around a fully open architecture pyFormex allows the user to combine the
program with nearly any other software and to extend the program to suit his
own needs.

pyFormex is being developed at the IBiTech, Ghent University, and can be
distributed under the GNU General Public License, version 3 or later.
(C) 2004-2012 Benedict Verhegghe (benedict.verhegghe@ugent.be))
"""

# Get the pyformex dir and put it on the head of sys.path
# This has to be done *before* importing pyformex, so it
# can only be done here.

import sys,os
_bindir = sys.path[0]

# In case we execute the pyformex script from inside the
# pyformex package dir: add the parent to the front of sys.path
# to pick up the package here instead of from default path

if _bindir.endswith('pyformex'):
    sys.path[0] = os.path.dirname(_bindir)

try:
    import pyformex
except:
    print("Could not import pyformex.")
    print("This probably means that pyFormex was not properly installed.")
    raise

# Remember where we got started: save the _bindir inside pyformex
pyformex.bindir = _bindir

if __name__ == "__main__":
    from pyformex import main
    sys.exit(main.run(sys.argv[1:]))

# End
