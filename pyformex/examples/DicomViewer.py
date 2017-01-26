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



def readImage(fn,reader='any'):
    """Read an image from file fn.

    This can be either a file that can be read by QImage,
    or a DICOM image that can be read by python-dicom or python-gdcm

    reader can be 'qimage' or 'dicom'

    Returns the image as an ndarray of an integer type.
    """
    if reader in ['any','qimage']:
        try:
            ar = qimage2numpy(fn)
            return ar
        except:
            if reader == 'qimage':
                raise
    if reader in ['any','dicom']:
        try:
            ar = readDicom(f)(fn)
            return ar
        except:
            if reader == 'dicom':
                raise


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
    pixar = DS.pixar(raw)
    # if pixar.dtype.kind == 'i':
    #     dtyp = dtype('u'+pixar.dtype.name)
    #     print("Converting integer data type %s to unsigned integer type %s." % (pixar.dtype,dtyp))
    #     pixar = pixar.astype(dtyp)
    print(pixar.shape)
    print("Data: %s (%s..%s)" % (pixar.dtype,pixar.min(),pixar.max()))
    scale = DS.spacing()
    if (scale == scale[0]).all():
        print("Scale: %s " % scale[0])
    else:
        print("Scale is not uniform!")

    maxval = pixar.max()
    nx,ny,nz = pixar.shape

    # Create a 2D grid of nx*ny elements
    model = 'Dots'
    dotsize = 3
    if model == 'Dots':
        base = '1:0'
    else:
        base = '4:0123'
    F = Formex(base).replic2(nx,ny).toMesh()

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
