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
_topics = ['surface','vtk']
_techniques = ['inside']

from gui.draw import *
import simple
import timer

from multi import *
def multitask(tasks,nproc=-1):
    """Perform tasks in parallel.

    Runs a number of tasks in parallel over a number of subprocesses.

    Parameters:

    - `tasks` : a list of (function,args) tuples, where function is a
      callable and args is a tuple with the arguments to be passed to the
      function.
    - ` nproc`: the number of subprocesses to be started. This may be
      different from the number of tasks to run: processes finishing a
      task will pick up a next one. There is no benefit in starting more
      processes than the number of tasks or the number of processing units
      available. The default will set `nproc` to the minimum of these two
      values.
    """
    if nproc < 0:
        nproc = min(len(tasks),cpu_count())

    pf.debug("Multiprocessing using %s processors" % nproc,pf.DEBUG.MULTI)
    pool = Pool(nproc)
    res = pool.map(dofunc,tasks)
    return res

filename = os.path.join(getcfg('datadir'),'horse.off')


def selectSurfaceFile(fn):
    fn = askFilename(fn,filter=utils.fileDescription('surface'))
    return fn


def getData():
    """Ask input data from the user."""
    dia = Dialog(
        [ _G('Surface', [
            _I('surface','file',choices=['file','sphere']),
            _I('filename',filename,text='Image file',itemtype='button',func=selectSurfaceFile),
            _I('grade',8),
            _I('refine',0),
            ]),
          _G('Points', [
              _I('points','grid',choices=['grid','random']),
              _I('npts',[30,30,30],itemtype='ivector'),
              _I('scale',[1.,1.,1.],itemptype='point'),
              _I('trl',[0.,0.,0.],itemptype='point'),
              ]),
            _I('method',choices=['gts','vtk']),
            _I('nproc',1,),
          ],
        enablers = [
            ( 'surface','file','filename', ),
            ( 'surface','sphere','grade', ),
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
    nx,ny,nz = npts

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
        return None,None

    # Create points

    if points == 'grid':
        P = simple.regularGrid([-1.,-1.,-1.],[1., 1., 1.],[nx-1,ny-1,nz-1])
    else:
        P = random.rand(nx*ny*nz*3)

    sc = array(scale)
    siz = array(S.sizes())
    tr = array(trl)
    P = Formex(P.reshape(-1, 3)).resized(sc*siz).centered().translate(tr*siz)
    draw(P, marksize=1, color='black')
    zoomAll()

    return S,P


def testInside(S,P,method,nproc=1):
    """Test which of the points P are inside surface S"""

    print("Testing %s points against %s faces" % (P.nelems(),S.nelems()))

    bb = bboxIntersection(S,P)
    drawBbox(bb,color=array(red),linewidth=2)
    P = Coords(P).points()

    t = timer.Timer()

    if method == 'vtk' and not utils.hasModule('vtk'):
        warn("You need to install python-vtk!")
        return

    if nproc == 1:
        ind = S.inside(P,method=method)

    else:
        datablocks = splitar(P,nproc)
        datalen = [0] + [d.shape[0] for d in datablocks]
        #print(datalen)
        shift = array(datalen[:-1]).cumsum()
        #print(shift)
        ind = [S.inside(d) for d in datablocks]
        indlen = array([len(i) for i in ind])
        #print(indlen,indlen.sum())
        ind = concatenate([ i+s for i,s in zip(ind,shift)])
        #print(len(ind))
        #tasks = [(S.inside,(d)) for d in datablocks]
        #ind = multitask2(tasks,nproc)
        #ind = concatenate([ i+s for i,s in zip(ind,shift)])
 
    print("%sinside: %s points / %s faces: found %s inside points in %s seconds" % (method,P.shape[0],S.nelems(),len(ind),t.seconds()))

    if len(ind) > 0:
        draw(P[ind],color=green,marksize=3,ontop=True,nolight=True,bbox='last')


def run():
    resetAll()
    clear()
    smooth()

    if getData():
        S,P = create()
        if S:
            testInside(S,P,method,nproc)


if __name__ == 'draw':
    run()
# End


