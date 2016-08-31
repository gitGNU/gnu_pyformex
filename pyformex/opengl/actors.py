# $Id$
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
"""OpenGL Actors.

This module defines all OpenGL Actors that are directly available to the users.

"""
from __future__ import absolute_import, division, print_function

from pyformex import arraytools as at
from pyformex.opengl.drawable import Actor
# This is to make alle Actors available through this module
from pyformex.opengl.decors import *
from pyformex.opengl.textext import *


#  TODO: this replaces legacy PlaneActor, but could probably be derived from
#  decors.Grid

class PlaneActor(Actor):
    """A plane in a 3D scene.

    The default plane is perpendicular to the x-axis at the origin.
    """
    def __init__(self,n=(1.0,0.0,0.0),P=(0.0,0.0,0.0),sz=(1.,1.,0.),color='white',alpha=0.5,mode='flatwire',linecolor='black',**kargs):
        """A plane perpendicular to the x-axis at the origin."""
        from pyformex.formex import Formex
        F = Formex('4:0123').replic2(2,2).centered().scale(sz).rotate(90.,1).rotate(at.rotMatrix(n)).trl(P)
        F.attrib(mode=mode,lighting=False,color=color,alpha=alpha,linecolor=linecolor)
        print("kargs")
        print(kargs)
        Actor.__init__(self,F,**kargs)



# End
