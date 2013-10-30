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
from attributes import Attributes
#import utils

from drawable import GeomActor

class Renderer(object):

    def __init__(self,canvas,shader=None):
        self.canvas = canvas
        self.camera = canvas.camera
        self.canvas.makeCurrent()
        self.mode = canvas.rendermode

        if shader is None:
            shader = Shader()
        self.shader = shader


    def loadLightProfile(self):
        lightprof = self.canvas.lightprof
        mat = self.canvas.material
        #print(lightprof)
        lights = [ light for light in lightprof.lights if light.enabled ]
        #for light in lights:
        #    print(light)
        nlights = len(lights)
        ambient = lightprof.ambient * np.ones(3) # global ambient
        for light in lights:
            ambient += light.ambient
        ambient = np.clip(ambient,0.,1.) # clip, OpenGL does anyways
        diffuse = np.array([ light.diffuse for light in lights ]).ravel()
        specular = np.array([ light.specular for light in lights ]).ravel()
        position = np.array([ light.position[:3] for light in lights ]).ravel()
        #print("diffcolor = %s" % diffuse)
        #print("lightdir = %s" % position)
        settings = Attributes({
            'nlights': nlights,
            'ambicolor': ambient,
            'diffcolor': diffuse,
            'speccolor': specular,
            'lightdir': position,
            'ambient': mat.ambient,
            'diffuse': mat.diffuse,
            'specular': mat.specular,
            'shininess': mat.shininess,
            'alpha':self.canvas.settings.transparency,
            })
        #print("LIGHT PROFILE to shader: %s" % settings)
        self.shader.loadUniforms(settings)


    def setDefaults(self):
        """Set the GL context and the shader uniforms to default values."""
        # FIRST, the context
        GL.glLineWidth(self.canvas.settings.linewidth)
        # Enable setting pointsize in the shader
        # Maybe we should do pointsize with gl context?
        GL.glEnable(GL.GL_VERTEX_PROGRAM_POINT_SIZE)
        # NEXT, the shader uniforms
        # When all attribute names are correct, this could be done with a
        # single statement like
        #   self.shader.loadUniforms(self.canvas.settings)
        #print("DEFAULTS",self.canvas.settings)
        self.shader.uniformInt('builtin',0)
        self.shader.uniformInt('highlight',0)
        self.shader.uniformFloat('lighting',self.canvas.settings.lighting)
        self.shader.uniformInt('useObjectColor',1)
        self.shader.uniformVec3('objectColor',self.canvas.settings.fgcolor)
        self.shader.uniformFloat('pointsize',self.canvas.settings.pointsize)
        self.loadLightProfile()


    def renderObjects(self,objects):
        """Render a list of objects"""
        for obj in objects:
            GL.glDepthFunc(GL.GL_LESS)
            self.setDefaults()
            obj.render(self)


    def pickObjects(self,objects):
        """Draw a list of objects in picking mode"""
        for i,obj in enumerate(objects):
            #print("PUSH %s" % i)
            GL.glPushName(i)
            obj.render(self)
            #print("POP %s" % i)
            GL.glPopName()


    def render(self,scene,pick=None):
        """Render the geometry for the scene."""
        self.shader.bind(picking=bool(pick))
        try:

            # Get the current modelview*projection matrix
            modelview = self.camera.modelview
            #print("MODELVIEW-R",modelview)
            projection = self.camera.projection
            #print("PROJECTION-R",projection)

            # Propagate the matrices to the uniforms of the shader
            self.shader.uniformMat4('modelview',modelview.gl())
            self.shader.uniformMat4('projection',projection.gl())
            if pick:
                import camera
                pickmat = camera.pick_matrix(*pick)
                self.shader.uniformMat4('pickmat',pickmat.gl())

            # draw the scene actors (sorted)
            actors = scene.back_actors() + scene.front_actors()
            actors =  [ o for o in actors if o.visible is not False ]
            if pick:
                # PICK MODE
                self.pickObjects(actors)

            elif not self.canvas.settings.alphablend:
                # NO ALPHABLEND
                self.renderObjects(actors)

            else:
                # ALPHABLEND
                opaque = [ a for a in actors if a.opak ]
                transp = [ a for a in actors if not a.opak ]
                self.renderObjects(opaque)
                GL.glEnable (GL.GL_BLEND)
                #GL.glDepthMask (GL.GL_FALSE)
                #if pf.cfg['draw/disable_depth_test']:
                #    GL.glDisable(GL.GL_DEPTH_TEST)
                GL.glEnable(GL.GL_DEPTH_TEST)
                GL.glBlendFunc (GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
                self.renderObjects(transp)
                GL.glEnable(GL.GL_DEPTH_TEST)
                GL.glDepthMask (GL.GL_TRUE)
                GL.glDisable (GL.GL_BLEND)

        finally:
            self.shader.unbind()


# End
