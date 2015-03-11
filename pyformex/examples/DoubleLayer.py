# $Id$
##
##  This file is part of pyFormex 0.9.1  (Tue Oct 15 21:05:25 CEST 2013)
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
"""DoubleLayer

Shows a spatial frame structure consisting of two layers of horizontal
bars (in red and green) connected by diagonals (blue).
"""
from __future__ import print_function


_status = 'checked'
_level = 'beginner'
_topics = ['structure']
_techniques = ['color']

from pyformex.gui.draw import *

from pyformex.plugins import formian

def run():
    clear()
    wireframe()
    n=10; a=2./3.; d=1./n;
    e1 = Formex([[[0, 0, d], [2, 0, d]], [[2, 0, d], [1, 1, d]], [[1, 1, d], [0, 0, d]]], prop=1)
    e2 = Formex([[[0, 0, d], [1, 1-a, 0]], [[2, 0, d], [1, 1-a, 0]], [[1, 1, d], [1, 1-a, 0]]], prop=3)
    # top and bottom layers
    e4 = e1.replic2(n, n, 2, 1, bias=1, taper=-1).bb(1./(2*n), 1./(2*n)/tand(30))
    e5 = e1.replic2(n-1, n-1, 2, 1, bias=1, taper=-1).translate([1, 1-a, -d]).bb(1./(2*n), 1./(2*n)/tand(30))
    # diagonals
    e6 = e2.replic2(n, n, 2, 1, bias=1, taper=-1).bb(1./(2*n), 1./(2*n)/tand(30))
    e5.setProp(2)
    # full structure
    out = (e4+e5+e6).translate(2, -d)
    draw(out)

if __name__ == '__draw__':
    run()
# End

