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
"""Coordinate Systems.

"""
from __future__ import print_function

from pyformex import utils
from pyformex import arraytools as at
from pyformex.coords import Coords

import numpy as np

###########################################################################
##
##   class CoordSys
##
#########################
#

#
# TODO: This could be improved:
#   - generalized: cartesian, cylindrical, spherical
#   - different initializations: e.g. as in arraytools.trfMatrix, matrix
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

    >>> C = CoordSys()
    >>> print(C.points())
    [[ 1.  0.  0.]
     [ 0.  1.  0.]
     [ 0.  0.  1.]
     [ 0.  0.  0.]]
    >>> print(C.origin())
    [ 0.  0.  0.]

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

        self.rot = rot
        self.trl = trl


    @property
    def trl(self):
        """Return the origin as a (3,) vector"""
        return self._trl

    @trl.setter
    def trl(self, value):
        """Set the origin to (3,) value"""
        self._trl =  at.checkArray(value,shape=(3,),kind='f')


    @property
    def rot(self):
        """Return the (3,3) rotation matrix"""
        return self._rot

    @rot.setter
    def rot(self, value):
        """Set the rotation matrix to (3,3) value"""
        self._rot = at.checkArray(value,shape=(3,3),kind='f')

    @property
    def axes(self):
        """Return the unit vectors along the axes of the CoordinateSystem."""
        return self.rot.transpose()

    @property
    def u(self):
        """Return unit vector along axis 0 (x)"""
        return self.axes[0]

    @property
    def v(self):
        """Return unit vector along axis 1 (y)"""
        return self.axes[1]

    @property
    def w(self):
        """Return unit vector along axis 2 (z)"""
        return self.axes[2]

    @property
    def o(self):
        """Return the origin"""
        return self.trl


    # Simple transformation methods
    # These return self so that they can be concatenated

    def translate(self,trl):
        self.trl = self.trl+trl
        return self


    def rotate(self,*args,**kargs):
        """Rotate the CoordSys.

        Parameters: either a single (3,3) rotation matrix, or parameters
        like in the :meth:`coords.Coords.rotate` method.
        """
        if len(args)==1 and not kargs:
            self.rot = np.dot(self.rot,args[0])
        else:
            X = self.points().rotate(*args,**kargs)
            self.__init__(points=X)
        return self


    # methods retained for compatibility with CoordinateSystem
    def origin(self):
        return self.trl

    def points(self):
        return Coords.concatenate([self.trl + self.rot.transpose(),self.trl])


class CoordinateSystem(Coords):
    """_A CoordinateSystem defines a coordinate system in 3D space.

    The coordinate system is defined by and stored as a set of four points:
    three endpoints of the unit vectors along the axes at the origin, and
    the origin itself as fourth point.

    The constructor takes a (4,3) array as input. The default constructs
    the standard global Cartesian axes system.

    Example:

    >>> C = CoordinateSystem()
    >>> print(C.points())
    [[ 1.  0.  0.]
     [ 0.  1.  0.]
     [ 0.  0.  1.]
     [ 0.  0.  0.]]
    >>> print(C.origin())
    [ 0.  0.  0.]

    """
    @utils.deprecated_by('CoordinateSystem','CoordSys')
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
