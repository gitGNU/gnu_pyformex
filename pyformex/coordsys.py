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
from __future__ import absolute_import, division, print_function

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
    vector, which transform the global coordinate axes into the axes of the
    CoordSys.
    Clearly, the translation vector is the origin of the CoordSys, and the
    rows of the rotation matrix are the unit vectors along the three axes.

    The CoordSys can be initialized in different ways:

    - `oab`: (3,3) float array. The CoordSys is specified by three points:
      the origin O, a point A along the first axis, and a point B in the plane
      of the first two axes. The three points should not be collinear.
    - `points`: (4,3) float array. The CoordSys is specified by four points:
      the origin (last point) and one point on each of the axes (first three
      points). The use of this parameter is deprecated. It can be replaced
      with `oab=points[3,0,1]`.
    - `rot`,`trl`: directly specify the (3,3) rotation matrix and the (3,)
      translation vector. The caller is responsible to make sure that `rot`
      is a proper orthonormal rotation matrix.

    Example:

    Three points O,A,B in the xy-plane, first two parallel to x-axis,
    third at higher y-value.
    >>> OAB = Coords([[2.,1.,0.],[5.,1.,0.],[0.,3.,0.]])

    Resulting CoordSys is global axes translated to point O.
    >>> print(CoordSys(oab=OAB))
    CoordSys: trl=[ 2.  1.  0.]; rot=[[ 1.  0.  0.]
                                      [ 0.  1.  0.]
                                      [ 0.  0.  1.]]

    Now translate the points so that O is on the z-axis, and rotate the
    points 30 degrees around z-axis.
    >>> OAB = OAB.trl([-2.,-1.,5.]).rot(30)
    >>> print(OAB)
    [[ 0.    0.    5.  ]
     [ 2.6   1.5   5.  ]
     [-2.73  0.73  5.  ]]
    >>> C = CoordSys(oab=OAB)
    >>> print(C)
    CoordSys: trl=[ 0.  0.  5.]; rot=[[ 0.87  0.5   0.  ]
                                      [-0.5   0.87  0.  ]
                                      [ 0.   -0.    1.  ]]

    Reverse x,y-axes. The resulting CoordSys is still righthanded. This is
    equivalent to a rotation over 180 degrees around z-axis.
    >>> print(C.reverse(0,1))
    CoordSys: trl=[ 0.  0.  5.]; rot=[[-0.87 -0.5  -0.  ]
                                      [ 0.5  -0.87 -0.  ]
                                      [ 0.   -0.    1.  ]]

    Now rotate C over 150 degrees around z-axis to become parallel with
    the global axes. Remember that transformations change the CoordSys
    in place (unlike Geometry classes).
    >>> print(C.rotate(150,2))
    CoordSys: trl=[ 0.  0.  5.]; rot=[[ 1.  0.  0.]
                                      [-0.  1.  0.]
                                      [ 0.  0.  1.]]

    """
    def __init__(self,oab=None,points=None,rot=None,trl=None):
        """Initialize the CoordSys"""
        if oab is not None:
            oab = at.checkArray(oab,(3,3),'f')
            rot = at.rotmat(oab)
            trl = oab[0]
        elif points is not None:
            points = at.checkArray(points,(4,3),'f')
            rot = at.normalize(points[:3] - points[3])
            trl = points[3]
        else:
            if rot is None:
                rot = np.eye(3, 3)
            if trl is None:
                trl = np.zeros((3,))

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
    def u(self):
        """Return unit vector along axis 0 (x)"""
        return self.axis(0)

    @property
    def v(self):
        """Return unit vector along axis 1 (y)"""
        return self.axis(1)

    @property
    def w(self):
        """Return unit vector along axis 2 (z)"""
        return self.axis(2)

    @property
    def o(self):
        """Return the origin"""
        return self.trl

    # Some aliases
    origin = o
    axes = rot

    def points(self):
        """Return origin and endpoints of unit vectors along axes."""
        return Coords.concatenate([self.axes+self.trl, self.trl])

    def axis(self,i):
        """Return the unit vector along the axis i (0..2)."""
        return self.rot[i]


    # Simple transformation methods
    # These methods modify the object inplace
    # They still return self, so that they can be concatenated

    def _translate(self,trl):
        """Translate the CoordSys.

        Translates the origin of the CoordSys, keeping its axes directions.
        """
        self.trl += trl
        return self


    def _rotate(self,rot):
        """Rotate the CoordSys.

        Parameters: (3,3) rotation matrix
        """
        rot = checkArray(rot,(3,3))
        self.rot = np.dot(self.rot,rot)
        return self


    def translate(self,*args,**kargs):
        """Translate the CoordSys like a Coords object.

        """
        return CoordSys(points=self.points().translate(*args,**kargs))


    def rotate(self,*args,**kargs):
        """Rotate the CoordSys like a Coords object.

        """
        return CoordSys(points=self.points().rotate(*args,**kargs))


    def reverse(self,*axes):
        """Reverse some axes of the CoordSys.

        Parameters:

        - `axes`: one or more ints in the range 0..2. The specified
        axes will be reversed.

        Note the reversing a single axis will change a right-hand-sided
        CoordSys into a left-hand-sided one. Therefore, this method is
        normally used only with two axis numbers, unless you want to change
        the handedness.
        """
        for axis in axes:
            self.rot[axis] *= -1.0
        return self


    def __str__(self):
        return at.stringar("CoordSys: trl=%s; rot=" % self.trl,self.rot)



class CoordinateSystem(CoordSys):
    @utils.deprecated_by('CoordinateSystem','CoordSys')
    def __init__(coords):
        """Initialize the CoordinateSystem"""
        CoordSys.init(self,points=coords)


### End
