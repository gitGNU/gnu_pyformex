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
"""Stars

This example illustrates the use of random values. It generates a collection
of stars with random number of points (between 5 and 15). A random noise is
applied on the geometry and the stars are place with random position and
orientation in a confined space. Finally, the stars are drawn with random
RGB colors.
"""
from __future__ import absolute_import, division, print_function
from pyformex import zip

_status = 'checked'
_level = 'beginner'
_topics = ['geometry']
_techniques = ['color', 'random']

from pyformex.gui.draw import *

nstars = 200 # number of stars
minpoints = 5 # minimum number of points in the stars
maxpoints = 15# maximum number of points in the stars
noise = 0.2 # relative amplitude of noise in the shape of the star
displ = sqrt(nstars)*3.0 # relative displacement of the stars
maxrot = 70. # maximum rotation angle (in degrees)

def star(n,noise=0.,prop=0):
    """Create a regular n-pointed star, possibly with noise and properties.

    n should be odd and >= 3. With 3 however, the result is a triangle,
    so at least 5 is recommended. If an even number is given, 1 is added.
    A noise parameter can be given to vary the regular shape.
    A prop can be set too.
    """
    if n < 3:
        n = 3
    if n % 2 == 0:
        n += 1
    f = Formex([[[0, 1]]]).rosette(n, (n//2)*360./n).view()
    if noise != 0.:
        f = f + noise * random.random(f.shape)
    P = Formex(concatenate([f, f[:1]]))
    return connect([P, P], bias=[0, 1]).setProp(prop)

def run():
    # create random number of points, rotation and translation
    npts = random.randint(minpoints-1, maxpoints, (nstars,))
    rot = random.random((nstars, 3))
    ang = random.random((nstars,)) * maxrot
    trl = random.random((nstars, 3)) * displ
    # create the stars
    Stars = Formex.concatenate([ star(n, noise, i).rotate(a, r).translate(t) for i, n, a, r, t in zip(arange(nstars), npts, ang, rot, trl) ])
    # draw them with random colors
    colors = random.random((nstars, 3))
    clear()
    flat()
    draw(Stars, colormap=colors)

if __name__ == '__draw__':
    run()
# End
