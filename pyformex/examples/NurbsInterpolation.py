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

"""NurbsInterpolation

This example illustrates the creation of NurbsCurves interpolating or
approximating a given point set.
"""
from __future__ import absolute_import, division, print_function


_status = 'checked'
_level = 'advanced'
_topics = ['geometry', 'curve']
_techniques = ['nurbs', 'connect', 'border', 'frenet']

from pyformex.gui.draw import *
from pyformex import simple
from pyformex.plugins.curve import *
from pyformex.plugins.nurbs import *



point_sets = {
#    'pt_9.1': [
#        ( 3.5,),
#        ( 4.9,),
#        ( 7.0,),
#        ( 9.0,),
#        (11.0,),
#    ],
    'pt_9.3': [
        ( 3.9,-6.4),
        ( 4.0,-5.2),
        ( 5.3,-3.5),
        ( 8.0,-4.2),
        ( 9.4,-5.6),
        (10.7,-5.3),
        (12.2,-5.5),
    ],
    'pt_9.7': [
        (-12.1,-8.6),
        (-12.1,-7.8),
        (-12.1,-4.9),
        (-12.1,-4.0),
        (-10.7,-2.6),
        (- 9.3,-2.6),
        (- 8.6,-3.3),
        (- 8.6,-4.0),
        (- 8.6,-4.8),
        (- 7.9,-5.6),
        (- 7.2,-5.6),
        (- 4.4,-5.6),
        (- 3.5,-5.6),
    ],
}

point_patterns = [
    '51414336',
    '51i4143I36',
    '2584',
    '25984',
    '184',
    '514',
    '1234',
    '5858585858',
    '12345678',
    '121873',
    '1218973',
    '8585',
    '85985',
    '214121',
    '214412',
    '151783',
    'ABCDABCD',
    ]


def drawNurbs(points,degree,strategy,Clear=False):
    if Clear:
        clear()

    print("Selected poin t set: %s" % points)
    if points in point_sets:
        X = Coords(point_sets[points])
    else:
        X = pattern(points)
    F = Formex(X)
    draw(F, marksize=10, bbox='auto', view='front')
    drawNumbers(F, prefix='P', trl=[0.02, 0.02, 0.])
    N = globalInterpolationCurve(X, degree=degree, strategy=strategy)
    draw(N, color=degree)


dialog = None


def close():
    global dialog
    if dialog:
        dialog.close()
        dialog = None
    # Release script lock
    scriptRelease(__file__)


def show():
    dialog.acceptData()
    res = dialog.results
    export({'_Nurbs_data_':res})
    drawNurbs(**res)

def showAll():
    dialog.acceptData()
    res = dialog.results
    export({'_Nurbs_data_':res})
    for points in predefined:
        print(res)
        res['points'] = points
        drawNurbs(**res)


def timeOut():
    showAll()
    wait()
    close()

data_items = [
    _I('points', text='Point set', choices=utils.hsorted(point_sets.keys()) + point_patterns ),
    _I('degree', 3),
    _I('strategy', 0.5),
    _I('Clear', True),
    ]


def run():
    global dialog
    clear()
    setDrawOptions({'bbox':None})
    linewidth(2)
    flat()

    ## Closing this dialog should release the script lock
    dialog = Dialog(
        data_items,
        caption = 'Nurbs parameters',
        actions = [('Close', close), ('Clear', clear), ('Show All', showAll), ('Show', show)],
        default = 'Show',
        )

    if '_Nurbs_data_' in pf.PF:
        dialog.updateData(pf.PF['_Nurbs_data_'])

    dialog.timeout = timeOut
    dialog.show()

    # Block other scripts
    scriptLock(__file__)


if __name__ == '__draw__':
    run()
# End
