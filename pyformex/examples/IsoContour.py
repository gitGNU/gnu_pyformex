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
    global filename # because we set it before updating globals
    resetAll()
    clear()
    # Set default image filename
    filename = getcfg('datadir')+'/butterfly.png'
    # Give user a change to change it
    viewer = widgets.ImageView(filename, maxheight=200)
    res = askItems([
        _I('filename', filename, text='Image file', itemtype='filename', filter='img', exist=True, preview=viewer),
        viewer,
        _I('value',None, choices=['luminance','intensity','red','green','blue']),
        _I('n', 10, text='Number of isocontours'),
        _I('levelmin', 0.0, text='Minimum level value'),
        _I('levelmax', 1.0, text='Maximum level value'),
        _I('npalette', 8, text='Number of different colors'),
        _I('remove', False, text='Remove original image'),
        ])

    if not res:
        return
    globals().update(res)
    print(res)
    print(filename)
    # This is picked from pyformex.opengl.draw.drawImage3D
    from pyformex.plugins.imagearray import qimage2glcolor, resizeImage
    image = resizeImage(filename, 0, 0)
    nx, ny = image.width(), image.height()
    print("Image size: %s x %s" % (nx,ny))
    color, colortable = qimage2glcolor(image)
    color = color.reshape(ny,nx,3)
    #color = color[130:176,100:146] # uncomment to pick a part from the image
    ny,nx = color.shape[:2]   # pixels move fastest in x-direction!
    color = color.reshape(-1,3)
    F = Formex('1:0').replic2(nx, ny)
    FA = draw(F, color=color, colormap=colortable, nolight=True)
    FA.alpha = 0.6

    if value == 'luminance':
        data = luminance(FA.color)
    elif value == 'intensity':
        data = FA.color.sum(axis=-1) / 3
    elif value == 'red':
        data = FA.color[...,0]
    elif value == 'green':
        data = FA.color[...,1]
    elif value == 'blue':
        data = FA.color[...,2]
    data = data.reshape(ny,nx)

    levels = levelmin + arange(1,n) * (levelmax-levelmin) / n # change levels to adjust number and position of contours
    #print(levels)
    pf.canvas.settings.colormap = pf.refcfg.canvas.colormap[:npalette]
    transparent()
    for col,level in enumerate(levels):
        seg = isoline(data,level,nproc=-1)
        C = Formex(seg)
        draw(C,color=col+1,linewidth=3)

    if remove:
        undraw(FA)

if __name__ == '__draw__':
    run()

# End
