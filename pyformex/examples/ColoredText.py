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
"""ColoredText

This example illustrates the drawing of text on the 2D OpenGL canvas.
It also shows how to generate random values and how to remove 2D decorations
from the canvas.

The application starts with the generation of (n,8) random numbers between
0.0 and 1.0, and where n is the number of text strings that will be displayed.
The 8 random numbers for each case are use as follows:

- 0, 1: the relative position on the canvas viewport,
- 2: the relative font size, ranging from 12 to 48,
- 3, 4, 5: the color (resp. red, green and blue components),
- 6: the text to be shown, selected from a list of predefined texts,
- 7: the font to be used, also selected from a list of fonts.

The texts are shown one by one, with a small pause between.
During the display of the first half of the set of texts,
the previous text is removed after each new one is shown.
During the second half, all texts remain on the canvas.
"""
from __future__ import absolute_import, print_function


_status = 'checked'
_level = 'beginner'
_topics = []
_techniques = ['color', 'text', 'random', 'animation']

from pyformex.gui.draw import *
from pyformex.opengl.textext import *

def run():
    n = 40
    T = ['Python', 'NumPy', 'OpenGL', 'QT4', 'pyFormex']
    fonts = utils.listMonoFonts()

    ftmin, ftmax = 12, 48

    r = random.random((n, 8))
    w, h = pf.canvas.width(), pf.canvas.height()
    a = r[:, :2] * array([w, h]).astype(int)
    size = (ftmin + r[:, 2] * (ftmax-ftmin)).astype(int)
    colors = r[:, 3:6]
    t = (r[:, 6] * len(T)).astype(int)
    f = (r[:, 7] * len(fonts) - 0.5).astype(int).clip(0, len(fonts)-1)
    clear()

    bgcolor(white)
    lights(False)
    TA = None


    for i,s in enumerate(size):
        TB = drawText(T[t[i]], a[i], font=fonts[f[i]], size=s, color=list(colors[i]))
        sleep(0.5)
        breakpt()
        if i < n/2:
            undecorate(TA)
        TA = TB

if __name__ == '__draw__':
    run()
# End
