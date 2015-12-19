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
    # Set default image filename
    filename = getcfg('datadir')+'/butterfly.png'
    # Give user a change to change it
    filename = askImageFile(filename)
    # This is picked from pyformex.opengl.draw.drawImage3D
    from pyformex.plugins.imagearray import qimage2glcolor, resizeImage
    image = resizeImage(filename, 0, 0)
    nx, ny = image.width(), image.height()
    print("Image size: %s x %s" % (nx,ny))
    color, colortable = qimage2glcolor(image)
    #butterfly nx,ny = 376,327
    #zonnebloem nx,ny = 176,173
    color = color.reshape(ny,nx,3)
    #color = color[130:176,100:146] # uncomment to pick a part from the image
    ny,nx = color.shape[:2]   # pixels move fastest in x-direction!
    color = color.reshape(-1,3)
    F = Formex('1:0').replic2(nx, ny)
    FA = draw(F, color=color, colormap=colortable, nolight=True)
    FA.alpha = 0.6

    intens = FA.color.sum(axis=-1) / 3
    data = intens.reshape(ny,nx)

    n = 10
    levels = arange(1,n) * 1. / n # change levels to adjust number and position of contours
    print(levels)
    transparent()
    for col,level in enumerate(levels):
        seg = isoline(data,level,nproc=-1)
        C = Formex(seg)
        draw(C,color=col+1,linewidth=3)

    sleep(2)
    undraw(FA)

if __name__ == '__draw__':
    run()

# End
