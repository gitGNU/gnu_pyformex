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

"""Postprocessing functions

Postprocessing means collecting a geometrical model and computed values
from a numerical simulation, and render the values on the domain.
"""
from __future__ import print_function

from pyformex.arraytools import *


# Some functions to calculate a scalar value from a vector

def norm2(A):
    return sqrt(square(asarray(A)).sum(axis=-1))

def norm(A, x):
    return power(power(asarray(A), x).sum(axis=-1), 1./x)

def max(A):
    return asarray(A).max(axis=-1)

def min(A):
    return asarray(A).min(axis=-1)


def frameScale(nframes=10,cycle='up',shape='linear'):
    """Return a sequence of scale values between -1 and +1.

    ``nframes`` : the number of steps between 0 and -1/+1 values.

    ``cycle``: determines how subsequent cycles occur:

      ``'up'``: ramping up

      ``'updown'``: ramping up and down

      ``'revert'``: ramping up and down then reverse up and down

    ``shape``: determines the shape of the amplitude curve:

      ``'linear'``: linear scaling

      ``'sine'``: sinusoidal scaling
    """
    s = arange(nframes+1)
    if cycle in [ 'updown', 'revert' ]:
        s = concatenate([s, fliplr(s[:-1].reshape((1, -1)))[0]])
    if cycle in [ 'revert' ]:
        s = concatenate([s, -fliplr(s[:-1].reshape((1, -1)))[0]])
    return s.astype(float)/nframes



def drawField(mesh,fldtype,data,scale='RAINBOW',symmetric_scale=False):
    """Draw intensity of a scalar field over a Mesh.

    Parameters:

    - `mesh`: a Mesh, specifying the geometric domain over which the field
      is defined.
    - `fldtype`: string: defines the type of field. Currently available:

      - 'elemc': the field is constant per element;
      - 'elemn': the field varies over the element and is defined at its nodes;

    - `data`: float array with the field values at the specified points.
      Its shape is dependent on the value of `fldtype`:

      - 'elemc': ( mesh.nelems(), )
      - 'elemn': ( mesh.nelems(), mesh.nplex() )

    Note: this function is under development and still experimental. It does
      not do a lot of error checking yet.
    """
    import pyformex as pf
    from pyformex.gui.colorscale import ColorScale
    from pyformex.opengl.decors import ColorLegend
    from pyformex.gui import draw

    # create a colorscale and draw the colorlegend
    vmin, vmax = data.min(), data.max()
    if vmin*vmax < 0.0 and not symmetric_scale:
        vmid = 0.0
    else:
        vmid = 0.5*(vmin+vmax)

    scalev = [vmin, vmid, vmax]
    if max(scalev) > 0.0:
        logv = [ abs(a) for a in scalev if a != 0.0 ]
        logs = log10(logv)
        logma = int(logs.max())
    else:
        # All data = 0.0
        logma = 0

    if logma < 0:
        multiplier = 3 * ((2 - logma) / 3 )
    else:
        multiplier = 0

    CS = ColorScale('RAINBOW', vmin, vmax, vmid, 1., 1.)
    cval = array([CS.color(v) for v in data.flat])
    cval = cval.reshape(data.shape+(3,))
    CLA = ColorLegend(CS, 256, 20, 20, 30, 200, scale=multiplier)
    draw.drawActor(CLA)
    draw.draw(mesh, color=cval)


# End
