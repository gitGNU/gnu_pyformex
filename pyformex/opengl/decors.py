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
"""Decorations for the OpenGL canvas.

This module contains a collection of predefined decorations that
can be useful additions to a geometry scene rendering.
"""
from __future__ import print_function

from pyformex import simple
from pyformex.formex import Formex
from pyformex.opengl.drawable import Actor
from pyformex.opengl.sanitize import *
from pyformex.gui import colorscale as cs

### Decorations ###############################################


class BboxActor(Actor):
    """Draws a bounding bbox.

    A bounding box is a hexaeder in global axes. The heaxeder is
    drawn in wireframe mode with default color black.
    """
    def __init__(self,bbox,color=black,**kargs):
        F = simple.cuboid(*bbox)
        Actor.__init__(self,F,rendertype=1,mode='wireframe',color=red,lighting=False,opak=True,**kargs)


class Rectangle(Actor):
    """A 2D-rectangle on the canvas."""
    def __init__(self,x1,y1,x2,y2,**kargs):
        F = Formex([[[x1,y1],[x2,y1],[x2,y2],[x1,y2]]])
        Actor.__init__(self,F,rendertype=2,**kargs)


class Line(Actor):
    """A 2D-line on the canvas."""
    def __init__(self,x1,y1,x2,y2,**kargs):
        F = Formex([[[x1,y1],[x2,y2]]])
        Actor.__init__(self,F,rendertype=2,**kargs)


class Grid(Actor):
    """A 2D-grid on the canvas."""
    def __init__(self,x1,y1,x2,y2,nx=1,ny=1,lighting=False,rendertype=2,**kargs):
        F = Formex([[[x1,y1],[x1,y2]]]).replic(nx+1,step=float(x2-x1)/nx,dir=0) + \
            Formex([[[x1,y1],[x2,y1]]]).replic(ny+1,step=float(y2-y1)/ny,dir=1)
        Actor.__init__(self,F,rendertype=rendertype,lighting=lighting,**kargs)


