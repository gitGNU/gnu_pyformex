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
"""Coordinate Systems.

"""
from __future__ import print_function


from pyformex.coords import Coords
import numpy as np
from pyformex import arraytools as at


###########################################################################
##
##   class CoordSys
##
#########################
#

#
# TODO: This should be redone:
#   - generalized: cartesian, cylindrical, spherical
#   - different initializations: e.g. as in arraytools.trfMatrix, matrix
#   - internal implementation is probably a 4x4 mat or (r,t) as in trfMatrix
#

class CoordSys(object):
    """A Cartesian coordinate system in 3D space.

    The coordinate system is stored as a rotation matrix and a translation
    vector.

    It can be initialized from a rotation matrix and translation vector,
    or from a set of 4 points: the 3 endpoints of the unit vectors along
    the axes, and the origin.

    Parameters:

    - `rot`: rotation matrix (3,3): default is identity matrix.
    - `trl`: translation vector (3,) or (1,3): default is [0,0,0].
    - `points`: Coords-like (4,3): if specified, `rot` and `trl` arugments
      are ignored and determined from::

         rot = points[:3] - points[3]
         trl = points[3]

    Example:

      >>> print(CoordSys().points())
      [[ 1.  0.  0.]
       [ 0.  1.  0.]
       [ 0.  0.  1.]
       [ 0.  0.  0.]]

    """
    def __init__(self,rot=None,trl=None,points=None):
        """Initialize the CoordSys"""
        if points is None:
            if rot is None:
                rot = np.eye(3, 3)
            if trl is None:
                trl = np.zeros((3,))
        else:
            rot = (points[:3] - points[3]).transpose()
            trl = points[3]

        self.rot = at.checkArray(rot,shape=(3,3),kind='f')
        self.trl = at.checkArray(trl,shape=(3,),kind='f')


    def points(self):
        return Coords.concatenate([self.trl + self.rot.transpose(),self.trl])


class CoordinateSystem(Coords):
    """A CoordinateSystem defines a coordinate system in 3D space.

    The coordinate system is defined by and stored as a set of four points:
    three endpoints of the unit vectors along the axes at the origin, and
    the origin itself as fourth point.

    The constructor takes a (4,3) array as input. The default constructs
    the standard global Cartesian axes system::

      1.  0.  0.
      0.  1.  0.
      0.  0.  1.
      0.  0.  0.
    """
    def __new__(clas,coords=None,origin=None,axes=None):
        """Initialize the CoordinateSystem"""
        if coords is None:
            coords = np.eye(4, 3)
            if axes is not None:
                coords[:3] = axes
            if origin is not None:
                coords += origin
        else:
            coords = at.checkArray(coords, (4, 3), 'f', 'i')
        coords = Coords.__new__(clas, coords)
        return coords


    def origin(self):
        """Return the origin of the CoordinateSystem."""
        return Coords(self[3])


    def axes(self):
        """Return the axes of the CoordinateSystem."""
        return Coords(self[:3]-self[3])

    def points(self):
        return self

### End
