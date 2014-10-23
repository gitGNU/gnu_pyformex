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

"""FuseParts

This example demonstrates the use of the Mesh.fuse and Coords.adjust methods
to fuse a Mesh by parts and adjust the nonfused nodes.

- First it creates 5 elements with a gap, spread over 3 differently colored
  parts.
- Then a Mesh.fuse operation is used (with a proper atol setting) to fuse
  the parts together, but not fuse between parts.
- Finally the Coords.adjust operation is used to give the nodes on the
  part boundaries identical coordinates.
"""
from __future__ import print_function


_status = 'checked'
_level = 'normal'
_topics = ['mesh']
_techniques = ['fuse']

from pyformex.gui.draw import *

def run():
    clear()
    # create 5 elements with a gap
    M = Formex('l:1').toMesh().scale(0.9)
    M = Mesh.concatenate([ M.trl([i*1.,0.,0.]) for i in range(5)],fuse=False)
    M.setProp([1,1,2,3,3])
    print(M.coords)
    print(M.elems)
    draw(M)
    draw(M.coords)
    drawNumbers(M.coords)
    pf.canvas.camera.lock()
    sleep(1)
    # fuse by parts
    M = M.trl([0.,-0.2,0.])
    M = M.fuse(M.prop,atol=0.2)
    print(M.coords)
    print(M.elems)
    draw(M)
    draw(M.coords)
    drawNumbers(M.coords)
    sleep(1)
    # fuse by parts
    M = M.trl([0.,-0.2,0.])
    M = M.adjust(atol=0.2)
    print(M.coords)
    print(M.elems)
    draw(M)
    draw(M.coords)
    drawNumbers(M.coords)


if __name__ == 'draw':
    clear()
    resetAll()
    wireframe()
    lights(False)
    run()


# End
