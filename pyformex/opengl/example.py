# Example script for testing opengl2
#
#

vshader = ask("Vertex shader",["_simple","_new","default"])
if vshader == "default":
    vshader = ''




from opengl.shader import Shader
from opengl.renderer import Renderer
vs = os.path.join(os.path.dirname(__file__),'vertex_shader%s.c'%vshader)
S = Shader(vs)
R = Renderer(pf.canvas,S)
pf.canvas.renderer = R


#R = pf.canvas.renderer

def clearAll():
    clear()
    R.clear()

clearAll()
A = Formex('3:.12')#.replic2(10,6)

B = Formex([[
    [ 0.75,  0.75, 0.0],
    [ 0.75, -0.75, 0.0],
    [-0.75, -0.75, 0.0],
    ]])

C = Formex([
    [[  0, 1, 0 ],
     [ -1,-1, 0 ],
     [  1,-1, 0 ]],
    [[  2,-1, 0 ],
     [  4,-1, 0 ],
     [  4, 1, 0 ]],
    [[  2,-1, 0 ],
     [  4, 1, 0 ],
     [  2, 1, 0 ]],
    ])

#draw(A,color=green)
draw(A.trl([0.01,0.01,0.01]),color=green)

R.add(A)
#R.add(B)
#R.add(C)

pf.canvas.update()
