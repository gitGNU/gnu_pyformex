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

"""Octree

A sphere mesh is created and the octree octants are computed.

Every level of the octree is repeatedly shown. The mesh properties of the
octree correspond to the number of points in each octant.

Finally all the octants of the octree which include at least one point are
shown.

"""
from __future__ import absolute_import, print_function


_status = 'checked'
_level = 'normal'
_topics = ['Mesh', 'Geometry']
_techniques = ['Octree', 'Vtk']

from pyformex.gui.draw import *
from pyformex.simple import sphere3
from pyformex.plugins.vtk_itf import octree

smoothwire()
transparent()

def run():
    clear()

    sf = sphere3(20, 20, bot=-90, top=90).scale(10).toMesh()

    levels = octree(sf,return_levels=True)

    A = draw(sf, color='yellow',)
    zoomAll()
    for lev in levels[1]:
        B = draw(levels[0].select(lev), alpha=0.5)
        delay(1)
        wait()
        undraw(B)

    transparent(False)
    M = levels[0]
    draw(M.select(M.prop>0))


if __name__ == '__draw__':
    run()
# End
