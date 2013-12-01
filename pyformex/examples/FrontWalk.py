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
"""FrontWalk

Show applications of the front walk method of a Mesh.
"""
from __future__ import print_function
from future_builtins import zip

_status = 'checked'
_level = 'normal'
_topics = ['mesh']
_techniques = ['frontwalk']
_opengl2 = True

from gui.draw import *

def gradColor(n):
    """Create gradually varying colors for n values"""
    from gui.colorscale import ColorScale
    CS = ColorScale('RGB', 0, float(n))
    return array([CS.color(i) for i in 1.*arange(n+1)])

def run():
    from mesh import rectangle
    clear()
    M = rectangle(L=1, W=1, nl=50, nw=50)
    draw(M)

    # Walk 0: start at elements 10 and 600
    e0 = [10, 600]
    p0 = M.frontWalk(startat=e0)

    # Walk 1: start at nodes 1834 and 2000
    n0 = [1444, 2020]
    e1 = M.connectedTo(n0)
    p1 = M.frontWalk(startat=e1)

    # Walk 2: start at elements and nodes
    e2 = concatenate([e0, e1])
    p2 = M.frontWalk(startat=e2)

    # Walk 3: start at elements and nodes, but the nodes start 1 step later
    q = M.frontWalk(startat=e0, maxval=1) # single step from elements e0
    eq = where(q==1)[0]  # find the first next front
    e3 = concatenate([eq, e1])
    p3 = M.frontWalk(startat=e3) + 1  # add 1 to account for first step
    p3[e0] = 0

    # Draw all 4 cases
    c = [ p0, p1, p2, p3 ]
    cm = [ gradColor(ci.max()) for ci in c ]

    smoothwire()
    view('front')
    nc = len(c)
    layout(nc)

    for i in range(nc):
        viewport(i)
        clear()
        view('front')
        draw(M, color=c[i])


    if ack("Redraw with smooth colors?"):
        for i in range(nc):
            viewport(i)
            clear()
            draw(M, color=c[i], colormap=cm[i])


if __name__ == 'draw':
    run()

# End
