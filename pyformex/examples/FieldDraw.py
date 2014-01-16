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
from pyformex.plugins.postproc import drawField


def run():

    clear()
    smoothwire()
    layout(2)

    F = simple.rectangle(4,3)
    M = F.toMesh()
    #M.attrib(color=yellow)

    # add some fields

    # 1. distance from point 7, defined at nodes

    data = length(M.coords - M.coords[7])
    M.addField('dist','node',data)

    # 2. convert to field defined at element nodes
    data = M.convertField(M.getField('dist'),'node','elemn')
    M.addField('distn','elemn',data)

    # 3. convert to field constant over elements
    data = M.convertField(M.getField('distn'),'elemn','elemc')
    M.addField('distc','elemc',data)

    # draw two fields
    viewport(0)
    drawField(M,'elemn',M.getField('distn')[0])
    zoom(1.25)
    viewport(1)
    drawField(M,'elemc',M.getField('distc')[0])
    zoom(1.25)

    writeGeomFile('field.pgf',{'mesh':M})

if __name__ == 'draw':
    run()
# End
