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
"""Playing with colors.

This module defines some colors and color conversion functions.
It also defines a default palette of colors.

The following table shows the colors of the default palette, with their name,
RGB values in 0..1 range and luminance.

>>> for k,v in palette.iteritems():
...     print("%12s = %s -> %0.3f" % (k,v,luminance(v)))
    darkgrey = (0.4, 0.4, 0.4) -> 0.133
         red = (1.0, 0.0, 0.0) -> 0.213
       green = (0.0, 1.0, 0.0) -> 0.715
        blue = (0.0, 0.0, 1.0) -> 0.072
        cyan = (0.0, 1.0, 1.0) -> 0.787
     magenta = (1.0, 0.0, 1.0) -> 0.285
      yellow = (1.0, 1.0, 0.0) -> 0.928
       white = (1.0, 1.0, 1.0) -> 1.000
       black = (0.0, 0.0, 0.0) -> 0.000
     darkred = (0.5, 0.0, 0.0) -> 0.046
   darkgreen = (0.0, 0.5, 0.0) -> 0.153
    darkblue = (0.0, 0.0, 0.5) -> 0.015
    darkcyan = (0.0, 0.5, 0.5) -> 0.169
 darkmagenta = (0.5, 0.0, 0.5) -> 0.061
  darkyellow = (0.5, 0.5, 0.0) -> 0.199
   lightgrey = (0.8, 0.8, 0.8) -> 0.604

"""
from __future__ import print_function

import pyformex as pf
from gui import QtCore,QtGui
from arraytools import array,isInt,Int,concatenate
from odict import ODict


def GLcolor(color):
    """Convert a color to an OpenGL RGB color.

    The output is a tuple of three RGB float values ranging from 0.0 to 1.0.
    The input can be any of the following:

    - a QColor
    - a string specifying the Xwindow name of the color
    - a hex string '#RGB' with 1 to 4 hexadecimal digits per color
    - a tuple or list of 3 integer values in the range 0..255
    - a tuple or list of 3 float values in the range 0.0..1.0

    Any other input may give unpredictable results.

    Examples:
    >>> GLcolor('indianred')
    (0.803921568627451, 0.3607843137254902, 0.3607843137254902)
    >>> print(GLcolor('#ff0000'))
    (1.0, 0.0, 0.0)
    >>> GLcolor(red)
    (1.0, 0.0, 0.0)
    >>> GLcolor([200,200,255])
    (0.7843137254901961, 0.7843137254901961, 1.0)
    >>> GLcolor([1.,1.,1.])
    (1.0, 1.0, 1.0)
    >>> GLcolor(0.6)
    (0.6, 0.6, 0.6)
    """
    col = color

    # as of Qt4.5, QtGui.Qcolor no longer raises an error if given
    # erroneous input. Therefore, we check it ourselves

    # Check if it is a palette color name
    if isinstance(col, str) and col in palette:
        col = palette[col]

    # str or QtCore.Globalcolor: convert to QColor
    if ( isinstance(col, str) or
         isinstance(col,QtCore.Qt.GlobalColor) ):
        try:
            col = QtGui.QColor(col)
        except:
            pass

    # QColor: convert to (r,g,b) tuple (0..255)
    if isinstance(col,QtGui.QColor):
        col = (col.red(),col.green(),col.blue())

    # Convert to a list and check length
    try:
        col = tuple(col)
        if len(col) == 3:
            if isInt(col[0]):
                # convert int values to float
                col = [ c/255. for c in col ]
            col = map(float,col)
            # SUCCESS !
            return tuple(col)
    except:
        pass

    # A single float value in the range 0..1 is converted to a grey value
    try:
        col = float(col)
        if col >= 0.0 and col <= 1.0:
            return grey(col)
    except:
        pass

    # No success: raise an error
    raise ValueError("GLcolor: unexpected input of type %s: %s" % (type(color),color))

