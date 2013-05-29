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
from shader import Shader
from attributes import Attributes
from formex import Formex
from mesh import Mesh
from elements import elementType
import geomtools as gt
import utils


### Drawable Objects ###############################################


def glObjType(nplex):
    if nplex <= 3:
        return [GL.GL_POINTS,GL.GL_LINES,GL.GL_TRIANGLES][nplex-1]
    else:
        # everything higher is a polygon
        return GL.GL_TRIANGLE_FAN


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





class Drawable(Attributes):
    """Proposal for drawn objects

    __init__:  store all static values: attributes, geometry, vbo's
    prepare: creates sanitized and derived attributes/data
    render: push values to shader and render the object

    __init__ is only dependent on input attributes and geometry

    prepare may depend on current canvas settings:
      mode, transparent, avgnormals

    render depends on canvas and renderer

    This is the basic drawable object. It can not have extras nor
    children. The geometry is initialized by a coords,elems
    tuple. This class is normally not added directly to renderer,
    but through one of the *Actor classes.
    The passed parameters should at least contain vbo.
    """

    # A list of acceptable attributes in the drawable
    attributes = Shader.uniforms + [
        'glmode', 'frontface', 'backface', 'vbo', 'ibo', 'nbo', 'cbo',
        ]

    def __init__(self,**kargs):
        """Create a new drawable."""

        print("DRAWABLE MODE %s" % kargs['glmode'])
        kargs = utils.selectDict(kargs,Drawable.attributes)

        Attributes.__init__(self,kargs)


    def render(self,renderer):
        """Render the geometry of this object"""

        def render_geom():
            if self.ibo:
                GL.glDrawElementsui(self.glmode,self.ibo)
            else:
                GL.glDrawArrays(self.glmode,0,asarray(self.vbo.shape[:-1]).prod())

        self.vbo.bind()
        if self.builtin:
            GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
            GL.glVertexPointerf(self.vbo)
        else:
            GL.glEnableVertexAttribArray(renderer.shader.attribute['vertexPosition'])
            GL.glVertexAttribPointer(renderer.shader.attribute['vertexPosition'],3, GL.GL_FLOAT,False,0,self.vbo)

        if self.ibo:
            self.ibo.bind()

        if self.nbo:
            self.nbo.bind()
            if self.builtin:
                GL.glEnableClientState(GL.GL_NORMAL_ARRAY)
                GL.glNormalPointerf(self.nbo)
            else:
                GL.glEnableVertexAttribArray(renderer.shader.attribute['vertexNormal'])
                GL.glVertexAttribPointer(renderer.shader.attribute['vertexNormal'],3, GL.GL_FLOAT,False,0,self.nbo)

        if self.cbo:
            self.cbo.bind()
            if self.builtin:
                GL.glEnableClientState(GL.GL_COLOR_ARRAY)
                GL.glColorPointerf(self.cbo)
            else:
                GL.glEnableVertexAttribArray(renderer.shader.attribute['vertexColor'])
                GL.glVertexAttribPointer(renderer.shader.attribute['vertexColor'],3, GL.GL_FLOAT,False,0,self.cbo)


        if self.frontface:
            # Draw front faces
            GL.glEnable(GL.GL_CULL_FACE)
            GL.glCullFace(GL.GL_BACK)
        elif self.backface:
            # Draw back faces
            GL.glEnable(GL.GL_CULL_FACE)
            GL.glCullFace(GL.GL_FRONT)

        self.builtin = renderer.shader.builtin
        renderer.shader.loadUniforms(self)
        render_geom()

        GL.glDisable(GL.GL_CULL_FACE)

        if self.ibo:
            self.ibo.unbind()
        if self.cbo:
            self.cbo.unbind()
            if self.builtin:
                GL.glDisableClientState(GL.GL_COLOR_ARRAY)
            else:
                GL.glDisableVertexAttribArray(renderer.shader.attribute['vertexColor'])
        if self.nbo:
            self.nbo.unbind()
            if self.builtin:
                GL.glDisableClientState(GL.GL_NORMAL_ARRAY)
            else:
                GL.glDisableVertexAttribArray(renderer.shader.attribute['vertexNormal'])
        self.vbo.unbind()
        if self.builtin:
            GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        else:
            GL.glDisableVertexAttribArray(renderer.shader.attribute['vertexPosition'])



