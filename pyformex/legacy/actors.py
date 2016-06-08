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
"""OpenGL actors for populating the 3D scene.

"""
from __future__ import print_function


import pyformex as pf
from pyformex import arraytools as at
import sys
from OpenGL import GL

from pyformex.legacy.drawable import *
from pyformex.formex import *
from pyformex.elements import elementType
from pyformex.mesh import Mesh

from pyformex.trisurface import TriSurface
from pyformex.plugins.nurbs import NurbsCurve, NurbsSurface

from pyformex import timer

### Actors ###############################################

class Actor(Drawable):
    """An Actor is anything that can be drawn in an OpenGL 3D Scene.

    The visualisation of the Scene Actors is dependent on camera position and
    angles, clipping planes, rendering mode and lighting.

    An Actor subclass should minimally reimplement the following methods:

    - `bbox()`: return the actors bounding box.
    - `drawGL(mode)`: to draw the actor. Takes a mode argument so the
      drawing function can act differently depending on the mode. There are
      currently 5 modes: wireframe, flat, smooth, flatwire, smoothwire.
      drawGL should only contain OpenGL calls that are allowed inside a
      display list. This may include calling the display list of another
      actor but *not* creating a new display list.

    The interactive picking functionality requires the following methods,
    for which we provide do-nothing defaults here:

    - `npoints()`:
    - `nelems()`:
    - `pickGL()`:
    """

    def __init__(self,**kargs):
        Drawable.__init__(self,**kargs)

    def bbox(self):
        """Default implementation for bbox()."""
        try:
            return self.coords.bbox()
        except:
            raise ValueError("No bbox() defined and no coords attribute")

    def npoints(self):
        return 0
    def nelems(self):
        return 0
    def pickGL(self, mode):
        pass


class AxesActor(Actor):
    """An actor showing the three axes of a coordinate system.

    If no coordinate system is specified, the global coordinate system is drawn.

    The default actor consists of three colored lines of unit length along
    the unit vectors of the axes and three colored triangles representing the
    coordinate planes. This can be modified by the following parameters:

    size: scale factor for the unit vectors.
    color: a set of three colors to use for x,y,z axes.
    colored_axes = False: draw black axes.
    draw_planes = False: do not draw the coordinate planes.
    """
    from pyformex import coordsys

    def __init__(self,cs=None,size=1.0,psize=0.5,color=[red, green, blue],colored_axes=True,draw_planes=True,draw_reverse=True,linewidth=2,alpha=0.5,**kargs):
        Actor.__init__(self,**kargs)
        if cs is None:
            cs = coordsys.CoordinateSystem()
        self.cs = cs
        self.color = saneColorArray(saneColor(color), (3, 1))
        self.alpha = alpha
        self.opak = False
        self.nolight = True
        self.colored_axes = colored_axes
        self.draw_planes = draw_planes
        self.draw_reverse = draw_reverse
        self.linewidth = linewidth
        self.setSize(size, psize)

    def bbox(self):
        origin = self.cs[3]
        return array([origin-self.size, origin+self.size])

    def setSize(self, size, psize):
        self.size = 1.0
        size = float(size)
        if size > 0.0:
            self.size = size
        if psize is None:
            self.psize = 0.5 * self.size
        psize = float(psize)
        if psize > 0.0:
            self.psize = psize
        self.delete_list()

    def drawGL(self,**kargs):
        """Draw the axes."""
        if self.draw_planes:
            x = self.cs.trl(-self.cs[3]).scale(self.psize).trl(self.cs[3])
            e = array([[3, 1, 2], [3, 2, 0], [3, 0, 1]])
            drawPolygons(x, e, color=self.color, alpha=self.alpha)

        x = self.cs.trl(-self.cs[3]).scale(self.size).trl(self.cs[3])
        e = array([[3, 0], [3, 1], [3, 2]])
        if self.colored_axes:
            c = self.color
        else:
            c = None
        if self.linewidth:
            GL.glLineWidth(self.linewidth)
        drawLines(x, e, c)
        if self.draw_reverse:
            x[:3] = 2*x[3] - x[:3]
            drawLines(x, e, 1.0-c)


class CoordPlaneActor(Actor):
    """Draws a set of 3 coordinate planes."""

    def __init__(self,nx=(1, 1, 1),ox=(0.0, 0.0, 0.0),dx=(1.0, 1.0, 1.0),linecolor=black,linewidth=None,planecolor=white,alpha=0.5,lines=True,planes=True,**kargs):
        Actor.__init__(self,**kargs)
        self.linecolor = saneColor(linecolor)
        self.planecolor = saneColor(planecolor)
        self.linewidth = linewidth
        self.alpha = alpha
        self.opak = False
        self.lines = lines
        self.planes = planes
        self.nx = asarray(nx)
        self.x0 = asarray(ox)
        self.x1 = self.x0 + self.nx * asarray(dx)

    def bbox(self):
        return array([self.x0, self.x1])

    def drawGL(self,**kargs):
        """Draw the grid."""

        for i in range(3):
            nx = self.nx.copy()
            nx[i] = 0

            if self.lines:
                if self.linewidth:
                    GL.glLineWidth(self.linewidth)
                glColor(self.linecolor)
                drawGridLines(self.x0, self.x1, nx)

            if self.planes:
                glColor(self.planecolor, self.alpha)
                drawGridPlanes(self.x0, self.x1, nx)



class NurbsActor(Actor):

    def __init__(self,data,color=None,colormap=None,bkcolor=None,bkcolormap=None,**kargs):
        from pyformex.legacy.drawable import saneColor
        Actor.__init__(self,**kargs)
        self.object = data
        self.setColor(color, colormap)
        self.setBkColor(bkcolor, bkcolormap)
        if isinstance(self.object, NurbsCurve):
            self.samplingTolerance = 5.0
        elif isinstance(self.object, NurbsSurface):
            self.samplingTolerance = 10.0
        self.list = None


    def shape(self):
        return self.object.coords.shape[:-1]


    def setColor(self,color,colormap=None):
        """Set the color of the Actor."""
        self.color, self.colormap = saneColorSet(color, colormap, self.shape())


    def setBkColor(self,color,colormap=None):
        """Set the backside color of the Actor."""
        self.bkcolor, self.bkcolormap = saneColorSet(color, colormap, self.shape())


    def bbox(self):
        return self.object.bbox()


    def drawGL(self,canvas=None,**kargs):
        if canvas is None:
            canvas = pf.canvas

        mode = canvas.rendermode

        if mode.endswith('wire'):
            mode = mode[:-4]

        if isinstance(self.object, NurbsCurve):
            drawNurbsCurves(self.object.coords, self.object.knots, color=self.color, samplingTolerance=self.samplingTolerance)
        elif isinstance(self.object, NurbsSurface):
            if mode == 'wireframe':
                pass
            else:
                drawNurbsSurfaces(self.object.coords, self.object.vknots, self.object.uknots, color=self.color, normals='auto', samplingTolerance=self.samplingTolerance)


# End
