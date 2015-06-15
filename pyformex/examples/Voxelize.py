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
    vox,P = S.voxelize(nmax,return_formex=True)
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
