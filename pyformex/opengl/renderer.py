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
from __future__ import absolute_import, division, print_function

import pyformex as pf
from pyformex.attributes import Attributes
from pyformex.opengl.matrix import Matrix4
from pyformex.opengl.camera import orthogonal_matrix
from pyformex.opengl.shader import Shader

import numpy as np
from OpenGL import GL


class Renderer(object):

    def __init__(self,canvas,shader=None):
        self.canvas = canvas
        self.camera = canvas.camera
        self.canvas.makeCurrent()

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
        ambient = np.clip(ambient, 0., 1.) # clip, OpenGL does anyways
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
            'alphablend': self.canvas.settings.alphablend,
            'alpha': self.canvas.settings.transparency,
            'bkalpha': self.canvas.settings.transparency,
            })
        #print("LIGHT PROFILE to shader: %s" % settings)
        self.shader.loadUniforms(settings)


    def setDefaults(self):
        """Set the GL context and the shader uniforms to default values."""
        GL.glLineWidth(self.canvas.settings.linewidth)
        # Enable setting pointsize in the shader
        # Maybe we should do pointsize with gl context?
        GL.glEnable(GL.GL_VERTEX_PROGRAM_POINT_SIZE)
        # NEXT, the shader uniforms
        # When all attribute names are correct, this could be done with a
        # single statement like
        #   self.shader.loadUniforms(self.canvas.settings)
        #
        self.shader.uniformInt('highlight', 0)
        self.shader.uniformFloat('lighting', self.canvas.settings.lighting)
        self.shader.uniformInt('useObjectColor', 1)
        self.shader.uniformVec3('objectColor', self.canvas.settings.fgcolor)
        self.shader.uniformVec3('objectBkColor', self.canvas.settings.fgcolor)
        self.shader.uniformFloat('pointsize', self.canvas.settings.pointsize)
        self.loadLightProfile()


    def renderObjects(self, objects):
        """Render a list of objects"""
        for obj in objects:
            GL.glDepthFunc(GL.GL_LESS)
            self.setDefaults()
            if obj.trl or obj.rot or obj.trl0:
                self.loadMatrices(rot=self.rot,trl=self.trl,trl0=self.trl0)
            obj.render(self)
            if obj.trl or obj.rot or obj.trl0:
                self.loadMatrices()


    def pickObjects(self, objects):
        """Draw a list of objects in picking mode"""
        for i, obj in enumerate(objects):
            GL.glPushName(i)
            obj.render(self)
            GL.glPopName()


    def loadMatrices(self,rot=None,trl=None,trl0=None):
        """Load the rendering matrices.

        rot, trl, trl0 are additional rotation, translation and
        pre-translation for the object.
        """
        # Get the current modelview*projection matrix
        modelview = self.camera.modelview
        if trl0:
            modelview.translate(trl0)
        if rot:
            modelview.rotate(rot)
        if trl:
            modelview.translate(trl)
        projection = self.camera.projection
        transinv = self.camera.modelview.transinv().rot

        # Propagate the matrices to the uniforms of the shader
        self.shader.uniformMat4('modelview', modelview.gl())
        self.shader.uniformMat4('projection', projection.gl())
        self.shader.uniformMat3('normalstransform', transinv.flatten().astype(np.float32))


    def render3D(self,actors,pick=None):
        """Render the 3D actors in the scene.

        """
        if not actors:
            return

        ## # Split off rendertype 1
        ## actors1 = [ a for a in actors if a.rendertype == -1 ]
        ## actors = [ a for a in actors if a.rendertype != -1 ]

        # Get the current modelview*projection matrix
        modelview = self.camera.modelview
        projection = self.camera.projection
        transinv = self.camera.modelview.transinv().rot

        # Propagate the matrices to the uniforms of the shader
        self.shader.uniformMat4('modelview', modelview.gl())
        self.shader.uniformMat4('projection', projection.gl())
        self.shader.uniformMat3('normalstransform', transinv.flatten().astype(np.float32))

        # sort actors in back and front, and select visible
        actors = back(actors) + front(actors)
        actors =  [ o for o in actors if o.visible is not False ]

        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDepthMask (GL.GL_TRUE)

        if pick:
            # PICK MODE
            from pyformex.opengl import camera
            pickmat = camera.pick_matrix(*pick)
            self.shader.uniformMat4('pickmat', pickmat.gl())

            self.pickObjects(actors)

        elif not self.canvas.settings.alphablend:
            # NO ALPHABLEND
            self.renderObjects(actors)

        else:
            # ALPHABLEND
            # 2D actors are by default transparent!
            opaque = [ a for a in actors if a.opak ]
            transp = [ a for a in actors if not a.opak ]

            # First render the opaque objects
            self.renderObjects(opaque)

            # Then the transparent ones
            # Disable writing to the depth buffer
            # as everything behind the transparent object
            # also needs to be drawn
            GL.glDepthMask (GL.GL_FALSE)

            if pf.cfg['render/transp_nocull']:
                GL.glDisable(GL.GL_CULL_FACE)

            GL.glEnable(GL.GL_BLEND)
            GL.glBlendEquation(GL.GL_FUNC_ADD)
            if pf.cfg['render/alphablend'] == 'mult':
                GL.glBlendFunc(GL.GL_ZERO, GL.GL_SRC_COLOR)
            elif pf.cfg['render/alphablend'] == 'add':
                GL.glBlendFunc(GL.GL_ONE, GL.GL_ONE)
            elif pf.cfg['render/alphablend'] == 'trad1':
                GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE)
            else:
                GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
            self.renderObjects(transp)
            GL.glDisable (GL.GL_BLEND)

        ## if actors1:
        ##     modelview = Matrix4()
        ##     modelview[:3,:3] = self.camera.modelview.rot
        ##     projection = perspective_matrix(-1, 0.5, -1, 0.5, 0.1, 10.)

        ##     #self.shader.uniformMat4('modelview', modelview.gl())
        ##     self.shader.uniformMat4('projection', projection.gl())
        ##     self.renderObjects(actors1)


        GL.glDepthMask (GL.GL_TRUE)


    def render2D(self,actors):
        """Render 2D decorations.

        """
        if not actors:
            return

        #print("Render %s decorations" % len(actors))

        # Set modelview/projection
        modelview = Matrix4()
        self.shader.uniformMat4('modelview', modelview.gl())

        left = 0. # -0.5
        right = float(self.canvas.width()) # -0.5
        bottom = 0. # -0.5
        top = float(self.canvas.height()) # -0.5
        near = -1.
        far = 1.
        projection = orthogonal_matrix(left, right, bottom, top, near, far)
        self.shader.uniformMat4('projection', projection.gl())

        GL.glDisable(GL.GL_DEPTH_TEST)
        GL.glDisable(GL.GL_CULL_FACE)
        GL.glDepthMask (GL.GL_FALSE)

        # ALPHABLEND
        #
        # We need blending for text rendering!
        #
        # 2D actors are by default opak!
        opaque = [ a for a in actors if a.opak is None or a.opak ]
        transp = [ a for a in actors if a.opak is False]

        # First render the opaque objects
        self.renderObjects(opaque)

        # Then the transparent ones
        # Disable writing to the depth buffer
        # as everything behind the transparent object
        # also needs to be drawn

        GL.glEnable(GL.GL_BLEND)
        GL.glBlendEquation(GL.GL_FUNC_ADD)
        if pf.cfg['render/textblend'] == 'mult':
            GL.glBlendFunc(GL.GL_ZERO, GL.GL_SRC_COLOR)
        elif pf.cfg['render/textblend'] == 'add':
            GL.glBlendFunc(GL.GL_ONE, GL.GL_ONE)
        elif pf.cfg['render/textblend'] == 'trad1':
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE)
        elif pf.cfg['render/textblend'] == 'zero':
            GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ZERO)
        else:
             GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        self.renderObjects(transp)
        GL.glDisable (GL.GL_BLEND)
        GL.glDepthMask (GL.GL_TRUE)


    def renderBG(self,actors):
        """Render 2D background actors.

        """
        if not actors:
            return

        #print("Render %s backgrounds" % len(actors))

        # Set modelview/projection
        modelview = projection = Matrix4()

        self.shader.uniformMat4('modelview', modelview.gl())
        self.shader.uniformMat4('projection', projection.gl())

        self.canvas.zoom_2D()  # should be combined with above

        # in clip space
        GL.glDisable(GL.GL_DEPTH_TEST)
        self.renderObjects(actors)


    def render(self,scene,pick=None):
        """Render the geometry for the scene."""
        self.shader.bind(picking=bool(pick))
        try:

            # The back backgrounds
            self.renderBG(back(scene.backgrounds))

            # The 2D back decorations
            self.render2D(back(scene.decorations)+back(scene.annotations))

            # The 3D actors
            self.render3D(scene.actors,pick)

            # The 2D front decorations
            self.render2D(front(scene.annotations)+front(scene.decorations))

            # The front backgrounds
            self.renderBG(front(scene.backgrounds))

        finally:
            self.shader.unbind()


def front(actorlist):
    """Return the actors from the list that have ontop=True"""
    return [ a for a in actorlist if a.ontop ]


def back(actorlist):
    """Return the actors from the list that have ontop=False"""
    return [ a for a in actorlist if not a.ontop ]


# End
