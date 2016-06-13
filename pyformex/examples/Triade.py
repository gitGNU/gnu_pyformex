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
"""SetTriade.py

This example shows how to use a customized Triade
"""
from __future__ import print_function

_status = 'checked'
_level = 'advanced'
_topics = ['decors']
_techniques = ['setTriade']

from pyformex.gui.draw import *
from OpenGL import GL
from pyformex.opengl.drawable import Actor


def geomTriade(pos,size):
    """A generic Triade Actor.

    The function takes pos and size as parameters.
    It should return an Actor with rendertype -2.
    The Actor shoud save attributes 'size' and 'x','y' (the
    actual canvas position of the origin for rotation).

    This Triade Actor is customizable by setting _triade_geometry.
    """
    x, y, w, h = GL.glGetIntegerv(GL.GL_VIEWPORT)
    if pos[0] == 'l':
        x0 = x + size
    elif pos[0] =='r':
        x0 = x + w - size
    else:
        x0 = x + w / 2
    if pos[1] == 'b':
        y0 = y + size
    elif pos[1] == 't':
        y0 = y + h - size
    else:
        y0 = y + h / 2

    F = _triade_geometry.centered().scale(size)
    A = Actor(F,rendertype=-2,lighting=False,opak=True,linewidth=2)
    # Save some values for drawing
    A.size = size
    A.x, A.y = x0,y0

    return A


def run():
    global _triade_geometry

    # Clear
    clear()
    reset()
    smoothwire()

    # Draw something
    F = Formex.read(getcfg('datadir')+'/horse.pgf').scale(10)
    draw(F)
    pause()

    # Set default Triade on
    pf.canvas.setTriade(on=True)
    pf.canvas.update()
    pause()

    # Set a wireframe cube as Triade, left top
    _triade_geometry = Formex(simple.Pattern['cube']).setProp([1,2,1,2,3,3,3,3,1,2,1,2])
    pf.canvas.setTriade(on=True,pos='lt',triade=geomTriade)
    pf.canvas.update()
    pause()

    # Use the displayed geometry (F) itself as Triade, left center
    _triade_geometry = F
    pf.canvas.setTriade(on=True,pos='lc',triade=geomTriade)
    pf.canvas.update()
    pause()

    # Reset the original Triade, center top
    pf.canvas.setTriade(on=True,pos='ct')
    pf.canvas.update()



if __name__ == '__draw__':
    run()

# End
