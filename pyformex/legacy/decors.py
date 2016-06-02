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
"""2D decorations for the OpenGL canvas.

2D decorations are objects that are drawn in 2D on the flat canvas
instead of through the 3D OpenGL engine.
"""
from __future__ import print_function
from pyformex import zip

from OpenGL import GL
from pyformex.gui import QtOpenGL
from pyformex.opengl import colors

from pyformex.legacy.drawable import *
from pyformex.legacy.text import *
from pyformex.legacy.marks import TextMark


import sys
if (sys.hexversion & 0xFFFF0000) < 0x03000000:
    # GLUT currently fails with Python3
    # We should remove GLUT anyways
    from pyformex.legacy import gluttext


### Some drawing functions ###############################################


def drawDot(x, y):
    """Draw a dot at canvas coordinates (x,y)."""
    GL.glBegin(GL.GL_POINTS)
    GL.glVertex2f(x, y)
    GL.glEnd()


def drawLine(x1, y1, x2, y2):
    """Draw a straight line from (x1,y1) to (x2,y2) in canvas coordinates."""
    GL.glBegin(GL.GL_LINES)
    GL.glVertex2f(x1, y1)
    GL.glVertex2f(x2, y2)
    GL.glEnd()


def drawGrid(x1, y1, x2, y2, nx, ny):
    """Draw a rectangular grid of lines

    The rectangle has (x1,y1) and and (x2,y2) as opposite corners.
    There are (nx,ny) subdivisions along the (x,y)-axis. So the grid
    has (nx+1) * (ny+1) lines. nx=ny=1 draws a rectangle.
    nx=0 draws 1 vertical line (at x1). nx=-1 draws no vertical lines.
    ny=0 draws 1 horizontal line (at y1). ny=-1 draws no horizontal lines.
    """
    GL.glBegin(GL.GL_LINES)
    ix = range(nx+1)
    if nx==0:
        jx = [1]
        nx = 1
    else:
        jx = ix[::-1]
    for i, j in zip(ix, jx):
        x = (i*x2+j*x1)/nx
        GL.glVertex2f(x, y1)
        GL.glVertex2f(x, y2)

    iy = range(ny+1)
    if ny==0:
        jy = [1]
        ny = 1
    else:
        jy = iy[::-1]
    for i, j in zip(iy, jy):
        y = (i*y2+j*y1)/ny
        GL.glVertex2f(x1, y)
        GL.glVertex2f(x2, y)
    GL.glEnd()


def drawRect(x1, y1, x2, y2):
    """Draw the circumference of a rectangle."""
    drawGrid(x1, y1, x2, y2, 1, 1)


def drawRectangle(x1,y1,x2,y2,color,texture=None):
    """Draw a single rectangular quad."""
    x = array([(x1, y1), (x2, y1), (x2, y2), (x1, y2)])
    c = resize(asarray(color), (4, 3))
    ##drawPolygons(coord,None,'flat',color=color,texture=texture)
    if texture is not None:
        glTexture(texture)
        t = [[0., 0.], [1., 0.], [1., 1.], [0., 1.]]
    else:
        t = None
    GL.glBegin(GL.GL_QUADS)
    for i in range(4):
        GL.glColor3fv(c[i])
        if texture is not None:
            GL.glTexCoord2fv(t[i])
        GL.glVertex2fv(x[i])
    GL.glEnd()


### Decorations ###############################################

class Decoration(Drawable):
    """A decoration is a 2-D drawing at canvas position x,y.

    All decorations have at least the following attributes:

    - x,y : (int) window coordinates of the insertion point
    - drawGL() : function that draws the decoration at (x,y).
               This should only use openGL function that are
               allowed in a display list.

    """

    def __init__(self,x,y,**kargs):
        """Create a decoration at canvas coordinates x,y"""
        self.x = int(x)
        self.y = int(y)
        if 'nolight' not in kargs:
            kargs['nolight'] = True
        if 'ontop' not in kargs:
            kargs['ontop'] = True
        Drawable.__init__(self,**kargs)


class GlutText(Decoration):
    """A viewport decoration showing a text string.

    - text: a simple string, a multiline string or a list of strings. If it is
      a string, it will be splitted on the occurrence of '\\n' characters.
    - x,y: insertion position on the canvas
    - gravity: a string that determines the adjusting of the text with
      respect to the insert position. It can be a combination of one of the
      characters 'N or 'S' to specify the vertical positon, and 'W' or 'E'
      for the horizontal. The default(empty) string will center the text.

    """

    def __init__(self,text,x,y,font='9x15',size=None,gravity=None,color=None,zoom=None,**kargs):
        """Create a text actor"""
        Decoration.__init__(self,x,y,**kargs)
        self.text = str(text)
        self.font = gluttext.glutSelectFont(font, size)

        if gravity is None:
            gravity = 'E'
        self.gravity = gravity
        self.color = saneColor(color)
        self.zoom = zoom

    def drawGL(self,**kargs):
        """Draw the text."""
        ## if self.zoom:
        ##     pf.canvas.zoom_2D(self.zoom)
        if self.color is not None:
            GL.glColor3fv(self.color)
        gluttext.glutDrawText(self.text, self.x, self.y, font=self.font, gravity=self.gravity)
        ## if self.zoom:
        ##     pf.canvas.zoom_2D()

Text = GlutText


class Rectangle(Decoration):
    """A 2D-rectangle on the canvas."""
    def __init__(self,x1,y1,x2,y2,color=None,texture=None,**kargs):
        Decoration.__init__(self,x1,y1,**kargs)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.setColor(color, ncolors=4)
        self.setTexture(texture)

    def drawGL(self,**kargs):
        from pyformex.gui.canvas import glFill
        glFill()
        drawRectangle(self.x1, self.y1, self.x2, self.y2, self.color, self.texture)


class Grid2D(Decoration):
    """A 2D-grid on the canvas."""
    def __init__(self,x1,y1,x2,y2,nx=1,ny=1,color=None,linewidth=None,**kargs):
        Decoration.__init__(self,x1,y1,**kargs)
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.nx = nx
        self.ny = ny
        self.color = saneColor(color)
        self.linewidth = saneLineWidth(linewidth)

    def drawGL(self,**kargs):
        if self.color is not None:
            GL.glColor3fv(self.color)
        if self.linewidth is not None:
            GL.glLineWidth(self.linewidth)
        drawGrid(self.x1, self.y1, self.x2, self.y2, self.nx, self.ny)


class LineDrawing(Decoration):
    """A collection of straight lines on the canvas."""
    def __init__(self,data,color=None,linewidth=None,**kargs):
        """Initially a Line Drawing.

        data can be a 2-plex Formex or equivalent coordinate data.
        The z-coordinates of the Formex are unused.
        A (n,2,2) shaped array will do as well.
        """
        data = data.view()
        data = data.reshape((-1, 2, data.shape[-1]))
        data = data[:,:, :2]
        self.data = data.astype(Float)
        x1, y1 = self.data[0, 0]
        Decoration.__init__(self,x1,y1,**kargs)
        self.color = saneColor(color)
        self.linewidth = saneLineWidth(linewidth)


    def drawGL(self,**kargs):
        if self.color is not None:
            GL.glColor3fv(self.color)
        if self.linewidth is not None:
            GL.glLineWidth(self.linewidth)
        GL.glBegin(GL.GL_LINES)
        for e in self.data:
            GL.glVertex2fv(e[0])
            GL.glVertex2fv(e[1])
        GL.glEnd()


# End
