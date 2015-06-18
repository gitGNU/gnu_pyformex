# $Id$
##
##  This file is part of pyFormex 1.0.2  (Thu Jun 18 15:35:31 CEST 2015)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2015 (C) Benedict Verhegghe (benedict.verhegghe@feops.com)
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
"""Some additional classes.

"""

from numpy import *
from pyformex.coords import Coords

class BoundVectors(Coords):
    """A collection of bound vectors in a 3D Cartesian space.

    Parameters:

    - `coords`: a (...,2,3) shaped array of bound vectors defined by their
      initial and terminal points.
    - `origins`, `vectors`: (...,3) shaped arrays defining the initial
      points and vectors from initial to terminal points.

    The default constructs a unit vector along the global x-axis.
    """
    def __new__(clas,coords=None,origins=None,vectors=None):
        """Initialize the BoundVectors."""
        if coords is None:
            coords = eye(2, 3, -1)
            if vectors is not None:
                coords = resize(coords, vectors.shape[:-1]+(2, 3))
                coords[..., 1,:] = vectors
            if origins is not None:
                coords += origins[..., newaxis,:]
        elif coords.shape[-2:] != (2, 3):
            raise ValueError("Expected shape (2,3) for last two array axes.")
        return Coords.__new__(clas, coords)


    def origins(self):
        """Return the initial points of the BoundVectors."""
        return Coords(self[..., 0,:])


    def heads(self):
        """Return the endpoints of the BoundVectors."""
        return Coords(self[..., 1,:])


    def vectors(self):
        """Return the vectors of the BoundVectors."""
        return Coords(self.heads()-self.origins())


    def actor(self,**kargs):
        """_This allows a BoundVectors object to be drawn directly."""
        from pyformex.formex import connect
        return connect([self.origins(), self.heads()]).actor(**kargs)


# End
