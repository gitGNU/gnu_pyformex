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

from opengl.drawable import *

if not pf.options.opengl2:
    warning("This example only runs with the new opengl2 engine!")
    exit()


_clear = clear

def clearall():
    pf.canvas.renderer.clear()
    _clear()


def draw(o,**kargs):
    pf.canvas.renderer.add(o,**kargs)
def drawActor(o):
    pf.canvas.renderer.addActor(o)


def modified(obj):
    pf.canvas.renderer.shader.loadUniforms(obj)


clearall()


#transparent()

from simple import sphere

S = sphere(6)
S = S.toSurface().fixNormals()#.toFormex()
print(S.npoints())
col = [red,red]*81
print(len(col))
SA = GeomActor(S,ambient=0.5,diffuse=1,specular=0.5,color=red,alpha=0.7,light=(0.,1.,1.),shininess=20)

T = Formex('4:0123').replic2(2,3).toMesh().align('-00')
TA = GeomActor(T,ambient=0.5,diffuse=0.5,color=blue,bkcolor=green,alpha=0.9,light=(0.,1.,1.))

SA.children.append(TA)

drawActor(SA)

zoomAll()

## n = 10
## for x in arange(n+1) / float(n):
##     print(x)
##     TA.objColor = red + x * green
##     modified(TA)
##     sleep(1)

# End