class ColorLegend(Actor):
    """A labeled colorscale legend.

    When showing the distribution of some variable over a domain by means
    of a color encoding, the viewer expects some labeled colorscale as a
    guide to decode the colors. The ColorLegend decoration provides
    such a color legend. This class only provides the visual details of
    the scale. The conversion of the numerical values to the matching colors
    is provided by the :class:`colorscale.ColorLegend` class.

    Parameters:

    - `colorscale`: a :class:`colorscale.ColorScale` instance providing
      conversion between numerical values and colors
    - `colorlegend`: int: the number of different colors to use.
    - `x,y,w,h`: four integers specifying the position and size of the
      color bar rectangle
    - `ngrid`: int: number of intervals for the grid lines to be shown.
      If > 0, grid lines are drawn around the color bar and between the
      ``ngrid`` intervals.
      If = 0, no grid lines are drawn.
      If < 0 (default), the value is set equal to the number of colors
      or to 0 if this number is higher than 50.
    - `linewidth`: float: width of the grid lines. If not specified, the
      current canvas line width is used.
    - `nlabel`: int: number of intervals for the labels to be shown.
      If > 0, labels will be displayed at `nlabel` interval borders, if
      possible. The number of labels displayed thus will be ``nlabel+1``,
      or less if the labels would otherwise be too close or overlapping.
      If 0, no labels are shown.
      If < 0 (default), a default number of labels is shown.
    - `font`, `size`: font and size to be used for the labels
    - `dec`: int: number of decimals to be used in the labels
    - `scale`: int: exponent of 10 for the scaling factor of the label values.
      The displayed values will be equal to the real values multiplied with
      ``10**scale``.
    - `lefttext`: bool: if True, the labels will be drawn to the left of the
      color bar. The default is to draw the labels at the right.

    Some practical guidelines:

    - The number of colors is defined by the ``colorlegend`` argument.
    - Large numbers of colors result inb a quasi continuous color scheme.
    - With a high number of colors, grid lines disturb the image, so either
      use ``ngrid=0`` or ``ngrid=`` to only draw a border around the colors.
    - With a small number of colors, set ``ngrid = len(colorlegend.colors)``
      to add gridlines between each color.
      Without it, the individual colors in the color bar may seem to be not
      constant, due to an optical illusion. Adding the grid lines reduces
      this illusion.
    - When using both grid lines and labels, set both ``ngrid`` and ``nlabel``
      to the same number or make one a multiple of the other. Not doing so
      may result in a very confusing picture.
    - The best practices are to use either a low number of colors (<=20) and
      the default ``ngrid`` and ``nlabel``, or a high number of colors (>=200)
      and the default values or a low value for ``nlabel``.

    The `ColorScale` example script provides opportunity to experiment with
    different settings.
    """
    def __init__(self,colorscale,ncolors,x,y,w,h,ngrid=0,linewidth=None,nlabel=-1,size=18,dec=2,scale=0,lefttext=False,**kargs):
        """Initialize the ColorLegend."""
        self.cl = cs.ColorLegend(colorscale,ncolors)
        self.x = float(x)
        self.y = float(y)
        self.w = float(w)
        self.h = float(h)
        self.ngrid = int(ngrid)
        if self.ngrid < 0:
            self.ngrid = ncolors
            if self.ngrid > 50:
                self.ngrid = 0
        self.linewidth = saneLineWidth(linewidth)
        self.nlabel = int(nlabel)
        if self.nlabel < 0:
            if self.ngrid > 0:
                self.nlabel = self.ngrid
            else:
                self.nlabel = ncolors
        self.dec = dec   # number of decimals
        self.scale = 10 ** scale # scale all numbers with 10**scale
        self.lefttext = lefttext
        self.xgap = 4  # hor. gap between color bar and labels
        self.ygap = 4  # (min) vert. gap between labels

        F = simple.rectangle(1,ncolors,self.w,self.h).trl([self.x,self.y,0.])
        Actor.__init__(self,F,rendertype=2,lighting=False,color=self.cl.colors,**kargs)

        if self.ngrid > 0:
            F = simple.rectangle(1,self.ngrid,self.w,self.h).trl([self.x,self.y,0.])
            G = Actor(F,rendertype=2,lighting=False,color=black,linewidth=self.linewidth,mode='wireframe')
            self.children.append(G)

        # labels
        print("LABELS: %s" % self.nlabel)
        if self.nlabel > 0:
            from pyformex.opengl import textext
            from pyformex.coords import Coords

            self.font = textext.default_font
            fh = self.font.height
            pf.debug("FONT HEIGHT %s" % fh,pf.DEBUG.DRAW)

            if self.lefttext:
                x = F.coords[0,0,0] - self.xgap
                gravity = 'W'
            else:
                x = F.coords[0,1,0] + self.xgap
                gravity = 'E'

            # minimum label distance
            dh = fh + self.ygap
            da = self.h / self.nlabel

            # Check if labels will fit
            if da < dh and self.nlabel == ncolors:
                # reduce number of labels
                self.nlabel = int(self.h/dh)
                da = self.h / self.nlabel

            vals = cs.ColorLegend(colorscale,self.nlabel).limits
            #print("VALS",vals)

            ypos = self.y + da * arange(self.nlabel+1)

            yok = self.y - 0.01*dh
            for (y,v) in zip (ypos,vals):
                #print(y,v,yok)
                if y >= yok:
                    t = textext.Text(("%%.%df" % self.dec) % (v*self.scale), (x,y), size=size, gravity=gravity)
                    self.children.append(t)
                    yok = y + dh


## class LineDrawing(Decoration):
##     """A collection of straight lines on the canvas."""
##     def __init__(self,data,color=None,linewidth=None,**kargs):
##         """Initially a Line Drawing.

##         data can be a 2-plex Formex or equivalent coordinate data.
##         The z-coordinates of the Formex are unused.
##         A (n,2,2) shaped array will do as well.
##         """
##         data = data.view()
##         data = data.reshape((-1, 2, data.shape[-1]))
##         data = data[:,:, :2]
##         self.data = data.astype(Float)
##         x1, y1 = self.data[0, 0]
##         Decoration.__init__(self,x1,y1,**kargs)
##         self.color = saneColor(color)
##         self.linewidth = saneLineWidth(linewidth)


##     def drawGL(self,**kargs):
##         if self.color is not None:
##             GL.glColor3fv(self.color)
##         if self.linewidth is not None:
##             GL.glLineWidth(self.linewidth)
##         GL.glBegin(GL.GL_LINES)
##         for e in self.data:
##             GL.glVertex2fv(e[0])
##             GL.glVertex2fv(e[1])
##         GL.glEnd()


## class Triade(Drawable):
##     """An OpenGL actor representing a triade of global axes.

##     - `pos`: position on the canvas: two characters, of which first sets
##       horizontal position ('l', 'c' or 'r') and second sets vertical
##       position ('b', 'c' or 't').

