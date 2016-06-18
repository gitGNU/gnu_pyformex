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
"""FieldColor

This examples shows how to use the 'fld:name' color attribute in drawing
and how to interactively select the colors displayed on an object.
"""
from __future__ import print_function


_status = 'checked'
_level = 'normal'
_topics = ['image']
_techniques = ['color', 'field', 'field color', 'slider']

from pyformex.gui.draw import *
from pyformex.plugins.imagearray import *


def changeColorDirect(i):
    """Change the displayed color by directly changing color attribute."""
    global FA
    F = FA.object
    color = F.getField('color_%s' % i).data
    FA.drawable[0].changeVertexColor(color)
    pf.canvas.update()


def setFrame(item):
    changeColorDirect(item.value())


def run():
    global width,height,FA,dia,dotsize
    clear()
    smooth()
    lights(False)
    view('front')

    # read an image from pyFormex data
    filename = os.path.join(getcfg('datadir'), 'butterfly')
    print(filename)
    im = QtGui.QImage(filename)
    if im.isNull():
        warning("Could not load image '%s'" % fn)
        return
    nx, ny = im.width(), im.height()
    print("Image size: %s x %s" % (nx,ny))

    # Create a 2D grid of nx*ny elements
    model = 'Dots'
    dotsize = 3
    if model == 'Dots':
        base = '1:0'
    else:
        base = '4:0123'
    F = Formex(base).replic2(nx,ny).toMesh()

    # Draw the image
    color, colormap = qimage2glcolor(im)
    if colormap is not None:
        print("This image is not fit for our purposes.")
        return

    FA = draw(F, color=color, colormap=None, marksize=dotsize, name='image')

    # Create some color fields
    # The color fields consist of the original image with one of
    # the standard colors mixed in.
    nframes = 10
    mix = [ 0.7, 0.3 ]
    for i in range(nframes):
        fld = mix[0] * color + mix[1] * pf.canvas.settings.colormap[i]
        F.addField('node',fld,'color_%s' % i)

    frame = 0
    dia = Dialog([
        _I('frame',frame,itemtype='slider',min=0,max=nframes-1,ticks=1,func=setFrame,tooltip="Move the slider to see one of the color fields displayed on the original Actor"),
        ])
    dia.show()
    dia.setMinimumWidth(500)


if __name__ == '__draw__':
    run()

# End
