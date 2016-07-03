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
from pyformex.plugins.nurbs import *
from pyformex.plugins.curve import *
from pyformex.plugins.nurbs_menu import _options#, drawNurbs
from .NurbsCurveExamples import _decors, clearDecors, drawNurbs, nurbs_book_examples, createNurbs


def showCurve():
    """Select and show a Nurbs curve."""
    global N,dia

    if dia:
        dia.acceptData()
        res = dia.results
        curv = res['curv']
    else:
        curv = ''

    N = createNurbs(curv)
    print(N)
    drawNurbs(N,linewidth=1,color=magenta,knotsize=5)
    zoomAll()


def insertKnot():
    """Insert a knot in the knot vector of Nurbs curve N."""
    global N,dia

    dia.acceptData()
    res = dia.results
    u = eval('[%s]' % res['u'])
    N = N.insertKnots(u)
    print(N)
    drawNurbs(N,linewidth=5,color=blue,knotsize=5)
    zoomAll()


def removeKnot():
    """Remove a knot from the knot vector of Nurbs curve N."""
    global N,dia

    dia.acceptData()
    res = dia.results
    ur = res['ur']
    m = res['m']
    N = N.removeKnot(ur,m,0.001)
    print(N)
    drawNurbs(N,linewidth=5,color=blue,knotsize=5)
    zoomAll()


def removeAllKnots():
    """Remove all removable knots."""
    global N,dia

    N = N.removeAllKnots()
    print(N)
    drawNurbs(N,linewidth=5,color=blue,knotsize=5)
    zoomAll()


def elevateDegree():
    """Elevate the degree of the Nurbs curve N."""
    global N,dia

    dia.acceptData()
    res = dia.results
    nd = res['nd']
    N = N.elevateDegree(nd)
    print(N)
    drawNurbs(N,linewidth=5,color=blue,knotsize=5)
    zoomAll()


def decompose():
    """Decompose Nurbs curve N"""
    global N,C,dia

    N1 = N.decompose()
    print(N1)
    drawNurbs(N1,linewidth=5,color=red,knotsize=10,knot_values=False)
    zoomAll()
    C = BezierSpline(control=N1.coords.toCoords(), degree=N1.degree)
    draw(C, color=blue)


    for i,Ci in enumerate(C.split()):
        Ci.setProp(i)
        draw(Ci,color=i,linewidth=5)



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
                _I('curv', 'default', choices=['ex%s' % k for k in sorted(nurbs_book_examples.keys())]),
            ]),
            _G('Knot Insertion',[
                _I('u', 0.2, text='Knot value(s) to insert',tooltip='A single value or a comma separated sequence'),
            ]),
            _G('Knot Removal',[
                _I('ur', 0.2, text='Knot value to remove'),
                _I('m', 1, text='How many times to remove'),
            ]),
            _G('Degree Elevation',[
                _I('nd', 1, text='How much to elevate the degree'),
            ]),
        ], actions=[
            ('Close',close),
            ('Show Curve',showCurve),
            ('Insert Knot',insertKnot),
            ('Remove Knot',removeKnot),
            ('Remove All',removeAllKnots),
            ('Elevate Degree',elevateDegree),
            ('Decompose',decompose),
        ])
    dia.show()



if __name__ == '__draw__':
    run()

# End
