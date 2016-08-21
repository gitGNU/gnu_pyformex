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

"""Pickable

This example illustrates the use of the pickable argument in pick functions
and the pickable attribute of Actors.
"""
from __future__ import absolute_import, print_function


_status = 'checked'
_level = 'normal'
_topics = ['pick']
_techniques = ['pickable']

from pyformex.gui.draw import *
from pyformex.examples.WebGL import createGeometry


def run():
    reset()
    clear()
    smoothwire()
    bgcolor(white)
    view('right')

    # Create some geometrical objects (sphere, cone, cylinder)
    objects = createGeometry()

    # Make the cone non-pickable
    objects[1].attrib(pickable=False)

    # draw the objects
    actors = draw(objects)
    zoomAll()

    # pick elements
    pick('element',prompt="Pick elements and notice that the cone is not pickable")

    # force pick from sphere and cone!
    pick('element',pickable=actors[:2],prompt="Pick elements and notice that this time only the sphere and the cone are pickable")


if __name__ == '__draw__':
    run()

# End
