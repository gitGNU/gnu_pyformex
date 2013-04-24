# $Id$
"""opengl/renderer.py

Python OpenGL framework for pyFormex

This OpenGL framework is intended to replace (in due time)
the current OpenGL framework in pyFormex.

(C) 2013 Benedict Verhegghe and the pyFormex project.

"""
from __future__ import print_function

import os
import pyformex as pf
from coords import bbox
from formex import Formex
from mesh import Mesh
import numpy as np
from OpenGL import GL
from shader import Shader
from OpenGL.arrays.vbo import VBO


def glObjType(nplex):
    try:
        return [GL.GL_POINTS,GL.GL_LINES,GL.GL_TRIANGLES][nplex-1]
    except:
        return None


class Renderer(object):

    def __init__(self,canvas,shader=None):
        self.canvas = canvas
        self.camera = canvas.camera
        self.canvas.makeCurrent()

        if shader is None:
            shader = Shader()
        self.shader = shader
        self.clear()


    def clear(self):
        self._objects = []
        self._vbo = {}
        self._ibo = {}
        self._bbox = bbox([0.,0.,0.])


    def add(self,obj):
        if not isinstance(obj,Mesh) and not isinstance(obj,Formex):
            try:
                obj = obj.toFormex()
            except:
                raise ValueError,"Can only render Mesh, Formex and objects that can be converted to Formex"
        glmode = glObjType(obj.nplex())
        if glmode is None:
            raise ValueError,"Can only render plex-1/2/3 objects"
        obj.glmode = glmode

        oid = id(obj)
        self._vbo[oid] = VBO(obj.coords)
        if isinstance(obj,Mesh):
            self._ibo[oid] = VBO(obj.elems,target=GL.GL_ELEMENT_ARRAY_BUFFER)
        self._objects.append(obj)
        self._bbox = bbox([self._bbox,obj])
        self.canvas.camera.focus = self._bbox.center()
        print("NEW BBOX: %s" % self._bbox)


    def setDefaults(self):
        """Set all the uniforms to default values."""
        self.shader.uniformFloat('lighting',True) # self.canvas....
        self.shader.uniformInt('useObjectColor',True)
        self.shader.uniformVec3('objectColor',self.canvas.settings.fgcolor)
        GL.glEnable(GL.GL_VERTEX_PROGRAM_POINT_SIZE)
        GL.glLineWidth(5.) #self.canvas.settings.linewidth)
        # Should do pointsize with gl context?
        self.shader.uniformFloat('pointsize',5.0)
        self.shader.uniformFloat('ambient',0.3) # self.canvas....
        self.shader.uniformFloat('diffuse',0.8) # self.canvas....
        self.shader.uniformFloat('specular',0.2) # self.canvas....


    def setUniforms(self,obj):
        """Set all the uniforms that may be object dependent."""
        if hasattr(obj,'lighting'):
            self.shader.uniformInt('lighting',obj.lighting)
        if hasattr(obj,'objectColor'):
            self.shader.uniformInt('useObjectColor',True)
            self.shader.uniformVec3('objectColor',obj.objectColor)
        # Set float attributes
        for a in ['pointsize','ambient','diffuse','specular']:
            if hasattr(obj,a):
                self.shader.uniformFloat(a,getattr(obj,a))


    def renderObject(self,obj):
        oid = id(obj)
        vbo = self._vbo[oid]
        vbo.bind()

        try:
            GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
            GL.glVertexPointerf(vbo)
            if oid in self._ibo:
                ibo = self._ibo[oid]
                ibo.bind()
                GL.glDrawElementsui(obj.glmode,ibo)
            else:
                GL.glDrawArrays(obj.glmode,0,obj.npoints())
        finally:
            vbo.unbind()
            if oid in self._ibo:
                ibo.unbind()
            GL.glDisableClientState(GL.GL_VERTEX_ARRAY)


    def render(self):
        """Render the geometry for the scene."""
        self.shader.bind()

        # Get the current modelview*projection matrix
        modelview = self.camera.modelview
        #print("MODELVIEW-R",modelview)
        projection = self.camera.projection
        #print("PROJECTION-R",projection)

        # Propagate the matrices to the uniforms of the shader
        self.shader.uniformMat4('modelview',modelview.gl())
        self.shader.uniformMat4('projection',projection.gl())
        self.setDefaults()

        try:
            for obj in self._objects:
                if hasattr(obj,'visible') and not obj.visible:
                    # skip invisible object
                    continue
                try:
                    self.setUniforms(obj)
                    self.renderObject(obj)
                except:
                    pass
        finally:
            self.shader.unbind()


# End
