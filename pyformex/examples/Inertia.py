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
"""Inertia

"""
from __future__ import absolute_import, division, print_function


_status = 'checked'
_level = 'beginner'
_topics = ['geometry']
_techniques = ['color', 'axes']

from pyformex.gui.draw import *

def unitAxes():
    """Create a set of three axes."""
    Hx = Formex('l:1', 5).translate([-0.5, 0.0, 0.0])
    Hy = Hx.rotate(90)
    Hz = Hx.rotate(-90, 1)
    Hx.setProp(4)
    Hy.setProp(5)
    Hz.setProp(6)
    return Formex.concatenate([Hx, Hy, Hz])

def showPrincipal1(F):
    """Show the principal axes."""
    clear()
    I = F.coords.inertia()
    C = I.ctr
    print("Total mass: %s" % I.mass)
    print("Center: %s" % I.ctr)
    print("Inertia tensor: %s" % I.tensor)
    Iprin, Iaxes = I.principal()
    pf.debug("Principal Values: %s" % Iprin)
    pf.debug("Principal Directions:\n%s" % Iaxes)

    siz = F.dsize()
    H = unitAxes().scale(siz).affine(Iaxes.transpose(), C)
    Ax, Ay, Az = Iaxes[:, 0], Iaxes[:, 1], Iaxes[:, 2]
    G = Formex([[C, C+Ax], [C, C+Ay], [C, C+Az]], 3)
    draw([F, G, H])


def run():
    reset()
    wireframe()
    view('front')

    #F = Formex('l:1').replic(2,2,1).replic(2,2,2).scale(2)
    nx, ny, nz = 2, 3, 4
    dx, dy, dz = 4, 3, 2
    F = Formex([[[0, 0, 0]]]).replic(nx, dx, 0).replic(ny, dy, 1).replic(nz, dz, 2)

    Fr = F
    showPrincipal1(Fr)

    sleep(2)
    Fr = F.rotate(30, 0).rotate(45, 1).rotate(60, 2)
    showPrincipal1(Fr)


    ## sleep(2)
    ## Fo = Formex([[C]])
    ## Fc = connect([Fo,Fr],loop=True)
    ## draw(Fc)

if __name__ == '__draw__':
    run()
# End
