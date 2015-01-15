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
"""IsoContour

This example illustrates how to create isocontours through pixel data.
"""
from __future__ import print_function

_status = 'checked'
_level = 'expert'
_topics = ['image', 'curve']
_techniques = ['isoline', ]

from pyformex.gui.draw import *
from pyformex.plugins.isosurface import isoline

def run():
    resetAll()
    clear()
    filename = getcfg('datadir')+'/leeuw24.png'
    # This is picked from pyformex.opengl.draw.drawImage3D
    from pyformex.plugins.imagearray import image2glcolor, resizeImage
    image = resizeImage(filename, 0, 0)
    nx, ny = image.width(), image.height()
    color, colortable = image2glcolor(image)
    color = color.reshape(ny,nx,3)
    ny,nx = color.shape[:2]   # pixels move fastest in x-direction!
    color = color.reshape(-1,3)
    F = Formex('1:0').replic2(nx, ny)
    FA = draw(F, color=color, colormap=colortable, nolight=True)
    intens = FA.color.sum(axis=-1) / 3
    data = intens.reshape(ny,nx)
    level = 0.3
    seg = isoline(data,level)
    C = Formex(seg)
    draw(C,color=red,linewidth=3)
    transparent()

if __name__ == 'draw':
    run()

# End
