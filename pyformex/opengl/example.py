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

## vshader = ask("Vertex shader",["_simple","_new","default"])
## if vshader == "default":
##     vshader = ''


## from opengl.shader import Shader
## from opengl.renderer import Renderer
## vs = os.path.join(os.path.dirname(__file__),'vertex_shader%s.c'%vshader)
## S = Shader(vs)
## R = Renderer(pf.canvas,S)
## pf.canvas.renderer = R


if pf.options.opengl2:
    def draw(o):
        pf.canvas.renderer.add(o)
    _clear = clear
    def clear():
        pf.canvas.renderer.clear()
        _clear()


clear()


from simple import sphere
A = Formex('3:012').replic2(2,1)
A.attrib(color=red)
B = Formex('l:127')
B.attrib(color=blue)

C = Formex('1:012')
C.attrib(color=yellow,pointsize=10)

D = A.trl([1.,1.,0.]).toMesh()
D.attrib(lighting=True,ambient=0.3,diffuse=0.2,color=green,bkcolor=blue)

E = Formex(D.points())
E.attrib(pointsize=20)

draw(A)
draw(B)
draw(C)
draw(D)
draw(E)

# End
