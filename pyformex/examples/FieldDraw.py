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
#
"""FieldDraw

This example demonstrates how to use field variables and how to render them.
"""
from __future__ import print_function

_status = 'checked'
_level = 'advanced'
_topics = [ 'mesh', 'postprocess']
_techniques = ['field', 'color']

from pyformex.gui.draw import *

from pyformex import simple
from pyformex import geomfile


def run():

    clear()
    smoothwire()
    layout(3)

    F = simple.rectangle(4,3)
    M = F.toMesh()
    #M.attrib(color=yellow)

    # add some fields

    # 1. distance from point 7, defined at nodes

    data = length(M.coords - M.coords[7])
    M.addField('node',data,'dist')


    # 2. convert to field defined at element nodes
    M.convertField('dist','elemn','distn')

    # 3. convert to field constant over elements
    M.convertField('distn','elemc','distc')

    print(M.fieldReport())

    # draw two fields
    viewport(0)
    drawField(M.getField('distn'))
    zoom(1.25)
    viewport(1)
    drawField(M.getField('distc'))
    zoom(1.25)
    viewport(2)
    drawField(M.getField('dist'))
    zoom(1.25)


if __name__ == '__draw__':
    run()
# End
