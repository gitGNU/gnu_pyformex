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

"""Ftgl

This example demonstrates the use of FTGL library to render text as 3D objects.
To be able to run it, you need to have the FTGL library and its Python bindings
installed.

The pyFormex source repository contains a directory pyformex/extra/pyftgl
containing a Makefile to install the libraries.
"""
from __future__ import print_function
_status = 'checked'
_level = 'advanced'
_topics = ['text']
_techniques = ['ftgl', 'font']

from gui.draw import *

try:
    import FTGL

except ImportError:
    warning("You do not have FTGL and its Python bindings (pyftgl).\nSee the pyformex/extra/pyftgl directory in the pyFormex source tree for instructions.")

from gui import colors, image
import odict


extra_fonts = [
    getcfg('datadir')+"/blippok.ttf",
    ]

fonts = [ f for f in utils.listFontFiles() if f.endswith('.ttf') ]
fonts += [ f for f in extra_fonts if os.path.exists(f) ]
fonts.sort()
print("Number of available fonts: %s" % len(fonts))

fonttypes = odict.ODict([
    ('polygon', FTGL.PolygonFont),
    ('outline', FTGL.OutlineFont),
    ('texture', FTGL.TextureFont),
#    ('extrude',FTGL.ExtrudeFont),
    ('bitmap', FTGL.BitmapFont),
#    ('buffer',FTGL.BufferFont),
    ])

def showSquare():
    F = Formex(pattern('1234'))
    draw(F)


def showText(text, font, fonttype, facesize, color, pos):
    from gui.actors import Text3DActor, TranslatedActor
    font = fonttypes[fonttype](font)
    t = Text3DActor(text, font, facesize, color, pos)
    t.nolight=True
    drawAny(t)
    zoomAll()  #  !! Removing this may cause errors
    return t


def rotate():
    sleeptime = 0.1
    n = 1
    m = 5
    val = m * 360. / n
    for i in range(n):
        pf.canvas.camera.rotate(val, 0., 1., 0.)
        pf.canvas.update()
        sleep(sleeptime)
        sleeptime *= 0.98



_items = [
    _I('text', 'pyFormex'),
    _I('font', choices=fonts),
    _I('fonttype', choices=fonttypes.keys()),
    _I('facesize', (24, 36)),
    _I('color', colors.pyformex_pink),
    _I('pos', (0., 0., 0.)),
    ]

dialog = None


def close():
    global dialog
    if dialog:
        dialog.close()
        dialog = None
    # Release script lock
    scriptRelease(__file__)


def show(all=False):
    global text, font, facesize, color
    dialog.acceptData()
    globals().update(dialog.results)
    export({'_Ftgl_data_':dialog.results})

    clear()
    print(dialog.results)
    F = Formex('3:012').replic2(10, 6).align('+-0')
    draw(F, color='yellow')
    showText(**dialog.results)
    zoomAll()

    #image.save("test.eps")


def timeOut():
    showAll()
    wait()
    close()


def run():
    global dialog
    dialog = Dialog(
        items=_items,
#        enablers=_enablers,
        caption='Ftgl parameters',
        actions = [('Close', close), ('Clear', clear), ('Show', show)],
        default='Show')

    if '_Ftgl_data_' in pf.PF:
        dialog.updateData(pf.PF['_Ftgl_data_'])

    dialog.timeout = timeOut
    dialog.show()
    # Block other scripts
    scriptLock(__file__)


if __name__ == 'draw':
    chdir(__file__)
    clear()
    reset()
    #view('iso')
    smooth()
    lights(False)
    run()


# End
