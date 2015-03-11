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
"""ClippingBoxVTK

Clips a mesh with sheared box using VTK.
"""
from __future__ import print_function


_status = 'checked'
_level = 'normal'
_topics = ['surface','mesh','vtk']
_techniques = ['intersection','clip','cut','vtk']

from pyformex.gui.draw import *
from pyformex.simple import sphere,cuboid
from pyformex.plugins.vtk_itf import vtkClip


def run():
    
    clear()
    transparent()
    smoothwire
    
    nsphere = 10
    S = sphere(nsphere)
    
    bbs=cuboid(*S.bbox()).toMesh().scale([0.8,0.8,1]).rot(30,1).rot(20,0).shear(2,1,0.3)
    
    clippedIn=vtkClip(S,implicitdata=bbs,method='boxplanes',insideout=0)[1]
    clippedOut=vtkClip(S,implicitdata=bbs,method='boxplanes',insideout=1)[1]

    draw(clippedIn,color=red,alpha=1)
    draw(clippedOut,color=blue,alpha=1)
    draw(bbs,color=yellow)

if __name__ == '__draw__':
    run()