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
"""Interpolate

This examples illustrates the working of the 'interpolate' method.

First, two lines are created, each one consisting of two line segments.
Then new lines are created by interpolating between the two.
Next, an interpolation is created with the element order swapped.
Finally, the lines are subdivided in smaller segments.
"""
from __future__ import absolute_import, division, print_function


_status = 'checked'
_level = 'beginner'
_topics = ['geometry']
_techniques = ['color', 'interpolate']

from pyformex.gui.draw import *

def run():
    clear()
    wireframe()

    a = Formex([[[0, 0, 0], [1, 0, 0]], [[1, 0, 0], [2, 0, 0]]])
    b = Formex([[[0, 1, 0], [1, 1, 0]], [[1, 1, 0], [2, 1, 0]]])
    print("Two lines")
    draw(a+b)
    drawNumbers(a+b)

    n = 10
    v = 1./n * arange(n+1)
    p = arange(n)

    pause()
    c = interpolate(a, b, v)
    c.setProp(p)
    print("Interpolate between the two")
    draw(c)
    drawNumbers(c)

    pause()
    d = interpolate(a, b, v, swap=True)
    d.setProp(p)
    clear()
    print("Interpolate again with swapped order")
    draw(d)
    drawNumbers(d)
    #return

    pause()
    f = c.divide(v)
    f.setProp((1, 2))
    clear()
    print("Divide the set of lines")
    draw(f)
    drawNumbers(f)


if __name__ == '__draw__':
    run()
# End
