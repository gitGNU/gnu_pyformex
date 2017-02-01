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
"""DicomViewer

This example shows how to interactively switch the colors display on an
object.

Select a single image from a DICOM stack to read all the images.
Then use the slider to traverse the images.

"""
from __future__ import print_function


_status = 'checked'
_level = 'advanced'
_topics = ['image', 'field']
_techniques = ['color', 'filename', 'dialog']

from pyformex import utils
utils.requireModule('gdcm')

from pyformex.gui.draw import *
from pyformex.plugins.imagearray import DicomStack


def allcloseV(a,**kargs):
    """Check that all values in a have the same value

    a is 1D or 2D array.
    If 2D: checks that all rows are the same. Values
    inside a row may differ.
    """
    if a.ndim == 1:
        return allclose(a[1:],a[0],**kargs)
    elif a.ndim == 2:
        for i in range(a.shape[-1]):
            if not allclose(a[1:,i],a[0,i],**kargs):
                return False
        return True
    else:
        raise ValueError("a should be 1- or 2-dim array")


def changeColorDirect(i):
    """Change the displayed color by directly changing color attribute."""
    global FA
    F = FA.object
    color = F.getField('slice_%s' % i).data
    FA.drawable[0].changeVertexColor(color)
    pf.canvas.update()


def setFrame(item):
    i = item.value()
    dia.acceptData()
    res = dia.results
    changeColorDirect(i)


def run():
    global width,height,FA,dia,dotsize
    clear()
    smooth()
    lights(False)
    view('front')

    # reading image files
    fp = askFilename()
    if not fp:
        return
    print("You selected %s" % fp)
    dirname,base,ext = utils.splitFilename(fp)
    if ext:
        filepat = [ '.*\.%s$' % ext[1:] ]
    else:
        filepat = None
    files = utils.listTree(dirname,listdirs=False,sorted=True,includefiles=filepat)

    print("Number of files: %s" % len(files))

    pf.GUI.setBusy()
    DS = DicomStack(files)
    pf.GUI.setBusy(False)
    print("z-value of the slices:]n",DS.zvalue())

    raw = ack("Use RAW values instead of Hounsfield?")

    pf.GUI.setBusy()
    pixar = DS.pixar(raw).astype(Float)  # TODO: Set in DicomStack
    print(pixar.shape)
    print("Data: %s (%s..%s)" % (pixar.dtype,pixar.min(),pixar.max()))
    scale = DS.spacing()
    origin = DS.origin()
    zscale = origin[1:,2] - origin[:-1,2]
    if allcloseV(scale) and allcloseV(origin[:,:2]) and allcloseV(zscale):
        scale = scale[0]
        scale[2] = zscale[0]
        print("Scale: %s " % scale)
    else:
        print("Scale/origin is not uniform!")

    maxval = pixar.max()
    nx,ny,nz = pixar.shape

    # Create a 2D grid of nx*ny elements
    model = 'Dots'
    dotsize = 3
    if model == 'Dots':
        base = '1:0'
    else:
        base = '4:0123'
    F = Formex(base).replic2(nx,ny).toMesh().reflect(1)  # Image rows are top down, should change in DicomStack

    for iz in range(nz):
        color = pixar[:,:,iz] / Float(maxval)
        color = repeat(color[...,newaxis],3).reshape(-1,3)
        F.addField('node',color,'slice_%s' % iz)

    FA = draw(F, color='fld:slice_0', colormap=None, marksize=dotsize, name='image')
    pf.GUI.setBusy(False)

    nframes = nz
    frame = 0
    dia = Dialog([
        _I('frame',frame,itemtype='slider',min=0,max=nframes-1,func=setFrame),
        ])
    dia['frame'].setMinimumWidth(800)
    dia.show()


if __name__ == '__draw__':
    run()


# End
