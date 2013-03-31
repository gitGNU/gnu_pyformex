# $Id$
"""opengl/renderer.py

Python OpenGL framework for pyFormex

This OpenGL framework is intended to replace (in due time)
the current OpenGL framework in pyFormex.

(C) 2013 Benedict Verhegghe and the pyFormex project.

"""

import os
import pyformex as pf
import numpy as np
from OpenGL import GL
from OpenGL.GL import shaders
from OpenGL.arrays import vbo


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


## _dirname = os.path.dirname(__file__)
## _vertexshader_filename = os.path.join(_dirname,"vertex_shader_simple.c")
## _fragmentshader_filename = os.path.join(_dirname,"fragment_shader_simple.c")



triangle1 = np.array([
    [ 0.75,  0.75, 0.0, 1.0],
    [ 0.75, -0.75, 0.0, 1.0],
    [-0.75, -0.75, 0.0, 1.0],
    ],'f')

triangle3 = np.array( [
    [  0, 1, 0 ],
    [ -1,-1, 0 ],
    [  1,-1, 0 ],
    [  2,-1, 0 ],
    [  4,-1, 0 ],
    [  4, 1, 0 ],
    [  2,-1, 0 ],
    [  4, 1, 0 ],
    [  2, 1, 0 ],
],'f')


class Renderer(object):

    def __init__(self,canvas=None):
        self.canvas = canvas
        self.canvas.makeCurrent()
        vertex_shader = shaders.compileShader(VertexShader,GL.GL_VERTEX_SHADER)
        fragment_shader = shaders.compileShader(FragmentShader,GL.GL_FRAGMENT_SHADER)
        self.shader = shaders.compileProgram(vertex_shader,fragment_shader)
        self.vbo = vbo.VBO(triangle1)


    def render(self):
        """Render the geometry for the scene."""
        shaders.glUseProgram(self.shader)
        try:
            self.vbo.bind()
            try:
                GL.glEnableClientState(GL.GL_VERTEX_ARRAY)
                GL.glVertexPointerf(self.vbo)
                GL.glDrawArrays(GL.GL_TRIANGLES,0,3)
            finally:
                self.vbo.unbind()
                GL.glDisableClientState(GL.GL_VERTEX_ARRAY)
        finally:
            shaders.glUseProgram(0)


# End
