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
- curve decomposing
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

class _decors:
    ctrl_numbers = None


def clearDecors():
    undraw(_decors.ctrl_numbers)

# TODO: This function should be merged with plugins.nurbs_menu.drawNurbs
def drawNurbs(N,**kargs):
    """Draw the Nurbs curve N, with options"""
    clear()
    if not isinstance(N,NurbsCurve):
        return
    for k in kargs:
        setattr(_options,k,kargs[k])

    clearDecors()
    draw(N, color=_options.color, nolight=True)
    if _options.ctrl:
        draw(N.coords.toCoords(), color=_options.color, nolight=True)
        if _options.ctrl_polygon:
            draw(PolyLine(N.coords.toCoords()), color=_options.color, nolight=True)
        if _options.ctrl_numbers:
            _decors.ctrl_numbers = drawNumbers(N.coords.toCoords())
    if _options.knots:
        draw(N.knotPoints(), color=_options.color, marksize=_options.knotsize)
        if _options.knot_numbers:
            drawNumbers(N.knotPoints())
        if _options.knot_values:
            drawMarks(N.knotPoints(), ["%f"%i for i in N.knots], leader='  --> ')


def createNurbs():
    """Create a Nurbs curve."""
    global N,dia

    # TODO: these data could be customized from the dialog
    C = Formex('12141214').toCurve()
    #C = Formex('214').toCurve()
    degree = 4
    N = NurbsCurve(C.coords, degree=degree)#,blended=False)
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
    """Insert a knot in the knot vector of Nurbs curve N."""
    global N,dia

    dia.acceptData()
    res = dia.results
    ur = res['ur']
    m = res['m']
    N = N.removeKnot(ur,m,0.001)
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

    createNurbs()

    if dia:
        dia.close()
    dia = Dialog([
            _G('Knot Insertion',[
                _I('u', 0.2, text='Knot value(s) to insert',tooltip='A single value or a comma separated sequence'),
            ]),
            _G('Knot Removal',[
                _I('ur', 0.2, text='Knot value to remove'),
                _I('m', 1, text='How many times to remove'),
            ]),
        ], actions=[
            ('Close',close),
            ('Insert Knot',insertKnot),
            ('Remove Knot',removeKnot),
            ('Decompose',decompose),
        ])
    dia.show()



if __name__ == '__draw__':
    run()

# End
