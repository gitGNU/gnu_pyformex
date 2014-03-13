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
from pyformex.opengl.drawable import Base, Actor
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

        #print(image.shape,image.dtype)
        Texture.__init__(self,image,format=GL.GL_ALPHA,texformat=GL.GL_ALPHA)


    def activate(self,mode=None):
        """Bind the texture and make it ready for use.

        Returns the texture id.
        """
        GL.glEnable(GL.GL_BLEND)
        Texture.activate(self,filtr=1)


    default_font = None
    @classmethod
    def default(clas):
        if clas.default_font is None:
            default_font_file = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSansMono.ttf'
            default_font_size = 36
            clas.default_font = FontTexture(default_font_file,default_font_size)
        return clas.default_font


class Text(Actor):
    """A text drawn at a 2D or 3D position.

    Parameters:

    - `text`: string: the text to display. If not a string, the string
      representation of the object will be drawn.
    - `pos`: a 2D or 3D position. If 2D, the values are measured in pixels.
      If 3D, it is a point in global 3D space.

    The text is drawn in 2D, inserted at the specified position.
    """

    def __init__(self,text,pos,size=18,width=None,fonttex=None,gravity=None,**kargs):
        self.text = str(text)
        if len(pos) == 2:
            rendertype = 2
            pos = [pos[0],pos[1],0.]
            offset3d = None
        else:
            rendertype = 1
            offset3d = pos
            pos = [.0,.0,0.]
        self.size = size
        if not fonttex:
            fonttex = FontTexture.default()
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
        #print("Gravity %s = aligment %s on point %s" % (gravity,alignment,pos))
        F = F.align(alignment,pos)
        #print("Text bbox: %s" % str(F.bbox()))
        Actor.__init__(self,F,rendertype=rendertype,texture=fonttex,texmode=0,texcoords=texcoords,opak=False,ontop=True,offset3d=offset3d,**kargs)


class MarkList(Text):
    """A list of numbers drawn at 3D positions.

    pos is an (N,3) array of positions.
    val is an (N,) array of marks to be plot at those positions.

    While intended to plot integer numbers, val can be any object
    that allows index operations for the required length N and allows
    its items to be formatted as a string.

    """

    def __init__(self,pos,val,leader='',**kargs):
        """Create a MarkList."""
        if len(val) != len(pos):
            raise ValueError("pos and val should have same length")

        # Make sure we have strings
        val = [ leader+str(v) for v in val ]
        cs = cumsum([0,] + [ len(v) for v in val ])
        val = ''.join(val)
        # Create a text with the concatenation
        Text.__init__(self,val,[0.,0.,0.],invisible=True,**kargs)
        #
        # TODO: we should transform this to using different offsets
        # for the partial strings, instead of using children
        #
        # Create a text for each mark
        for p,i,j in zip(pos,cs[:-1],cs[1:]):
            t = Text(val[i:j],p,**kargs)
            self.children.append(t)


class Mark(Actor):
    """A 2D drawing inserted at a 3D position of the scene.

    The minimum attributes and methods are:

    - `pos` : 3D point where the mark will be drawn
    """

    def __init__(self,pos,tex,size,**kargs):
        self.pos = pos
        F = Formex([[[0,0],[1,0],[1,1],[0,1]]]).scale(size).align('000')
        Actor.__init__(self,F,rendertype=1,texture=tex,texmode=0,offset3d=pos,opak=False,ontop=True,**kargs)


# End
