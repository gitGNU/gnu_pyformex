# $Id$
##
##  This file is part of pyFormex 0.9.1  (Tue Oct 15 21:05:25 CEST 2013)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2013 (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
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
"""Text rendering on the OpenGL canvas.

This module uses textures on quads to render text on an OpenGL canvas.
It is dependent on freetype and the Python bindings freetype-py.
"""
from __future__ import print_function

import pyformex as pf
from pyformex import utils
from pyformex.formex import Formex
from pyformex.opengl.drawable import Base, GeomActor
from pyformex.opengl.texture import Texture
from pyformex.opengl.sanitize import *


from OpenGL import GL
import freetype as ft
import numpy


def is_mono_font(fontfile,size=24):
    "Test whether a fontfile is a fixed width font or not"""
    face = ft.Face(fontfile)
    #face.set_char_size(size*64)
    return face.is_fixed_width


def listMonoFonts():
    fonts = [ f for f in utils.listFontFiles() if f.endswith('.ttf') ]
    fonts = [ f for f in fonts if is_mono_font(f) ]
    return sorted(fonts)


class FontTexture(Texture):
    """A Texture class for text rendering.

    """
    def __init__(self,filename,size):
        """Initialize a FontTexture"""

        # Load font  and check it is monotype
        face = ft.Face(filename)
        face.set_char_size( size*64 )
        if not face.is_fixed_width:
            raise RuntimeError,'Font is not monotype'

        # Determine largest glyph size
        width, height, ascender, descender = 0, 0, 0, 0
        for c in range(32,128):
            face.load_char( chr(c), ft.FT_LOAD_RENDER | ft.FT_LOAD_FORCE_AUTOHINT )
            bitmap    = face.glyph.bitmap
            width     = max( width, bitmap.width )
            ascender  = max( ascender, face.glyph.bitmap_top )
            descender = max( descender, bitmap.rows-face.glyph.bitmap_top )
        height = ascender+descender

        # Generate texture data
        self.width, self.height = width,height
        image = numpy.zeros((height*6, width*16), dtype=numpy.ubyte)
        for j in range(6):
            for i in range(16):
                face.load_char(chr(32+j*16+i), ft.FT_LOAD_RENDER | ft.FT_LOAD_FORCE_AUTOHINT )
                bitmap = face.glyph.bitmap
                x = i*width  + face.glyph.bitmap_left
                y = j*height + ascender - face.glyph.bitmap_top
                image[y:y+bitmap.rows,x:x+bitmap.width].flat = bitmap.buffer

        print(image.shape,image.dtype)
        Texture.__init__(self,image,format=GL.GL_ALPHA,texformat=GL.GL_ALPHA)


    def activate(self,mode=None):
        """Bind the texture and make it ready for use.

        Returns the texture id.
        """
        GL.glEnable(GL.GL_BLEND)
        Texture.activate(self,filtr=1)


default_font_file = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSansMono.ttf'
default_font_size = 36
default_font = FontTexture(default_font_file,default_font_size)


class Text(GeomActor):
    """A text drawn at a 2D position."""

    def __init__(self,text,x,y,size=18,width=None,fonttex=None,gravity=None,**kargs):
        self.text = text
        self.x,self.y = x,y
        self.size = size
        if not fonttex:
            fonttex = default_font
        if not width:
            aspect = float(fonttex.width) / fonttex.height
            width = size * aspect
        self.width = width
        if gravity is None:
            gravity = 'E'
        self.gravity = gravity

        n = len(text)
        dx,dy = 1./16,1./6
        texcoords = []
        for c in text:
            k = ord(c)-32
            i,j = k%16, k//16
            x0,y0 = i*dx,j*dy
            texcoords.append([[x0,y0+dy],[x0+dx,y0+dy],[x0+dx,y0],[x0,y0]])
        texcoords = array(texcoords)
        F = Formex('4:0123').replic(n).scale([width,size,0.])

        alignment = ['0','0','0']
        if 'W' in gravity:
            alignment[0] = '+'
        elif 'E' in gravity:
            alignment[0] = '-'
        if 'S' in gravity:
            alignment[1] = '+'
        elif 'N' in gravity:
            alignment[1] = '-'
        alignment = ''.join(alignment)
        print("Gravity %s = aligment %s" % (gravity,alignment))
        F = F.align(alignment,[x,y,0.])
        GeomActor.__init__(self,F,rendertype=2,texture=default_font,texmode=0,texcoords=texcoords,opak=False,ontop=True,**kargs)


# End
