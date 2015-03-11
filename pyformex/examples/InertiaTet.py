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
"""Inertia

"""
from __future__ import print_function


_status = 'checked'
_level = 'beginner'
_topics = ['geometry']
_techniques = ['inertia']

from pyformex.gui.draw import *
from pyformex.simple import sphere,cuboid
from pyformex import inertia

def run():
    smoothwire()

    print("======================")
    print("A cube with side = 1.0")
    F = cuboid().toMesh().convert('tet4').toFormex()
    clear()
    draw(F.toMesh().getBorderMesh())
    print("Number of tetrahedrons: %s" % F.shape[0])
    print("Bounding box: %s" % F.bbox())
    V,M,C,I = inertia.tetrahedral_inertia(F.coords)
    # Analytical
    Va = 1.
    Ma = Va
    Ca = [0.5,0.5,0.5]
    Ia = [1./6, 1./6, 1./6, 0., 0., 0. ]
    print("Volume = %s (corr. %s)" % (V,Va))
    print("Mass = %s (corr. %s)" % (M,Ma))
    print("Center of mass = %s (corr. %s)" % (C,Ca))
    print("Inertia tensor = %s (corr. %s)" % (I,Ia))

    pause()
    print("======================")
    print("A sphere with radius = 1.0")
    # Increase the quality to better approximate the sphere
    quality=4
    F = sphere(quality).tetgen().toFormex()
    clear()
    draw(F.toMesh().getBorderMesh())
    print("Number of tetrahedrons: %s" % F.shape[0])
    print("Bounding box: %s" % F.bbox())
    V,M,C,I = inertia.tetrahedral_inertia(F.coords)
    # Analytical
    Va = 4*pi/3
    Ma = Va
    Ca = [0.,0.,0.]
    ia = 8*pi/15
    Ia = [ia, ia, ia, 0., 0., 0. ]
    print("Volume = %s (corr. %s)" % (V,Va))
    print("Mass = %s (corr. %s)" % (M,Ma))
    print("Center of mass = %s (corr. %s)" % (C,Ca))
    print("Inertia tensor = %s (corr. %s)" % (I,Ia))

if __name__ == '__draw__':
    run()

# End

