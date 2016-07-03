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

"""NurbsCurveExamples

A collection of NurbsCurve exmaples taken from the Nurbs book.

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
            drawMarks(N.knotPoints(), ["%f(%s)"%(v,m) for v,m in N.knotv.knots()], leader='  --> ')


# Example curves from the Nurbs book
nurbs_book_examples = {
    '3.1': ([
        [-12.0,-7.7],
        [-10.5,-3.7],
        [- 6.7,-3.0],
        [- 4.3,-7.6],
        ],3,),
    '3.2': ([
        [ 3.5,12.0 ],
        [ 7.0,12.0 ],
        [ 7.0,15.0 ],
        [10.5,15.0 ],
        [11.7,11.6 ],
        [ 9.5, 9.5 ],
        [ 7.0,10.7 ],
        ],3,),
    '3.3': ([
        [-12.3,12.0 ],
        [-11.5,14.3 ],
        [ -8.2,14.7 ],
        [ -9.7,10.3 ],
        [ -5.0,10.3 ],
        [ -6.6,13.2 ],
        [ -4.2,13.6 ],
        ],2,),
    '3.4': ([
        [  3.9,-6.3 ],
        [  3.7,-3.2 ],
        [  8.0,-3.2 ],
        [  5.8,-7.8 ],
        [ 12.5,-7.8 ],
        [ 11.0,-4.7 ],
        ],2,),
    '3.5': ([
        [  3.9,-6.3 ],
        [  3.7,-3.2 ],
        [  8.0,-3.2 ],
        [  5.8,-7.8 ],
        [ 12.5,-7.8 ],
        [ 11.0,-4.7 ],
        ],3,),
    '3.6': ([
        [-10.2,-5.5 ],
        [-11.4,-3.5 ],
        [- 6.6,-3.0 ],
        [- 7.8,-5.8 ],
        [- 9.0,-8.6 ],
        [- 4.5,-8.6 ],
        [- 5.2,-6.0 ],
        ],2,),
    '3.7': ([
        [-11.7, 6.5 ],
        [- 8.9, 6.5 ],
        [- 8.9, 9.5 ],
        [- 5.3, 9.1 ],
        [- 8.2, 5.2 ],
        [- 4.7, 3.6 ],
        [-10.0, 3.6 ],
        ],3,),
    '3.8a': ([
        [  3.5,-5.5 ],
        [  4.2,-4.3 ],
        [  4.6,-5.5 ],
        [  5.7,-3.2 ],
        [  7.4,-3.3 ],
        [  8.2,-7.8 ],
        [  9.7,-5.5 ],
        [ 10.4,-6.2 ],
        [ 11.8,-4.0 ],
        [ 12.5,-4.5 ],
        ],9,),
    '3.8b': ([
        [  3.5,-5.5 ],
        [  4.2,-4.3 ],
        [  4.6,-5.5 ],
        [  5.7,-3.2 ],
        [  7.4,-3.3 ],
        [  8.2,-7.8 ],
        [  9.7,-5.5 ],
        [ 10.4,-6.2 ],
        [ 11.8,-4.0 ],
        [ 12.5,-4.5 ],
        ],2,),
    '3.9': ([
        [-12.0,-6.0 ],
        [-12.3,-3.0 ],
        [- 8.0,-3.0 ],
        [- 9.3,-7.5 ],
        [- 3.5,-7.5 ],
        [- 5.0,-4.5 ],
        ],2,),
    '3.10': ([
        [-12.2, 3.7 ],
        [-12.0, 5.8 ],
        [- 9.5, 7.2 ],
        [- 8.0, 6.0 ],
        [- 8.0, 3.7 ],
        [- 6.0, 3.7 ],
        [- 4.0, 5.0 ],
        [- 5.2, 6.7 ],
        ],2,
        [0.,0.,0.,0.2,0.4,0.6,0.8,0.8,1.,1.,1.]),
    '3.11': ([
        [-12.2, 3.7 ],
        [-12.0, 5.8 ],
        [- 9.5, 7.2 ],
        [- 8.0, 6.0 ],
        [- 8.0, 3.7 ],
        [- 6.0, 3.7 ],
        [- 4.0, 3.7 ],
        [- 5.2, 6.7 ],
        ],2,
        [0.,0.,0.,0.2,0.4,0.6,0.8,0.8,1.,1.,1.]),
    '3.12': ([
        [-12.2, 3.7 ],
        [-12.0, 5.8 ],
        [- 9.5, 7.2 ],
        [- 8.0, 6.0 ],
        [- 8.0, 3.7 ],
        [- 6.0, 3.7 ],
        [- 4.0, 5.0 ],
        [- 5.2, 6.7 ],
        ],3,
        [0.,0.,0.,0.,0.25,0.5,0.75,0.75,1.,1.,1.,1.]),
     '3.13': ([
        [-12.0,-0.0 ],
        [-10.0,-4.0 ],
        [- 8.0,-1.0 ],
        [- 8.0,-1.0 ],
        [- 6.0,-4.0 ],
        [- 4.0,-0.0 ],
        ],2,),
     '3.14': ([
        [- 2.0,-6.0 ],
        [- 3.5,-2.5 ],
        [  0.0, 0.0 ],
        [  0.0, 0.0 ],
        [  3.5,-2.5 ],
        [  2.0,-6.0 ],
        ],3,
        [0.,0.,0.,0.,0.25,0.75,1.,1.,1.,1.]),
     '3.15': ([
        [- 2.0,-6.0 ],
        [- 3.5,-2.5 ],
        [  0.0, 0.0 ],
        [  0.0, 0.0 ],
        [  3.5,-2.5 ],
        [  2.0,-6.0 ],
        ],3,
        [0.,0.,0.,0.,0.50,0.50,1.,1.,1.,1.]),
   '5.37': ([
        [ 4.5,-7.8],
        [ 5.2,-3.5],
        [ 7.5,-3.5],
        [ 8.3,-6.2],
        [10.8,-6.0],
        [11.3,-2.5],
        ],3,),
    '5.39': ([
        [ 6.2,-7.3],
        [ 4.5,-6.7],
        [ 4.0,-5.2],
        [ 4.9,-3.5],
        [ 7.6,-2.5],
        [10.3,-3.3],
        [11.2,-5.0],
        [10.7,-6.7],
        [ 9.0,-7.5],
        ],4,
        [0.,0.,0.,0.,0.,1/3.,1/3.,2/3.,2/3.,1.,1.,1.,1.,1.]),
}


def createNurbs(curv):
    """Create a Nurbs curve."""
    if curv[:2] == 'ex':
        key = curv[2:]
        data = nurbs_book_examples[key]
        if len(data) > 2:
            coords,degree,knots = data
        else:
            coords,degree = data
            knots = None
        N = NurbsCurve(coords,degree=degree,knots=knots)
    else:
        C = Formex('12141214').toCurve()
        #C = Formex('214').toCurve()
        degree = 4
        N = NurbsCurve(C.coords, degree=degree)
    return N


def run():
    global N, dia
    clear()
    reset()
    flat()

    clear()
    linewidth(1)
    _options.ctrl = True
    _options.ctrl_numbers = True
    _options.ctrl_polygon = True
    _options.knot_values = True


    res = askItems([
            _I('curv', 'default', choices=['ex%s' % k for k in utils.hsorted(nurbs_book_examples.keys())]),
        ])
    if res:
        N = createNurbs(res['curv'])
        print(N)
        drawNurbs(N,linewidth=1,color=magenta,knotsize=5)
        zoomAll()


if __name__ == '__draw__':
    run()

# End
