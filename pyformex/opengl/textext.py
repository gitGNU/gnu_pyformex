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
from pyformex.opengl.drawable import Base, GeomActor
from pyformex.opengl.texture import Texture
from pyformex.opengl.sanitize import *

from OpenGL import GL
import freetype as ft

def is_mono_font(fontfile,size=24):
    "Test whether a fontfile is a fixed width font or not"""
    face = ft.Face(fontfile)
    #face.set_char_size(size*64)
    return face.is_fixed_width


def list_mono_fonts():
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
        Texture.activate(self,filtr=1)


default_font_file = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSansMono.ttf'
default_font_size = 36
default_font = FontTexture(default_font_file,default_font_size)


## class TextMark(Mark):
##     """A text drawn at a 3D position."""

##     def __init__(self,pos,text,color=None,fonttex='',size=18,gravity=None,**kargs):
##         Mark.__init__(self,pos,**kargs)
##         self.text = text
##         self.color = saneColor(color)
##         if not fonttex:
##             fonttex = default_font
##         self.tex = fonttex
##         self.tex.bind()
##         print(self.tex.texid)


##     def drawGL(self,**kargs):

##         if self.color is not None:
##             GL.glColor3fv(self.color)
##         GL.glRasterPos3fv(self.pos)
##         self.tex.render(self.text,0,0)


class Text(GeomActor):
    """A text drawn at a 2D position."""

    def __init__(self,text,x,y,fonttex=None,size=18,gravity=None,**kargs):
        self.text = text
        if not fonttex:
            fonttex = default_font
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
        print(texcoords)
        F = Formex('4:0123').replic(n).scale(size).trl([x,y,0.])
        GeomActor.__init__(self,F,rendertype=2,texture=fonttex,texmode=2,texcoords=texcoords,**kargs)



if __name__ == "draw":

    image = os.path.join(pf.cfg['pyformexdir'], 'data', 'butterfly.png')
    image = default_font

    resetAll()
    clear()
    view('front')
    smooth()
    transparent()
    fonts = list_mono_fonts()
    for f in fonts:
        print(f)

    F = Formex('4:0123').toMesh()
    G = F.scale(600).trl([200,200,0])
    #A = draw(F.scale(400),color=yellow,texture=image,texcoords=array([[0,1],[1,1],[1,0],[0,0]]),texmode=2)
    #B = draw(F,color=yellow,texture=image,texcoords=array([[0,1],[1,1],[1,0],[0,0]]),rendertype=3,opak=False,lighting=True,alpha=0.5)
    #C = draw(F.scale(400),color=yellow,texture=image,texcoords=array([[0,1],[1,1],[1,0],[0,0]]),rendertype=2,texmode=2)


    T = Text("Hegemony!",100,100,size=50,color=red)
    decorate(T)
    decorate(Text("Hegemony!",20,20,size=20,color=None))
# End
