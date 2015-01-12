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
"""ContourView

Saves the contour of an object as shown in the viewport.

"""
from __future__ import print_function


_status = 'checked'
_level = 'normal'
_topics = ['contour','vtk']
_techniques = ['vtk']

from pyformex.gui.draw import *

from pyformex.plugins.trisurface import TriSurface
from pyformex.plugins.vtk_itf import *
import pyformex as pf


def run():
    clear()
    S = TriSurface.read(getcfg('datadir')+'/horse.off')
    perspective(state=False)
    draw(S)
    pause()
    clear()
    rot=pf.canvas.camera.rot
    contour = viewContour(S)
    draw(S.rot(rot),color=blue)
    draw(contour,view=None,color=red)


if __name__ == 'draw':
    run()
# End
