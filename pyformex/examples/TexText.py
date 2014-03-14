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
"""Text rendering on the OpenGL canvas.

This example illustrates some of the possibilities of text drawing
using textures. Yuo
"""
from __future__ import print_function

_status = 'checked'
_level = 'normal'
_topics = ['Text']
_techniques = ['texture']

import pyformex as pf
from pyformex.gui.draw import *

from pyformex.opengl.textext import *

def run():
    #
    # TODO: RESETALL does not properly layout the canvas in the viewport
    #resetAll()
    clear()
    view('front')
    smooth()
    fonts = listMonoFonts()
    ## for f in fonts:
    ##     print(f)

    # - draw a square
    # - use the full character set in the default font as a texture
    # - the font textures are currently upside down, therefore we need
    #   to specify texcoords to flip the image
    F = Formex('4:0123').scale(200).toMesh()
    A = draw(F,color=yellow,texture=FontTexture.default(),texcoords=array([[0,1],[1,1],[1,0],[0,0]]),texmode=2)

    # draw a string using the default_font texture
    T = Text("Hegemony!",(100,100),size=50,offset=(0.0,0.0,1))
    decorate(T)

    # the text is currently adjusted horizontally left, vertically centered
    # on the specified point. Adjustement using gravity will be added later.
    # Also, the color is currently not honoured.
    decorate(Text("Hegemony!",(0,10),size=20,color=red))
    decorate(Text("Hegemony!",(10,30),size=20,color=red))
    for i,txt in [
        (0,"Lower left corner"),
        (1,"Lower right corner"),
        (2,"Upper right corner"),
        (3,"Upper left corner"),
        ]:
        j = F.elems[0,i]
        decorate(Text(txt,F.coords[j],size=30,color=red))


    #drawViewportAxes3D((0.,0.,0.),color=blue)
    print(len(pf.canvas.scene.oldactors))
    #decorate(Text('+',(100,100,0),gravity='',size=100,color=red))

    image = os.path.join(pf.cfg['pyformexdir'], 'data', 'mark_cross.png')
    from pyformex.plugins.imagearray import image2numpy
    image = image2numpy(image, indexed=False)
    ## print(image.shape)
    ## image1 = image[14:18]
    ## print(image1[...,0])
    ## print(image1[...,1])
    ## print(image1[...,2])
    ## print(image1[...,3])
    #F = Formex('4:0123').scale(40).toMesh().trl([200,200,0])
    #draw(F,texture=image,texcoords=array([[0,1],[1,1],[1,0],[0,0]]),texmode=0,rendertype=2,opak=False,ontop=True)
    F = Formex('4:0123').scale(40).toMesh().align('000')
    draw(F,texture=image,texcoords=array([[0,1],[1,1],[1,0],[0,0]]),texmode=0,rendertype=1,opak=False,ontop=True,offset3=(200.,200.,0.))
    drawActor(Mark((0,200,0),image,size=40,color=red))


if __name__ == 'draw':
    run()

# End
