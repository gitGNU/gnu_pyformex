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

from pyformex import olist

linetable = (
    (), (0,3), (0,1), (1,3), (1,2), (0,1,2,3), (0,2), (2,3),
    (2,3), (0,2), (0,3,1,2), (1,2), (1,3), (0,1), (0,3), (),
    )

vertextable = [
    [0, 1],
    [1, 2],
    [2, 3],
    [3, 0],
    ]

def splitSquare(pos, val, level):
    """Split a single square

    """
    from pyformex.lib.misc import vertexinterp

    pos = pos.astype(float32)

    # Determine the index into the edge table which
    # tells us which vertices are inside of the surface

    cubeindex = 0
    for i in range(4):
        if val[i] >= level:
            cubeindex |= 1 << i

    # Find the vertices where the surface intersects the cube
    vertlist = []

    for edges in olist.group(linetable[cubeindex],2):
        for e in edges:
            verts = vertextable[e]
            p1, p2 = pos[verts]
            val1, val2 = val[verts]
            vert = vertexinterp(level, p1, p2, val1, val2)
            vertlist.append(vert)

    return vertlist


grid = np.array([
    [0, 0],
    [1, 0],
    [1, 1],
    [0, 1],
    ])


def isoline(data, level):
    """Create an isoline through data at given level.

    - `data`: (nx,ny) shaped array of data values at points with
      coordinates equal to their indices. This defines a 2D area
      [0,nx-1], [0,ny-1],
    - `level`: data value at which the isoline is to be constructed

    Returns an (nseg,2,2) array defining the segments of the isoline.
    The result may be empty (if level is outside the data range).
    """
    segments=[]
    def addSegments(x, y):
        pos = grid + [x, y]
        val = data[pos[:, 1], pos[:, 0]]
        t = splitSquare(pos, val, level)
        segments.extend(t)
        return len(segments)

    [ [ addSegments(x, y)
        for x in range(data.shape[1]-1) ]
      for y in range(data.shape[0]-1) ]

    segments = asarray(segments).reshape(-1, 2, 2)
    return segments


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
    color = color[100:160,100:160,:]
    nx,ny = color.shape[:2]
    color = color.reshape(-1,3)
    F = Formex('1:0').replic2(nx, ny)
    FA = draw(F, color=color, colormap=colortable, nolight=True)
    col = FA.color
    intens = FA.color.sum(axis=-1) / 3
    data = intens.reshape(ny,nx)
    seg = isoline(data,0.5)
    F = Formex(seg)
    draw(F,color=red,linewidth=2)

if __name__ == 'draw':
    run()

# End
