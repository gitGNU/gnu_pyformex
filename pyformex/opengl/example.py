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

clear()

pf.canvas.renderer.shader.builtin = True  # Set to 0 to not use builtin attributes

A = Formex('3:012').replic2(2,1)
A = A.setProp(1+arange(A.nelems()))
A.attrib(color='prop')


AA = Formex('4:0123').trl([0.,1.,0.]).replic2(2,1)#.toMesh()
AA = AA.setProp(4+arange(AA.nelems()))
AA.attrib(color='prop')

draw([AA])
exit()

A.attrib(color=red)


A.attrib(lighting=True,ambient=0.5,diffuse=0.5,specular=0.5,color=[[red,green,blue],[cyan,magenta,yellow]])

A.attrib(color=[[0,1,2],[3,4,5]])
A.attrib(color=[1,2])

B = Formex('l:127')
B.attrib(color=blue)

C = Formex('1:012')
C.attrib(color=yellow,pointsize=10)

D = A.trl([1.,1.,0.]).toMesh()
D.attrib(lighting=True,color=green,bkcolor=blue,ambient=0.5,diffuse=0.5,specular=0.0,alpha=1.0)

E = Formex(D.points())
E.attrib(pointsize=20)
#D.attrib(color=[red,green,blue,magenta,yellow])


#print(draw.__doc__)
#print(gui.draw.draw.__doc__)


draw(A)
#draw(B)
#draw(C)
#draw(D)
#draw(E)

zoomAll()
#pf.app.processEvents()



# End