# TODO: Should convert result to Int8 ?
def RGBcolor(color):
    """Return an RGB (0-255) tuple for a color

    color can be anything that is accepted by GLcolor.
    Returns the corresponding RGB tuple.
    """
    col = array(GLcolor(color))*255
    return col.round().astype(Int)


def RGBAcolor(color,alpha):
    """Return an RGBA (0-255) tuple for a color and alpha value.

    color can be anything that is accepted by GLcolor.
    Returns the corresponding RGBA tuple.
    """
    col = concatenate([array(GLcolor(color)),[alpha]])*255
    return col.round().astype(Int)


def WEBcolor(color):
    """Return an RGB hex string for a color

    color can be anything that is accepted by GLcolor.
    Returns the corresponding WEB color, which is a hexadecimal string
    representation of the RGB components.
    """
    col = RGBcolor(color)
    return "#%02x%02x%02x" % tuple(col)


def colorName(color):
    """Return a string designation for the color.

    color can be anything that is accepted by GLcolor.
    In the current implementation, the returned color name is the
    WEBcolor (hexadecimal string).

    Examples:
    >>> colorName('red')
    '#ff0000'
    >>> colorName('#ffddff')
    '#ffddff'
    >>> colorName([1.,0.,0.5])
    '#ff0080'
    """
    return WEBcolor(color)


def luminance(color,gamma=True):
    """Compute the luminance of a color.

    Returns a floating point value in the range 0..1 representing the
    luminance of the color. The higher the value, the brighter the color
    appears to the human eye.

    This can be for example be used to derive a good contrasting
    foreground color to display text on a colored background.
    Values lower than 0.5 contrast well with white, larger value
    contrast better with black.

    Example:

    >>> print([ "%0.2f" % luminance(c) for c in ['black','red','green','blue']])
    ['0.00', '0.21', '0.72', '0.07']
    """
    lum = lambda c: ((c+0.055)/1.055) ** 2.4 if c > 0.04045 else c/12.92
    color = GLcolor(color)
    if gamma:
        R,G,B = map(lum,color)
    else:
        R,G,B = color
    return 0.2126 * R + 0.7152 * G + 0.0722 * B


def createColorDict():
    for c in QtGui.QColor.colorNames():
        col = QtGui.QColor
        print("Color %s = %s" % (c,colorName(c)))


def closestColorName(color):
    """Return the closest color name."""
    pass


def RGBA(rgb,alpha=1.0):
    """Adds an alpha channel to an RGB color"""
    return GLcolor(rgb)+(alpha,)


def GREY(val,alpha=1.0):
    """Returns a grey OpenGL color of given intensity (0..1)"""
    return (val,val,val,1.0)

def grey(i):
    return (i,i,i)


black       = (0.0, 0.0, 0.0)
red         = (1.0, 0.0, 0.0)
green       = (0.0, 1.0, 0.0)
blue        = (0.0, 0.0, 1.0)
cyan        = (0.0, 1.0, 1.0)
magenta     = (1.0, 0.0, 1.0)
yellow      = (1.0, 1.0, 0.0)
white       = (1.0, 1.0, 1.0)
darkred     = (0.5, 0.0, 0.0)
darkgreen   = (0.0, 0.5, 0.0)
darkblue    = (0.0, 0.0, 0.5)
darkcyan    = (0.0, 0.5, 0.5)
darkmagenta = (0.5, 0.0, 0.5)
darkyellow  = (0.5, 0.5, 0.0)

pyformex_pink = (1.0,0.2,0.4)

lightlightgrey = grey(0.9)
lightgrey = grey(0.8)
mediumgrey = grey(0.6)
darkgrey = grey(0.4)


def setPalette(colors):
    global palette
    palette = ODict([ (k,GLcolor(k)) for k in colors ])


# Set default palette
# !! THIS IS CURRENTLY NOT USED YET
palette = ODict([ (k,globals()[k]) for k in ['darkgrey','red','green','blue','cyan','magenta','yellow','white','black','darkred','darkgreen','darkblue','darkcyan','darkmagenta','darkyellow','lightgrey'] ])

# End
