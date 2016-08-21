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

"""RectangularMesh

This example illustrates the use of the mesh_ext.rectangular function
and the use of seeds in generating Meshes.

"""
from __future__ import absolute_import, print_function


_status = 'checked'
_level = 'beginner'
_topics = ['geometry', 'mesh']
_techniques = ['rectangular', 'seed', 'layout']


from pyformex.gui.draw import *
from pyformex.plugins.mesh_ext import *
from pyformex.gui.viewportMenu import clearAll


def run():
    """Main function.

    This is executed on each run.
    """
    clearAll()
    smoothwire()
    fgcolor(red)
    layout(6, 3)

    viewport(0)
    M = rectangle(1., 1., 6, 3)
    draw(M)

    viewport(1)
    M = rectangle(1., 1., (6, 0.3), (6, 0.3))
    draw(M)

    viewport(2)
    M = rectangle(1., 1., (6, 0.3), (6, -0.5))
    draw(M)

    viewport(3)
    M = rectangle(1., 1., (6, 0.5, 0.5), (6, 1, 1))
    draw(M)

    viewport(4)
    M = rectangle(1., 1., (6, -1, -1), (6, -1, -1))
    draw(M)

    viewport(5)
    M = rectangle(2., 1., (6, -1, -1), (6, -1, -1))
    draw(M)


if __name__ == '__draw__':
    run()
# End
