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
"""Layers

Subdivide a cylindrical mesh in different (radial) layers.
To every layer a different property is assigned.
"""
from __future__ import print_function

_status = 'checked'
_level = 'normal'
_topics = ['surface', 'cylinder']
_techniques = ['surface', 'subdivide','frontwalk','layers','partitioning']

from pyformex.gui.draw import *
from pyformex.simple import cylinder

def splitAlongPath(path,mesh,atol=0.0,sort='area'):
    '''
    Given split mesh into different regions along closed path(s) matching coords of mesh
    '''
    cpath= Mesh(mesh.coords, mesh.getEdges()).matchCentroids(path)
    mask=complement(cpath, mesh.getEdges().shape[0])
    p=mesh.maskedEdgeFrontWalk(mask=mask, frontinc=0)
    if sort=='area':
        p = sortSubsets(p, mesh.areas())
    return p

def run():
    pass

    clear()
    cyl = cylinder(L=8., D=2., nt=36, nl=20, diag='').centered().toMesh()
    cyl = cyl.connect(cyl.scale([1.2,1.2,1]))
    cyl = cyl.subdivide(1,1,[0,0.1,0.3,0.6,1])
    draw(cyl,color=red)
    pause()
    clear()
    
    cylbrd = cyl.getBorderMesh()
    cyledgs = cyl.getFreeEntitiesMesh(level=1)
    pcyl = splitAlongPath(cyledgs,cylbrd)
    cylbrd = cylbrd.setProp(pcyl)
    
    innds = cyl.matchCoords(cylbrd.selectProp(1,compact=True))
    inelems = cyl.connectedTo(innds)
    
    play = cyl.frontWalk(startat=inelems)
    cyl = cyl.setProp(play)
    draw(cyl,color='prop')


if __name__ == '__draw__':
    run()
# End
