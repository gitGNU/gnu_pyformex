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
from __future__ import absolute_import, division, print_function


import pyformex as pf
from pyformex import arraytools as at
import sys
from OpenGL import GL

from pyformex.legacy.drawable import drawNurbsCurves, drawNurbsSurfaces
from pyformex.opengl.sanitize import saneColorSet
from pyformex.formex import *

from pyformex.plugins.nurbs import NurbsCurve, NurbsSurface


### Drawable Objects ###############################################

class Drawable(object):
    """A Drawable is anything that can be drawn on the OpenGL Canvas.

    This defines the interface for all drawbale objects, but does not
    implement any drawable objects.
    Drawable objects should be instantiated from the derived classes.
    Currently, we have the following derived classes:
      Actor: a 3-D object positioned and oriented in the 3D scene. Defined
             in actors.py.
      Mark: an object positioned in 3D scene but not undergoing the camera
             axis rotations and translations. It will always appear the same
             to the viewer, but will move over the screen according to its
             3D position. Defined in marks.py.
      Decor: an object drawn in 2D viewport coordinates. It will unchangeably
             stick on the viewport until removed. Defined in decors.py.

    A Drawable subclass should minimally reimplement the following methods:
      bbox(): return the actors bounding box.
      nelems(): return the number of elements of the actor.
      drawGL(mode): to draw the object. Takes a mode argument so the
        drawing function can act differently depending on the rendering mode.
        There are currently 5 modes:
           wireframe, flat, smooth, flatwire, smoothwire.
        drawGL should only contain OpenGL calls that are allowed inside a
        display list. This may include calling the display list of another
        actor but *not* creating a new display list.
    """

    def __init__(self,nolight=False,ontop=False,**kargs):
        self.list = None
        self.listmode = None # stores mode of self.list: wireframe/smooth/flat
        self.mode = None # subclasses can set a persistent drawing mode
        self.opak = True
        self.nolight = nolight
        self.ontop = ontop
        self.extra = [] # list of dependent Drawables


    def __del__(self):
        self.delete_list()


    def drawGL(self,**kargs):
        """Perform the OpenGL drawing functions to display the actor."""
        pass

    def pickGL(self,**kargs):
        """Mimick the OpenGL drawing functions to pick (from) the actor."""
        pass

    def redraw(self,**kargs):
        self.draw(**kargs)

    def draw(self,**kargs):
        self.prepare_list(**kargs)
        self.use_list()

    def prepare_list(self,**kargs):
        mode = self.mode
        if mode is None:
            if 'mode' in kargs:
                mode = kargs['mode']
            else:
                canvas = kargs.get('canvas', pf.canvas)
                mode = canvas.rendermode

        if mode.endswith('wire'):
            mode = mode[:-4]

        if self.list is None or mode != self.listmode:
            kargs['mode'] = mode
            self.delete_list()
            self.list = self.create_list(**kargs)

    def use_list(self):
        if self.list:
            GL.glCallList(self.list)
        for i in self.extra:
            i.use_list()

    def create_list(self,**kargs):
        displist = GL.glGenLists(1)
        pf.debug("CREATE LIST %s" % displist, pf.DEBUG.OPENGL)
        GL.glNewList(displist, GL.GL_COMPILE)
        ok = False
        try:
            if self.nolight:
                GL.glDisable(GL.GL_LIGHTING)
            if self.ontop:
                GL.glDepthFunc(GL.GL_ALWAYS)
            self.drawGL(**kargs)
            ok = True
        finally:
            if not ok:
                pf.debug("Error while creating a display list", pf.DEBUG.DRAW)
                displist = None
            GL.glEndList()
        self.listmode = kargs['mode']
        return displist

    def delete_list(self):
        pf.debug("DELETE LIST %s" % self.list, pf.DEBUG.OPENGL)
        if self.list:
            GL.glDeleteLists(self.list, 1)
            pf.debug("REALLY DELETED", pf.DEBUG.OPENGL)
        else:
            pf.debug("NOT REALLY DELETED", pf.DEBUG.OPENGL)
        self.list = None


    def setLineWidth(self, linewidth):
        """Set the linewidth of the Drawable."""
        self.linewidth = saneLineWidth(linewidth)

    def setLineStipple(self, linestipple):
        """Set the linewidth of the Drawable."""
        self.linestipple = saneLineStipple(linestipple)

    def setColor(self,color=None,colormap=None,ncolors=1):
        """Set the color of the Drawable."""
        self.color, self.colormap = saneColorSet(color, colormap, shape=(ncolors,))

    def setTexture(self, texture):
        """Set the texture data of the Drawable."""
        from pyformex.opengl.texture import Texture
        if texture is not None:
            if not isinstance(texture, Texture):
                try:
                    texture = Texture(texture)
                except:
                    texture = None
        self.texture = texture

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


class NurbsActor(Actor):

    def __init__(self,data,color=None,colormap=None,bkcolor=None,bkcolormap=None,**kargs):
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
