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
from __future__ import absolute_import, division, print_function

import pyformex as pf
from pyformex import simple
from pyformex.formex import Formex
from . import colors
from .drawable import Actor
from .textext import FontTexture
from .sanitize import saneLineWidth

import numpy as np

### Decorations ###############################################


class BboxActor(Actor):
    """Draws a bounding bbox.

    A bounding box is a hexaeder in global axes. The hexaeder is
    drawn in wireframe mode with default color black.
    """
    def __init__(self,bbox,**kargs):
        F = simple.cuboid(*bbox)
        Actor.__init__(self,F,mode='wireframe',lighting=False,opak=True,**kargs)


class Rectangle(Actor):
    """A 2D-rectangle on the canvas."""
    def __init__(self,x1,y1,x2,y2,**kargs):
        F = Formex([[[x1,y1],[x2,y1],[x2,y2],[x1,y2]]])
        Actor.__init__(self,F,rendertype=2,**kargs)


class Line(Actor):
    """A 2D-line on the canvas.

    Parameters:

    - `x1, y1, x2, y2`: floats: the viewport coordinates of the
      endpoints of the line
    - `kargs`: keyword arguments to be passed to the :class:`Actor`.
    """
    def __init__(self,x1,y1,x2,y2,**kargs):
        F = Formex([[[x1,y1],[x2,y2]]])
        Actor.__init__(self,F,rendertype=2,**kargs)


class Lines(Actor):
    """A collection of straight lines on the canvas.

    Parameters:

    - `data`: data that can initialize a 2-plex Formex: the viewport coordinates
      of the 2 endpoints of the n lines. The third coordinate is ignored.
    - `kargs`: keyword arguments to be passed to the :class:`Actor`.

    """
    def __init__(self,data,color=None,linewidth=None,**kargs):
        """Initialize a Lines."""
        F = Formex(data)
        Actor.__init__(self,F,rendertype=2,**kargs)


class Grid2D(Actor):
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
    - `size`: font size to be used for the labels
    - `font`: font to be used for the labels. It can be a
      :class:`textext.FontTexture` or a string with the path to a monospace
      .ttf font. If unspecified, the default font is used.
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
    def __init__(self,colorscale,ncolors,x,y,w,h,ngrid=0,linewidth=None,nlabel=-1,size=18,font=None,dec=2,scale=0,lefttext=False,**kargs):
        """Initialize the ColorLegend."""
        from pyformex.gui import colorscale as cs
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
            G = Actor(F,rendertype=2,lighting=False,color=colors.black,linewidth=self.linewidth,mode='wireframe')
            self.children.append(G)

        # labels
        # print("LABELS: %s" % self.nlabel)
        if self.nlabel > 0:
            from pyformex.opengl import textext

            if font is None:
                font = FontTexture.default()
            elif isinstance(font,(str,unicode)):
                font = FontTexture(font,size)
            self.font = font
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

            ypos = self.y + da * np.arange(self.nlabel+1)

            yok = self.y - 0.01*dh
            for (y,v) in zip (ypos,vals):
                #print(y,v,yok)
                if y >= yok:
                    t = textext.Text(("%%.%df" % self.dec) % (v*self.scale), (x,y), size=size, gravity=gravity)
                    self.children.append(t)
                    yok = y + dh


def Grid(nx=(1, 1, 1),ox=(0.0, 0.0, 0.0),dx=(1.0, 1.0, 1.0),lines='b',planes='b',linecolor=colors.black,planecolor=colors.white,alpha=0.3,**kargs):
    """Creates a (set of) grid(s) in (some of) the coordinate planes.

    Parameters:

    - `nx`: a list of 3 integers, specifying the number of divisions of the
      grid in the three coordinate directions. A zero value may be specified
      to avoid the grid to extend in that direction. Thus, setting the last
      value to zero will result in a planar grid in the xy-plane.
    - `ox`: a list of 3 floats: the origin of the grid.
    - `dx`: a list of 3 floats: the step size in each coordinate direction.
    - `planes`: one of 'first', 'box', 'all', 'no' (the string can be
      shortened to the first chartacter): specifies how many planes are
      drawn in each direction: 'f' only draws the first, 'b' draws the first
      and the last, resulting in a box, 'a' draws all planes,
      'n' draws no planes.

    Returns a list with up to two Meshes: the planes, and the lines.

    """
    from pyformex import simple
    from pyformex.olist import List
    from pyformex.mesh import Mesh
    G = List()

    planes = planes[:1].lower()
    P = []
    L = []
    for i in range(3):
        n0,n1,n2 = np.roll(nx,i)
        d0,d1,d2 = np.roll(dx,i)
        if n0*n1:
            if planes != 'n':
                M = simple.rectangle(b=n0*d0,h=n1*d1)
                if n2:
                    if planes == 'b':
                        M = M.replic(2,dir=2,step=n2*d2)
                    elif planes == 'a':
                        M = M.replic(n2+1,dir=2,step=d2)
                P.append(M.rollAxes(-i).toMesh())
            if lines != 'n':
                M = Formex('1').scale(n0*d0).replic(n1+1,dir=1,step=d1) + \
                    Formex('2').scale(n1*d1).replic(n0+1,dir=0,step=d0)
                if n2:
                    if lines == 'b':
                        M = M.replic(2,dir=2,step=n2*d2)
                    elif lines == 'a':
                        M = M.replic(n2+1,dir=2,step=d2)

                L.append(M.rollAxes(-i).toMesh())

    if P:
        M = Mesh.concatenate(P)
        M.attrib(name='__grid_planes__',mode='flat',lighting=False,color=planecolor,alpha=alpha,**kargs)
        G.append(M)
    if L:
        M = Mesh.concatenate(L)
        M.attrib(name='__grid_lines__',mode='flat',lighting=False,color=linecolor,alpha=0.6,**kargs)
        G.append(M)

    return G.trl(ox)


__all__ = [ 'BboxActor', 'Rectangle', 'Line', 'Lines', 'Grid2D', 'ColorLegend',
            'Grid' ]


# End
