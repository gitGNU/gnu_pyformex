# $Id$ *** pyformex app ***
##
##  This file is part of pyFormex
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2012 (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
##  Distributed under the GNU General Public License version 3 or later.
##
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
"""Palette

This example displays all the colors in the default palette on a grid
of (ncolors+1) x (ncolors-1) squares.
"""
from __future__ import print_function
_status = 'checked'
_level = 'beginner'
_topics = ['color']
_techniques = ['palette']

from gui.draw import *

def run():
    clear()
    flat()
    palette = pf.canvas.settings.colormap
    ncolors = len(palette)
    F = Formex('4:0123').replic2(ncolors+1,ncolors-1).setProp(range(ncolors))
    draw(F,color='prop')


if __name__ == 'draw':
    run()
# End