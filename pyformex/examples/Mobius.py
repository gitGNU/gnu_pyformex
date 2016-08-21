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
"""Mobius Ring

"""
from __future__ import absolute_import, print_function


_status = 'checked'
_level = 'advanced'
_topics = ['geometry', 'surface']
_techniques = ['dialog', 'animation', 'color']

from pyformex.gui.draw import *
from pyformex.opengl.textext import *

def run():
    reset()
    smoothwire()

    res = askItems([
        _I('w', 3, text='width', tooltip='Number of unit squares along the width'),
        _I('l', 30, text='length', tooltip='Number of unit squares along the length'),
        _I('n', 1, text='number of turns', tooltip='Number of 180 degree turns to apply'),
        ])
    if not res:
        return

    globals().update(res)

    ft = FontTexture.default()
    text = ' pyFormex ' * int(ceil(l*w/10.))
    text = text[0:w*l]
    tc = FontTexture.default().texCoords(text)
    #print("%s * %s = %s = %s" % (l,w,l*w,len(text)))
    cell = Formex('4:0123')
    strip = cell.replic2(l, w, 1., 1.).translate(1, -0.5*w)
    TA = draw(strip, color='orange', bkcolor='red',texture=ft,texcoords=tc,texmode=2)


    sleep(1)

    nsteps = 40
    step = n*180./nsteps/l
    for i in arange(nsteps+1):
        a = i*step
        torded = strip.map(lambda x, y, z: [x, y*cosd(x*a), y*sind(x*a)])
        TB = draw(torded, color='orange', bkcolor='red',texture=ft,texcoords=tc,texmode=2)
        undraw(TA)
        TA = TB

    sleep(1)
    #TA = None
    nsteps = 60
    step = 360./nsteps
    for i in arange(1, nsteps+1):
        ring = torded.trl(2, l*nsteps/pi/i).scale([i*step/l, 1., 1.]).trl(0, -90).cylindrical(dir=[2, 0, 1])
        TB = draw(ring, color='orange', bkcolor='red',texture=ft,texcoords=tc,texmode=2)
        undraw(TA)
        TA = TB

    sleep(1)
    nsteps = 80
    step = 720./nsteps
    for i in arange(1, nsteps+1):
        mobius = ring.rotate(i*step, 1)
        TB = draw(mobius, name='mobius',color='orange', bkcolor='red',texture=ft,texcoords=tc,texmode=2, bbox='last')
        undraw(TA)
        TA = TB


if __name__ == '__draw__':
    run()
# End
