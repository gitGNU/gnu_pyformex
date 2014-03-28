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
"""pyFormex legacy modules.

The modules in this directory are deprecated and should no longer
be used. They are here for compatibility reasons, to ease the
transition to the newer replacement modules, and as an emrgency
rescue for cases where the new modules are not working yet.

Do not remove this file. It is used by pyFormex to flag the parent
directory as a Python package.
"""
from __future__ import print_function

#### Set the Formex and Mesh actor method ####

## def _set_actors():
##     def actor(self,**kargs):

##         if self.nelems() == 0:
##             return None

##         from pyformex.legacy.actors import GeomActor

##         return GeomActor(self,**kargs)

##     from pyformex import formex
##     formex.Formex.actor = actor
##     from pyformex import mesh
##     mesh.Mesh.actor = actor

## _set_actors()

#### Set the WebGL format_actor method

# End
