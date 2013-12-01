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

"""OpenGL shader programs

Python OpenGL framework for pyFormex

This OpenGL framework is intended to replace (in due time)
the current OpenGL framework in pyFormex.

(C) 2013 Benedict Verhegghe and the pyFormex project.

"""

import os
from OpenGL import GL
from OpenGL.GL import shaders


class Shader(object):
    """An OpenGL shader consisting of a vertex and a fragment shader pair.

    Class attributes:

    - `_vertexshader` : the vertex shader source.
      By default, a basic shader supporting vertex positions and vertex colors
      is defined

    - `_fragmentshaderSource` : the fragment shader source.
      By default, a basic shader supporting fragment colors is defined.

    - `attributes`: the shaders' vertex attributes.
    - `uniforms`: the shaders' uniforms.
    """

    # Default shaders
    _dirname = os.path.dirname(__file__)
    _vertexshader_filename = os.path.join(_dirname, "vertex_shader.c")
    _fragmentshader_filename = os.path.join(_dirname, "fragment_shader.c")

    # Default attributes and uniforms
    attributes = [
    'vertexPosition',
    'vertexNormal',
    'vertexColor',
    'vertexTexturePos',
    'vertexScalar',
    ]

    # int and bool uniforms
    uniforms_int = [
        'highlight',
        'useObjectColor',
        'lighting',
        'nlights',
        ]

    uniforms_float = [
        'pointsize',
        'ambient',
        'diffuse',
        'specular',
        'shininess',
        'alpha',
        ]

    uniforms_vec3 = [
        'objectColor',
        'ambicolor',
        'diffcolor',
        'speccolor',
        'lightdir',
    ]

    uniforms = uniforms_int + uniforms_float +  uniforms_vec3 + [
        'modelview',
        'projection',
        'pickmat',
        'builtin',
        'picking',
    ]

    def __init__(self,vshader=None,fshader=None,attributes=None,uniforms=None):
        #print("LOADING SHADER PROGRAMS")
        if vshader is None:
            vshader = Shader._vertexshader_filename
        with open(vshader) as f:
            VertexShader = f.read()

        if fshader is None:
            fshader = Shader._fragmentshader_filename
        with open(fshader) as f:
            FragmentShader = f.read()

        if attributes is None:
            attributes = Shader.attributes

        if uniforms is None:
            uniforms = Shader.uniforms

        vertex_shader = GL.shaders.compileShader(VertexShader, GL.GL_VERTEX_SHADER)
        fragment_shader = GL.shaders.compileShader(FragmentShader, GL.GL_FRAGMENT_SHADER)
        self.shader = GL.shaders.compileProgram(vertex_shader, fragment_shader)

        self.attribute = self.locations(GL.glGetAttribLocation, attributes)
        self.uniform = self.locations(GL.glGetUniformLocation, uniforms)
        self.builtin = 0  # Use builtin attributes?
        self.picking = 0  # Default render mode


    def locations(self, func, keys):
        """Create a dict with the locations of the specified keys"""
        return dict([(k, func(self.shader, k)) for k in keys ])


    def uniformInt(self, name, value):
        """Load a uniform integer or boolean into the shader"""
        loc = self.uniform[name]
        GL.glUniform1i(loc, value)


    def uniformFloat(self, name, value):
        """Load a uniform float into the shader"""
        loc = self.uniform[name]
        GL.glUniform1f(loc, value)


    ## def uniformVec3(self,name,value):
    ##     """Load a uniform vec3 into the shader"""
    ##     loc = self.uniform[name]
    ##     GL.glUniform3fv(loc,1,value)


    def uniformVec3(self, name, value):
        """Load a uniform vec3[n] into the shader

        The value should be a 1D array or list.
        """
        loc = self.uniform[name]
        n = len(value) // 3
        GL.glUniform3fv(loc, n, value)


    def uniformMat4(self, name, value):
        """Load a uniform mat4 into the shader"""
        loc = self.uniform[name]
        GL.glUniformMatrix4fv(loc, 1, False, value)


    def bind(self,picking=False):
        GL.shaders.glUseProgram(self.shader)
        self.uniformInt('builtin', self.builtin)
        self.uniformInt('picking', picking)


    def unbind(self):
        GL.shaders.glUseProgram(0)


    def loadUniforms(self, D):
        """Load the uniform attributes defined in D"""
        for attribs, func in [
            (self.uniforms_int, self.uniformInt),
            (self.uniforms_float, self.uniformFloat),
            (self.uniforms_vec3, self.uniformVec3),
            ]:
            for a in attribs:
                v = D[a]
                #print("LOAD %s = %s" % (a,v))
                if v is not None:
                    func(a, v)


    def __del__(self):
        self.unbind()

# End
