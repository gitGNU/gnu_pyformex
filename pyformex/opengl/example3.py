# $Id$
##
##  This file is part of pyFormex 0.9.0  (Mon Mar 25 13:52:29 CET 2013)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2012 (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
##  Distributed under the GNU General Public License version 3 or later.
##
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

"""WebGL

This example illustrates the use of the webgl plugin to create WebGL models
in pyFormex.

The example creates a sphere, a cylinder and a cone, draws them with color
and transparency, and exports an equivalent WebGL model in the current
working directory. Point your WebGL capable browser to the created
'scene1.html' file to view the WebGL model.
"""
from __future__ import print_function

_status = 'checked'
_level = 'normal'
_topics = ['export']
_techniques = ['webgl']

from gui.draw import *

from simple import sphere,sector,cylinder
from mydict import Dict
from plugins.webgl import WebGL



def run():
    reset()
    clear()
    smooth()
    transparent()
    view('right')

    # Create some geometry
    S = sphere()
    T = sector(1.0,360.,6,36,h=1.0,diag='u').toSurface().scale(1.5).reverse()
    C = cylinder(1.2,1.5,24,4,diag='u').toSurface().trl([0.5,0.5,0.5]).reverse()

    # Draw the geometry with given colors/opacity
    # Settings colors and opacity in this way makes the model
    # directly ready to export as WebGL
    Sa = S.attrib
    Sa.color = red
    Sa.alpha = 0.7
    Sa.caption = 'A sphere'
    Sa.control = ['visible','opacity','color']
    #Sa.setNormals('avg')

    Ta = T.attrib
    Ta.color = blue
    Ta.caption = 'A cone'
    Ta.alpha = 1.0
    Ta.control = ['visible','opacity','color']
    #S.setNormals('auto')

    Ca = C.attrib
    Ca.color = 'yellow'
    Ca.caption = 'A cylinder'
    Ca.alpha = 0.8
    Ca.control = ['visible','opacity','color']
    #S.setNormals('auto')

    export({'sphere':S,'cone':T,'cylinder':C})

    #SA,TA,CA = draw([S,T,C])
    CA = draw(C)

    zoomAll()
    rotRight(30.)

    camera = pf.canvas.camera
    print("Camera focus: %s; eye: %s" % (camera.focus, camera.eye))


    for i in range(11):

        alpha = 0.1*i
        print("%s -> %s"% (CA.alpha,alpha))
        print(CA.caption)
        CA.alpha = alpha
        CA.modified = True
        print(CA.alpha)
        pf.canvas.update()
        sleep(0.1)

    CA.visible = False
    pf.canvas.update()
    sleep(0.5)
    CA.visible = True
    pf.canvas.update()
    sleep(0.5)
    print(CA.objectColor)


    def set_attr(field):
        actor = field.data
        key = field.text()
        val = field.value()
        if key == 'objectColor':
            print("VALUE %s" % val)
            val = GLcolor(val)
        print("%s: %s = %s" % (actor.name,key,val))
        setattr(actor,key,val)
        pf.canvas.update()

    def obj_dialog(obj):
        items = [
            _I('name',obj.name),
            _I('visible',True,func=set_attr,data=obj),
            ]
        if 'objectColor' in obj:
            items.append(_I('objectColor',CA.objectColor,itemtype='color',min=0.0,max=100.0,scale=0.01,func=set_attr,data=CA))
        if 'alpha' in obj:
            items.append(_I('alpha',CA.alpha,itemtype='fslider',min=0.0,max=100.0,scale=0.01,func=set_attr,data=CA))
        return Dialog(items)


    dia = obj_dialog(CA)
    dia.show()

    ## if checkWorkdir():
    ##     # Export everything to webgl
    ##     W = WebGL()
    ##     W.addScene()
    ##     W.export('Scene1','Two spheres and a cone',createdby=True)

if __name__ == 'draw':
    run()

# End
