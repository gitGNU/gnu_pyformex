# Example script for testing opengl2
#
#

R = pf.canvas.renderer

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

draw(A.trl([0.1,0.1,0.1]),color=green)

R.add(A)
#R.add(B)
#R.add(C)

pf.canvas.update()
