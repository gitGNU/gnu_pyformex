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

import pyformex as pf
from gui.drawable import *
from OpenGL import GL
from OpenGL.arrays.vbo import VBO
from attributes import Attributes
from formex import Formex
from mesh import Mesh
from elements import elementType
import geomtools as gt


### Drawable Objects ###############################################


def glObjType(nplex):
    try:
        return [GL.GL_POINTS,GL.GL_LINES,GL.GL_TRIANGLES][nplex-1]
    except:
        return None


def computeMeshNormals(obj,avg=False,tol=None):
    """Compute the normals of a Mesh object"""
    if avg:
        if tol is None:
            tol = pf.cfg['render/avgnormaltreshold']
        return gt.averageNormals(obj.coords,obj.elems,False,tol)

    else:
        return computeFormexNormals(obj.toFormex())


def computeFormexNormals(obj,avg=False,tol=None):
    """Compute the normals of a Formex"""
    if avg:
        if tol is None:
            tol = pf.cfg['render/avgnormaltreshold']
        return computeMeshNormals(obj.toMesh(),avg,tol)

    else:
       return gt.polygonNormals(obj.coords)


def computeNormals(obj,avg=False,tol=None):
    """Compute the normals of the object to draw"""
    if isinstance(obj,Formex):
        return computeFormexNormals(obj,avg,tol)
    elif isinstance(obj,Mesh):
        return computeMeshNormals(obj,avg,tol)


class GeomActor(Attributes):
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
        self.object = obj

        if isinstance(obj,Mesh): # should we store coords, elems and eltype?
            coords = obj.coords.astype(float32)
            elems = obj.elems.astype(int32)
            eltype = obj.elName()

        elif isinstance(obj,Formex):
            coords = obj.coords.astype(float32)
            elems = None
            eltype = obj.eltype

        if hasattr(obj,'normals'):
            self.normals = obj.normals

        # Get the local connectivity for drawing the edges/faces
        if eltype is None:
            # should these objects be drawn as polygons or should
            # a default element type based on the plexitude be used?
            drawelems = None
        else:
            eltype = elementType(eltype)
            if eltype.ndim == 0:
                drawelems = None
            elif eltype.ndim == 1:
                drawelems = eltype.getDrawEdges()[0]
            else:
                drawelems = eltype.getDrawFaces()[0]

        # get the coords, connectivity and plexitude
        if drawelems is None:
            nplex = obj.nplex()
        elif elems is None:
            coords = coords[:,drawelems,:]
            nplex = coords.shape[2]
        else:
            elems = elems[:,drawelems]
            nplex = elems.shape[2]

        # get and check the primitive type
        glmode = glObjType(nplex)
        if glmode is None:
            raise ValueError,"Can only render plex-1/2/3 objects"
        self.glmode = glmode

        # Acknowledge all object attributes and passed parameters
        self.update(obj.attrib)
        self.update(kargs)

        # Create the static data buffers
        self.vbo = VBO(coords)
        if elems is not None:
            self.ibo = VBO(elems,target=GL.GL_ELEMENT_ARRAY_BUFFER)

        if self.normals:
            self.nbo = VBO(self.normals)


    def prepare(self,renderer):
        # set proper attributes
        print("PREPARE ACTOR")
        self.setColor(self.color,self.colormap)
        self.setBkColor(self.bkcolor,self.bkcolormap)
        self.setAlpha(self.alpha,self.bkalpha)
        self.setLineWidth(self.linewidth)
        self.setLineStipple(self.linestipple)

        # Set derived uniforms for shader
        # colormode:
        # 0 = None
        # 1 = object
        # 2 = element
        # 3 = vertex
        if self.color is None:
            self.colormode = 0
        else:
            self.colormode = self.color.ndim
        if self.colormode == 1:
            self.objectColor = self.color
        elif self.colormode == 2:
            self.elemColor = self.color
        elif self.colormode == 3:
            self.vertexColor = self.color

        self.lighting = True
        self.opacity = 1.0
        self.ambient = 0.3
        self.diffuse = 0.2
        print("PREPARED",self)

        if renderer.canvas.rendermode.startswith('smooth'):
            if self.nbo is None:
                normals = computeNormals(self.object,renderer.canvas.settings.avgnormals)
                self.nbo = VBO(normals)

        if self.vertexColor is not None:
            self.cbo = VBO(self.vertexColor)


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


    def setLineWidth(self,linewidth):
        """Set the linewidth of the Drawable."""
        self.linewidth = saneLineWidth(linewidth)

    def setLineStipple(self,linestipple):
        """Set the linewidth of the Drawable."""
        self.linestipple = saneLineStipple(linestipple)


    def render(self,renderer):
        """Render the geometry of this object"""

        def render_geom():
            if self.ibo:
                GL.glDrawElementsui(self.glmode,self.ibo)
            else:
                GL.glDrawArrays(self.glmode,0,asarray(self.vbo.shape[:-1]).prod())

        self.vbo.bind()
        GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
        GL.glVertexPointerf(self.vbo)

        if self.ibo:
            self.ibo.bind()

        if self.nbo:
            self.nbo.bind()
            GL.glEnableClientState(GL.GL_NORMAL_ARRAY)
            GL.glNormalPointerf(self.nbo)

        if self.cbo:
            print("BIND VERTEX COLOR %s" % str(self.cbo.shape))
            self.cbo.bind()
            GL.glEnableClientState(GL.GL_COLOR_ARRAY)
            GL.glColorPointerf(self.cbo)

        if self.bkcolor is not None:
            # Enable drawing front and back with different colors
            GL.glEnable(GL.GL_CULL_FACE)
            GL.glCullFace(GL.GL_BACK)

        render_geom()

        if self.bkcolor is not None:
            # Draw the back sides in another color
            bk = Attributes()
            bk.colormode = self.bkcolor.ndim
            if bk.colormode == 1:
                bk.objectColor = self.bkcolor
            renderer.shader.loadUniforms(bk)

            GL.glCullFace(GL.GL_FRONT)
            render_geom()
            GL.glDisable(GL.GL_CULL_FACE)

        if self.ibo:
            self.ibo.unbind()
        if self.cbo:
            self.cbo.unbind()
            GL.glDisableClientState(GL.GL_COLOR_ARRAY)
        if self.nbo:
            self.nbo.unbind()
            GL.glDisableClientState(GL.GL_NORMAL_ARRAY)
        self.vbo.unbind()
        GL.glDisableClientState(GL.GL_VERTEX_ARRAY)



### End
