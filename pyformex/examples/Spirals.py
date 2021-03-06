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
"""Spirals

This exampoe shows how to create a spiral curve and how to spread points
evenly along a curve.

See also the Sweep example for a more sophisticated application of spirals.
"""
from __future__ import absolute_import, division, print_function


_status = 'checked'
_level = 'normal'
_topics = ['geometry', 'curve']
_techniques = ['transform', 'spiral']

from pyformex.gui.draw import *
from pyformex.plugins import curve

m = 100 # number of cells along spiral
a = 1. # number of 360 degree turns

F = Formex(origin()) # base pattern, here a point
F = F.replic(m, 1., 0)#.reflect(0)
s = a*2*pi/(m-1)
F = F.scale(s)


def spiral(X,dir=[0, 1, 2],rfunc=lambda x:1,zfunc=lambda x:0):
    """Perform a spiral transformation on a coordinate array"""
    theta = X[..., dir[0]]
    #print(theta)
    r = rfunc(theta) + X[..., dir[1]]
    x = r * cos(theta)
    y = r * sin(theta)
    z = zfunc(theta) + X[..., dir[2]]
    X = hstack([x, y, z]).reshape(X.shape)
    return Coords(X)


nwires=6

phi = 30.
alpha2 = 70.
c = 1.
a = c*tand(phi)
b = tand(phi) / tand(alpha2)


zf = lambda x : c * exp(b*x)
rf = lambda x : a * exp(b*x)


S = spiral(F.coords, [0, 1, 2], rf)#.rosette(nwires,360./nwires)

PL = curve.PolyLine(S[:, 0,:])

def run():
    linewidth(2)
    clear()
    flat()
    draw(origin())
    draw(F, color=blue)
    drawNumbers(F, color=blue)
    draw(PL, color=red)
    draw(PL.coords, color=red)
    drawNumbers(PL.coords, color=red)
    return


    if ack("Spread point evenly?"):
        at = PL.atLength(PL.nparts)
        X = PL.pointsAt(at)
        PL2 = curve.PolyLine(X)
        clear()
        draw(PL2, color=blue)
        draw(PL2.coords, color=blue)

if __name__ == '__draw__':
    run()
# End
