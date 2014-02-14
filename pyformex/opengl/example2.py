# Example script for testing opengl2
##
##  This file is part of the pyFormex project.
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
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
#


if not pf.options.opengl2:
    warning("This example only runs with the new opengl2 engine!")

pf.cfg['render/experimental'] = False

resetAll()
clear()
smooth()
transparent()


def modified(obj):
    pf.canvas.renderer.shader.loadUniforms(obj)



from pyformex.simple import sphere
from OpenGL import GL

S = sphere(6)
S = S.toSurface().fixNormals().toFormex()
T = Formex('4:0123').replic2(2, 3).toMesh().align('-00')

S1 = S.scale(0.5)
S2 = S.scale(0.25)
S2 = S2.trl([0., 0., -2.]) +  S2.trl([0., 0., 2.])

draw(S1,name='red_sphere', color=red, opak=False, alpha=0.5)
draw(S2,name='blue_sphere', color=blue, opak=True, alpha=1.0)
draw(T,name='rectangular_plate', color=green, bkcolor=darkgreen,alpha=0.9,bkalpha=0.5)
draw(S,name='yellow_sphere', color=yellow, alpha=0.5)

zoomAll()


# End
