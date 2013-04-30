# $Id$
##
##  This file is part of the pyFormex project.
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
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
"""OpenGL rendering objects for the new OpenGL2 engine.

"""
from __future__ import print_function

from gui.drawable import *
from OpenGL import GL
from OpenGL.arrays.vbo import VBO
from attributes import Attributes
from formex import Formex
from mesh import Mesh


### Drawable Objects ###############################################



def glObjType(nplex):
    try:
        return [GL.GL_POINTS,GL.GL_LINES,GL.GL_TRIANGLES][nplex-1]
    except:
        return None


class Actor(Attributes):
    """Proposal for drawn objects

    __init__:  store all static values: attributes, geometry, vbo's
    prepare: creates sanitized and derived attributes/data
    render: push values to shader and render the object

    __init__ is only dependent on input attributes and geometry

    prepare may depend on current canvas settings:
      mode, transparent,

    render depends on canvas and renderer
    """

    def __init__(self,obj,**kargs):
        Attributes.__init__(self)

        # Check it is something we can draw
        if not isinstance(obj,Mesh) and not isinstance(obj,Formex):
            try:
                obj = obj.toFormex()
            except:
                raise ValueError,"Can only render Mesh, Formex and objects that can be converted to Formex"
        glmode = glObjType(obj.nplex())
        self.object = obj

        if glmode is None:
            raise ValueError,"Can only render plex-1/2/3 objects"
        self.glmode = glmode

        # Acknowledge all object attributes and passed parameters
        self.update(obj.attrib)
        self.update(kargs)

        # Create the static data buffers
        self.vbo = VBO(obj.coords)
        if isinstance(obj,Mesh):
            self.ibo = VBO(obj.elems,target=GL.GL_ELEMENT_ARRAY_BUFFER)
        else:
            self.ibo = None


    def prepare(self,renderer):
        print("PREPARE ACTOR")
        # colormode:
        # 0 = None
        # 1 = object
        # 2 = element
        # 3 = vertex
        self.setColor(self.color,self.colormap)
        self.setBkColor(self.bkcolor,self.bkcolormap)
        self.setAlpha(self.alpha,self.bkalpha)
        print(self.color)
        if self.color is None:
            self.colormode = 0
        self.colormode = 1
        self.objectColor = red
        self.lighting = True
        self.opacity = 1.0
        self.ambient = 0.3
        self.diffuse = 0.2
        print(self)


    def setColor(self,color,colormap=None):
        """Set the color of the Actor."""
        self.color,self.colormap = saneColorSet(color,colormap,self.object.shape)


    def setBkColor(self,color,colormap=None):
        """Set the backside color of the Actor."""
        self.bkcolor,self.bkcolormap = saneColorSet(color,colormap,self.object.shape)


    def setAlpha(self,alpha,bkalpha):
        """Set the Actors alpha value."""
        try:
            self.alpha = float(alpha)
        except:
            self.alpha = None
        if bkalpha is None:
            bkalpha = alpha
        try:
            self.bkalpha = float(bkalpha)
        except:
            self.bkalpha = None
        self.opak = (self.alpha == 1.0) or (self.bkalpha == 1.0 )


    def render(self):
        """Render the geometry of this object"""
        self.vbo.bind()

        try:
            GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
            GL.glVertexPointerf(self.vbo)
            if self.ibo:
                self.ibo.bind()
                GL.glDrawElementsui(self.glmode,self.ibo)
            else:
                GL.glDrawArrays(self.glmode,0,self.object.npoints())
        finally:
            self.vbo.unbind()
            if self.ibo:
                self.ibo.unbind()
            GL.glDisableClientState(GL.GL_VERTEX_ARRAY)



### End
