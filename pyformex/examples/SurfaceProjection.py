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

"""SurfaceProjection.py

This example illustrates the use of Coords.projectOnSurface and
trisurface.intersectSurfaceWithLines as a method to render a 2D image
onto a 3D surface.

"""
from __future__ import absolute_import, division, print_function

_status = 'checked'
_level = 'normal'
_topics = ['surface']
_techniques = ['transform', 'projection', 'dialog', 'image', 'isopar']

from pyformex.gui.draw import *
from pyformex import elements
from pyformex.gui.widgets import ImageView
from pyformex.plugins.imagearray import *


def loadImage(fn):
    global image, scaled_image
    image = QImage(fn)
    if image.isNull():
        warning("Could not load image '%s'" % fn)
        return None
    return image


def makeGrid(nx, ny, eltype):
    """Create a 2D grid of nx*ny elements of type eltype.

    The grid is scaled to unit size and centered.
    """
    elem = getattr(elements, eltype)
    return elem.toFormex().replic2(nx, ny).resized(1.).centered()


def drawImage(grid, base, patch):
    """Draw the image on the specified patch grid.

    The image colors are specified in the global variable pcolor.
    grid is a Formex with px*py Quad8 elements.
    Each element of grid will be filled by a kx*ky patch of colors.
    """
    mT = [ patch.isopar('quad8', x, base) for x in grid.coords ]
    return [ draw(i, color=c, alpha=0.99, bbox='last', nolight=True, wait=False) for i, c in zip (mT, pcolor)]


def run():
    global viewer, pcolor, px, py
    clear()
    smooth()
    lights(True)
    transparent(False)
    view('iso')

    image = None
    scaled_image = None

    # read the teapot surface
    T = TriSurface.read(getcfg('datadir')+'/teapot.off')
    xmin, xmax = T.bbox()
    T= T.trl(-T.center()).scale(4./(xmax[0]-xmin[0])).setProp(2)
    draw(T)

    # default image file
    dfilename = getcfg('datadir')+'/benedict_6.jpg'
    viewer = ImageView(dfilename, maxheight=200)

    res = askItems([
        _I('filename', dfilename, text='Image file', itemtype='filename', filter='img', exist=True, preview=viewer),
        viewer,
        _I('px', 4, text='Number of patches in x-direction'),
        _I('py', 6, text='Number of patches in y-direction'),
        _I('kx', 30, text='Width of a patch in pixels'),
        _I('ky', 30, text='Height of a patch in pixels'),
        _I('scale', 0.8, text='Scale factor'),
        _I('trl', [-0.4, -0.1, 2.], itemtype='point', text='Translation'),
        ])

    if not res:
        return

    globals().update(res)

    nx, ny = px*kx, py*ky # pixels
    print('The image is reconstructed with %d x %d pixels'%(nx, ny))

    F = Formex('4:0123').replic2(nx, ny).centered()
    if image is None:
        print("Loading image")
        image = loadImage(filename)
        wpic, hpic = image.width(), image.height()
        print("Image size is %sx%s" % (wpic, hpic))

    if image is None:
        return

    # Create the colors
    color, colortable = qimage2glcolor(image.scaled(nx, ny))
    # Reorder by patch
    pcolor = color.reshape((py, ky, px, kx, 3)).swapaxes(1, 2).reshape(-1, kx*ky, 3)
    print("Shape of the colors array: %s" % str(pcolor.shape))

    mH = makeGrid(px, py, 'Quad8')

    try:
        ratioYX = float(hpic)/wpic
        mH = mH.scale(ratioYX, 1) # Keep original aspect ratio
    except:
        pass

    mH0 = mH.scale(scale).translate(trl)

    dg0 = draw(mH0, mode='wireframe')
    zoomAll()
    zoom(0.5)
    print("Create %s x %s patches" % (px, py))

    # Create the transforms
    base = makeGrid(1, 1, 'Quad8').coords[0]
    patch = makeGrid(kx, ky, 'Quad4').toMesh()
    d0 = drawImage(mH0, base, patch)

    pts = mH0.coords.projectOnSurface(T, [0., 0., 1.], '-f')
    dp = draw(pts, marksize=6, color='white')
    mH2 = Formex(pts.reshape(-1, 8, 3))

    x = connect([mH0.points(), mH2.points()])
    dx = draw(x)

    print("Create projection mapping using the grid points")
    d2 = drawImage(mH2.trl([0., 0., 0.01]), base, patch)
    # small translation to make sure the image is above the surface, not cutting it

    print("Finally show the finished image")
    undraw(dp);
    undraw(dx);
    undraw(d0);
    undraw(dg0);
    view('front')
    zoomAll()

if __name__ == '__draw__':
    run()
# End
