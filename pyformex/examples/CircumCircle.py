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
"""CircumCircle

"""
from __future__ import absolute_import, division, print_function
from pyformex import zip

_status = 'checked'
_level = 'beginner'
_topics = ['geometry']
_techniques = ['function', 'import', 'dialog', 'viewport']

from pyformex.gui.draw import *
from pyformex import simple
from pyformex.examples.Cube import cube_tri
from pyformex.geomtools import *


def draw_circles(circles,color=red):
    for r, c, n in circles:
        C = simple.circle(r=r, n=n, c=c)
        draw(C, color=color)


def drawCircles(F,func,color=red):
    r, c, n = func(F.coords)
    draw(c, color=color)
    draw_circles(zip(r, c, n), color=color)


def run():
    layout(2)
    wireframe()

    # draw in viewport 0
    viewport(0)
    view('front')
    clear()
    rtri = Formex('3:016932').scale([1.5, 1, 0])
    F = rtri + rtri.shear(0, 1, -0.5).trl(0, -4.0) + rtri.shear(0, 1, 0.75).trl(0, 3.0)
    draw(F)

    drawCircles(F, triangleCircumCircle, color=red)
    zoomAll()
    drawCircles(F, triangleInCircle, color=blue)
    drawCircles(F, triangleBoundingCircle, color=black)
    zoomAll()


    # draw in viewport 1
    viewport(1)
    view('iso')
    clear()
    F, c = cube_tri()
    draw(F)
    drawCircles(F, triangleInCircle)
    zoomAll()

    if not ack("Keep both viewports ?"):
        print("Removing a viewport")
        # remove last viewport
        removeViewport()

if __name__ == '__draw__':
    run()
# End
