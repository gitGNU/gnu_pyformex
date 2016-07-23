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

_options.color = blue
_options.pcolor = magenta
_options.ctrl = True



class _decors:
    ctrl_numbers = None
    knot_values = None


def clearDecors():
    undraw(_decors.ctrl_numbers)
    undraw(_decors.knot_values)


# TODO: This function should be merged with plugins.nurbs_menu.drawNurbs
def drawNurbs(N,clear=True,**kargs):
    """Draw the Nurbs curve N, with options"""
    if not isinstance(N,NurbsCurve):
        return
    for k in kargs:
        setattr(_options,k,kargs[k])

    clearDecors()
    draw(N, clear=clear, color=_options.color, nolight=True)
    if _options.ctrl:
        draw(N.coords.toCoords(), color=_options.pcolor, nolight=True)
        if _options.ctrl_polygon:
            draw(PolyLine(N.coords.toCoords()), color=_options.pcolor, nolight=True)
        if _options.ctrl_numbers:
             _decors.ctrl_numbers = drawNumbers(N.coords.toCoords())
    if _options.knots:
        draw(N.knotPoints(), color=_options.color, marksize=_options.knotsize)
#        if _options.knot_numbers:
#           _decors.knot_numbers = drawNumbers(N.knotPoints())
        if _options.knot_values:
           _decors.knot_values = drawMarks(N.knotPoints(), ["%f(%s)"%(v,m) for v,m in N.knotv.knots()], leader='  --> ')


