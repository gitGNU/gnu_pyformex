# $Id$
##
##  This file is part of pyFormex
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2013 (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
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
"""General Qt4 utility functions.

"""
from __future__ import print_function

import pyformex as pf

def Size(widget):
    """Return the size of a widget as a tuple."""
    s = widget.size()
    return s.width(), s.height()

def Pos(widget):
    """Return the position of a widget as a tuple."""
    p = widget.pos()
    return p.x(), p.y()

def relPos(w,parent=None):
    """Return the position of a widget relative to a parent.

    If no parent is specified, it is taken as the GUI main window.
    """
    if parent is None:
        parent = pf.GUI
    x,y = 0,0
    while w != parent:
        #print(w)
        dx,dy = w.x(),w.y()
        x += dx
        y += dy
        #print("rel pos = %s, %s; abs pos = %s, %s" % (dx,dy,x,y))
        w = w.parent()
        if not w:
            break
    return x,y

def MaxSize(*args):
    """Return the maximum of a list of sizes"""
    return max([i[0] for i in args]), max([i[1] for i in args])

def MinSize(*args):
    """Return the maximum of a list of sizes"""
    return min([i[0] for i in args]), min([i[1] for i in args])

def printpos(w,t=None):
    print("%s %s x %s" % (t, w.x(), w.y()))
def sizeReport(w,t=None):
    return "%s %s x %s" % (t, w.width(), w.height())


#### End
