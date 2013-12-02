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
"""LineIntersection

Find the intersection points of polylines
"""
from __future__ import print_function


_status = 'checked'
_level = 'normal'
_topics = ['curve']
_techniques = ['intersection']

from pyformex.gui.draw import *
from pyformex.plugins.curve import *
from geomtools import *
from pyformex.simple import circle


def intersection(F1, F2):
    """Return the intersection of two Formices.

    Currently this only works for plex-2 Formices.

    Returns a tuple:

    - `X`: Coords with the intersection points
    - `w1`: index of the intersection elements in F1
    - `w2`: index of the intersection elements in F2
    """
    if F1.nplex() != 2 or F2.nplex() != 2:
        raise ValueError("Can only interesect plex-2 Formices")

    from geomtools import intersectionTimesLWL

    errh = seterr(divide='ignore', invalid='ignore') # ignore division errors
    q1 = F1[:, 0]
    m1 = F1[:, 1]-F1[:, 0]
    q2 = F2[:, 0]
    m2 = F2[:, 1]-F2[:, 0]

    # Compute all intersection points of the lines
    t1, t2 = intersectionTimesLWL(q1, m1, q2, m2, mode='all')
    X1 = pointsAtLines(q1[:, newaxis], m1[:, newaxis], t1)
    X2 = pointsAtLines(q2, m2, t2)
    seterr(**errh) # reactivate division errors

    # Keep intersecting segments
    inside = (t1>=0.0)*(t1<=1.0)*(t2>=0.0)*(t2<=1.0)
    w1, w2 = where(inside)

    # Find coinciding intersection points and the intersecting segments
    X1, X2 = X1[inside], X2[inside]
    matches = X2.match(X1)
    ok = matches!=-1

    return X1[ok], w1[ok], w2[ok]


def run():

    reset()
    clear()
    flat()

    line1 = circle(30.)
    line2 = line1.trl(0, 0.4)

    # Find the intersection of the segments
    X, w1, w2 = intersection(line1, line2)

    # Change the color of the intersecting segments
    line1.setProp(1).prop[w1] = 5
    line2.setProp(3).prop[w2] = 4

    draw([line1, line2], linewidth=3)
    draw(X, marksize=10, ontop=True)


if __name__ == 'draw':
    run()
# End
