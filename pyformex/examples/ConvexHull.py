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

"""ConvexHull

This example demonstrates the use of the Coords.convexHull method.
You need to have the python-scipy version 0.12.0 or higher to run this
example.

The example creates a set of random points in space, and then constructs
and draws the 3D convex hull of the points, as well as the 2D
convex hulls of the points projected on each of the coordinate planes.

Switch off perspective and look along one of the global axis directions
to see the 2D hulls matching.
"""
from __future__ import print_function


_status = 'checked'
_level = 'beginner'
_topics = ['geometry']
_techniques = ['convexhull', 'random']

from pyformex.gui.draw import *


def run():
    clear()
    reset()
    smoothwire()
    transparent()

    n = 100
    X = Coords(randomNoise((n,3)))
    draw(X)

    ch = X.convexHull(return_mesh=True)
    draw(ch,color=yellow)

    ch2 = [ X.convexHull(i,return_mesh=True).setProp(1+i) for i in range(3) ]
    draw(ch2,linewidth=3)



if __name__ == '__draw__':
    run()


# End
