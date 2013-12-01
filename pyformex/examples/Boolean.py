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
"""Boolean

Perform boolean operations on surfaces
"""
from __future__ import print_function
_status = 'checked'
_level = 'normal'
_topics = ['surface', 'gts']
_techniques = ['boolean', 'intersection']
_opengl2 = True
_opengl2_comments = """
- No color
- Not enough light
"""

from gui.draw import *
from simple import cylinder
from connectivity import connectedLineElems
from plugins.trisurface import TriSurface, fillBorder

def splitAlongPath(path,mesh,atol=0.0):
    '''
    Given split mesh into opposite regions along a closed path matching coords of mesh
    '''
    cpath= Mesh(mesh.coords, mesh.getEdges()).matchCentroids(path)
    mask=complement(cpath, mesh.getEdges().shape[0])
    p=mesh.maskedEdgeFrontWalk(mask=mask, frontinc=0)
    msplit=mesh.setProp(p)
    return msplit

def drawResults(**res):

    op = res['op'][0]
    verbose = res['verbose']
    split = res['split']
    path = None
    if op in '+-*':
        I = F.boolean(G, op, verbose=verbose)
        if split:
            path = F.intersection(G, verbose=verbose)
            I = splitAlongPath(path.toMesh(), I.fuse(atol=0).compact()) # with atol = 0 removes repeted nodes which may results after boolean operation
    else:
        I = F.intersection(G, verbose=verbose)
    clear()
    draw(I)

    if op in '+-*':
        return

    else:
        if ack('Create a surface inside the curve ?'):
            I = I.toMesh()
            e = connectedLineElems(I.elems)
            I = Mesh(I.coords, connectedLineElems(I.elems)[0])
            clear()
            draw(I, color=red, linewidth=3)
            S = fillBorder(I, method='planar')
            draw(S)




def close():
    global dialog
    if dialog:
        dialog.close()
        dialog = None
    # Release script lock
    scriptRelease(__file__)

def show():
    dialog.acceptData()
    res = dialog.results
    drawResults(**res)

def timeOut():
    show()
    wait()
    close()

def run():
    global dialog, F, G
    clear()
    smooth()
    view('iso')
    F = cylinder(L=8., D=2., nt=36, nl=20, diag='u').centered()
    F = TriSurface(F).setProp(3).close(method='planar').fixNormals().fuse().compact()
    G = F.rotate(90., 0).trl(0, 1.).setProp(1)
    export({'F':F,'G':G})
    draw([F, G])

    _items =\
        [ _I('op', text='Operation', choices=[
            '+ (Union)',
            '- (Difference)',
            '* Intersection',
            'Intersection Curve',
            ]),
          _I('split', False, text='Split along intersection'),
          _I('verbose', False, text='Show stats'),
        ]
    _enablers = [('op', '+ (Union)', 'split'),
        ('op', '- (Difference)', 'split'),
        ('op', '* Intersection', 'split'),]

    dialog = Dialog(
        items=_items,
        enablers=_enablers,
        actions=[('Close', close), ('Show', show)],
        default='Show')

    dialog.timeout=timeOut
    dialog.show()


if __name__ == 'draw':
    run()
# End
