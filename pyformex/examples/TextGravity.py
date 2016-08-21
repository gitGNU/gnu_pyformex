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
"""TextGravity

Show the use of the text gravity parameter.
"""
from __future__ import absolute_import, print_function


_status = 'checked'
_level = 'beginner'
_topics = []
_techniques = ['text']

from pyformex.gui.draw import *
from pyformex.opengl.actors import *
from pyformex.opengl.textext import *

def run():
    clear()
    lights(False)
    x,y = pf.canvas.width()/2,pf.canvas.height()/2
    H = Grid2D(x-200,y-200,x+200,y+200, 2,2,rendertype=2,color=red,linewidth=2)
    drawActor(H)


    delay(2)
    for g in [ 'NW', 'N', 'NE', 'W', 'C', 'E', 'SW', 'S', 'SE' ]:
        T = drawText("XXX  %s  XXX"%g, (x,y), gravity=g, size=24)
        wait()
        undecorate(T)

    delay(1)
    for f in utils.listMonoFonts():
        print(f)
        font = FontTexture(f,24)
        S = drawText(f, (20, 20), font=font,size=24)
        T = drawText('X', (x, y), font=font,size=48, gravity='')
        wait()
        undecorate(S)
        undecorate(T)

if __name__ == '__draw__':
    run()
# End
