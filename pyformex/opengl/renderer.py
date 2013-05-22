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
import numpy as np
from OpenGL import GL
from shader import Shader


def glObjType(nplex):
    try:
        return [GL.GL_POINTS,GL.GL_LINES,GL.GL_TRIANGLES][nplex-1]
    except:
        return None


from drawable import GeomActor

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
        self._bbox = None


    @property
    def bbox(self):
        """Return the bbox of all objects in the renderer"""
        if self._bbox is None:
            self._bbox = bbox([o.object.bbox() for o in self._objects])
        return self._bbox


    def add(self,obj,**kargs):
        actor = GeomActor(obj,**kargs)
        self.addActor(actor)


    def addActor(self,actor):
        actor.prepare(self)
        self._objects.append(actor)
        self._bbox = None
        self.canvas.camera.focus = self.bbox.center()
        print("NEW BBOX: %s" % self.bbox)


    def setDefaults(self):
        """Set all the uniforms to default values."""
        #self.shader.loadUniforms(self.canvas.settings)
        #print("DEFAULTS",self.canvas.settings)
        self.shader.uniformFloat('lighting',self.canvas.settings.lighting)
        self.shader.uniformInt('colormode',1)
        self.shader.uniformVec3('objectColor',self.canvas.settings.fgcolor)
        self.shader.uniformFloat('alpha',0.5)
        GL.glEnable(GL.GL_VERTEX_PROGRAM_POINT_SIZE)
        GL.glLineWidth(5.) #self.canvas.settings.linewidth)
        # Should do pointsize with gl context?
        self.shader.uniformFloat('pointsize',5.0)
        self.shader.uniformFloat('ambient',0.3) # self.canvas....
        self.shader.uniformFloat('diffuse',0.8) # self.canvas....
        self.shader.uniformFloat('specular',0.3) # self.canvas....
        self.shader.uniformFloat('shininess',10.) # self.canvas....
        self.shader.uniformVec3('light',(0.,1.,1.))
        self.shader.uniformVec3('speccolor',(1.,1.,0.8))
        #self.shader.loadUniforms(DEFAULTS)


    def renderObjects(self,objects):
        """Render a list of objects"""
        for obj in objects:
            self.setDefaults()

            try:
                obj.render(self)
            except:
                raise


    def render(self):
        """Render the geometry for the scene."""
        self.shader.bind()
        try:

            # Get the current modelview*projection matrix
            modelview = self.camera.modelview
            #print("MODELVIEW-R",modelview)
            projection = self.camera.projection
            #print("PROJECTION-R",projection)

            # Propagate the matrices to the uniforms of the shader
            self.shader.uniformMat4('modelview',modelview.gl())
            self.shader.uniformMat4('projection',projection.gl())

            # Make compatible with older code
            self.actors = [ o for o in self._objects if o.visible is not False ]
            self.annotations = []

            # draw the scene actors and annotations
            sorted_actors = [ a for a in self.annotations if not a.ontop ] + \
                            [ a for a in self.actors if not a.ontop ] + \
                            [ a for a in self.actors if a.ontop ] + \
                            [ a for a in self.annotations if a.ontop ]
            if self.canvas.settings.alphablend:
                print('ALPHABLEND')
                opaque = [ a for a in sorted_actors if a.opak ]
                transp = [ a for a in sorted_actors if not a.opak ]
                self.renderObjects(opaque)
                GL.glEnable (GL.GL_BLEND)
                GL.glDepthMask (GL.GL_FALSE)
                ## if pf.cfg['draw/disable_depth_test']:
                ##     GL.glDisable(GL.GL_DEPTH_TEST)
                GL.glEnable(GL.GL_DEPTH_TEST)
                GL.glBlendFunc (GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
                self.renderObjects(transp)
                GL.glEnable(GL.GL_DEPTH_TEST)
                GL.glDepthMask (GL.GL_TRUE)
                GL.glDisable (GL.GL_BLEND)
            else:
                print("NO ALPHABLEND")
                self.renderObjects(sorted_actors)


        finally:
            self.shader.unbind()


# End
