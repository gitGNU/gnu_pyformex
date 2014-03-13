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

"""Texture

Shows how to draw with textures and how to set a background image.
"""
from __future__ import print_function

_status = 'checked'
_level = 'normal'
_topics = ['Image', 'Geometry']
_techniques = ['texture']

from pyformex.gui.draw import *
from pyformex import simple

def run():
    clear()
    smooth()

    image = os.path.join(pf.cfg['pyformexdir'], 'data', 'butterfly.png')

    F = simple.cuboid().centered().toMesh()
    G = Formex('4:0123')
    H = G.replic2(3, 2).toMesh().setProp(arange(1, 7)).centered()
    K = G.scale(200).toMesh()
    K.attrib(color=yellow,rendertype=2, texture=image)
    draw([F,H,K], texture=image)

    view('iso')
    zoomAll()
    zoom(0.5)

    bgcolor(color=white,image=image)

if __name__ == 'draw':
    run()
# End
