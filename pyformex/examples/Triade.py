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
"""SetTriade.py

This example shows how to use a customized Triade
"""
from __future__ import absolute_import, division, print_function

_status = 'checked'
_level = 'advanced'
_topics = ['decors']
_techniques = ['setTriade']

from pyformex.gui.draw import *
from OpenGL import GL
from pyformex.opengl.drawable import Actor


def run():
    global _triade_geometry

    clear()
    resetAll()
    smoothwire()

    print('Draw something')
    F = Formex.read(getcfg('datadir')+'/horse.pgf').scale(10)
    draw(F)
    pause()

    print('Set default Triade on')
    setTriade(on=True)
    pause()

    print('Set Triade off')
    setTriade(False)
    pause()

    print('Set a man as triade, right bottom')
    setTriade(triade='man',pos='rb')
    pause()

    print('Set a cube as triade, left top')
    cube = Formex(simple.Pattern['cube']).setProp([1,2,1,2,3,3,3,3,1,2,1,2]).centered()
    setTriade(on=True,pos='lt',triade=cube)
    pause()

    print('Use the displayed geometry (F) itself as Triade, left center')
    setTriade(on=True,pos='lc',triade=F)
    pause()

    print('Reset the original Triade, center top')
    setTriade(on=True,pos='ct',triade='axes')


if __name__ == '__draw__':
    run()

# End
