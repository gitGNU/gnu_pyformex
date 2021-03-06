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
from pyformex.odict import OrderedDict


ctype_color = [ 'red', 'green', 'blue', 'cyan', 'magenta', 'yellow', 'white' ]
point_color = [ 'black', 'white' ]

open_or_closed = { True:'A closed', False:'An open' }

TA = None


curvetypes = [
    'PolyLine',
    'BezierSpline',
    'BezierSpline2',
    'NaturalSpline',
    'NurbsCurve',
]



def drawCurve(ctype,dset,closed,degree,endcond,curl,nseg,chordal,method,approx,extend,scale=None,cutWP=False,frenet=False,avgdir=True,upvector=None,sweep=False):
    global S, TA
    P = dataset[dset]
    text = "%s %s with %s points" % (open_or_closed[closed], ctype.lower(), len(P))
    if TA is not None:
        undecorate(TA)
    TA = drawText(text, (10, 20), size=20)
    draw(P, color='black', nolight=True)
    drawNumbers(Formex(P))
    if ctype == 'PolyLine':
        S = PolyLine(P, closed=closed)
    elif ctype == 'BezierSpline':
        S = BezierSpline(P, degree=degree, curl=curl, closed=closed, endzerocurv=(endcond, endcond))
    elif ctype == 'BezierSpline2':
        S = BezierSpline(P, degree=2, closed=closed)
    elif ctype == 'NaturalSpline':
        S = NaturalSpline(P, closed=closed, endzerocurv=(endcond, endcond))
        directions = False
    elif ctype == 'NurbsCurve':
        S = NurbsCurve(P, closed=closed)#,blended=closed)
        scale = None
        directions = False
        drawtype = 'Curve'

    if scale:
        S = S.scale(scale)

    im = curvetypes.index(ctype)
    print("%s control points" % S.coords.shape[0])
    draw(S.approx(),color=black)

    if approx:
        print(method)
        if method == 'chordal':
            nseg = None

        PL = S.approx(nseg=nseg,chordal=chordal,equidistant=method=='equidistant')

        if cutWP:
            PC = PL.cutWithPlane([0., 0.42, 0.], [0., 1., 0.])
            draw(PC[0], color=red)
            draw(PC[1], color=green)
        else:
            draw(PL, color=ctype_color[im])
        draw(PL.pointsOn(), color=black)

    if approx:
        C = PL
    else:
        C = S

    if frenet:
        X, T, N, B = C.frenet(upvector=upvector, avgdir=avgdir)[:4]
        drawVectors(X, T, size=1., nolight=True, color='red')
        drawVectors(X, N, size=1., nolight=True, color='green')
        drawVectors(X, B, size=1., nolight=True, color='blue')
        if  C.closed:
            X, T, N, B = C.frenet(upvector=upvector, avgdir=avgdir, compensate=True)[:4]
            drawVectors(X, T, size=1., nolight=True, color='magenta')
            drawVectors(X, N, size=1., nolight=True, color='yellow')
            drawVectors(X, B, size=1., nolight=True, color='cyan')

    if sweep and isinstance(C,Curve):
        F = Formex('l:b').mirror(2)
        draw(F)
        F = C.sweep(F.scale(0.05*C.dsize()))
        smoothwire()
        draw(F,color=red,mode='smoothwire')


