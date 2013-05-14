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

_clear = clear

def clearall():
    pf.canvas.renderer.clear()
    _clear()


if pf.options.opengl2:
    def draw(o):
        pf.canvas.renderer.add(o)


clearall()


## from simple import sphere

## S = sphere(4)
## print(S.npoints())
## col = [red,red]*81
## print(len(col))
## S.attrib(lighting=True,ambient=0,diffuse=0,color=red)
## draw(S)
## zoomAll()
## exit()


A = Formex('3:012').replic2(2,1)
A.attrib(color=red)
A.attrib(color=[[red,green,blue],[cyan,magenta,yellow]])

B = Formex('l:127')
B.attrib(color=blue)

C = Formex('1:012')
C.attrib(color=yellow,pointsize=10)

D = A.trl([1.,1.,0.]).toMesh()
D.attrib(lighting=True,ambient=0.9,diffuse=0.9,color=green,bkcolor=blue)

E = Formex(D.points())
E.attrib(pointsize=20)
#D.attrib(color=[red,green,blue,magenta,yellow])

draw(A)
draw(B)
draw(C)
draw(D)
draw(E)

# End
