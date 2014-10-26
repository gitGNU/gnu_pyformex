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
from pyformex import freetype as ft
from pyformex.coords import Coords
from pyformex.formex import Formex
from pyformex.opengl.drawable import Base, Actor
from pyformex.opengl.texture import Texture
from pyformex.opengl.sanitize import *

from OpenGL import GL

import numpy


class FontTexture(Texture):
    """A Texture class for text rendering.

    """
    def __init__(self,filename,size):
        """Initialize a FontTexture"""

        print("Creating FontTexture(%s) in size %s" % (filename,size))
        # Load font  and check it is monotype
        face = ft.Face(str(filename))
        face.set_char_size(int(size*64))
        if not face.is_fixed_width:
            raise RuntimeError("Font is not monotype")

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


    def texCoords(self,ord):
        """Return the texture coordinates for ascii character position ord.

        ord is an integer in the range 32..127
        Returns the font texture coordinates of the square containing the
        character with the ordinal number ord.
        """
        dx,dy = 1./16,1./6
        k = ord-32
        x0,y0 = (k%16)*dx, (k//16)*dy
        return (x0,y0+dy), (x0+dx,y0+dy), (x0+dx,y0), (x0,y0)


    default_font = None
    @classmethod
    def default(clas):
        if clas.default_font is None:
            default_font_file = utils.defaultMonoFont()
            default_font_size = 36
            clas.default_font = FontTexture(default_font_file,default_font_size)
        return clas.default_font


class Text(Actor):
    """A text drawn at a 2D or 3D position.

    Parameters:

    - `text`: string: the text to display. If not a string, the string
      representation of the object will be drawn.
    - `pos`: a 2D or 3D position. If 2D, the values are measured in pixels.
      If 3D, it is a point in global 3D space. The text is drawn in 2D,
      inserted at the specified position.
    - `gravity`: a string that determines the adjusting of the text with
      respect to the insert position. It can be a combination of one of the
      characters 'N or 'S' to specify the vertical positon, and 'W' or 'E'
      for the horizontal. The default(empty) string will center the text.
    """

    def __init__(self,text,pos,gravity=None,size=18,width=None,font=None,grid=None,texmode=4,**kargs):
        self.text = str(text)
        pos = checkArray(pos)
        if pos.shape[-1] == 2:
            rendertype = 2
            pos = [pos[0],pos[1],0.]
            offset3d = None
        else:
            rendertype = 1
            offset3d = Coords(pos)
            pos = [0.,0.,0.]
            if offset3d.ndim > 1:
                if offset3d.shape[0] != len(text):
                    raise ValueError("Length of text(%s) and pos(%s) should match!" % (len(text),len(pos)))
                # Flag vertex offset to shader
                rendertype = -1

        if font is None:
            font = FontTexture.default()
        if isinstance(font,(str,unicode)):
            font = FontTexture(font,size)
        if width is None:
            aspect = float(font.width) / font.height
            width = size * aspect
        self.width = width
        if gravity is None:
            gravity = 'E'

        texcoords = array([ font.texCoords(ord(c)) for c in text ])

        if grid is None:
            grid = Formex('4:0123').replic(len(text))

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

        grid = grid.scale([width,size,0.]).align(alignment,pos)

        ## print("TEXT")
        ## print("  width,size = %s,%s" % (width,size))
        ## print("  grid = %s" % grid)
        ## print("  rendertype = %s" % rendertype)
        ## print("  offset3d = %s" % offset3d)
        ## print("  texcoords = %s" % texcoords)
        ## print("  shape",grid.shape,offset3d.shape,texcoords.shape)
        Actor.__init__(self,grid,rendertype=rendertype,texture=font,texmode=texmode,texcoords=texcoords,opak=False,ontop=True,offset3d=offset3d,**kargs)


class TextArray(Text):
    """A array of texts drawn at a 2D or 3D positions.

    Parameters:

    - `text`: a list of N strings: the texts to display. If an item is
      not a string, the string representation of the object will be drawn.
    - `pos`: either an [N,2] or [N,3] shaped array of 2D or 3D positions.
      If 2D, the values are measured in pixels. If 3D, it is a point in
      global 3D space.

    The text is drawn in 2D, inserted at the specified position, with
    alignment specified by the gravity.
    """

    def __init__(self,val,pos,leader='',**kargs):
        # Make sure we have strings
        val = [ str(i) for i in val ]
        pos = checkArray(pos,shape=(len(val),-1))
        if len(val) != pos.shape[0]:
            raise ValueError("val and pos should have same length")

        # concatenate all strings
        val = [ leader+str(v) for v in val ]
        cs = cumsum([0,] + [ len(v) for v in val ])
        val = ''.join(val)
        nc = cs[1:] - cs[:-1]

        pos = [ multiplex(p,n,0) for p,n in zip(pos,nc) ]
        pos = concatenate(pos,axis=0)
        pos = multiplex(pos,4,1)

        # Create the grids for the strings
        F = Formex('4:0123')
        grid = Formex.concatenate([ F.replic(n) for n in nc ])

        # Create a text with the concatenation
        Text.__init__(self,val,pos=pos,grid=grid,**kargs)


## class MarkList(Text):
##     """A list of numbers drawn at 3D positions.

##     pos is an (N,3) array of positions.
##     val is an (N,) array of marks to be plot at those positions.

##     While intended to plot integer numbers, val can be any object
##     that allows index operations for the required length N and allows
##     its items to be formatted as a string.

##     """

##     def __init__(self,pos,val,leader='',**kargs):
##         """Create a MarkList."""
##         if len(val) != len(pos):
##             raise ValueError("pos and val should have same length")

##         # Make sure we have strings
##         val = [ leader+str(v) for v in val ]
##         cs = cumsum([0,] + [ len(v) for v in val ])
##         val = ''.join(val)
##         # Create a text with the concatenation
##         Text.__init__(self,val,[0.,0.,0.],invisible=True,**kargs)
##         #
##         # TODO: we should transform this to using different offsets
##         # for the partial strings, instead of using children
##         #
##         # Create a text for each mark
##         for p,i,j in zip(pos,cs[:-1],cs[1:]):
##             t = Text(val[i:j],p,**kargs)
##             self.children.append(t)


class Mark(Actor):
    """A 2D drawing inserted at a 3D position of the scene.

    The minimum attributes and methods are:

    - `pos` : 3D point where the mark will be drawn
    """

    def __init__(self,pos,tex,size,opak=False,ontop=True,**kargs):
        self.pos = pos
        F = Formex([[[0,0],[1,0],[1,1],[0,1]]]).scale(size).align('000')
        Actor.__init__(self,F,rendertype=1,texture=tex,texmode=4,offset3d=pos,opak=opak,ontop=ontop,lighting=False,**kargs)


# End