dataset = [
    Coords([[1., 0., 0.], [0., 1., 0.], [-1., 0., 0.],  [0., -1., 0.]]),
    Coords([[6., 7., 12.], [9., 5., 6.], [11., -2., 6.],  [9.,  -4., 14.]]),
    Coords([[-5., -10., -4.], [-3., -5., 2.], [-4., 0., -4.], [-4.,  5, 4.],
            [6., 3., -1.], [6., -9., -1.]]),
    Coords([[-1., 7., -14.], [-4., 7., -8.], [-7., 5., -14.], [-8., 2., -14.],
            [-7.,  0, -6.], [-5., -3., -11.], [-7., -4., -11.]]),
    Coords([[-1., 1., -4.], [1., 1., 2.], [2.6, 2., -4.], [2.9,  3.5, 4.],
            [2., 4., -1.], [1., 3., 1.], [0., 0., 0.], [0., -3., 0.],
            [2., -1.5, -2.], [1.5, -1.5, 2.], [0., -8., 0.], [-1., -8., -1.],
            [3., -3., 1.]]),
    Coords([[0., 1., 0.], [0., 0.1, 0.], [0.1, 0., 0.],  [1., 0., 0.]]),
    Coords([[0., 1., 0.], [0., 0., 0.], [0., 0., 0.], [1., 0., 0.]]),
    Coords([[0., 0., 0.], [1., 0., 0.], [1., 1., 1.], [0., 1., 0.]]).scale(3),
    Coords([
[  1.49626994, 30.21483994,  17.10247993],
[  9.15044022, 27.19248009, 15.05076027],
[ 15.75351048, 24.26766014, 12.36573982],
[ 13.35517025, 17.80452919,  9.27042007],
[ 31.15517044, 18.58106995,  0.63323998],
[ 27.05437088, -0.60475999, -2.6461401 ],
[  7.66548014, -12.33625031, 17.51568985],
[ -3.34934998, -12.35941029, 28.64728928],
[ -9.86301041, -10.66467953, 38.48815918],
[ -19.86301041, -10.66467953, 0.],
[ -19.86301041, 10.66467953, 0.],
[ -19.86301041, 10.66467953, 10.],
]),
    ]

_items = [
    _I('DataSet', '0', choices=[str(i) for i in range(len(dataset))]),
    _I('CurveType', choices=curvetypes),
    _I('Closed', False),
    _I('Degree', 3, min=1, max=3),
    _I('Curl', 1./3.),
    _I('EndCurvatureZero', False),
    _G('Approximation', [
        _I('Method', choices=['chordal','parametric','equidistant']),
        _I('Chordal', 0.01),
        _I('Nseg', 4),
        ], checked=False),
    _I('ExtendAtStart', 0.0),
    _I('ExtendAtEnd', 0.0),
    _I('Scale', [1.0, 1.0, 1.0]),
    _I('CutWithPlane', False),
    _I('Clear', True),
    _G('FrenetFrame', [
        _I('AvgDirections', True),
        _I('AutoUpVector', True),
        _I('UpVector', [0., 0., 1.]),
        ], checked=False),
    _I('Sweep', False),
    ]

_enablers = [
    ('CurveType', 'BezierSpline', 'Degree', 'Curl', 'EndCurvatureZero'),
    ('Method', 'chordal', 'Chordal'),
    ('Method', 'parametric', 'Nseg'),
    ('Method', 'equidistant', 'Nseg'),
    ('AutoUpVector', False, 'UpVector'),
    ]


clear()
setDrawOptions({'bbox':'auto','view':'front'})
linewidth(2)
flat()

dialog = None

from pyformex import script

#
# TODO: closing the window (by a button) should also
#       call a function to release the scriptlock!
#
def close():
    global dialog
    if dialog:
        dialog.close()
        dialog = None
    # Release script lock
    scriptRelease(__file__)



def show(all=False):
    dialog.acceptData()
    res = dialog.results
    if res['AutoUpVector']:
        res['UpVector'] = None
    globals().update(res)
    export({'_Curves_data_':res})
    if Clear:
        clear()
    if all:
        Types = curvetypes
    else:
        Types = [CurveType]
    setDrawOptions({'bbox':'auto'})
    for Type in Types:
        drawCurve(Type, int(DataSet), Closed, Degree, EndCurvatureZero, Curl, Nseg, Chordal, Method, Approximation, [ExtendAtStart, ExtendAtEnd], Scale, CutWithPlane, FrenetFrame, AvgDirections, UpVector, Sweep)
        setDrawOptions({'bbox':None})

def showAll():
    show(all=True)

def timeOut():
    showAll()
    wait()
    close()


def run():
    global dialog
    dialog = Dialog(
        items=_items,
        enablers=_enablers,
        caption='Curve parameters',
        actions = [('Close', close), ('Clear', clear), ('Show All', showAll), ('Show', show)],
        default='Show')

    if '_Curves_data_' in pf.PF:
        #print pf.PF['_Curves_data_']
        dialog.updateData(pf.PF['_Curves_data_'])

    dialog.timeout = timeOut
    dialog.show()
    # Block other scripts
    scriptLock(__file__)



if __name__ == '__draw__':
    run()
# End
