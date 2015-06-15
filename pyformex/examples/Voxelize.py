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

"""Voxelize

This example illustrates the use of the gtsinside program to create a
voxelization of a closed surface.
"""
from __future__ import print_function


_status = 'checked'
_level = 'advanced'
_topics = ['surface']
_techniques = ['voxelize', 'image']

from pyformex.gui.draw import *
from pyformex.plugins.imagearray import *
from pyformex import simple


def showGreyImage(a):
    F = Formex('4:0123').rep([a.shape[1], a.shape[0]], [0, 1], [1., 1.]).setProp(a)
    return draw(F)

def saveBinaryImage(a, f):
    c = flipud(a)
    c = dstack([c, c, c])
    im = numpy2qimage(c)
    im.save(f)


def voxelize(self,n,bbox=0.01,return_formex=False):
    """Voxelize the volume inside a closed surface.

    Parameters:

    - `n`: int or (int, int, int): resolution, i.e. number of voxel cells
      to use along the three axes.
      If a single int is specified, the number of cells will be adapted
      according to the surface's :meth:`sizes` (as the voxel cells are always
      cubes). The specified number of voxels will be use along the largest
      direction.
    - `bbox`: float or (point,point): defines the bounding box of the volume
      that needs to be voxelized. A float specifies a relative amount to add
      to the surface's boundibng box. Note that this defines the bounding box
      of the centers of the voxels.
    - `return_formex`: bool; if True, also returns a Formex with the centers
      of the voxels, and property 0 or 1 if the point is repsectively outside
      or inside the surface.

    Returns a plex-1 Formex with the centers of the voxels and property value
    set to 0 for points outside the surface, and to 1 for points inside the
    surface. The voxel cell ordering is in z-direction first, then y, then x.

    """
    if not self.isClosedManifold():
        raise ValueError("The surface is non a closed manifold")

    if isFloat(bbox):
        a,b = 1.0+bbox, bbox
        bbox = self.bbox()
        bbox = [ a*bbox[0]-b*bbox[1], a*bbox[1]-b*bbox[0]]
    bbox = checkArray(bbox,shape=(2,3),kind='f')

    if isInt(n):
        sz = bbox[1]-bbox[0]
        step = sz.max() / (n-1)
        n = ceil(sz / step).astype(Int)
    n = checkArray(n,shape=(3,),kind='i')
    X = simple.regularGrid(bbox[0], bbox[0]+n*step, n)
    ind = self.inside(X)
    vox = zeros(n+1, dtype=uint8)
    vox.ravel()[ind] = 1
    if return_formex:
        P = Formex(X.reshape(-1,3))
        P.setProp(vox)
        return vox,P
    return vox


def run():
    reset()
    smooth()
    lights(True)

    S = TriSurface.read(getcfg('datadir')+'/horse.off')
    SA = draw(S)

    store = pf.PF.get('_Voxelize_data_',{'Resolution':100})
    res = askItems(store=store,items=[
        _I('Resolution',),
        ])
    if not res:
        return

    pf.PF['_Voxelize_data_'] = res

    nmax = res['Resolution']
    vox,P = voxelize(S,nmax,return_formex=True)
    draw(P, marksize=5)
    transparent()

    dirname = askDirname()
    if not dirname:
        return

    chdir(dirname)
    # Create output file
    if not checkWorkdir():
        print("Could not open a directory for writing. I have to stop here")
        return

    fs = utils.NameSequence('horse', '.png')
    clear()
    flat()
    A = None
    for frame in vox:
        B = showGreyImage(frame)
        saveBinaryImage(frame*255, fs.next())
        undraw(A)
        A = B

# The following is to make it work as a script
if __name__ == '__draw__':
    run()


# End