# Example curves from the Nurbs book
nurbs_book_examples = {
    'pt3.1': ([
        [-12.0,-7.7],
        [-10.5,-3.7],
        [- 6.7,-3.0],
        [- 4.3,-7.6],
        ],3,),
    'pt3.2': ([
        [ 3.5,12.0 ],
        [ 7.0,12.0 ],
        [ 7.0,15.0 ],
        [10.5,15.0 ],
        [11.7,11.6 ],
        [ 9.5, 9.5 ],
        [ 7.0,10.7 ],
        ],3,),
    'pt3.3': ([
        [-12.3,12.0 ],
        [-11.5,14.3 ],
        [ -8.2,14.7 ],
        [ -9.7,10.3 ],
        [ -5.0,10.3 ],
        [ -6.6,13.2 ],
        [ -4.2,13.6 ],
        ],2,),
    'pt3.4': ([
        [  3.9,-6.3 ],
        [  3.7,-3.2 ],
        [  8.0,-3.2 ],
        [  5.8,-7.8 ],
        [ 12.5,-7.8 ],
        [ 11.0,-4.7 ],
        ],2,),
    'pt3.5': ([
        [  3.9,-6.3 ],
        [  3.7,-3.2 ],
        [  8.0,-3.2 ],
        [  5.8,-7.8 ],
        [ 12.5,-7.8 ],
        [ 11.0,-4.7 ],
        ],3,),
    'pt3.6': ([
        [-10.2,-5.5 ],
        [-11.4,-3.5 ],
        [- 6.6,-3.0 ],
        [- 7.8,-5.8 ],
        [- 9.0,-8.6 ],
        [- 4.5,-8.6 ],
        [- 5.2,-6.0 ],
        ],2,),
    'pt3.7': ([
        [-11.7, 6.5 ],
        [- 8.9, 6.5 ],
        [- 8.9, 9.5 ],
        [- 5.3, 9.1 ],
        [- 8.2, 5.2 ],
        [- 4.7, 3.6 ],
        [-10.0, 3.6 ],
        ],3,),
    'pt3.8a': ([
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
    'pt3.8b': ([
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
    'pt3.9': ([
        [-12.0,-6.0 ],
        [-12.3,-3.0 ],
        [- 8.0,-3.0 ],
        [- 9.3,-7.5 ],
        [- 3.5,-7.5 ],
        [- 5.0,-4.5 ],
        ],2,),
    'pt3.10': ([
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
    'pt3.11': ([
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
    'pt3.12': ([
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
    'pt3.13': ([
        [-12.0,-0.0 ],
        [-10.0,-4.0 ],
        [- 8.0,-1.0 ],
        [- 8.0,-1.0 ],
        [- 6.0,-4.0 ],
        [- 4.0,-0.0 ],
        ],2,),
    'pt3.14': ([
        [- 2.0,-6.0 ],
        [- 3.5,-2.5 ],
        [  0.0, 0.0 ],
        [  0.0, 0.0 ],
        [  3.5,-2.5 ],
        [  2.0,-6.0 ],
        ],3,
        [0.,0.,0.,0.,0.25,0.75,1.,1.,1.,1.]),
    'pt3.15': ([
        [- 2.0,-6.0 ],
        [- 3.5,-2.5 ],
        [  0.0, 0.0 ],
        [  0.0, 0.0 ],
        [  3.5,-2.5 ],
        [  2.0,-6.0 ],
        ],3,
        [0.,0.,0.,0.,0.50,0.50,1.,1.,1.,1.]),
    'pt5.27': ([
        [ 3.6, 5.2],
        [ 3.4, 6.5],
        [ 4.5, 8.2],
        [ 6.3, 8.7],
        [ 7.0, 8.6],
        [ 7.7, 8.5],
        [ 8.1, 8.2],
        [ 8.8, 6.7],
        [ 8.6, 5.2],
        [11.0, 5.2],
        ],3,
        [0.,0.,0.,0.,0.3,0.5,0.5,0.5,0.7,0.7,1.,1.,1.,1.]),
    'pt5.29': ([
        [ 4.2,-6.8],
        [ 5.5,-6.8],
        [ 6.7,-5.8],
        [ 7.2,-3.4],
        [ 8.5,-2.4],
        [10.0,-2.4],
        [11.2,-3.1],
        [11.7,-4.5],
        [11.0,-5.7],
        [ 9.3,-6.1],
        [ 8.0,-6.1],
        ],3,
        [0.,0.,0.,0.,0.16,0.31,0.45,0.5501,0.702,0.8,0.901,1.,1.,1.,1.]),
    'pt5.35': ([
        [ 5.5,-7.4],
        [ 4.5,-5.0],
        [ 6.3,-2.5],
        [ 9.8,-2.5],
        [11.5,-4.6],
        [10.5,-7.4],
        ],3,
        [0.,0.,0.,0.,0.3,0.7,1.,1.,1.,1.]),
    'pt5.37': ([
        [ 4.5,-7.8],
        [ 5.2,-3.5],
        [ 7.5,-3.5],
        [ 8.3,-6.2],
        [10.8,-6.0],
        [11.3,-2.5],
        ],3,),
    'pt5.39': ([
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
    'pt5.40a': ([
        [ 4.0,-7.8],
        [ 4.0,-4.8],
        [ 5.8,-4.8],
        [ 5.8,-6.2],
        [ 8.7,-6.2],
        [ 8.7,-3.5],
        [11.0,-3.5],
        [11.0,-6.5],
        ],7,
        ),
    'pt5.40b': ([
        [ 4.2, 6.7],
        [ 4.2,10.4],
        [ 6.6,10.4],
        [ 6.6, 8.0],
        [11.0, 8.0],
        [11.0,11.0],
        [ 7.8,11.0],
        ],6,
        ),
    'pt5.41': ([
        [- 9.3, 2.7],
        [-10.6, 2.7],
        [-11.3, 3.3],
        [-11.8, 4.8],
        [-11.3, 6.2],
        [-10.0, 7.3],
        [- 9.1, 7.0],
        [- 8.2, 6.0],
        [- 7.7, 4.8],
        [- 6.7, 3.8],
        [- 5.9, 3.6],
        [- 4.6, 4.6],
        [- 4.0, 6.0],
        [- 4.5, 7.5],
        [- 5.2, 8.0],
        [- 6.5, 8.0],
        ],5,
        [0,0,0,0,0,0,0.15,0.15,0.3,0.3,0.5,0.5,0.7,0.7,0.85,0.85,1,1,1,1,1,1]),
    'pt5.42': ([
        [- 2.8, 0.0],
        [- 0.8, 0.0],
        [- 0.8, 3.0],
        [- 2.8, 3.0],
        [- 2.8, 6.0],
        [  2.8, 6.0],
        [  2.8, 3.0],
        [  0.8, 3.0],
        [  0.8, 0.0],
        [  2.8, 0.0],
        ],3,
        [0,0,0,0,0.3,0.3,0.5,0.5,0.7,0.7,1,1,1,1]),
    'pt12.1a': ([
        [-12.0,-6.3],
        [-11.0,-3.9],
        [- 8.9,-3.0],
        [- 7.0,-4.3],
        [- 6.3,-6.2],
        [- 4.4,-7.0],
        ],2,
        [-3,-2,-1,0,1,2,3,4,5]),
    'pt12.1b': ([
        [-12.0, 7.3],
        [-11.4,10.6],
        [- 8.2,10.6],
        [- 7.5, 7.3],
        [- 4.3, 6.6],
        ],3,
        [-3,-2,-1,0,1,2,3,4,5]),
    'pt12.2': ([
        [  6.5,-3.0],
        [  5.3,-6.1],
        [  8.3,-9.3],
        [ 11.4,-6.2],
        [ 10.2,-3.0],
        ],3,
        [0,1,2,3,4,5,6,7,8,9,10,11],True),
    'ze229_1': ([
        [ 50, 40, 0, 20],
        [ 10, 40, 0, 10],
        [ 48, 70, 0, 12],
        [175,100, 0, 25],
        [ 65, 26, 0, 13],
        ],4,
        [1.1, 2.2, 3.3, 4.2, 4.8, 6, 6.7, 8.5, 9, 11]),
}


def createNurbs(curv):
    """Create a Nurbs curve."""
    if curv in nurbs_book_examples:
        data = nurbs_book_examples[curv]
        knots = None
        closed = False
        print("LEN %s" % len(data))
        if len(data) == 4:
            coords,degree,knots,closed = data
            print("CLOSED %s" % closed)
        elif len(data) == 3:
            coords,degree,knots = data
        else:
            coords,degree = data
        N = NurbsCurve(coords,degree=degree,knots=knots,closed=closed)
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
            _I('curv', 'default', choices=['%s' % k for k in utils.hsorted(nurbs_book_examples.keys())]),
        ])
    if res:
        N = createNurbs(res['curv'])
        print(N)
        print("This Nurbs uses a%sclamped knot vector" % (' ' if N.isClamped() else 'n un'))
        drawNurbs(N,linewidth=1,color=magenta,knotsize=5)
        zoomObj(N)


if __name__ == '__draw__':
    run()

# End
