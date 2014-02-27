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
"""Texture rendering.

This module defines tools for texture rendering in pyFormex.
"""
from __future__ import print_function


from OpenGL import GL
import numpy as np

### Textures ###############################################

def glTexture(texture,mode='*'):
    """Render-time texture environment setup"""
    texmode = {'*': GL.GL_MODULATE, '1': GL.GL_DECAL}[mode]
    # Configure the texture rendering parameters
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
    GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
    GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, texmode)
    # Re-select the texture
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture.tex)


class Texture(object):
    """An OpenGL 2D Texture.

    Parameters:

    - `image`: raw image data (unsigned byte RGBA data)

    """

    def __init__(self,image):
        self.tex = None
        image = np.asarray(image)
        # print "Texture: type %s, size %s" % (image.dtype, image.shape)
        image = np.require(image, dtype='ubyte', requirements='C')
        # print "Converted to: type %s, size %s" % (image.dtype, image.shape)
        ny, nx = image.shape[:2]

        # Generate a texture id
        tex = GL.glGenTextures(1)
        # Make our new texture the current 2D texture
        GL.glEnable(GL.GL_TEXTURE_2D)
        #GL.glTexEnvf(GL.GL_TEXTURE_ENV,GL.GL_TEXTURE_ENV_MODE,GL.GL_MODULATE)
        GL.glBindTexture(GL.GL_TEXTURE_2D, tex)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        # Copy the texture data into the current texture
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, 4, nx, ny, 0,
                        GL.GL_RGBA, GL.GL_UNSIGNED_BYTE, image)
        self.tex = tex


    def __del__(self):
        if self.tex:
            GL.glDeleteTextures(self.tex)


### End
