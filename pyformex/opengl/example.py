# Example script for testing opengl2
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
A.objectColor = red

B = Formex('l:127')
B.objectColor = blue

C = Formex('1:012')
C.objectColor = magenta

D = A.trl([1.,1.,0.]).toMesh()
D.objectColor = green

print(A)
print(B)
print(C)
print(D)

print(A.npoints())
print(D.npoints())
E = Formex(D.points())
E.pointsize = 20.
#E.invisible = True

D.attrib(lighting=True,ambient=0.3,diffuse=0.2,color='orange')
D.attrib(color='red')
D.attrib(lighting=None)
print(D._render)



A.lighting = False
E.lighting = False

draw(A)
draw(B)
draw(C)
draw(D)
draw(E)

# End
