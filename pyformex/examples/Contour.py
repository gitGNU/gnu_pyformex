# $Id$
##
##  This file is part of pyFormex 1.0.2  (Thu Jun 18 15:35:31 CEST 2015)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2015 (C) Benedict Verhegghe (benedict.verhegghe@feops.com)
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

"""Contour

This example demonstrates the use of FTGL library to render text as 3D objects.
To be able to run it, you need to have the FTGL library and its Python bindings
installed.

The pyFormex source repository contains a directory pyformex/extra/pyftgl
containing a Makefile to install the libraries.
"""
from __future__ import absolute_import, print_function


_status = 'checked'
_level = 'advanced'
_topics = ['text']
_techniques = ['contour', 'font']

from pyformex.gui.draw import *
from pyformex.plugins.curve import *
from pyformex.opengl.textext import *


class FontOutline(Geometry):
    """A class for font outlines.

    """
    def __init__(self,filename,size):
        """Initialize a FontTexture"""
        Geometry.__init__(self)
        print("Creating FontTexture(%s) in size %s" % (filename,size))
        face = ft.Face(str(filename))
        face.set_char_size(int(size*64))
        if not face.is_fixed_width:
            raise RuntimeError("Font is not monospace")
        self.face = face


    def outline(self,c):
        """Return the outlines for glyph i"""
        self.face.load_char( c, ft.FT_LOAD_RENDER | ft.FT_LOAD_FORCE_AUTOHINT )
        return self.face.glyph.outline


def pointsToContour(points,tags):
    if tags[0] & 1 == 0:
        raise ValueError("First point should be on curve!")
    elems = []
    elem = []

    def store():
        if elem:
            elem.append(i)
            if len(elem) > 4:
                raise ValueError("Too many points (%s) in stroke %s" % (len(elem),len(elems)))
            elems.append(elem)

    for i,t in enumerate(tags):
        if t & 1:
            store()
            elem = []
        elem.append(i)
    i = 0
    store()
    return Contour(Coords(points),elems)


def outlineToCurve(outline):
    out = List([])
    i = 0
    for k in outline.contours:
        j = k+1
        C = pointsToContour(outline.points[i:j],outline.tags[i:j])
        print(C.elems)
        i = j
        out.append(C)
    return out


def drawChar(c):
    clear()
    CO = font.outline(c)
    O = outlineToCurve(CO)
    C = O[0]
    print("nparts: %s" % C.nparts)
    print(C.stroke((C.nparts)-1))
    draw(O,clear=True)
    #draw(C.approx())
    X = Coords(CO.points)
    draw(X)
    drawNumbers(X)


def callback(item):
    c = item.value()
    drawChar(c)

def setFont(default):
    global font
    font = FontOutline(default,24)


def run():
    fonts = utils.listMonoFonts()
    default = utils.defaultMonoFont()
    setFont(default)

    while True:
        choices = [ chr(i) for i in range(32,127) ]
        res = askItems([
            _I('font',choices=fonts,value=default,onselect=setFont),
            _I('char',itemtype='hpush',choices=choices,func=callback,count=16),
            ])
        if not res:
            break
        default = res['font']
        setFont(default)
        drawChar(res['char'])


if __name__ == '__draw__':
    clear()
    reset()
    smooth()
    lights(False)
    run()


# End
