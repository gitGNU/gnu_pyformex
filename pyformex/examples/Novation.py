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
"""Novation

"""
from __future__ import print_function


_status = 'checked'
_level = 'normal'
_topics = ['geometry', 'surface']
_techniques = ['dialog', 'persistence', 'color']

from pyformex.gui.draw import *

def run():
    reset()

    basechoices = ['Triangles', 'Quadrilaterals']
    renderchoices = renderModes()
    res = askItems([
        _I('baseGeom', itemtype='radio', choices=basechoices, text='Type of surface element'),
        _I('nbumps', 3, text='Number of bumps'),
        _I('rendermode', choices=renderchoices, text='Render mode'),
        _I('transp', False, text='Transparent'),
        _I('bottom', False, text='Add a bottom plate'),
        _I('shrink', False, text='Shrink elements'),
        _I('export', False, text='Export to .stl'),
        ])
    if not res:
        return

    globals().update(res)

    n = 10*nbumps

    if baseGeom == 'Triangles':
        # The base consists of two triangles
        e = Formex([[[0, 0, 0], [1, 0, 0], [0, 1, 0]], [[1, 0, 0], [1, 1, 0], [0, 1, 0]]], 1).replic2(n, n, 1, 1)
    else:
        # The base is one quadrilateral
        e = Formex([[[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]], 1).replic2(n, n, 1, 1)

    # Novation (Spots)
    s = nbumps+1
    r = n/s
    h = 12
    a = [ [r*i, r*j, h]  for j in range(1, s) for i in range(1, s) ]

    if bottom:
        # create a bottom
        b = e.reverse()
        #b.setProp(2)

    # create the bumps
    for p in a:
        e = e.bump(2, p, lambda x:exp(-0.5*x), [0, 1])

    renderMode(rendermode)
    setDrawOptions({'shrink':shrink})
    if transp:
        transparent(True)
    if bottom:
        draw(b, color=yellow, alpha=1.0)

    draw(e, alpha=0.8)

    if export and checkWorkdir():
        F = e # + b
        # Create triangles
        G = F.selectNodes([0, 1, 2])
        # If polygones, add more triangles
        for i in range(3, F.nplex()):
            G += F.selectNodes([0, i-1, i])
        clear()
        draw(G)
        from filewrite import writeSTL
        writeSTL('novation.stl', G.coords)

if __name__ == 'draw':
    run()
# End
