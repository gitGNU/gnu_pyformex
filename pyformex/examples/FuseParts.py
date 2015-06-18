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
from pyformex import arraytools as at


def run():
    clear()
    # create 9 elements with a gap
    M = Formex('4:1234').toMesh().scale(0.9)
    M = Mesh.concatenate([ M.trl([i*1.,j*1.,0.]) for i in range(3) for j in range(3) ],fuse=False)
    M.setProp([1,2,3])
    print(M.coords)
    print(M.elems)
    draw(M)
    drawNumbers(M)
    draw(M.coords)
    drawNumbers(M.coords)
    sleep(1)

    # fuse by parts
    M = M.trl([3.5,0.0,0.])
    M = M.fuse(parts=M.prop,atol=0.2)
    print(M.coords)
    print(M.elems)
    draw(M)
    draw(M.coords)
    drawNumbers(M.coords)
    sleep(1)

    # fuse between parts, but only in the right halve
    M = M.trl([3.5,0.0,0.])
    t = M.coords.test(min=M.coords.center()[0])
    w = where(t)[0]
    print("NODES TO FUSE: %s" % w)
    M = M.fuse(nodes=w,atol=0.2)
    print(M.coords)
    print(M.elems)
    draw(M)
    draw(M.coords)
    drawNumbers(M.coords)
    sleep(1)

    # adjust remaining nodes to close gaps, unfused
    M = M.trl([3.5,0.,0.])
    drawNumbers(M.coords)
    M.coords = M.coords.adjust(atol=0.2)
    print(M.coords)
    print(M.elems)
    draw(M)
    draw(M.coords)


if __name__ == '__draw__':
    clear()
    resetAll()
    smoothwire()
    lights(True)
    run()


# End