##     - `size`: size in pixels of the zone displaying the triade.

##     - `pat`: shape to be drawn in the coordinate planes. Default is a square.
##       '16' givec a triangle. '' disables the planes.

##     - `legend`: text symbols to plot at the end of the axes. A 3-character
##       string or a tuple of 3 strings.

##     """

##     def __init__(self,pos='lb',siz=100,pat='3:012934',legend='xyz',color=[red, green, blue, cyan, magenta, yellow],**kargs):
##         Drawable.__init__(self,**kargs)
##         self.pos = pos
##         self.siz = siz
##         self.pat = pat
##         self.legend = legend
##         self.color = color


##     def _draw_me(self):
##         """Draw the triade components."""
##         GL.glBegin(GL.GL_LINES)
##         pts = Formex('1').coords.reshape(-1, 3)
##         GL.glColor3f(*black)
##         for i in range(3):
##             #GL.glColor(*self.color[i])
##             for x in pts:
##                 GL.glVertex3f(*x)
##             pts = pts.rollAxes(1)
##         GL.glEnd()
##         # Coord planes
##         if self.pat:
##             GL.glBegin(GL.GL_TRIANGLES)
##             pts = Formex(self.pat)
##             #pts += pts.reverse()
##             pts = pts.scale(0.5).coords.reshape(-1, 3)
##             for i in range(3):
##                 pts = pts.rollAxes(1)
##                 GL.glColor3f(*self.color[i])
##                 for x in pts:
##                     GL.glVertex3f(*x)
##             GL.glEnd()
##         # Coord axes denomination
##         for i, x in enumerate(self.legend):
##             p = unitVector(i)*1.1
##             t = TextMark(p, x)
##             t.drawGL()


##     def _draw_relative(self):
##         """Draw the triade in the origin and with the size of the 3D space."""
##         GL.glMatrixMode(GL.GL_MODELVIEW)
##         GL.glPushMatrix()
##         GL.glTranslatef (*self.pos)
##         GL.glScalef (self.size, self.size, self.size)
##         self._draw_me()
##         GL.glMatrixMode(GL.GL_MODELVIEW)
##         GL.glPopMatrix()


##     def _draw_absolute(self):
##         """Draw the triade in the lower left corner."""
##         GL.glMatrixMode(GL.GL_MODELVIEW)
##         GL.glPushMatrix()
##         # Cancel the translations
##         rot = GL.glGetFloatv(GL.GL_MODELVIEW_MATRIX)
##         rot[3, 0:3] = [0., 0., 0.]
##         GL.glLoadMatrixf(rot)
##         vp = GL.glGetIntegerv(GL.GL_VIEWPORT)
##         x, y, w, h = vp
##         w0, h0 = self.siz, self.siz # we force aspect ratio 1
##         if self.pos[0] == 'l':
##             x0 = x
##         elif self.pos[0] =='r':
##             x0 = x + w-w0
##         else:
##             x0 = x + (w-w0)/2
##         if self.pos[1] == 'b':
##             y0 = y
##         elif self.pos[1] =='t':
##             y0 = y + h-h0
##         else:
##             y0 = y + (h-h0)/2
##         GL.glViewport(x0, y0, w0, h0)
##         GL.glMatrixMode(GL.GL_PROJECTION)
##         GL.glPushMatrix()
##         GL.glLoadIdentity()
##         fovy = 45.
##         fv = tand(fovy*0.5)
##         fv *= 4.
##         fh = fv
##         # BEWARE: near/far should be larger than size, but not very large
##         # or the depth sort will fail
##         frustum = (-fh, fh, -fv, fv, -3., 100.)
##         GL.glOrtho(*frustum)
##         GL.glDisable(GL.GL_LIGHTING)
##         GL.glDisable (GL.GL_BLEND)
##         GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)
##         GL.glDisable(GL.GL_CULL_FACE)
##         GL.glClearDepth(1.0)
##         GL.glDepthMask (GL.GL_TRUE)
##         GL.glDepthFunc(GL.GL_LESS)
##         GL.glEnable(GL.GL_DEPTH_TEST)
##         self._draw_me()
##         GL.glViewport(*vp)
##         GL.glMatrixMode(GL.GL_PROJECTION)
##         GL.glPopMatrix()
##         GL.glMatrixMode(GL.GL_MODELVIEW)
##         GL.glPopMatrix()

##     def draw(self,**kargs):
##         self._draw_absolute()

# End
