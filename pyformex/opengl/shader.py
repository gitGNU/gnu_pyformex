# $Id$

"""OpenGL shader programs

Python OpenGL framework for pyFormex

This OpenGL framework is intended to replace (in due time)
the current OpenGL framework in pyFormex.

(C) 2013 Benedict Verhegghe and the pyFormex project.

"""

import os
from OpenGL import GL
from OpenGL.GL import shaders


VertexShader = """
#version 330
layout(location = 0) in vec4 position;
void main()
{
   gl_Position = position;
}
"""
FragmentShader = """
#version 330
out vec4 outputColor;
void main()
{
   outputColor = vec4(1.0f, 0.0f, 1.0f, 1.0f);
}
"""


_dirname = os.path.dirname(__file__)
_vertexshader_filename = os.path.join(_dirname,"vertex_shader.c")
_fragmentshader_filename = os.path.join(_dirname,"fragment_shader.c")


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

    def __init__(self):
        print("LOADING SHADER PROGRAMS")
        with open(_vertexshader_filename) as f:
            VertexShader = f.read()

        with open(_fragmentshader_filename) as f:
            FragmentShader = f.read()

        attributes = [
        'vertexPosition',
        'vertexNormal',
        'vertexColor',
        'vertexTexturePos',
        'vertexScalar',
        ]

        uniforms = [
        'perspective',
        'center',
        'objectTransform',
        'useObjectColor',
        'objectColor',
        'useScalars',
        'scalarsReplaceMode',
        'scalarsMin',
        'scalarsMax',
        'scalarsMinColor',
        'scalarsMaxColor',
        'scalarsMinThreshold',
        'scalarsMaxThreshold',
        'scalarsInterpolation',
        'pointSize',
        'objectOpacity',
        'normal',
        'usePicking',
        'useTexture',
        'useLabelMapTexture',
        'labelmapOpacity',
        'textureSampler',
        'textureSampler2',
        'volumeLowerThreshold',
        'volumeUpperThreshold',
        'volumeScalarMin',
        'volumeScalarMax',
        'volumeScalarMinColor',
        'volumeScalarMaxColor',
        'volumeWindowLow',
        'volumeWindowHigh',
        'volumeTexture'
        ]

        vertex_shader = GL.shaders.compileShader(VertexShader,GL.GL_VERTEX_SHADER)
        fragment_shader = GL.shaders.compileShader(FragmentShader,GL.GL_FRAGMENT_SHADER)
        self.shader = GL.shaders.compileProgram(vertex_shader,fragment_shader)

        self.attribute = self.locations(GL.glGetAttribLocation,attributes)
        self.uniform = self.locations(GL.glGetUniformLocation,uniforms)


    def locations(self,func,keys):
        """Create a dict with the locations of the specified keys"""
        return dict([(k,func(self.shader,k)) for k in keys ])


    def bind(self):
        GL.shaders.glUseProgram(self.shader)

    def unbind(self):
        GL.shaders.glUseProgram(0)


# End