class GeomActor(Attributes):
    """Proposal for drawn objects

    __init__:  store all static values: attributes, geometry, vbo's
    prepare: creates sanitized and derived attributes/data
    render: push values to shader and render the object

    __init__ is only dependent on input attributes and geometry

    prepare may depend on current canvas settings:
      mode, transparent, avgnormals

    render depends on canvas and renderer

    If the actor does not have a name, it will be given a
    default one.
    """

    # default names for the actors
    defaultname = utils.NameSequence('object-0')


    def __init__(self,obj,**kargs):

        if 'name' not in kargs:
            kargs['name'] = GeomActor.defaultname.next()

        Attributes.__init__(self)

        # Check it is something we can draw
        if not isinstance(obj,Mesh) and not isinstance(obj,Formex):
            try:
                obj = obj.toFormex()
            except:
                raise ValueError,"Object is of type %s.\nCan only render Mesh, Formex and objects that can be converted to Formex" % type(obj)
        self.object = obj

        if isinstance(obj,Mesh): # should we store coords, elems and eltype?
            coords = obj.coords
            elems = obj.elems.astype(int32)
            eltype = obj.elName()

        elif isinstance(obj,Formex):
            coords = obj.coords.astype(float32)
            elems = None
            eltype = obj.eltype

        # Externally specified normals
        ## if hasattr(obj,'normals'):
        ##     self.normals = obj.normals

        # Get the local connectivity for drawing the edges/faces
        if eltype is not None:
            eltype = elementType(eltype)
            if eltype.ndim == 0:
                drawelems = None
            elif eltype.ndim == 1:
                drawelems = eltype.getDrawEdges()[0]
            else:
                drawelems = eltype.getDrawFaces()[0]

            if drawelems is not None:
                if elems is None:
                    elems = arange(coords.npoints()).reshape(coords.shape[:-1])
                elems = elems[:,drawelems]


        # Set drawing plexitude (may be different from object plexitude)
        if elems is None:
            self.nplex = coords.shape[1]
        else:
            self.nplex = elems.shape[-1]

        # set the basic primitive type
        self.glmode = glObjType(self.nplex)

        self._edges = None # The edges in *wire modes


        self.children = []

        # Acknowledge all object attributes and passed parameters
        self.update(obj.attrib)
        self.update(kargs)

        # Create the static data buffers
        self.vbo = VBO(coords.astype(float32))
        if elems is not None:
            self.ibo = VBO(elems.astype(int32),target=GL.GL_ELEMENT_ARRAY_BUFFER)

        ## if self.normals:
        ##     self.nbo = VBO(normals.astype(float32))


    def prepare(self,renderer):
        """Prepare the attributes for the renderer.

        This sanitizes and completes the attributes for the renderer.
        Since the attributes may be dependent on the rendering mode,
        this method is called on each mode change.
        """
        print("PREPARE ACTOR")
        self.drawable = []
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

        # Prepare the buffer objects for this actor
        if renderer.mode.startswith('smooth'):
            if self.nbo is None:
                normals = computeNormals(self.object,renderer.canvas.settings.avgnormals)
                self.nbo = VBO(normals)

        if self.vertexColor is not None:
            self.cbo = VBO(self.vertexColor)

        #### BACK COLOR ####
        if self.bkcolor is not None:
            # Draw both sides separately
            # First, front sides
            self.drawable.append(Drawable(frontface=True,**self))
            # Make copy for back sides
            extra = Attributes(self)
            extra.colormode = self.bkcolor.ndim
            if extra.colormode == 1:
                extra.objectColor = self.bkcolor
            self.drawable.append(Drawable(backface=True,**extra))
        else:
            # Just draw both sides at once
            self.drawable.append(Drawable(**self))


        #### MODE DEPENDENT MODIFICATIONS ####
        self.changeMode(renderer)

        #### CHILDREN ####
        for child in self.children:
            child.prepare(renderer)


    def changeMode(self,renderer):
        """Modify the actor according to the specified mode"""
        print("CHANGE TO MODE %s"%renderer.mode)
        self.switchEdges(renderer.mode.endswith('wire'))


        print("PREPARED %s DRAWABLES" % len(self.drawable))
        for i,d in enumerate(self.drawable):
            print(i,d)


    def switchEdges(self,on):
        """Add or remove the edges depending on rendering mode"""
        if on:
            # Create a drawable for the edges
            if self.nplex > 1 and isinstance(self.object,Mesh):
                if self._edges is None:
                    edges = self.object.getEdges()
                    print(edges)
                    if len(edges) > 0:
                        extra = Attributes(self)
                        extra.colormode = 1
                        extra.objectColor = black
                        extra.opak = True
                        extra.lighting = False
                        extra.elems = edges
                        extra.glmode = glObjType(2)
                        extra.ibo = VBO(edges.astype(int32),target=GL.GL_ELEMENT_ARRAY_BUFFER)
                        # store, so we can switch on/off
                        self._edges = Drawable(**extra)
                        print("CREATED EDGES")
            if self._edges:
                print("ADDING EDGES")
                self.drawable.append(self._edges)
        else:
            if self._edges and self._edges in self.drawable:
                print("REMOVING EDGES")
                self.drawable.remove(self._edges)


    def setColor(self,color,colormap=None):
        """Set the color of the Actor."""
        #print("OBJECT COLOR= %s" % str(color))
        #print("OBJECT COLORMAP= %s" % str(colormap))
        #print("OBJECT SHAPE= %s" % str(self.object.shape))
        self.color,self.colormap = saneColorSet(color,colormap,self.object.coords.shape)


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

        for obj in self.drawable:
            obj.render(renderer)

        for obj in self.children:
            obj.render(renderer)


### End
