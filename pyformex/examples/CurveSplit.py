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
"""Curves

Examples showing the use of the 'curve' plugin

"""
from __future__ import absolute_import, division, print_function


_status = 'checked'
_level = 'normal'
_topics = ['geometry', 'curve']
_techniques = ['widgets', 'persistence', 'import', 'spline', 'frenet']

from pyformex.gui.draw import *
from pyformex.plugins.curve import *
from pyformex.plugins.nurbs import *

def run():

    clear()

    X = pattern('0214412214')
    print(X)

    def drawCurveWithPoints(C,color=black,linewidth=1):
        draw(C,color=color,linewidth=linewidth)
        draw(C.coords,color=color)
        drawNumbers(C.coords,color=color)

    C = BezierSpline(control=X)
    drawCurveWithPoints(C)

    if ack('Split?'):

        CL = C.splitAt([0.3,1.7,2.5])
        for i,c in  enumerate(CL):
            drawCurveWithPoints(c,color=i+1,linewidth=3)
            print("======= PART %s ========" % i)
            print(c.coords)

    else:

        D = C.insertPointsAt([0.3,1.7,2.5])
        drawCurveWithPoints(D,color=red,linewidth=3)
        print(D.coords)




if __name__ == '__draw__':
    run()
# End
