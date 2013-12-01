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

"""Octree

A sphere mesh is created and the octree octants are computed.

Every level of the octree is repeatedly shown. The mesh properties of the
octree correspond to the number of points in each octant.

Finally all the octants of the octree which includes at least one point are
shown.

"""
from __future__ import print_function
_status = 'checked'
_level = 'normal'
_topics = ['Mesh', 'Geometry']
_techniques = ['Octree', 'Vtk']

from gui.draw import *
from simple import sphere3
from plugins.vtk_itf import octree

smoothwire()
transparent()

def run():
    clear()

    sf = sphere3(50, 50, bot=-90, top=90).scale(10).toMesh()
    print(sf)

    levels = octree(sf)

    A = draw(sf, color='yellow',)
    zoomAll()
    for lev in levels:
        B = draw(lev, alpha=0.5)
        delay(1)
        wait()
        undraw(B)

    draw([lev.withoutProp(0) for lev in levels])


if __name__ == 'draw':
    run()
# End
