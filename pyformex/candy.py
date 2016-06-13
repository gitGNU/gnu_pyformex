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
"""Predefined geometries for a special purpose.

This module contains some predefined special purpose geometries functions.
You need to import this module in your scripts/apps to have access to its
contents.

Contents:

:class:`Axes` : a class representing a coordinate system
:class:`Horse`: a surface model of a horse

"""
from __future__ import print_function

from pyformex.formex import *
from pyformex.mesh import Mesh
from pyformex.coordsys import CoordSys
from pyformex.olist import List


class Axes(List):
    """A geometry representing the three axes of a coordinate system.

    The default geometry consists of three colored lines of unit length
    along the positive directions of the axes of the coordinate system,
    and three colored triangles representing the coordinate planes.
    The triangles extend from the origin to half the length of the
    unit vectors. Default colors for the axes is red, green, blue.

    Parameters:

    - `cs`: a :class:`coordsys.CoordSys`.
      If not specified, the global coordinate system is used.
    - `size`: scale factor for the unit vectors.
    - `psize`: relative scale factor for the coordinate plane triangles.
      If 0, no triangles will be drawn.
    - `reverse`: if True, also the negative unit axes are included, with
      colors 4..6.
    - `color`: a set of three or six colors to use for x,y,z axes.
      If `reverse` is True or psize > 0.0, the color set should have 6 colors,
      else 3 will suffice.
    - `kargs`: any other keyword arguments will be added as attributes
      to the geometry.

    Returns a List with two Meshes: lines and triangles.
    """

    def __init__(self,cs=None,size=1.0,psize=0.5,reverse=True,color=['red','green','blue','cyan','magenta','yellow'],linewidth=2,alpha=0.5,**kargs):
        """Initialize the AxesGeom"""

        if cs is None:
            cs = CoordSys()
        if not isinstance(cs,CoordSys):
            raise ValueError("cs should be a CoordSys")
        coords = cs.points().reshape(4,3)

        # Axes
        lines = [[3,0],[3,1],[3,2]]
        M = Mesh(coords.scale(size,center=coords[3]),lines)
        col = color[:3]
        if reverse:
            # Add negative axes
            M = Mesh.concatenate([M,M.reflect(dir=[0,1,2],pos=coords[3])])
            col = color[:6]
        M.attrib(color=col,lighting=False,opak=True,linewidth=linewidth,**kargs)
        L = [M]

        # Coord planes
        if psize > 0.0:
            planes = [[3,1,2],[3,2,0],[3,0,1]]
            M = Mesh(coords.scale(size*psize,center=coords[3]),planes)
            col = color[:3]
            bkcol = color[3:6] if reverse else col
            M.attrib(color=col,bkcolor=bkcol,lighting=False,alpha=alpha,**kargs)
            L.append(M)

        List.__init__(self,L)



# End
