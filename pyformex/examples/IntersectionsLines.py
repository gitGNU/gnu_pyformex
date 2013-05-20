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
"""IntersectionLines

Find the intersetion points of Polylines
"""
from __future__ import print_function
_status = 'checked'
_level = 'normal'
_topics = ['curve']
_techniques = ['intersection']

from gui.draw import *
from plugins.curve import *
from geomtools import *
from simple import circle



def run():
    clear()

    line1 = PolyLine(circle().coords[:,0].trl(1,0.2))
    line2 = PolyLine(circle().coords[:,0].trl(1,-0.2))

    draw([line1,line2])

    q1 = line1.pointsOn()[:-1]
    m1 = line1.vectors()
    q2 = line2.pointsOn()[:-1]
    m2 = line2.vectors()
    
    # computes the intersections all the possible intersections between all the vectors
    t1,t2 = intersectionTimesLWL(q1,m1,q2,m2,mode='all')
    X1 = pointsAtLines(q1[:,newaxis],m1[:,newaxis],t1)
    X2 = pointsAtLines(q2,m2,t2)
    
    # check which intersections are inside the segments boundaries
    inside = (t1>=0.0)*(t1<=1.0)*(t2>=0.0)*(t2<=1.0)
    wl1,wl2 = where(inside)
    
    # find the intersctions points and the intersecting elements
    X1,X2 = X1[inside],X2[inside]
    matches = X2.match(X1)
    coinc = matches!=-1
    wl1,wl2 = wl1[coinc],wl2[coinc]

    
    drawVectors(q1[wl1],m1[wl1],color='red',linewidth=3)
    drawVectors(q2[wl2],m2[wl2],color='green',linewidth=3)
    draw(X1[coinc],color=yellow,marksize=10)
    draw(X2[coinc],color=yellow,marksize=10)
    zoomAll()

if __name__ == 'draw':
    run()
# End