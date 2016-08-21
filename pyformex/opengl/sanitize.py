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
"""Sanitize data before rendering.

The pyFormex drawing functions were designed to require a minimal knowledge
of OpenGL and rendering principles in general. They allow the user to specify
rendering attributes in a simple, user-friendly, sometimes even sloppy way.
This module contains some functions to sanitize the user input into the more
strict attributes required by the OpenGl rendering engine.

These functions are generally not intended for direct used by the user, but
for use in the opengl rendering functions.
"""
from __future__ import absolute_import, print_function

import pyformex as pf
from pyformex.opengl.colors import GLcolor
import pyformex.arraytools as at
import numpy as np



### Sanitize settings ###############################################

def saneFloat(value):
    """Return a float value or None.

    If value can be converted to float, the float is returned, else None.
    """
    try:
        value = float(value)
    except:
        value = None
    return value


saneLineWidth = saneFloat


def saneLineStipple(stipple):
    """Return a sane line stipple tuple.

    A line stipple tuple is a tuple (factor,pattern) where
    pattern defines which pixels are on or off (maximum 16 bits),
    factor is a multiplier for each bit.
    """
    try:
        stipple = [int(i) for i in stipple]
    except:
        stipple = None
    return stipple


def saneColor(color=None):
    """Return a sane color array derived from the input color.

    A sane color is one that will be usable by the draw method.
    The input value of color can be either of the following:

    - None: indicates that the default color will be used,
    - a single color value in a format accepted by colors.GLcolor,
    - a tuple or list of such colors,
    - an (3,) shaped array of RGB values, ranging from 0.0 to 1.0,
    - an (n,3) shaped array of RGB values,
    - an (n,) shaped array of integer color indices.

    The return value is one of the following:
    - None, indicating no color (current color will be used),
    - a float array with shape (3,), indicating a single color,
    - a float array with shape (n,3), holding a collection of colors,
    - an integer array with shape (n,), holding color index values.

    !! Note that a single color can not be specified as integer RGB values.
    A single list of integers will be interpreted as a color index !
    Turning the single color into a list with one item will work though.
    [[ 0, 0, 255 ]] will be the same as [ 'blue' ], while
    [ 0,0,255 ] would be a color index with 3 values.
    """
    if color is None:
        # no color: use canvas color
        return None

    # detect color index
    try:
        c = np.asarray(color)
        if c.dtype.kind == 'i':
            # We have a color index
            return c
    except:
        pass

    # not a color index: it must be colors
    try:
        color = GLcolor(color)
    except ValueError:

        try:
            color = [GLcolor(co) for co in color]
        except ValueError:
            pass

    # Convert to array
    try:
        # REMOVED THE SQUEEZE: MAY BREAK SOME THINGS !!!
        color = np.asarray(color)#.squeeze()
        if color.dtype.kind == 'f' and color.shape[-1] == 3:
            # Looks like we have a sane color array
            return color.astype(np.float32)
    except:
        pass

    return None


def saneColorArray(color, shape):
    """Makes sure the shape of the color array is compatible with shape.

    Parameters:

    - `color`: set of colors
    - `shape`: (nelems,nplex) tuple

    A compatible color.shape is equal to shape or has either or both of its
    dimensions equal to 1.
    Compatibility is enforced in the following way:

    - if color.shape[1] != nplex and color.shape[1] != 1: take out first
      plane in direction 1
    - if color.shape[0] != nelems and color.shape[0] != 1: repeat the plane
      in direction 0 nelems times

    """
    color = np.asarray(color)
    if color.ndim == 1:
        return color
    if color.ndim == 3:
        if color.shape[1] > 1 and color.shape[1] != shape[1]:
            color = color[:, 0]
    if color.shape[0] > 1 and color.shape[0] != shape[0]:
        color = np.resize(color, (shape[0], color.shape[1]))
    return color


def saneColorSet(color=None,colormap=None,shape=(1,)):
    """Return a sane set of colors.

    A sane set of colors is one that guarantees correct use by the
    draw functions. This means either
    - no color (None)
    - a single color
    - at least as many colors as the shape argument specifies
    - a color index and a color map with enough colors to satisfy the index.
    The return value is a tuple color,colormap. colormap will be None,
    unless color is an integer array, meaning a color index.
    """
    if at.isInt(shape):  # make sure we get a tuple
        shape = (shape,)
    color = saneColor(color)
    if color is not None:
        pf.debug("SANECOLORSET: color %s, shape %s" % (color.shape, shape), pf.DEBUG.DRAW)
        if color.dtype.kind == 'i':
            ncolors = color.max()+1
            if colormap is None:
                colormap = pf.canvas.settings.colormap
            colormap = saneColor(colormap)
            colormap = saneColorArray(colormap, (ncolors,))
        else:
            color = saneColorArray(color, shape)
            colormap = None

        pf.debug("SANECOLORSET RESULT: %s" % str(color.shape), pf.DEBUG.DRAW)
    return color, colormap



### End
