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
"""Inside

This example shows how to find out if points are inside a closed surface.

"""
from __future__ import print_function

_status = 'checked'
_level = 'normal'
_topics = ['surface', 'vtk']
_techniques = ['inside']

from pyformex.gui.draw import *
from pyformex import zip
from pyformex import simple
from pyformex import timer
from pyformex.multi import *

filename = os.path.join(getcfg('datadir'), 'horse.off')


def selectSurfaceFile(field):
    fn = askFilename(field.value(), filter='surface')
    return fn


def getData():
    """Ask input data from the user."""
    dia = Dialog(
        [ _G('Surface', [
            _I('surface', 'file', choices=['file', 'sphere']),
            _I('filename', filename, text='Image file', itemtype='button', func=selectSurfaceFile),
            _I('grade', 8),
            _I('refine', 0),
            ]),
          _G('Points', [
              _I('points', 'grid', choices=['grid', 'random']),
              _I('npts', [30, 30, 30], itemtype='ivector'),
              _I('scale', [1., 1., 1.], itemptype='point'),
              _I('trl', [0., 0., 0.], itemptype='point'),
              ]),
            _I('method', choices=['gts', 'vtk']),
            _I('atol', 0.001),
            _I('nproc', 1,),
          ],
        enablers = [
            ( 'surface', 'file', 'filename', ),
            ( 'surface', 'sphere', 'grade', ),
            ],
        )
    if 'Inside_data' in pf.PF:
        dia.updateData(pf.PF['Inside_data'])
    res = dia.getResults()
    if res:
        globals().update(res)
        pf.PF['Inside_data'] = res

    return res


def create():
    """Create a closed surface and a set of points."""
    nx, ny, nz = npts

    # Create surface
    if surface == 'file':
        S = TriSurface.read(filename).centered()
    elif surface == 'sphere':
        S = simple.sphere(ndiv=grade)

    if refine > S.nedges():
        S = S.refine(refine)

    draw(S, color='red')

    if not S.isClosedManifold():
        warning("This is not a closed manifold surface. Try another.")
        return None, None

    # Create points

    if points == 'grid':
        P = simple.regularGrid([-1., -1., -1.], [1., 1., 1.], [nx-1, ny-1, nz-1])
    else:
        P = random.rand(nx*ny*nz*3)

    sc = array(scale)
    siz = array(S.sizes())
    tr = array(trl)
    P = Formex(P.reshape(-1, 3)).resized(sc*siz).centered().translate(tr*siz)
    draw(P, marksize=1, color='black')
    zoomAll()

    return S, P


def inside(S, P, method, atol):
    return S.inside(P, method=method, tol=atol, multi=False)


def testInside(S, P, method, nproc, atol):
    """Test which of the points P are inside surface S"""

    print("Testing %s points against %s faces" % (P.nelems(), S.nelems()))

    bb = bboxIntersection(S, P)
    drawBbox(bb, color=array(red), linewidth=2)
    P = Coords(P).points()

    t = timer.Timer()

    if method == 'vtk' and not utils.hasModule('vtk'):
        warning("You need to install python-vtk!")
        return

    if nproc == 1:
        ind = inside(S, P, method, atol)

    else:
        datablocks = splitar(P, nproc)
        datalen = [0] + [d.shape[0] for d in datablocks]
        shift = array(datalen[:-1]).cumsum()
        #print("METH %s" % method)
        tasks = [(inside, (S, d, method, atol)) for d in datablocks]
        ind = multitask(tasks, nproc)
        ind = concatenate([ i+s for i, s in zip(ind, shift)])

    print("%sinside: %s points / %s faces: found %s inside points in %s seconds" % (method, P.shape[0], S.nelems(), len(ind), t.seconds()))

    if len(ind) > 0:
        draw(P[ind], color=green, marksize=3, ontop=True, nolight=True, bbox='last')


def run():
    resetAll()
    clear()
    smooth()

    if getData():
        S, P = create()
        if S:
            print(method)
            testInside(S, P, method, nproc, atol)


if __name__ == '__draw__':
    run()
# End


