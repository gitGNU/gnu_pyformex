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
"""PixelCount

Count the pixels from a snapshot of the piformex canvas
"""
from __future__ import print_function


_status = 'checked'
_level = 'normal'
_topics = ['camera','image','vtk']
_techniques = ['image','vtk']

from pyformex.gui.draw import *
from pyformex.simple import cylinder
from pyformex.connectivity import connectedLineElems
from pyformex.trisurface import fillBorder
from pyformex import utils
from pyformex.gui.image import saveImage
from pyformex.plugins.vtk_itf import vtkClip
from pyformex.plugins.imagearray import *
import pyformex as pf

def run():

    clear()
    bgcolor('white')
    perspective(False)
    flat()
    
    #create the geometry 
    F = cylinder(L=8., D=2., nt=36, nl=20, diag='u').centered()
    F = TriSurface(F).close(method='planar').fixNormals().fuse().compact().setProp(1)
    G = F.rotate(57., 0).rotate(12., 1).trl(0, 1.).trl(2, 2.).setProp(1)

    I=vtkClip(F,implicitdata=G,method='surface',insideout=0)
    I=Mesh.concatenate(I)
    
    
    hole = I.getBorderMesh()
    focus = hole.center()

    #set the camera focus to the center of the cut and the eye set in the z direction with distance D
    D = 4
    dir = array([1,0,0,])
        
    draw(I,color=red,bkcolor=green)
    pf.canvas.camera.lookAt(focus=focus,eye=focus+dir*D)

    #ensure that the object is between the camera clipping planes
    pf.canvas.camera.setClip( D*1e-5, D*10000)
    pf.canvas.update()

    #~ Creating the image array from the canvas
    #~ this is a workaround as the image array cannot be taken directly from the buffer
    tmpimg = utils.tempFile(suffix='.png').name
    saveImage(tmpimg)
    im = QtGui.QImage(tmpimg)
    imar = qimage2numpy(im, resize=(0, 0) ,order='RGB',flip=True,indexed=None,expand=None)[0]
    
    #~ Counting the number of pixels per color
    from pyformex.connectivity import Connectivity
    colorTable = Connectivity(imar.reshape(-1, 3)) # table of no. of pixels x RGB
    colordict = colorTable.testDuplicate(permutations=False,return_multiplicity=True)[2] # dictionary {'number of pixels': index of the pixels with the unique color}
    for nopx in colordict.keys():
        ind = colordict[nopx] # index of the pixels with the unique color
        uniqcolor = colorTable[ind[0]]
        print ('the image includes color RGB %s in %d pixels'%(uniqcolor, nopx))

    os.remove(tmpimg)

if __name__ == '__draw__':
    run()
