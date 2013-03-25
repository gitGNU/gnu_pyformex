# $Id$
##
##  This file is part of pyFormex 0.9.0  (Mon Mar 25 13:52:29 CET 2013)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2012 (C) Benedict Verhegghe (benedict.verhegghe@ugent.be) 
##  Distributed under the GNU General Public License version 3 or later.
##
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
"""Multicut

This example shows how to cut a hole in a surface.
It uses the cutWithPlane function with a series of cutting planes.
"""
from __future__ import print_function
_status = 'checked'
_level = 'beginner'
_topics = ['surface']
_techniques = ['cut']

from gui.draw import *

def run():
    clear()
    smooth()

    from simple import sphere
    S = sphere(8).scale(3.)
    T = S.cutWithPlane([[2.,0.,0.],[0.,1.,0.],[-2.,0.,0.],[0.,-1.,0.]],
                       [[-1.,0.,0.],[0.,-1.,0.],[1.,0.,0.],[0.,+1.,0.]],
                       side = '-')
    draw(T)

if __name__ == 'draw':
    run()
# End
