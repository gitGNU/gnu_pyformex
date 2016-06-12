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

import numpy as np


class FontTexture(Texture):
    """A Texture class for text rendering.

    The FontTexture class is a texture containing the most important
    characters of a font. This texture can then be used to draw text
    on geometry. In the current implementation only the characters with
    ASCII ordinal in the range 32..127 are put in the texture.

    Parameters:

    - `filename`: path string. The font to be used. It should be the
      full file path of an existing monospace font on the system.
    - `size`: float: intended font heigth. The actual height might
      differ a bit.

    """
    def __init__(self,filename,size):
        """Initialize a FontTexture"""

        pf.debug("Creating FontTexture(%s) in size %s" % (filename,size),pf.DEBUG.FONT)
        # Load font  and check it is monospace
        face = ft.Face(str(filename))
        face.set_char_size(int(size*64))
        if not face.is_fixed_width:
            raise RuntimeError("Font is not monospace")

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
        image = np.zeros((height*6, width*16), dtype=np.ubyte)
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


    def texCoords(self,char):
        """Return the texture coordinates for a character or string.

        Parameters:

        - `char`: integer or ascii string. If an integer, it should be in the range
          32..127 (printable ASCII characters). If a string, all its characters
          should be ASCII printable characters (have an ordinal value in the
          range 32..127).

        If `char` is an integer, returns a tuple with the texture coordinates
        in the FontTexture corresponding with the specified character. This is a
        sequence of four (x,y) pairs corresponding respectively with the
        lower left, lower right, upper right, upper left corners of the character
        in the texture. Note that values for the lower corners are higher than those
        for the upper corners. This is because the FontTextures are (currently)
        stored from top to bottom, while opengl coordinates are from bottom to top.

        If `char` is a string of length `ntext`, returns a float array with shape
        (ntext,4,2) holding the texture coordinates needed to display
        the given text on a grid of quad4 elements.
        """
        if isInt(char):
            dx,dy = 1./16,1./6
            k = char-32
            x0,y0 = (k%16)*dx, (k//16)*dy
            return (x0,y0+dy), (x0+dx,y0+dy), (x0+dx,y0), (x0,y0)

        else:
            return np.array([ self.texCoords(ord(c)) for c in char ])


    default_font = None
    @classmethod
    def default(clas,size=18):
        """Set and return the default FontTexture.

        """
        if clas.default_font is None:
            default_font_file = utils.defaultMonoFont()
            default_font_size = size
            clas.default_font = FontTexture(default_font_file,default_font_size)
        return clas.default_font


#
# TODO: Docstring of Text should be extended (include grid parameter),
# or TextArray should be merged into Text.
#
class Text(Actor):
    """A text drawn at a 2D or 3D position.

    Parameters:

    - `text`: string: the text to display. If not a string, the string
      representation of the object will be drawn. Newlines in the string
      are supported. After a newline, the remainder of the string is continued
      from a lower vertical position and the initial horizontal position.
      The vertical line offset is determined from the font.
    - `pos`: a 2D or 3D position. If 2D, the values are measured in pixels.
      If 3D, it is a point in global 3D space. The text is drawn in 2D,
      inserted at the specified position.
    - `gravity`: a string that determines the adjusting of the text with
      respect to the insert position. It can be a combination of one of the
      characters 'N or 'S' to specify the vertical positon, and 'W' or 'E'
      for the horizontal. The default(empty) string will center the text.
    - `size`: float: size (height) of the font. This is the displayed height.
      The used font can have a different height and is scaled accordingly.
    - `width`: float: width of the font. This is the displayed width o a single
      character (currently only monospace fonts are supported).
      The default is set from the `size` and the aspect ratio of the font.
      Setting this to a different value allows the creation of condensed and
      expanded font types. Condensed fonts are often used to save space.
    - `font`: :class:`FontTexture` or string. The font to be used.
      If a string, it is the filename of an existing monospace font on
      the system.
    - `lineskip`: float: distance in pixels between subsequent baselines
      in case of multi-line text. Multi-line text results when the input
      `text` contains newlines.
    - `grid`: raster geometry for the text. This is the geometry where the
      generate text will be rendered on as a texture. The default is a
      grid of rectangles of size (`width`,`size`) which are juxtaposed
      horizontally. Each rectangle will be rendered with a single character
      on it.

    """

    def __init__(self,text,pos,gravity=None,size=18,width=None,font=None,lineskip=1.0,grid=None,texmode=4,**kargs):
        """Initialize the Text actor."""

        # split the string on newlines
        text = str(text).split('\n')

        # set pos and offset3d depending on pos type (2D vs 3D rendering)
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
                if offset3d.shape[0] != len(text[0]):
                    raise ValueError("Length of text(%s) and pos(%s) should match!" % (len(text),len(pos)))
                # Flag vertex offset to shader
                rendertype = -1

        # set the font characteristics
        if font is None:
            font = FontTexture.default(size)
        if isinstance(font,(str,unicode)):
            font = FontTexture(font,size)
        if width is None:
            #print("Font %s / %s" % (font.height,font.width))
            aspect = float(font.width) / font.height
            width = size * aspect
        self.width = width

        # set the alignment
        if gravity is None:
            gravity = 'E'
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

        # record the lengths of the lines, join all characters
        # together, create texture coordinates for all characters
        # create a geometry grid for the longest line
        lt = [ len(t) for t in text ]
        text = ''.join(text)
        texcoords = font.texCoords(text)
        if grid is None:
            grid = Formex('4:0123').replic(max(lt))
        grid = grid.scale([width,size,0.])

        # create the actor for the first line
        l = lt[0]
        g = grid.select(range(l)).align(alignment,pos)
        Actor.__init__(self,g,rendertype=rendertype,texture=font,texmode=texmode,texcoords=texcoords[:l],opak=False,ontop=True,offset3d=offset3d,**kargs)

        for k in lt[1:]:
            # lower the canvas y-value
            pos[1] -= font.height * lineskip
            g = grid.select(range(k)).align(alignment,pos)
            C = Actor(g,rendertype=rendertype,texture=font,texmode=texmode,texcoords=texcoords[l:l+k],opak=False,ontop=True,offset3d=offset3d,**kargs)
            self.children.append(C)
            # do next line
            l += k


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


class Mark(Actor):
    """A 2D drawing inserted at a 3D position of the scene.

    The minimum attributes and methods are:

    - `pos` : 3D point where the mark will be drawn
    """

    def __init__(self,pos,tex,size,opak=False,ontop=True,**kargs):
        self.pos = pos
        F = Formex([[[0,0],[1,0],[1,1],[0,1]]]).scale(size).align('000')
        Actor.__init__(self,F,rendertype=1,texture=tex,texmode=4,offset3d=pos,opak=opak,ontop=ontop,lighting=False,**kargs)


__all__ = [ 'FontTexture', 'Text', 'TextArray', 'Mark' ]

# End
