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

pf.cfg['render/experimental'] = False

def run():
    reset()
    clear()
    smooth()
    transparent()
    bgcolor(white)
    view('right')

    # Create some geometry
    S = sphere().scale(1.2)
    T = sector(1.0, 360., 6, 36, h=1.0, diag='u').toSurface().scale(1.5).reverse()
    C = cylinder(1.2, 1.5, 24, 4, diag='u').toSurface().trl([0.5, 0.5, 0.5]).reverse()

    # Draw the geometry with given colors/opacity
    # Settings colors and opacity in this way makes the model
    # directly ready to export as WebGL

    # Style 1: using function call
    S.attrib(color=red,#bkcolor=red,
             alpha=0.7,
             caption='A sphere',
#             control=['visible','opacity','color'],
             )
    #S.setNormals('avg')

    #r = pf.canvas.renderer
    #r.settings.nlights = 1

    # Style 2: setting attributes of the .attrib attribute
    Ta = T.attrib
    Ta.color = blue
    #Ta.bkcolor = blue
    Ta.caption = 'A cone'
    Ta.alpha = 0.5
    #Ta.opak = True
#    Ta.control = ['visible','opacity','color']
    #S.setNormals('auto')

    Ca = C.attrib
    Ca.color = 'yellow'
    Ca.bkcolor = 'green'
    Ca.caption = 'A cylinder'
    Ca.alpha = 1.0
    #Ca.opak = True
#    Ca.control = ['visible','opacity','color']
    #S.setNormals('auto')

    export({'sphere':S,'cone':T,'cylinder':C})

    draw([C, T, S])
    zoomAll()
    #rotRight(30.)

    camera = pf.canvas.camera
    print("Camera focus: %s; eye: %s" % (camera.focus, camera.eye))

    if checkWorkdir():
        # Export everything to webgl
        exportWebGL('Scene1', title='Two spheres and a cone')


if __name__ == 'draw':
    run()

# End
