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

"""NurbsDecompose

Illustrates some special techniques on Nurbs Curves:

- inserting knots
- removing knots
- curve decomposing
- degree elevation
"""
from __future__ import print_function


_status = 'checked'
_level = 'advanced'
_topics = ['Geometry', 'Curve']
_techniques = ['nurbs']

from pyformex.gui.draw import *
from pyformex.plugins.nurbs_menu import _options#, drawNurbs
from pyformex.plugins.curve import BezierSpline
from pyformex.examples.NurbsCurveExamples import drawNurbs, nurbs_book_examples, createNurbs
from pyformex import simple

from pyformex.lib.nurbs import BezDegreeReduce#, curveDegreeReduce
from pyformex.lib import nurbs
#nurbs.curveDegreeReduce = curveDegreeReduce


def showCurve(reverse=False):
    """Select and show a Nurbs curve."""
    global N,dia

    if dia:
        dia.acceptData()
        res = dia.results
        curv = res['curv']
    else:
        curv = ''

    N = createNurbs(curv)
    if reverse:
        N = N.reverse()
    print(N)
    drawNurbs(N,color=blue,knotsize=5)
    zoomAll()


def showReverse():
    showCurve(reverse=True)


def insertKnot():
    """Insert a knot in the knot vector of Nurbs curve N."""
    global N,dia

    dia.acceptData()
    res = dia.results
    u = eval('[%s]' % res['u'])
    N = N.insertKnots(u)
    print(N)
    drawNurbs(N,color=red,knotsize=5)
    zoomAll()


def removeKnot():
    """Remove a knot from the knot vector of Nurbs curve N."""
    global N,dia

    dia.acceptData()
    res = dia.results
    ur = res['ur']
    m = res['m']
    tol = res['tol']
    N = N.removeKnot(ur,m,tol)
    print(N)
    drawNurbs(N,color=blue,knotsize=5)
    zoomAll()


def removeAllKnots():
    """Remove all removable knots."""
    global N,dia

    dia.acceptData()
    res = dia.results
    tol = res['tol']
    N = N.removeAllKnots(tol=tol)
    print(N)
    drawNurbs(N,color=blue)
    zoomAll()


def elevateDegree():
    """Elevate the degree of the Nurbs curve N."""
    global N,dia

    dia.acceptData()
    res = dia.results
    nd = res['nd']
    if nd > 0:
        N = N.elevateDegree(nd)
    elif nd < 0:
        N = N.reduceDegree(-nd)
    else:
        return
    print(N)
    draw(N,color=cyan,linewidth=3)
    zoomAll()


def decompose():
    """Decompose Nurbs curve N"""
    global N,C,dia

    N1 = N.decompose()
    print(N1)
    drawNurbs(N1,color=black,knotsize=10,knot_values=False)
    zoomAll()
    C = BezierSpline(control=N1.coords.toCoords(), degree=N1.degree)
    #draw(C, color=blue)

    for i,Ci in enumerate(C.split()):
        print(Ci)
        Ci.setProp(i)
        draw(Ci,color=i,linewidth=5)


def projectPoints():
    """Project points on the NurbsCurve N"""
    global N,dia

    dia.acceptData()
    res = dia.results
    npts = res['npts']
    show_distance = res['show_distance']

    X = simple.randomPoints(npts,N.bbox())
    draw(X,marksize=5)

    for Xi in X:
        u,P = N.projectPoint(Xi)
        draw(Formex([[P,Xi]]),color=red)
        if show_distance:
            d = at.length(P-Xi)
            drawText("%s" %d, 0.5*(P+Xi))


def close():
    global dia
    dia.close()
    dia = None


dia = None

def run():
    global N, dia
    clear()
    flat()

    clear()
    linewidth(1)
    _options.ctrl = True
    _options.ctrl_numbers = True
    _options.ctrl_polygon = True
    _options.knot_values = True


    createNurbs('default')

    if dia:
        dia.close()
    dia = Dialog([
            _G('Curve Selection',[
                _I('curv', 'default', choices=sorted(nurbs_book_examples.keys()),
                   buttons=[('Show Curve',showCurve),('Show Reverse',showReverse)]),
            ]),
            _G('Knot Insertion',[
                _I('u', 0.5, text='Knot value(s) to insert',                   buttons=[('Insert Knot',insertKnot)]),
            ]),
            _G('Knot Removal',[
                _I('ur', 0.5, text='Knot value to remove'),
                _I('m', 1, text='How many times to remove',buttons=[('Remove Knot',removeKnot)]),
                _I('tol', 0.001, text='Tolerance',buttons=[('Remove All Knots',removeAllKnots)]),
            ]),
            _G('Degree Elevation/Reduction',[
                _I('nd', 1, text='How much to elevate/reduce the degree',buttons=[('Change Degree',elevateDegree)]),
            ]),
            _G('Point Projection',[
                _I('npts', 10, text='How many points to project',buttons=[('Project Points',projectPoints)]),
                _I('show_distance', True, text='Show distance'),
            ]),
        ], actions=[
            ('Close',close),
            ('Decompose',decompose),
        ])
    dia.show()



if __name__ == '__draw__':
    run()

# End
