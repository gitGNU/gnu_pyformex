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
from pyformex.plugins.imagearray import saveGreyImage
from pyformex import simple


filename = os.path.join(getcfg('datadir'), 'horse.off')

def getData():
    """Ask input data from the user."""
    store = pf.PF.get('_Voxelize_data_',{
        'surface':'file',
        'filename':filename,
        'grade':8,
        'resolution':100,
    })
    res = askItems(caption="Voxelize example",store=store,items=[
        _G('Model',[
            _I('surface', choices=['file', 'sphere']),
            _I('filename', text='Image file', itemtype='filename', filter='surface', exist=True),
            _I('grade', 8),
            ]),
        _G('Scan', [
            _I('resolution',),
            ]),
        ],
        enablers = [
        ( 'surface', 'file', 'filename', ),
        ( 'surface', 'sphere', 'grade', ),
        ],
    )
    if res:
        pf.PF['_Voxelize_data_'] = res
    return res


def createSurface(surface,filename,grade,**kargs):
    """Create and draw a closed surface from input data

    """
    if surface == 'file':
        S = TriSurface.read(filename).centered()
    elif surface == 'sphere':
        S = simple.sphere(ndiv=grade)

    draw(S)

    if not S.isClosedManifold():
        warning("This is not a closed manifold surface. Try another.")
        return None
    return S


# TODO: this should be merged with opengl.drawImage3D
def showGreyImage(a):
    """Draw pixel array on the canvas"""
    F = Formex('4:0123').rep([a.shape[1], a.shape[0]], [0, 1], [1., 1.]).setProp(a)
    return draw(F)


def saveScan(scandata,surface,filename,showimages=False,**kargs):
    """Save the scandata for the surface"""
    dirname = askDirname(caption="Directory where to store the images")
    if not dirname:
        return
    chdir(dirname)
    if not checkWorkdir():
        print("Could not open directory for writing. I have to stop here")
        return

    if surface == 'sphere':
        name = 'sphere'
    else:
        name = utils.projectName(filename)
    fs = utils.NameSequence(name, '.png')

    if showimages:
        clear()
        flat()
        A = None
    for frame in scandata:
        if showimages:
            B = showGreyImage(frame*7)
            undraw(A)
            A = B
        saveGreyImage(frame*255, fs.next())


def run():
    resetAll()
    clear()
    smooth()
    lights(True)

    res = getData()
    if res:
        S = createSurface(**res)

    if S:
        nmax = res['resolution']
        vox,P = S.voxelize(nmax,return_formex=True)
        scale = P.sizes() / array(vox.shape)
        origin = P.bbox()[0]
        print("Box size: %s" % P.sizes())
        print("Data size: %s " % array(vox.shape))
        print("Scale: %s" % scale)
        print("Origin: %s" % P.bbox()[0])
        draw(P, marksize=5)
        transparent()
        saveScan(vox,showimages=True,**res)


# The following is to make it work as a script
if __name__ == '__draw__':
    run()


# End
