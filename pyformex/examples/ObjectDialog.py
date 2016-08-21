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

"""ObjectDialog

This example illustrates the interactive modification of object rendering.

The example creates the same geometry as the WebGL example, and then pops up
a dialog to allow the user to interactively change the rendering of the
objects. Attributes that can be changed include color, opacity, visibility,

"""
from __future__ import absolute_import, print_function


_status = 'checked'
_level = 'normal'
_topics = ['export']
_techniques = ['webgl']

from pyformex.gui.draw import *

from pyformex.simple import sphere, sector, cylinder
from pyformex.mydict import Dict
from pyformex.plugins.webgl import WebGL
from pyformex.opengl.objectdialog import objectDialog
from pyformex.examples.WebGL import createGeometry


def run():
    reset()
    clear()
    smooth()
    transparent()
    bgcolor(white)
    view('right')

    # Create some geometrical objects
    objects = createGeometry()

    # make them available in the GUI
    export([(obj.attrib.name,obj) for obj in objects])

    # draw the objects
    drawn_objects = draw(objects)
    zoomAll()

    # create an object dialog
    dia = objectDialog(drawn_objects)
    if dia:
        dia.show()


if __name__ == '__draw__':
    run()

# End
