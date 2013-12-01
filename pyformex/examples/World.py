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
"""World

This examples shows how to use an image file to set colors on a
structure.

The user can select an image file. A rectangular grid with corrersponding
number of cells is constructed. The grid is shown with the colors from the
image and can possibly be transformed to a sphere or a half sphere.

.. note:
  This example is slow when using high resolution images.
"""
from __future__ import print_function
from future_builtins import zip

_status = 'checked'
_level = 'normal'
_topics = ['image']
_techniques = ['color', 'filename']

from gui.draw import *
from plugins.imagearray import *

def run():
    clear()
    smooth()
    lights(False)
    view('front')

    # default image
    fn = os.path.join(getcfg('datadir'), 'world.jpg')

    # pattern of files to select from
    pat = utils.fileDescription('img')

    res = askItems([
        _I('fn', fn, itemtype='file', pattern=pat, exist=True, text=''),
        _I('part', itemtype='radio', choices=["Plane", "Half Sphere", "Full Sphere"], text='Show image on'),
        ])
    if not res:
        return

    fn = res['fn']
    part = res['part']

    im = QtGui.QImage(fn)
    if im.isNull():
        warning("Could not load image '%s'" % fn)
        return

    nx, ny = im.width(), im.height()
    #nx,ny = 200,200

    # Create the colors
    color, colormap = image2glcolor(im.scaled(nx, ny))
    print("Size of colors: %s" % str(color.shape))
    if colormap is not None:
        print("Size of colormap: %s" % str(colormap.shape))


    # Create a 2D grid of nx*ny elements
    F = Formex('4:0123').replic2(nx, ny).centered().translate(2, 1.)

    #color = [ 'yellow' ]*(nx-2) + ['orange','red','orange']

    if part == "Plane":
        G = F
    else:
        if part == "Half Sphere":
            sx = 180.
        else:
            sx = 360.
        G = F.spherical(scale=[sx/nx, 180./ny, 2.*max(nx, ny)]).rollAxes(-1)
    draw(G, color=color, colormap=colormap)
    drawText('Created with pyFormex', 10, 10)

if __name__ == 'draw':
    run()
# End
