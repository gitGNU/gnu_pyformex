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

"""WebGL

This example illustrates the use of the webgl plugin to create WebGL models
in pyFormex.

The example creates a sphere, a cylinder and a cone, draws them with color
and transparency, and exports an equivalent WebGL model in the current
working directory. Point your WebGL capable browser to the created
'scene1.html' file to view the WebGL model.
"""
from __future__ import print_function


_status = 'checked'
_level = 'normal'
_topics = ['export']
_techniques = ['webgl']

from pyformex.gui.draw import *

from pyformex.simple import sphere, sector, cylinder
from pyformex.mydict import Dict
from pyformex.plugins.webgl import WebGL
from pyformex.opengl.objectdialog import objectDialog

pf.cfg['render/experimental'] = False

def createGeometry():
    """Create some geometry.

    This example creates a sphere, a cone and a cylinder, all
    partially overlapping. It sets some rendering attributes
    on the objects.
    """
    # A sphere
    S = sphere().scale(1.2)
    # A Cone
    T = sector(1.0, 360., 6, 36, h=1.0, diag='u').toSurface().scale(1.5).reverse()
    # A Cylinder
    C = cylinder(1.2, 1.5, 24, 4, diag='u').toSurface().trl([0.5, 0.5, 0.5]).reverse()

    # Add some rendering attributes. These attributes will be used
    # when doing default drawing. The attributes will also be exported
    # to WebGL models. Finally, the attributes can be used to create
    # a dialog for interactively changing the rendering.

    # Attributes can be created using different styles.

    # Style 1: specify them as parameters in the attrib() method call
    S.attrib(
        name = 'Sphere',
        caption = 'A sphere',
        color = red,
        alpha = 0.7,
        )

    T.attrib(
        name = 'Cone',
        caption = 'A cone',
        color = blue,
        alpha = 1.0,
       )

    C.attrib(
        name = 'Cylinder',
        caption = 'A cylinder',
        color = 'yellow',
        bkcolor = 'green',
        alpha = 1.0,
        )

    # Style 2: alternately, you can directly set the values as attributes
    # on the created attrib. This style is mostly used to modify or add
    # some attribute afterwards.
    T.attrib.alpha = 0.6

    return List([S,T,C])


def run():
    reset()
    clear()
    #smooth()
    transparent()
    bgcolor(white)
    view('right')

    # Create some geometrical objects
    objects = createGeometry()

    # make them available in the GUI
    export([(obj.attrib.name,obj) for obj in objects])

    # draw the objects
    draw(objects)
    zoomAll()

    # export to WebGL
    camera = pf.canvas.camera
    print("Camera focus: %s; eye: %s" % (camera.focus, camera.eye))
    fn = exportWebGL('Scene1',
                     title='Two spheres and a cone',
                     jsheader='// Created by pyFormex WebGL example',
                     cleanup=True)
    if fn and ack("Show the model in your browser?"):
        showHTML(fn)


if __name__ == 'draw':
    run()

# End
