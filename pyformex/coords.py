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
"""A structured collection of 3D coordinates.

The :mod:`coords` module defines the :class:`Coords` class, which is the basic
data structure in pyFormex to store the coordinates of points in a 3D space.

This module implements a data class for storing large sets of 3D coordinates
and provides an extensive set of methods for transforming these coordinates.
Most of pyFormex's classes which represent geometry (e.g. :class:`Geometry`,
:class:`Formex`, :class:`Mesh`, :class:`TriSurface`, :class:`Curve`) use a
:class:`Coords` object to store their coordinates, and thus inherit all the
transformation methods of this class.

While the user will mostly use the higher level classes, he might occasionally
find good reason to use the :class:`Coords` class directly as well.
"""
from __future__ import absolute_import, division, print_function

from pyformex import zip
from pyformex import utils

from pyformex.arraytools import *


###########################################################################
##
##   class Coords
##
#########################
#
class Coords(ndarray):
    """A structured collection of points in a 3D cartesian space.

    The :class:`Coords` class is the basic data structure used throughout
    pyFormex to store coordinates of points in a 3D space.
    It is used by other classes, such as :class:`Formex`
    and :class:`Surface`, which thus inherit the same transformation
    capabilities. Applications will mostly use the higher level
    classes, which usually have more elaborated consistency checking
    and error handling.

    :class:`Coords` is implemented as a subclass of :class:`numpy.ndarray`,
    and thus inherits all its methods and atttributes.
    The last axis of the :class:`Coords` always has a length equal to 3.
    Each set of 3 values along the last axis represents a single point
    in 3D cartesian space. The float datatype is only checked at creation
    time. It is the responsibility of the user to keep this consistent
    throughout the lifetime of the object.

    A new Coords object is created with the following syntax ::

      Coords(data=None,dtyp=Float,copy=False)

    Parameters:

    - `data`: array_like of type float.
      The last axis should have a length of 1, 2 or 3, bu will always be
      expanded to 3.
      If no data are specified, an empty Coords with shape (0,3) is created.

    - `dtyp`: the float datatype to be used.
      It not specified, the datatype of `data` is used, or the default
      :data:`Float` (which is equivalent to :data:`numpy.float32`).

    - `copy`: boolean.
      If ``True``, the data are copied. The default setting will try to use
      the original data if possible, e.g. if `data` is a correctly shaped and
      typed :class:`numpy.ndarray`.

    The Coords class has the following 'property' methods:

    - `x`: the X coordinates of the points
    - `y`: the Y coordinates of the points
    - `z`: the Z coordinates of the points
    - `xy`: the X and Y coordinates of the points
    - `xz`: the X and Z coordinates of the points
    - `yz`: the Y and Z coordinates of the points
    - `xyz`: all three coordinates of the points

    These all provide ndarrays that are views on Coords object and can thus be
    used to change (subsets of) the coordinates. They are merely a notational
    convenience.

    Example:

    >>> Coords([1.,0.])
    Coords([ 1.,  0.,  0.], dtype=float32)
    >>> X = Coords(arange(6).reshape(2,3))
    >>> print(X)
    [[ 0.  1.  2.]
     [ 3.  4.  5.]]
    >>> print(X.y)
    [ 1.  4.]
    >>> X.z[1] = 9.
    >>> print(X)
    [[ 0.  1.  2.]
     [ 3.  4.  9.]]
    >>> print(X.xz)
    [[ 0.  2.]
     [ 3.  9.]]
    >>> X.x = 0.
    >>> print(X)
    [[ 0.  1.  2.]
     [ 0.  4.  9.]]
    """
    #
    # :DEV
    # Because we have a __new__ constructor here and no __init__,
    # we have to list the arguments explicitely in the docstring above.
    #

    #
    # :DEV
    # Because the Coords class is sticky, results that are not conforming
    # to the requirements of being a Coords array, should be converted to
    # the general array class:   e.g.   return asarray(T)
    #

    def __new__(clas, data=None, dtyp=Float, copy=False):
        """Create a new instance of :class:`Coords`."""
        if data is None:
            # create an empty array : we need at least a 2D array
            # because we want the last axis to have length 3 and
            # we also need an axis with length 0 to have size 0
            ar = ndarray((0, 3), dtype=dtyp)
        else:
            # turn the data into an array, and copy if requested
            # DO NOT ADD ndmin=1 HERE ! (see below)
            ar = array(data, dtype=dtyp, copy=copy)

        #
        # The Coords object needs to be at least 1-D array, no a scalar
        # We could force 'ar' above to be at least 1-D, but that would
        # turn every scalar into a 1-D vector, which would circumvent
        # detection of input errors (e.g. with translation, where input
        # can be either a vector or an axis number)
        #
        if ar.ndim == 0:
            raise ValueError("Expected array data, not a scalar")

        if ar.shape[-1] == 3:
            pass
        elif ar.shape[-1] in [1, 2]:
            # make last axis length 3, adding 0 values
            ar = growAxis(ar, 3-ar.shape[-1], -1)
        elif ar.shape[-1] == 0:
            # allow empty coords objects
            ar = ar.reshape(0, 3)
        else:
            raise ValueError("Expected a length 1,2 or 3 for last array axis")

        # Make sure dtype is a float type
        if ar.dtype.kind != 'f':
            ar = ar.astype(Float)

        # Transform 'subarr' from an ndarray to our new subclass.
        ar = ar.view(clas)

        return ar


    ################ property methods ##########
    @property
    def x(self):
        """Returns the X-coordinates of all points.

        Returns an ndarray with shape `self.pshape()`, providing a view
        on the X-coordinates of all the points.

        """
        return self[..., 0].view(type=ndarray)

    @property
    def y(self):
        """Returns the Y-coordinates of all points.

        Returns an ndarray with shape `self.pshape()`, providing a view
        on the Y-coordinates of all the points.

        """
        return self[..., 1].view(type=ndarray)

    @property
    def z(self):
        """Returns the Z-coordinates of all points.

        Returns an ndarray with shape `self.pshape()`, providing a view
        on the Z-coordinates of all the points.

        """
        return self[..., 2].view(type=ndarray)

    @property
    def xy(self):
        """Returns the X- and Y-coordinates of all points.

        Returns an ndarray with shape `self.shape` except last axis
        is reduced to 2, providing a view on the X- and Y-coordinates
        of all the points.

        """
        return self[..., :2].view(type=ndarray)

    @property
    def xz(self):
        """Returns the X- and Y-coordinates of all points.

        Returns an ndarray with shape `self.shape` except last axis
        is reduced to 2, providing a view on the X- and Z-coordinates
        of all the points.

        """
        return self[..., (0,2)].view(type=ndarray)

    @property
    def yz(self):
        """Returns the X- and Y-coordinates of all points.

        Returns an ndarray with shape `self.shape` except last axis
        is reduced to 2, providing a view on the Y- and Z-coordinates
        of all the points.

        """
        return self[..., 1:].view(type=ndarray)

    @property
    def xyz(self):
        """Returns the coordinates of all points as an ndarray.

        Returns an ndarray with shape `self.shape` except last axis
        is reduced to 2, providing a view on all the coordinates
        of all the points.

        """
        return self.view(type=ndarray)

    ################ property setters ##############
    @x.setter
    def x(self, value):
        """Set the X coordinates of the points"""
        self[...,0] = value

    @y.setter
    def y(self, value):
        """Set the Y coordinates of the points"""
        self[...,1] = value

    @z.setter
    def z(self, value):
        """Set the Z coordinates of the points"""
        self[...,2] = value

    @xy.setter
    def xy(self, value):
        """Set the XY coordinates of the points"""
        self[...,:2] = value

    @yz.setter
    def yz(self, value):
        """Set the YZ coordinates of the points"""
        self[...,(0,2)] = value

    @xz.setter
    def xz(self, value):
        """Set the XZ coordinates of the points"""
        self[...,1:] = value

    @xyz.setter
    def xyz(self, value):
        """Set the XYZ coordinates of the points"""
        self[...] = value

    ################ end property methods ##########


###########################################################################
    #
    #   Methods that return information about a Coords object or other
    #   views on the object data, without changing the object itself.

    # General

    def points(self):
        """Returns the :class:`Coords` object as a simple set of points.

        This reshapes the array to a 2-dimensional array, flattening
        the structure of the points.
        """
        return self.reshape((-1, 3))

    @property
    def coords(self):
        """Returns the `Coords` object .

        This is added for consistence with other classes.
        """
        return self

    def pshape(self):
        """Returns the shape of the :class:`Coords` object.

        This is the shape of the `NumPy`_ array with the last axis removed.
        The full shape of the :class:`Coords` array can be obtained from
        its shape attribute.
        """
        return self.shape[:-1]

    def npoints(self):
        """Return the total number of points."""
        return array(self.shape[:-1]).prod()

    ncoords = npoints


    # Size, Bounds

    def bbox(self):
        """Returns the bounding box of a set of points.

        The bounding box is the smallest rectangular volume in the global
        coordinates, such that no point of the :class:`Coords` are outside
        that volume.

        Returns a Coords object with shape(2,3): the first point contains the
        minimal coordinates, the second has the maximal ones.

        Example:

          >>> X = Coords([[[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]]])
          >>> print(X.bbox())
          [[ 0.  0.  0.]
           [ 3.  3.  0.]]
        """
        if self.size > 0:
            x = self.points()
            bb = row_stack([ x.min(axis=0), x.max(axis=0) ])
        else:
            o = origin()
            bb = [o, o]
        return Coords(bb)


    def center(self):
        """Returns the center of the :class:`Coords`.

        The center of a :class:`Coords` is the center of its bbox().
        The return value is a (3,) shaped :class:`Coords` object.

        Example:

          >>> X = Coords([[[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]]])
          >>> print(X.center())
          [ 1.5  1.5  0. ]

        See also: :meth:`centroid`
        """
        X0, X1 = self.bbox()
        return 0.5 * (X0+X1)


    def bboxPoint(self, position):
        """Returns a bounding box point of a Coords.

        Bounding box points are points whose coordinates are either
        the minimal value, the maximal value or the middle value
        for the Coords.
        Combining the three values in three dimensions results in
        3*3 = 27 alignment points. The corner points of the
        bounding box are a subset of these.

        The 27 points are addressed by a position string of three
        characters, one for each direction. Each character should be
        one of the following

        - '-': use the minimal value for that coordinate,
        - '+': use the minimal value for that coordinate,
        - '0': use the middle value for that coordinate.

        Any other character will set the corresponding coordinate to zero.

        A string '000' is equivalent with center(). The values '---' and
        '+++' give the points of the bounding box.

        Example:

          >>> X = Coords([[[0.,0.,0.],[1.,1.,1.]]])
          >>> print(X.bboxPoint('-0+'))
          [ 0.   0.5  1. ]

        See also :func:`align`.
        """
        bb = self.bbox()
        al = { '-': bb[0], '+': bb[1], '0': 0.5*(bb[0]+bb[1]) }
        pt = zeros(3)
        for i, c in enumerate(position):
            if c in al:
                pt[i] = al[c][i]
        return Coords(pt)


    def bboxPoints(self):
        """Returns all the corners of the bounding box point of a Coords.

        Returns a Coords (8,3). The points are in the order of a hex8
        element.
        """
        from pyformex.simple import cuboid
        return cuboid(*self.bbox()).coords


    def average(self,wts=None,axis=0):
        """Returns a (weighted) average of the :class:`Coords`.

        The average of a :class:`Coords` is a :class:`Coords` with one
        axis less than the original, obtained by averaging all the points
        along that axis.
        The weights array can either be 1-D (in which case its length must
        be the size along the given axis) or of the same shape as a.
        Weights can be specified as a 1-D array with the length of that axis,
        or as an array with the same shape as the :class:`Coords`.
        The sum of the weights (along the specified axis if not 1-D) will
        generally be equal to 1.0.
        If wts=None, then all points are assumed to have a weight equal to
        one divided by the length of the specified axis.

        Example:

          >>> X = Coords([[[0.,0.,0.],[1.,0.,0.],[2.,0.,0.]], \
                  [[4.,0.,0.],[5.,0.,0.],[6.,0.,0.]]])
          >>> print(X.average())
          [[ 2.  0.  0.]
           [ 3.  0.  0.]
           [ 4.  0.  0.]]
          >>> print(X.average(axis=1))
          [[ 1.  0.  0.]
           [ 5.  0.  0.]]
          >>> print(X.average(wts=[0.5,0.25,0.25],axis=1))
          [[ 0.75  0.    0.  ]
           [ 4.75  0.    0.  ]]
        """
        return average(self, weights=wts, axis=axis)


    def centroid(self):
        """Returns the centroid of the :class:`Coords`.

        The centroid of a :class:`Coords` is the point whose coordinates
        are the mean values of all points.
        The return value is a (3,) shaped :class:`Coords` object.

        Example:

          >>> print(Coords([[[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]]]).centroid())
          [ 1.  1.  0.]

        See also: :meth:`center`
        """
        return self.points().mean(axis=0)


    def centroids(self):
        return self


    def sizes(self):
        """Returns the sizes of the :class:`Coords`.

        Returns an array with the length of the bbox along the 3 axes.

        Example:

          >>> print(Coords([[[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]]]).sizes())
          [ 3.  3.  0.]

        """
        X0, X1 = self.bbox()
        return X1-X0


    def dsize(self):
        """Returns an estimate of the global size of the :class:`Coords`.

        This estimate is the length of the diagonal of the bbox().

        Example:

          >>> print(Coords([[[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]]]).dsize())
          4.24264

        """
        X0, X1 = self.bbox()
        return length(X1-X0)


    def bsphere(self):
        """Returns the diameter of the bounding sphere of the :class:`Coords`.

        The bounding sphere is the smallest sphere with center in the
        center() of the :class:`Coords`, and such that no points of the
        :class:`Coords` are lying outside the sphere.

        Example:

          >>> print(Coords([[[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]]]).bsphere())
          2.12132

        """
        return self.distanceFromPoint(self.center()).max()


    def bboxes(self):
        """Returns the bboxes of all elements in the coords array.

        The returned array has shape (...,2,3). Along the -2 axis
        are stored the minimal and maximal values of the Coords
        along that axis.
        """
        return minmax(self, axis=1)


    # Inertia

    @utils.warning("warn_inertia_changed")
    def inertia(self,mass=None):
        """Returns inertia related quantities of the :class:`Coords`.

        Parameters:

        - `mass`: float array with ncoords weight values. The default is to
          attribute a weight 1.0 to each point.

        Returns an :class:`inertia.Inertia` instance with attributes

        - `mass`: the total mass (float)
        - `ctr`: the center of mass: float (3,)
        - `tensor`: the inertia tensor in the central axes: shape (3,3)

        Example:

        >>> from pyformex.elements import Tet4
        >>> I = Tet4.vertices.inertia()
        >>> print(I.tensor)
        [[ 1.5   0.25  0.25]
         [ 0.25  1.5   0.25]
         [ 0.25  0.25  1.5 ]]
        >>> print(I.ctr)
        [ 0.25  0.25  0.25]
        >>> print(I.mass)
        4.0

        """
        from . import inertia
        M,C,I = inertia.point_inertia(self.points(), mass)
        I = inertia.Tensor(I)
        return inertia.Inertia(I,ctr=C,mass=M)


    def principalCS(self,mass=None):
        """Returns a CoordSys formed by the principal axes of inertia.

        Parameters:

        - `mass`: float array with ncoords weight values. The default is to
          attribute a weight 1.0 to each point.

        Returns a CoordSys corresponding to the principal axes of the
        inertia, computed with the specified mass.

        """
        from pyformex.coordsys import CoordSys
        I = self.inertia(mass)
        prin, axes = I.principal()
        return CoordSys(rot=axes,trl=I.ctr)


    def principalSizes(self):
        """Return the sizes in the principal directions of the Coords.

        Returns an array with the length of the bbox along the 3
        principal axes. This is a convenient shorthand for::

          self.toCS(self.principalCS()).sizes()

        Example:

          >>> print(Coords([[[0.,0.,0.],[3.,0.,0.]]]).rotate(30,2).principalSizes())
          [ 0.  0.  3.]

        """
        return self.toCS(self.principalCS()).sizes()


    def centralCS(self,mass=None):
        """Returns the central coordinate system of the Coords.

        Parameters:

        - `mass`: float array with ncoords weight values. The default is to
          attribute a weight 1.0 to each point.

        Returns a CoordSys with origin at the center of mass of the
        Coords and axes parallel to the global axes.

        """
        from . import inertia
        from pyformex.coordsys import CoordSys
        M,C = inertia.point_inertia(self.points(),mass)
        return CoordSys(trl=C)


    #  Distance

    def distanceFromPlane(self, p, n):
        """Returns the distance of all points from the plane (p,n).

        Parameters:

        - `p`: is a point specified by 3 coordinates.
        - `n`: is the normal vector to a plane, specified by 3 components.

        The return value is a float array with shape ``self.pshape()`` with
        the distance of each point to the plane through p and having normal n.
        Distance values are positive if the point is on the side of the
        plane indicated by the positive normal.

        Example:

          >>> X = Coords([[[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]]])
          >>> print(X.distanceFromPlane([0.,0.,0.],[1.,0.,0.]))
          [[ 0.  3.  0.]]

        """
        p = asarray(p).reshape((3))
        n = asarray(n).reshape((3))
        n = normalize(n)
        d = inner(self, n) - inner(p, n)
        return asarray(d)


    def distanceFromLine(self, p, n):
        """Returns the distance of all points from the line (p,n).

        p,n are (1,3) or (npts,3) arrays defining 1 or npts lines

        Parameters:

        - `p`: is a point on the line specified by 3 coordinates.
        - `n`: is a vector specifying the direction of the line through p.

        The return value is a [...] shaped array with the distance of
        each point to the line through p with direction n.
        All distance values are positive or zero.

        Example:

        >>> X = Coords([[0.,0.,0.],[2.,0.,0.],[1.,3.,0.],[-1.,0.,0.]])
        >>> print(X.distanceFromLine([0.,0.,0.],[1.,1.,0.]))
        [ 0.    1.41  1.41  0.71]

        """
        p = asarray(p).reshape((3))
        n = asarray(n).reshape((3))
        n = normalize(n)
        xp = self-p
        xpt = dotpr(xp,n)
        a = dotpr(xp,xp)-xpt*xpt
        return sqrt(a.clip(0))


    def distanceFromPoint(self, p):
        """Returns the distance of all points from the point p.

        Parameters:

        - `p`: array_like (3): coordinates of a point in space

        Returns a [...] shaped array with the distance of
        each point to point p.
        All distance values are positive or zero.

        Example:

        >>> X = Coords([[[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]]])
        >>> print(X.distanceFromPoint([0.,0.,0.]))
        [[ 0.  3.  3.]]

        """
        p = asarray(p).reshape((3))
        return length(self-p)


    def closestToPoint(self, p, return_dist=False):
        """Returns the point closest to a given point p.

        Parameters:

        - `p`: array_like (3): coordinates of a point in space

        Returns: int: the index of the point in the Coords that has the
        minimal Euclidean distance to the point 'p'. Use this index
        with self.points() to get the coordinates of that point.

        Example:

        >>> X = Coords([[[0.,0.,0.],[3.,0.,0.],[0.,3.,0.]]])
        >>> X.closestToPoint([2.,0.,0.])
        1
        >>> X.closestToPoint([2.,0.,0.],True)
        (1, 1.0)

        """
        d = self.distanceFromPoint(p)
        i = d.argmin()
        if return_dist:
            return i,d.flat[i]
        else:
            return i


    def directionalSize(self,n,p=None,points=False):
        """Returns the extreme distances from the plane p,n.

        Parameters:

        - `n`: the direction can be specified by a 3 component vector or by
          a single integer 0..2 designating one of the coordinate axes.

        - `p`: is a point in space. If not specified, it is taken as the
          center() of the Coords.

        - `points`: bool. If True, returns the extremal tangent points
          instead of the distances of the extremal tangent planes.

        The default return value is a tuple of two float values specifying the
        distances of the extremal tangent planes parallel with the plane (p,n)
        to the said plane. If `point` is True, returns a tuple with the
        extremal tangent points instead.

        See also :meth:`directionalExtremes`
        """
        n = unitVector(n)

        if p is None:
            p = self.center()
        else:
            p = Coords(p)

        d = self.distanceFromPlane(p, n)
        dmin, dmax = d.min(), d.max()

        if points:
            return [p+dmin*n, p+dmax*n]
        else:
            return dmin, dmax


    def directionalExtremes(self,n,p=None):
        """Returns extremal planes in the direction n.

        `n` and `p` have the same meaning as in `directionalSize`.

        The return value is a list of two points on the line (p,n),
        such that the planes with normal n through these points define
        the extremal tangent planes of the Coords.

        This is a shorthand for using :meth:`directionalSize` with the
        `points` argument True.
        """
        return self.directionalSize(n, p, points=True)


    def directionalWidth(self, n):
        """Returns the width of a Coords in the given direction.

        The direction can be specified by a 3 component vector or by
        a single integer 0..2 designating one of the coordinate axes.

        The return value is the thickness of the object in the direction n.
        """
        dmin, dmax = self.directionalSize(n)
        return dmax-dmin

    # Test position

    def test(self,dir=0,min=None,max=None,atol=0.):
        """Flag points having coordinates between min and max.

        Tests the position of the points of the :class:`Coords` with respect to
        one or two planes. This method is very convenient in clipping a
        :class:`Coords` in a specified direction. In most cases the clipping
        direction is one of the global cooordinate axes, but a general
        direction may be used as well.

        Parameters:

        - `dir`: either a global axis number (0, 1 or 2) or a direction vector
          consisting of 3 floats. It specifies the direction in which the
          distances are measured. Default is the 0 (or x) direction.

        - `min`, `max`: position of the minimum and maximum clipping planes.
          If `dir` was specified as an integer (0,1,2), this is a single float
          value corresponding with the coordinate in that axis direction.
          Else, it is a point in the clipping plane with normal direction `dir`.
          One of the two clipping planes may be left unspecified.


        Returns:

          A 1D integer array with same length as the number of points.
          For each point the value is 1 (True) if the point is above the
          minimum clipping plane and below the maximum clipping plane,
          or 0 (False) otherwise.
          An unspecified clipping plane corresponds with an infinitely low or
          high value. The return value can directly be used as an index to
          obtain a :class:`Coords` with the points satisfying the test (or not).
          See the examples below.

        Example:

        >>> x = Coords([[0.,0.],[1.,0.],[0.,1.],[0.,2.]])
        >>> print(x.test(min=0.5))
        [False  True False False]
        >>> t = x.test(dir=1,min=0.5,max=1.5)
        >>> print(x[t])
        [[ 0.  1.  0.]]
        >>> print(x[~t])
        [[ 0.  0.  0.]
         [ 1.  0.  0.]
         [ 0.  2.  0.]]

        """
        if min is None and max is None:
            raise ValueError("At least one of min or max have to be specified.")

        if array(dir).size == 1:
            if min is not None:
                T1 = self[..., dir] > (min - atol)
            if max is not None:
                T2 = self[..., dir] < (max + atol)
        else:
            if min is not None:
                T1 = self.distanceFromPlane(min, dir) > - atol
            if max is not None:
                T2 = self.distanceFromPlane(max, dir) < atol

        if min is None:
            T = T2
        elif max is None:
            T = T1
        else:
            T = T1 * T2
        return asarray(T)


    ## THIS IS A CANDIDATE FOR THE LIBRARY
    ## (possibly in a more general arrayprint form)
    ## (could be common with calpy)

    def fprint(self,fmt="%10.3e %10.3e %10.3e"):
        """Formatted printing of a :class:`Coords` object.

        The supplied format should contain 3 formatting sequences for the
        three coordinates of a point.
        """
        for p in self.points():
            print(fmt % tuple(p))



##############################################################################

    def set(self, f):
        """Set the coordinates from those in the given array."""
        self[...] = f      # do not be tempted to use self = f !

##############################################################################
    #
    #   Transformations that preserve the topology (but change coordinates)
    #
    #   A. Affine transformations
    #
    #      Scaling
    #      Translation
    #      Central Dilatation = Scaling + Translation
    #      Rotation
    #      Shear
    #      Reflection
    #      Affine
    #
    #  The following methods return transformed coordinates, but by default
    #  they do not change the original data. If the optional argument inplace
    #  is set True, however, the coordinates are changed inplace.


    def scale(self,scale,dir=None,center=None,inplace=False):
        """Returns a copy scaled with scale[i] in direction i.

        The scale should be a list of 3 scaling factors for the 3 axis
        directions, or a single scaling factor.
        In the latter case, dir (a single axis number or a list) may be given
        to specify the direction(s) to scale. The default is to produce a
        homothetic scaling.
        The center of the scaling, if not specified, is the global origin.
        If a center is specified, the result is equivalent to::

          self.translate(-center).scale(scale,dir).translate(center)

        Example:

        >>> print(Coords([1.,1.,1.]).scale(2))
        [ 2.  2.  2.]
        >>> print(Coords([1.,1.,1.]).scale([2,3,4]))
        [ 2.  3.  4.]
        >>> print(Coords([1.,1.,1.]).scale(2,dir=[1,2]))
        [ 1.  2.  2.]

        """
        if center is not None:
            center = asarray(center)
            return self.trl(-center).scale(scale, dir).translate(center)

        if inplace:
            out = self
        else:
            out = self.copy()
        if dir is None:
            out *= scale
        else:
            out[..., dir] *= scale
        return out


    def translate(self,dir,step=None,inplace=False):
        """Translate a :class:`Coords` object.

        Translates the Coords in the direction `dir` over a distance
        `step * length(dir)`.

        Parameters:

        - `dir`: specifies the direction and distance of the translation. It
          can be either

          - an axis number (0,1,2), specifying a unit vector in the direction
            of one of the coordinate axes.
          - a single translation vector,
          - an array of translation vectors, compatible with the Coords shape.

        - `step`: If specified, the translation vector specified by `dir` will
          be multiplied with this value. It is commonly used with unit `dir`
          vectors to set the translation distance.

        Example:

        >>> x = Coords([1.,1.,1.])
        >>> print(x.translate(1))
        [ 1.  2.  1.]
        >>> print(x.translate(1,1.))
        [ 1.  2.  1.]
        >>> print(x.translate([0,1,0]))
        [ 1.  2.  1.]
        >>> print(x.translate([0,2,0],0.5))
        [ 1.  2.  1.]

        """
        if inplace:
            out = self
        else:
            out = self.copy()
        if isinstance(dir, int):
            dir = unitVector(dir)
        dir = Coords(dir, copy=True)
        if step is not None:
            dir *= step
        out += dir
        return out


    def centered(self):
        """Returns a centered copy of the Coords.

        Returns a Coords which is a translation thus that the center
        coincides with the origin.
        This is equivalent with::

          self.trl(-self.center())

        """
        return self.trl(-self.center())


    def align(self,alignment='---',point=[0., 0., 0.]):
        """Align a Coords on a given point.

        Alignment involves a translation such that the bounding box
        of the Coords object becomes aligned with a given point.
        By default this point is the origin of the global axes.
        The bounding box alignment is done by a translation of one
        of the bounding box points (see :func:`bboxPoint`) to the
        target point.

        The requested alignment is determined by a string of three characters,
        one for each of the coordinate axes. The character determines how
        the structure is aligned in the corresponding direction:

        - '-': aligned on the minimal value of the bounding box,
        - '+': aligned on the maximal value of the bounding box,
        - '0': aligned on the middle value of the bounding box.

        Any other value will make the alignment in that direction unchanged.

        The default alignment string ``'---'`` results in a translation which
        puts all the points in the octant with all positive coordinate values.
        A string ``'000'`` will center the object around the origin, just like
        the (slightly faster) :meth:`centered` method.

        See also the :func:`coords.align` function for aligning objects
        with respect to each other.
        """
        return self.translate(point-self.bboxPoint(alignment))


    def rotate(self,angle,axis=2,around=None):
        """Returns a copy rotated over angle around axis.

        The angle is specified in degrees.
        The axis is either one of (0,1,2) designating the global axes,
        or a vector specifying an axis through the origin.
        If no axis is specified, rotation is around the 2(z)-axis. This is
        convenient for working on 2D-structures.

        As a convenience, the user may also specify a 3x3 rotation matrix,
        in which case the function rotate(mat) is equivalent to affine(mat).

        All rotations are performed around the point [0.,0.,0.], unless a
        rotation origin is specified in the argument 'around'.
        """
        mat = asarray(angle)
        if mat.size == 1:
            mat = rotationMatrix(angle, axis)
        if mat.shape != (3, 3):
            raise ValueError("Rotation matrix should be 3x3")
        if around is not None:
            around = asarray(around)
            out = self.translate(-around)
        else:
            out = self
        return out.affine(mat, around)


    def shear(self,dir,dir1,skew,inplace=False):
        """Returns a copy skewed in the direction dir of plane (dir,dir1).

        The coordinate dir is replaced with (dir + skew * dir1).
        """
        if inplace:
            out = self
        else:
            out = self.copy()
        out[..., dir] += skew * out[..., dir1]
        return out


    # TODO: THIS SHOULD BE GENERALIZED TO TAKE SAME `dir` OPTIONS AS translate
    # NOT SURE: now using dir=[0,1] or dir=[0,1,2] would mirror w.r.t an
    # axis, resp. a point!
    #
    def reflect(self,dir=0,pos=0.,inplace=False):
        """Reflect the coordinates in direction dir against plane at pos.

        Parameters:

        - `dir`: int: direction of the reflection (default 0)
        - `pos`: float: offset of the mirror plane from origin (default 0.0)
        - `inplace`: boolean: change the coordinates inplace (default False)
        """
        if inplace:
            out = self
        else:
            out = self.copy()
        out[..., dir] = 2*pos - out[..., dir]
        return out


    def affine(self,mat,vec=None):
        """Perform a general affine transformation.

        Parameters:

        - `mat`: a 3x3 float matrix
        - `vec`: a length 3 list or array of floats

        The returned object has coordinates given by ``self * mat + vec``.
        If `mat` is a rotation matrix, than the operation performs a
        rigid rotation of the object plus a translation.
        """
        out = dot(self, mat)
        if vec is not None:
            out += vec
        return out


    def toCS(self,cs):
        """Transform the coordinates to another CoordSys.

        Parameters:

        - `cs`: :class:`coordsys.CoordSys`

        Returns an object identical to the input but having global coordinates
        equal to the coordinates of the input object in the cs CoordSys.

        This is the inverse transformation of :method:`fromCS`.
        """
        return self.trl(-cs.trl).rot(cs.rot.transpose())


    def fromCS(self,cs):
        """Transform the coordinates from another CoordSys.

        Parameters:

        - `cs`: :class:`CoordSys`

        Returns an object identical to the input but transformed in the
        same way as the global axes have been transformed to obtain the
        CoordSys cs.

        This is the inverse transformation of :method:`toCS`.

        """
        return self.rot(cs.rot).trl(cs.trl)


    def position(self, x, y):
        """Position an object so that points x are aligned with y.

        Parameters are as for :func:`arraytools.trfMatrix`
        """
        r, t =  trfMatrix(x, y)
        return self.affine(r, t)

#
#
#   B. Non-Affine transformations.
#
#      These always return copies !
#
#        Cylindrical, Spherical, Isoparametric
#

    def cylindrical(self,dir=[0, 1, 2],scale=[1., 1., 1.],angle_spec=DEG):
        """Converts from cylindrical to cartesian after scaling.

        Parameters:

        - `dir`: specifies which coordinates are interpreted as resp.
          distance(r), angle(theta) and height(z). Default order is [r,theta,z].
        - `scale`: will scale the coordinate values prior to the transformation.
          (scale is given in order r,theta,z).

        The resulting angle is interpreted in degrees.
        """
        # We put in a optional scaling, because doing this together with the
        # transforming is cheaper than first scaling and then transforming.
        f = zeros_like(self)
        theta = (scale[1]*angle_spec) * self[..., dir[1]]
        r = scale[0] * self[..., dir[0]]
        f[..., 0] = r*cos(theta)
        f[..., 1] = r*sin(theta)
        f[..., 2] = scale[2] * self[..., dir[2]]
        return f


    def hyperCylindrical(self,dir=[0, 1, 2],scale=[1., 1., 1.],rfunc=None,zfunc=None,angle_spec=DEG):
        if rfunc is None:
            rfunc = lambda x:1
        if zfunc is None:
            zfunc = lambda x:1
        f = zeros_like(self)
        theta = (scale[1]*angle_spec) * self[..., dir[1]]
        r = scale[0] * rfunc(theta) * self[..., dir[0]]
        f[..., 0] = r * cos(theta)
        f[..., 1] = r * sin(theta)
        f[..., 2] = scale[2] * zfunc(theta) * self[..., dir[2]]
        return f


    def toCylindrical(self,dir=[0, 1, 2],angle_spec=DEG):
        """Converts from cartesian to cylindrical coordinates.

        Parameters:

        - `dir`: specifies which coordinates axes are parallel to respectively the
          cylindrical axes distance(r), angle(theta) and height(z). Default
          order is [x,y,z].

        The angle value is given in degrees.
        """
        f = zeros_like(self)
        x, y, z = [ self[..., i] for i in dir ]
        f[..., 0] = sqrt(x*x+y*y)
        f[..., 1] = arctand2(y, x, angle_spec)
        f[..., 2] = z
        return f


    def spherical(self,dir=[0, 1, 2],scale=[1., 1., 1.],angle_spec=DEG,colat=False):
        """Converts from spherical to cartesian after scaling.

        Parameters:

        - `dir`: specifies which coordinates are interpreted as resp.
          longitude(theta), latitude(phi) and distance(r).
        - `scale`: will scale the coordinate values prior to the transformation.

        Angles are interpreted in degrees.
        Latitude, i.e. the elevation angle, is measured from equator in
        direction of north pole(90). South pole is -90.

        If colat=True, the third coordinate is the colatitude (90-lat) instead.
        """
        f = self.reshape((-1, 3))
        theta = (scale[0]*angle_spec) * f[:, dir[0]]
        phi = (scale[1]*angle_spec) * f[:, dir[1]]
        r = scale[2] * f[:, dir[2]]
        if colat:
            phi = 90.0*angle_spec - phi
        rc = r*cos(phi)
        f = column_stack([rc*cos(theta), rc*sin(theta), r*sin(phi)])
        return f.reshape(self.shape)


    def superSpherical(self,n=1.0,e=1.0,k=0.0, dir=[0, 1, 2],scale=[1., 1., 1.],angle_spec=DEG,colat=False):
        """Performs a superspherical transformation.

        superSpherical is much like spherical, but adds some extra
        parameters to enable the creation of virtually any surface.

        Just like with spherical(), the input coordinates are interpreted as
        the longitude, latitude and distance in a spherical coordinate system.

        Parameters:

        - `dir`: specifies which coordinates are interpreted as resp.longitude(theta),
          latitude(phi) and distance(r).
          Angles are then interpreted in degrees.
          Latitude, i.e. the elevation angle, is measured from equator in
          direction of north pole(90). South pole is -90.
          If colat=True, the third coordinate is the colatitude (90-lat) instead.

        - `scale`: will scale the coordinate values prior to the transformation.

        - `n`, `e`: parameters define exponential transformations of the
          north_south (latitude), resp. the east_west (longitude) coordinates.
          Default values of 1 result in a circle.

        - `k`: adds 'eggness' to the shape: a difference between the northern and
          southern hemisphere. Values > 0 enlarge the southern hemishpere and
          shrink the northern.
        """
        def c(o, m):
            c = cos(o)
            return sign(c)*abs(c)**m
        def s(o, m):
            c = sin(o)
            return sign(c)*abs(c)**m

        f = self.reshape((-1, 3))
        theta = (scale[0]*angle_spec) * f[:, dir[0]]
        phi = (scale[1]*angle_spec) * f[:, dir[1]]
        r = scale[2] * f[:, dir[2]]
        if colat:
            phi = 90.0*angle_spec - phi
        rc = r*c(phi, n)
        if k != 0:   # k should be > -1.0 !!!!
            x = sin(phi)
            rc *= (1.-k*x)/(1.+k*x)
        f = column_stack([rc*c(theta, e), rc*s(theta, e), r*s(phi, n)])
        return f.reshape(self.shape)


    def toSpherical(self,dir=[0, 1, 2],angle_spec=DEG):
        """Converts from cartesian to spherical coordinates.

        Parameters:

        - `dir`: specifies which coordinates axes are parallel to respectively
          the spherical axes distance(r), longitude(theta) and latitude(phi).
          Latitude is the elevation angle measured from equator in direction
          of north pole(90). South pole is -90.
          Default order is [0,1,2], thus the equator plane is the (x,y)-plane.

        The returned angle values are given in degrees.
        """
        v = self[..., dir].reshape((-1, 3))
        dist = sqrt(sum(v*v,-1))
        long = arctand2(v[:,0], v[:,2], angle_spec)
        lat = where(dist <= 0.0, 0.0, arcsind(v[:,1]/dist, angle_spec))
        f = column_stack([long, lat, dist])
        return f.reshape(self.shape)


    def bump1(self, dir, a, func, dist):
        """Returns a :class:`Coords` with a one-dimensional bump.

        Parameters:

        - `dir`: specifies the axis of the modified coordinates;
        - `a`: is the point that forces the bumping;
        - `dist`: specifies the direction in which the distance is measured;
        - `func`: is a function that calculates the bump intensity from distance
          and should be such that ``func(0) != 0``.
        """
        f = self.copy()
        d = f[..., dist] - a[dist]
        f[..., dir] += func(d)*a[dir]/func(0)
        return f


    def bump2(self, dir, a, func):
        """Returns a :class:`Coords` with a two-dimensional bump.

        Parameters:

        - `dir`: specifies the axis of the modified coordinates;
        - `a`: is the point that forces the bumping;
        - `func`: is a function that calculates the bump intensity from distance
          !! func(0) should be different from 0.
        """
        f = self.copy()
        dist = [0, 1, 2]
        dist.remove(dir)
        d1 = f[..., dist[0]] - a[dist[0]]
        d2 = f[..., dist[1]] - a[dist[1]]
        d = sqrt(d1*d1+d2*d2)
        f[..., dir] += func(d)*a[dir]/func(0)
        return f


    # This is a generalization of both the bump1 and bump2 methods.
    # If it proves to be useful, it might replace them one day

    # An interesting modification might be to have a point for definiing
    # the distance and a point for defining the intensity (3-D) of the
    # modification
    def bump(self,dir,a,func,dist=None):
        """Returns a :class:`Coords` with a bump.

        A bump is a modification of a set of coordinates by a non-matching
        point. It can produce various effects, but one of the most common
        uses is to force a surface to be indented by some point.

        Parameters:

        - `dir`: specifies the axis of the modified coordinates;
        - `a`: is the point that forces the bumping;
        - `func`: is a function that calculates the bump intensity from distance
          (!! func(0) should be different from 0)
        - `dist`: is the direction in which the distance is measured : this can
          be one of the axes, or a list of one or more axes.
          If only 1 axis is specified, the effect is like function bump1
          If 2 axes are specified, the effect is like bump2
          This function can take 3 axes however.
          Default value is the set of 3 axes minus the direction of
          modification. This function is then equivalent to bump2.
        """
        f = self.copy()
        if dist is None:
            dist = [0, 1, 2]
            dist.remove(dir)
        try:
            l = len(dist)
        except TypeError:
            l = 1
            dist = [dist]
        d = f[..., dist[0]] - a[dist[0]]
        if l==1:
            d = abs(d)
        else:
            d = d*d
            for i in dist[1:]:
                d1 = f[..., i] - a[i]
                d += d1*d1
            d = sqrt(d)
        f[..., dir] += func(d)*a[dir]/func(0)
        return f


    def flare (self,xf,f,dir=[0, 2],end=0,exp=1.):
        """Create a flare at the end of a :class:`Coords` block.

        The flare extends over a distance ``xf`` at the start (``end=0``)
        or end (``end=1``) in direction ``dir[0]`` of the coords block,
        and has a maximum amplitude of ``f`` in the ``dir[1]`` direction.
        """
        ix, iz = dir
        bb = self.bbox()
        if end == 0:
            xmin = bb[0][ix]
            endx = self.test(dir=ix, max=xmin+xf)
            func = lambda x: (1.-(x-xmin)/xf) ** exp
        else:
            xmax = bb[1][ix]
            endx = self.test(dir=ix, min=xmax-xf)
            func = lambda x: (1.-(xmax-x)/xf) ** exp
        x = self.copy()
        x[endx, iz] += f * func(x[endx, ix])
        return x


    def map(self, func):
        """Map a :class:`Coords` by a 3-D function.

        This is one of the versatile mapping functions.

        Parameters:

        - `func`: is a numerical function which takes three arguments and produces
          a list of three output values. The coordinates [x,y,z] will be
          replaced by func(x,y,z).

        The function must be applicable to arrays, so it should
        only include numerical operations and functions understood by the
        numpy module.
        This method is one of several mapping methods. See also map1 and mapd.

        Example:

          >>> print(Coords([[1.,1.,1.]]).map(lambda x,y,z: [2*x,3*y,4*z]))
          [[ 2.  3.  4.]]

        """
        # flatten coordinate sets to ease use of complicated functions
        # we should probably do this for map1 and mapd too
        X = self.points()
        f = zeros_like(X)
        f[..., 0], f[..., 1], f[..., 2] = func(X.x, X.y, X.z)
        return f.reshape(self.shape)


    def map1(self,dir,func,x=None):
        """Map one coordinate by a 1-D function of one coordinate.

        Parameters:

        - `func`: is a numerical function which takes one argument and produces
          one result. The coordinate dir will be replaced by func(coord[x]).
          If no x is specified, x is taken equal to dir.

        The function must be applicable on arrays, so it should only
        include numerical operations and functions understood by the
        numpy module.
        This method is one of several mapping methods. See also map and mapd.
        """
        if x is None:
            x = dir
        f = self.copy()
        f[..., dir] = func(self[..., x])
        return f


    def mapd(self,dir,func,point=[0., 0., 0.],dist=None):
        """Map one coordinate by a function of the distance to a point.

        Parameters:

        - `dir`: 0, 1 or 2: the coordinate that will be replaced with
          ``func(d)``, where `d` is calculated as the distance to `point`.
        - `func`: a numerical function which takes one float argument and
          produce one float result. The function must be applicable on arrays,
          so it should only include numerical operations and functions
          understood by the :mod:`numpy` module.
        - `point`: the point to where the distance `d` is computed.
        - `dist`: a list of coordinate directions that are used to compute
          the distances `d`. It can also be a single coordinate direction.
          The default is to use 3-D distances.

        This method is one of several mapping methods. See also
        :meth:`map3` and :meth:`map1`.

        Example::

          E.mapd(2,lambda d:sqrt(10**2-d**2),E.center(),[0,1])

        maps ``E`` on a sphere with radius 10.
        """
        f = self.copy()
        if dist is None:
            dist = [0, 1, 2]
        try:
            l = len(dist)
        except TypeError:
            l = 1
            dist = [dist]
        d = f[..., dist[0]] - point[dist[0]]
        if l==1:
            d = abs(d)
        else:
            d = d*d
            for i in dist[1:]:
                d1 = f[..., i] - point[i]
                d += d1*d1
            d = sqrt(d)
        f[..., dir] = func(d)
        return f


    def egg(self, k):
        """Maps the coordinates to an egg-shape"""
        return (1.-k*self)/(1.+k*self)


    def replace(self,i,j,other=None):
        """Replace the coordinates along the axes i by those along j.

        i and j are lists of axis numbers or single axis numbers.
        replace ([0,1,2],[1,2,0]) will roll the axes by 1.
        replace ([0,1],[1,0]) will swap axes 0 and 1.
        An optionally third argument may specify another :class:`Coords` object to take
        the coordinates from. It should have the same dimensions.
        """
        if other is None:
            other = self
        f = self.copy()
        f[..., i] = other[..., j]
        return f


    def swapAxes(self, i, j):
        """Swap coordinate axes i and j.

        Beware! This is different from numpy's swapaxes() method !
        """
        return self.replace([i, j], [j, i])


    def rollAxes(self,n=1):
        """Roll the axes over the given amount.

        Default is 1, thus axis 0 becomes the new 1 axis, 1 becomes 2 and
        2 becomes 0.
        """
        return roll(self, int(n) % 3, axis=-1)


    def projectOnPlane(self,n=2,P=[0., 0., 0.]):
        """Project a :class:`Coords` on a plane (or planes).

        Parameters:

        - `n`: the normal direction to the plane. It can be specified either
          by a list of three floats, or by a single integer (0, 1 or 2) to
          specify a plane perpendicular to one of the global axes.
        - `P`: a point in the plane, by default the global origin.

        .. note:: For a plane parallel to a coordinate plane, it is far more
          efficient to specify the normal by an axis number than by a
          three component vector.

        .. note:: This method will also work if any or both of P and n have
          the same shape as self, or can be reshaped to the same shape.
          This allows to project each point on its individual plane.

        Returns a :class:`Coords` with same shape as the original, with all
        the points projected on the specified plane(s).
        """
        x = self.reshape(-1,3).copy()
        P = Coords(P).reshape(-1, 3)
        if isinstance(n, int):
            x[:, n] = P[:, n]
        else:
            n = normalize(Coords(n).reshape(-1, 3))
            d = dotpr(n, x-P).reshape(-1,1)
            x -= d * n
        return x.reshape(self.shape)


    def projectOnSphere(self,radius=1.,center=[0., 0., 0.]):
        """Project :class:`Coords` on a sphere.

        The default sphere is a unit sphere at the origin.
        The center of the sphere should not be part of the :class:`Coords`.
        """
        d = self.distanceFromPoint(center)
        s = radius / d
        f = self - center
        for i in range(3):
            f[..., i] *= s
        f += center
        return f


    def projectOnCylinder(self,radius=1.,dir=0,center=[0., 0., 0.]):
        """Project the Coords on a cylinder with axis parallel to a global axis.

        The default cylinder has its axis along the x-axis and a unit radius.
        No points of the :class:`Coords` should belong to the axis..
        """
        d = self.distanceFromLine(center, unitVector(dir))
        s = radius / d
        c = resize(asarray(center), self.shape)
        c[..., dir] = self[..., dir]
        f = self - c
        for i in range(3):
            if i != dir:
                f[..., i] *= s
        f += c
        return f


    def projectOnSurface(self,S,dir=0,missing='error', return_indices=False):
        """Project the Coords on a triangulated surface.

        The points of the Coords are projected in the specified direction dir
        onto the surface S.

        Parameters:

        - `S`: TriSurface: any triangulated surface
        - `dir`: int or vector: specifies the direction of the projection
        - `missing`: float value or a string. Specifies a distance to set
          the position of the projection point in cases where the projective
          line does not cut the surface. The sign of the distance is taken
          into account. If specified as a string, it should be one of the
          strings 'c', 'f', or 'm', possibly preceded by a '+' or '-'.
          The distance will then be taken equal to the closest,
          the furthest, or the mean distance of a point to its projection,
          and applied in positive or negative direction as specified.
          Any other value of missing will result in an error if some point
          does not have any projection. An error will also be raised if not
          a single point projection intersects the surface.
        - `return_indices`: if True, also returns an index of the points that
          have a projection on the surface.

        Returns:

          A Coords with the same shape as the input. If `return_indices`
          is True, also returns an index of the points that have a projection
          on the surface. This index is a sequential one, no matter what the
          shape of the input Coords is.

        >>> from pyformex import simple
        >>> S = simple.sphere().scale(2)
        >>> x = pattern('0123')
        >>> print(x)
        [[ 0.  0.  0.]
         [ 1.  0.  0.]
         [ 1.  1.  0.]
         [ 0.  1.  0.]]
        >>> xp = x.projectOnSurface(S,[0.,0.,1.])
        >>> print(xp)
        [[ 0.    0.    2.  ]
         [ 1.    0.   -1.72]
         [ 1.    1.   -1.4 ]
         [ 0.    1.    1.73]]
        """
        from pyformex import olist
        from pyformex.geomtools import anyPerpendicularVector
        try:
            missing = float(missing)
        except:
            if isinstance(missing, str) and len(missing) > 0:
                if missing[0] not in '+-':
                    missing = '+' + missing
                missing = missing[:2]
            else:
                missing = None

        if isinstance(dir, int):
            dir = unitVector()
        else:
            dir = asarray(dir)
        x = self.reshape(-1, 3)
        # Create planes through x in direction n
        # WE SHOULD MOVE THIS TO geomtools?
        v1 = anyPerpendicularVector(dir)
        v2 = cross(dir, v1)
        # Create set of cuts with set of planes
        cuts = [ S.intersectionWithPlane(xi, v1) for xi in x ]
        nseg = [ c.nelems() for c in cuts ]
        # remove the empty intersections
        cutid = [ i for i, n in enumerate(nseg) if n > 0 ]
        cuts = olist.select(cuts, cutid)

        # cut the cuts with second set of planes
        cuts = [ c.toFormex().intersectionWithPlane(xi, v2).coords for c, xi in zip(cuts, x[cutid]) ]
        npts = [ p.shape[0] for p in cuts ]
        okid = [ i for i, n in enumerate(npts) if n > 0 ]
        # remove the empty intersections
        cutid = olist.select(cutid, okid)
        cuts = olist.select(cuts, okid)

        # find the points closest to self
        cuts = [ p.points()[p.closestToPoint(xi)] for p, xi in zip(cuts, x[cutid]) ]
        cuts = Coords.concatenate(cuts)

        if cuts.size == 0:
            raise ValueError("The projection does not intersect with the surface")
        if cuts.shape[0] < x.shape[0]:
            # fill in missing values or raise error
            if isinstance(missing, float):
                d = missing
            elif missing[1] in 'cfm':
                d = length(x[cutid] - cuts)
                if missing[1]=='c':
                    d = d.min()
                elif missing[1]=='f':
                    d = d.max()
                elif missing[1]=='m':
                    d = 0.5*(d.min()+d.max())
                if missing[0] == '-':
                    d *= -1.
                x = x.trl(d*dir)
                x[cutid] = cuts
            else:
                raise ValueError("The projection of some point(s) in the specified direction does not cut the surface")
        else:
            x = cuts

        x = x.reshape(self.shape)
        if return_indices:
            return x, cutid
        else:
            return x


    # Extra transformations implemented by plugins

    def isopar(self, eltype, coords, oldcoords):
        """Perform an isoparametric transformation on a Coords.

        This is a convenience method to transform a Coords object through
        an isoparametric transformation. It is equivalent to::

          Isopar(eltype,coords,oldcoords).transform(self)

        See :mod:`plugins.isopar` for more details.
        """
        from pyformex.plugins.isopar import Isopar
        return Isopar(eltype, coords, oldcoords).transform(self)


    def transformCS(self,currentCS,initialCS=None):
        """Perform a coordinate system transformation on the Coords.

        This method transforms the Coords object by the transformation that
        turns the initial coordinate system into the current coordinate system.

        currentCS and initialCS can be either :class:`CoordSys` instances or
        or (4,3) shaped Coords instances that can be used to initialize
        a :class:`CoordSys` with the points argument.

        If initialCS is None, the global (x,y,z) axes are used.
        For example, the default initialCS and a currentCS equal to::

           0.  1.  0.
          -1.  0.  0.
           0.  0.  1.
           0.  0.  0.

        result in a rotation of 90 degrees around the z-axis.

        """
        # This is currently implemented using isopar, but could
        # obviously also be done using affine
        # or fromCS and toCS
        return self.isopar('tet4', currentCS.points(), initialCS.points())


    def addNoise(self,rsize=0.05,asize=0.0):
        """Add random noise to a Coords.

        A random amount is added to eacho individual coordinate in the Coords.
        The difference of any coordinate from its original value will
        not be r than ``asize+rsize*self.sizes().max()``. The default
        is to set it to 0.05 times the geometrical size of the structure.
        """
        max = asize + rsize * self.sizes().max()
        return self + randomNoise(self.shape, -max, +max)


############################################################################
    #
    #   Transformations that change the shape of the Coords array
    #


    def replicate(self,n,dir=0,step=None):
        """Replicate a Coords n times with fixed step in any direction.

        Returns a Coords object with shape `(n,) + self.shape`, thus having
        an extra first axis.
        Each component along the axis 0 is equal to the previous component
        translated over `(dir,step)`, where `dir` and `step` are
        interpreted just like in the :meth:`translate` method.
        The first component along the axis 0 is identical to the
        original Coords.
        """
        n = int(n)
        if isinstance(dir, int):
            dir = unitVector(dir)
        dir = Coords(dir, copy=True)
        if step is not None:
            dir *= step
        f = resize(self, (n,)+self.shape)
        for i in range(1, n):
            f[i] += i*dir
        return Coords(f)


    def split(self):
        """Split the coordinate array in blocks along first axis.

        The result is a sequence of arrays with shape self.shape[1:].
        Raises an error if self.ndim < 2.
        """
        if self.ndim < 2:
            raise ValueError("Can only split arrays with dim >= 2")
        return [ self[i] for i in range(self.shape[0]) ]


    def sort(self,order=[0, 1, 2]):
        """Sort points in the specified order of their coordinates.

        The points are sorted based on their coordinate values. There is a
        maximum number of points (above 2 million) that can be sorted. If you
        need to sort more, first split up your data according to the first
        axis.

        Parameters:

        - `order`: permutation of [0,1,2], specifying the order in which
          the subsequent axes are used to sort the points.

        Returns:

          An int array which is a permutation of range(self.npoints()).
          If taken in the specified order, it is guaranteed that no point can
          have a coordinate that is larger than the corresponding coordinate
          of the next point.
        """
        n = self.shape[0]
        nmax = iinfo('int64').max # max integer, a bit above 2 million
        if n > nmax:
            raise ValueError("I can only sort %s points" % nmax)
        s0, s1, s2 = [ argsort(self[..., i]) for i in range(3) ]
        i0, i1, i2 = [ inverseUniqueIndex(i) for i in [s0, s1, s2] ]
        val = i2 + n * (i1 + n * i0)
        return argsort(val)


    def boxes(self,ppb=1,shift=0.5,minsize=1.e-5):
        """Create a grid of equally sized boxes spanning the points x.

        A regular 3D grid of equally sized boxes is created spanning all
        the points `x`. The size, position and number of boxes are determined
        from the specified parameters.

        Parameters:

        - `ppb`: int: mean number of points per box. The box sizes and
          number of boxes will be determined to approximate this number.
        - `shift`: float (0.0 .. 1.0): a relative shift value for the grid.
          Applying a shift of 0.5 will make the lowest coordinate values fall
          at the center of the outer boxes.
        - `minsize`: float: minimum absolute size of the boxes (same in each
          coordinate direction).

        Returns a tuple of:

        - `ox`: float array (3): minimal coordinates of the box grid,
        - `dx`: float array (3): box size in the three axis directions,
        - `nx`: in array (3): number of boxes in each of the coordinate
          directions.
        """
        # serialize points
        x = self.reshape(-1, 3)
        nnod = x.shape[0]
        # Calculate box size
        lo, hi = x.bbox()
        sz = hi-lo
        esz = sz[sz > 0.0]  # only keep the nonzero dimensions

        if esz.size == 0:
            # All points are coincident
            ox = zeros(3, dtype=Float)
            dx = ones(3, dtype=Float)
            nx = ones(3, dtype=Int)

        else:
            nboxes = max(1, nnod // ppb) # ideal total number of boxes
            vol = esz.prod()
            # avoid error message on the global sz/nx calculation
            errh = seterr(all='ignore')
            # set ideal box size, but not smaller than minsize
            boxsz = max(minsize, (vol/nboxes) ** (1./esz.shape[0]))
            nx = (sz/boxsz).astype(int32)
            dx = where(nx>0, sz/nx, boxsz)
            seterr(**errh)

        # perform the origin shift and adjust nx to make sure we enclose all
        ox = lo - dx*shift
        ex = ox + dx*nx
        adj = ceil((hi-ex)/dx).astype(Int).clip(min=0)
        nx += adj
        return ox, dx, nx


    def fuse(self,ppb=1,shift=0.5,rtol=1.e-5,atol=1.e-5,repeat=True):
        """Find (almost) identical nodes and return a compressed set.

        This method finds the points that are very close and replaces them
        with a single point.

        Parameters: (for explanation, see below: Method)

        - `ppb`: int: targeted number of points per box.
        - `shift`: float: relative shift to be applied on the boxes.
        - `rtol`: float: relative tolerance to consider points for fusing.
        - `atol`: float: absolute tolerance to consider points for fusing.
        - `repeat`: bool: if True, repeat the procedure with a second shift
          value.

        Returns a tuple of two arrays:

        - `coords`: the unique points as a :class:`Coords` object with shape
          (npoints,3),
        - `elems`: an int array holding an index in the unique
          coordinates array for each of the original nodes. The shape of
          the index array is equal to the shape of the input coords array
          minus the last dimension (also given by self.pshape()).

        Method:

        The procedure works by first dividing the 3D space in a number of
        equally sized boxes, with a mean population of ppb.
        The boxes are numbered in the 3 directions and a unique integer scalar
        is computed, that is then used to sort the nodes.
        Then only nodes inside the same box are compared on almost equal
        coordinates, using the numpy allclose() function. Two coordinates are
        considered close if they are within a relative tolerance rtol or
        absolute tolerance atol. See numpy for detail. The default atol is
        set larger than in numpy, because pyFormex typically runs with single
        precision.
        Close nodes are replaced by a single one.

        Running the procedure once does not guarantee to find all close nodes:
        two close nodes might be in adjacent boxes. The performance hit for
        testing adjacent boxes is rather high, and the probability of separating
        two close nodes with the computed box limits is very small.
        Therefore, the most sensible way is to run the procedure twice, with
        a different shift value (they should differ more than the tolerance).
        Specifying repeat=True will automatically do this with a second
        shift value equal to shift+0.25.

        Example:

          >>> X = Coords([[1.,1.,0.],[1.001,1.,0.],[1.1,1.,0.]])
          >>> x,e = X.fuse(atol=0.01)
          >>> print(x)
          [[ 1.   1.   0. ]
           [ 1.1  1.   0. ]]
          >>> print(e)
          [0 0 1]

        """
        from pyformex.lib import misc
        if self.size == 0:
            # allow empty coords sets
            return self, array([], dtype=Int).reshape(self.pshape())

        if repeat:
            # Apply twice with different shift value
            coords, index = self.fuse(ppb, shift, rtol, atol, repeat=False)
            coords, index2 = coords.fuse(ppb, shift+0.25, rtol, atol, repeat=False)
            index = index2[index]
            return coords, index

        #########################################
        # This is the single pass
        x = self.points()

        if (self.sizes()==0.).all():
            # All points are coincident
            e = zeros(x.shape[0], dtype=int32)
            x = x[:1]
            return x, e

        # Compute boxes
        ox, dx, nx = self.boxes(ppb=ppb, shift=shift, minsize=atol)

        # Create box coordinates for all nodes
        ind = floor((x-ox)/dx).astype(int32)
        # Create unique box numbers in smallest direction first
        o = argsort(nx)
        val = ( ind[:, o[2]] * nx[o[2]] + ind[:, o[1]] ) * nx[o[1]] + ind[:, o[0]]
        # sort according to box number
        srt = argsort(val)
        # rearrange the data according to the sort order
        val = val[srt]
        x = x[srt]
        # make sure we use int32 (for the fast fuse function)
        # Using int32 limits this procedure to 10**9 points, which is more
        # than enough for all practical purposes
        x = x.astype(float32)
        val = val.astype(int32)
        tol = float32(max(abs(rtol*self.sizes()).max(), atol))
        nnod = val.shape[0]
        flag = ones((nnod,), dtype=int32)   # 1 = new, 0 = existing node
        # new fusing algorithm
        sel = arange(nnod).astype(int32)      # replacement unique node nr
        misc._fuse(x, val, flag, sel, tol)     # fuse the close points
        x = x[flag>0]          # extract unique nodes
        s = sel[argsort(srt)]  # and indices for old nodes
        return (x, s.reshape(self.shape[:-1]))


    def adjust(self,**kargs):
        """Find (almost) identical nodes and adjust them to be identical.

        This function is very much like the :func:`fuse` operation, but
        it does not fuse the close neigbours to a single point. Instead
        it adjust the coordinates of the points to be identical.

        The parameters are the same as for the :func:`fuse` method.

        Returns a Coords with the same shape as the input.

        Example:

          >>> X = Coords([[1.,1.,0.],[1.001,1.,0.],[1.1,1.,0.]])
          >>> print(X.adjust(atol=0.01))
          [[ 1.   1.   0. ]
           [ 1.   1.   0. ]
           [ 1.1  1.   0. ]]

        """
        coords,elems = self.fuse(**kargs)
        return coords[elems]


    def match(self,coords,**kargs):
        """Match points from another Coords object.

        Find the points from the passed `coords` object that coincide with
        (or are very close to) points of `self`.
        This method works by concatenating the serialized point sets of
        both Coords and then fusing them.

        Parameters:

        - `coords`: a Coords object
        - `**kargs`: keyword arguments that you want to pass to the
          :meth:`fuse` method.

        Returns a 1D int array of length `coords.npoints()` holding the
        index of the points in `self` coinciding with those in `coords`.
        If no point in `self` coincides, a value -1 is returned. If
        multiple points in `self` coincide with the point in `coords`,
        any of the coinciding indices may be returned. To avoid this
        ambiguity, fuse() the Coords first.

        Example:

        >>> X = Coords([[1.],[2.],[3.],[1.]])
        >>> Y = Coords([[1.],[2.00001],[4.]])
        >>> print(X.match(Y))
        [ 3  1 -1]
        >>> print(X.fuse()[0].match(Y))
        [ 0  1 -1]
        >>> print(X.match(Y,clean=True))
        [ 3  1 -1]

        See also: :meth:`hasMatch`.

        """
        if 'clean' in kargs:
            utils.warn('warn_coords_match_changed')
            del kargs['clean']

        x = Coords.concatenate([self.points(), coords.points()])
        c, e = x.fuse(**kargs)
        e0, e1 = e[:self.npoints()], e[self.npoints():]
        return findIndex(e0, e1)


    def hasMatch(self,coords,**kargs):
        """Find points also in another Coords object.

        Find the points from the passed `coords` object that coincide with
        (or are very close to) points of `self`.
        This method is very similar to :meth:`match`, but does not give
        information about which point of `self` matches which point of
        `coords`.

        Parameters:

        - `coords`: a Coords object
        - `**kargs`: keyword arguments that you want to pass to the
          :meth:`fuse` method.

        Returns a 1D int array with the uhnnique sorted indices of the points
        in `self` that have a (nearly) matching point in `coords`.
        If multiple points in `self` coincide with the same point in
        `coords`, only one index will be returned for this case.

        Example:

        >>> X = Coords([[1.],[2.],[3.],[1.]])
        >>> Y = Coords([[1.],[2.00001],[4.]])
        >>> print(X.hasMatch(Y))
        [1 3]

        See also: :meth:`match`.

        """
        matches = self.match(coords,**kargs)
        return unique(matches[matches>-1])


    def append(self, coords):
        """Append coords to a Coords object.

        The appended coords should have matching dimensions in all
        but the first axis.

        Returns the concatenated Coords object, without changing the current.

        This is comparable to :func:`numpy.append`, but the result
        is a :class:`Coords` object, the default axis is the first one
        instead of the last, and it is a method rather than a function.
        """
        return Coords(append(self, coords, axis=0))


    @classmethod
    def concatenate(clas,L,axis=0):
        """Concatenate a list of :class:`Coords` object.

        All :class:`Coords` object in the list L should have the same shape
        except for the length of the specified axis.
        This function is equivalent to the numpy concatenate, but makes
        sure the result is a :class:`Coords` object,and the default axis
        is the first one instead of the last.

        The result is at least a 2D array, even when the list contains
        a single Coords with a single point.

        >>> X = Coords([1.,1.,0.])
        >>> Y = Coords([[2.,2.,0.],[3.,3.,0.]])
        >>> print(Coords.concatenate([X,Y]))
        [[ 1.  1.  0.]
         [ 2.  2.  0.]
         [ 3.  3.  0.]]
        >>> print(Coords.concatenate([X,X]))
        [[ 1.  1.  0.]
         [ 1.  1.  0.]]
        >>> print(Coords.concatenate([Y]))
        [[ 2.  2.  0.]
         [ 3.  3.  0.]]
        >>> print(Coords.concatenate([X]))
        [[ 1.  1.  0.]]
        """
        L2 = atleast_2d(*L)
        if len(L2) == 0 or max([len(x) for x in L2]) == 0:
            return Coords()
        if len(L)==1:
            return L2
        else:
            return Coords(data=concatenate(L2, axis=axis))


    @classmethod
    def fromstring(clas,fil,sep=' ',ndim=3,count=-1):
        """Create a :class:`Coords` object with data from a string.

        This convenience function uses the :func:`numpy.fromstring`
        function to read coordinates from a string.

        Parameters:

        - `fil`: a string containing a single sequence of float numbers separated
          by whitespace and a possible separator string.

        - `sep`: the separator used between the coordinates. If not a space,
          all extra whitespace is ignored.

        - `ndim`: number of coordinates per point. Should be 1, 2 or 3 (default).
          If 1, resp. 2, the coordinate string only holds x, resp. x,y
          values.

        - `count`: total number of coordinates to read. This should be a multiple
          of 3. The default is to read all the coordinates in the string.
          count can be used to force an error condition if the string
          does not contain the expected number of values.

        The return value is  Coords object.
        """
        x = fromstring(fil, dtype=Float, sep=sep, count=count)
        if count > 0 and x.size != count :
            raise RuntimeError("Number of coordinates read: %s, expected %s!" % (x.size, count))
        if x.size % ndim != 0 :
            raise RuntimeError("Number of coordinates read: %s, expected a multiple of %s!" % (x.size, ndim))
        return Coords(x.reshape(-1, ndim))


    @classmethod
    def fromfile(clas,fil,**kargs):
        """Read a :class:`Coords` from file.

        This convenience function uses the numpy fromfile function to read
        the coordinates from file.
        You just have to make sure that the coordinates are read in order
        (X,Y,Z) for subsequent points, and that the total number of
        coordinates read is a multiple of 3.
        """
        x = fromfile(fil,dtype=Float,**kargs)
        if x.size % 3 != 0 :
            raise RuntimeError("Number of coordinates read: %s, should be multiple of 3!" % x.size)
        return Coords(x.reshape(-1, 3))


    def interpolate(self, X, div):
        """Create interpolations between two :class:`Coords`.

        Parameters:

        - `X`: a :class:`Coords` with same shape as `self`.
        - `div`: a list of floating point values, or an int. If an int
          is specified, a list with (div+1) values for `div` is created
          by dividing the interval [0..1] into `div` equal distances.

        Returns:

          A :class:`Coords` with an extra (first) axis, containing the
          concatenation of the interpolations of `self` and `X` at all
          values in `div`.
          Its shape is (n,) + self.shape, where n is the number of values
          in `div`.

        An interpolation of F and G at value v is a :class:`Coords` H where
        each coordinate Hijk is obtained from:  Fijk = Fijk + v * (Gijk-Fijk).
        Thus, X.interpolate(Y,[0.,0.5,1.0]) will contain all points of
        X and Y and all points with mean coordinates between those of X and Y.

        F.interpolate(G,n) is equivalent with
        F.interpolate(G,arange(0,n+1)/float(n))
        """
        if self.shape != X.shape:
            raise RuntimeError("`X` should have same shape as `self`")
        div = unitDivisor(div)
        return self + outer(div, X-self).reshape((-1,)+self.shape)


    def convexHull(self,dir=None,return_mesh=False):
        """Return the convex hull of a Coords.

        Parameters:

        - `dir`: int (0..2): axis. If specified, the 2D convext hull
          in the specified viewing direction is returned. The default
          is to return the 3D convex hull.
        - `return_mesh`: bool. If True, returns the convex hull as a
          Mesh instead of a Connectivity.

        Returns a :class:`Connectivity` containing the indices of the points
        that constitute the convex hull of the Coords. For a 3D hull,
        the Connectivity has plexitude 3, and eltype 'tri3'; for a 2D
        hull these are respectively 2 and 'line2'. The values in the
        Connectivity refer to the flattened points array as obtained from
        :meth:`points`.

        If `return_mesh` is True, returns a compacted :class:`Mesh`
        instead of the Connectivity. For a 3D hull, the Mesh will be a
        TriSurface, otherwise a Mesh of 'line2' elements.

        The returned Connectivity or Mesh will be empty if all the points
        are in a plane (dir=None) or an a line in the viewing direction
        (dir=0..2).

        This requires SciPy version 0.12.0 or higher.

        """
        from pyformex.plugins import scipy_itf
        points = self.points()
        if dir is not None and isInt(dir):
            ind = range(3)
            ind.remove(dir)
            points = points[:,ind]
        hull = scipy_itf.convexHull(points)
        if return_mesh:
            from pyformex.mesh import Mesh
            hull = Mesh(self.points(),hull).compact()
            if dir is not None and isInt(dir):
                hull.coords[:,dir] = 0.0

        return hull



    # Convenient shorter notations
    rot = rotate
    trl = translate
    rep = replicate


    def actor(self,**kargs):
        """_This allows a Coords object to be drawn directly"""

        if self.npoints() == 0:
            return None

        from pyformex.formex import Formex
        return Formex(self.reshape(-1, 3)).actor(**kargs)



###########################################################################
##
##   functions
##
#########################
#


def bbox(objects):
    """Compute the bounding box of a list of objects.

    The bounding box of an object is the smallest rectangular cuboid
    in the global Cartesian coordinates, such that no points of the
    objects lie outside that cuboid. The resulting bounding box of the list
    of objects is the smallest bounding box that encloses all the objects
    in the list. Objects that do not have a :meth:`bbox` method or whose
    :meth:`bbox` method returns invalid values, are ignored.

    Parameters:

    - `objects`: a list of objects which should all have the method
      :meth:`bbox`, or a single such object.

    Returns:

      A Coords object with two points: the first contains the minimal
      coordinate values, the second has the maximal ones of the overall
      bounding box.

    Example:

    >>> bbox([Coords([-1.,1.,0.]),Coords([2,-3])])
    Coords([[-1., -3.,  0.],
           [ 2.,  1.,  0.]], dtype=float32)

    """
    if not isinstance(objects,list):
        objects = [ objects ]
    bboxes = [f.bbox() for f in objects if hasattr(f, 'bbox') and not isnan(f.bbox()).any()]
    bboxes = [bb for bb in bboxes if bb is not None]
    if len(bboxes) == 0:
        o = origin()
        bboxes = [ [o, o] ]
    return Coords(concatenate(bboxes)).bbox()


# TODO: should give a warning/ return None when no intersection?
def bboxIntersection(A, B):
    """Compute the intersection of the bounding box of two objects.

    A and B are objects having a bbox method. The intersection of the two
    bounding boxes is returned in boox format.
    """
    Amin, Amax = A.bbox()
    Bmin, Bmax = B.bbox()
    min = where(Amin>Bmin, Amin, Bmin)
    max = where(Amax<Bmax, Amax, Bmax)
    return Coords([min, max])

#
# TODO: this could be merged with the test method by allowing a list for
#       the parameters dir, min, max
#
def testBbox(A,bb,dirs=[0, 1, 2],nodes='any',atol=0.):
    """Test which part of A is inside a given bbox, applied in directions dirs.

    Parameters:

    - `A`: is any object having bbox and a test method (Formex, Mesh).
    - `bb`: is a bounding box, i.e. a (2,3) shape float array.
    - `dirs`: is a list of the three coordinate axes or a subset thereof.
    - `nodes`: has the same meaning as in Formex.test and Mesh.test.

    The result is a bool array flagging the elements that are inside the given
    bounding box.
    """
    test = [ A.test(nodes=nodes, dir=i, min=bb[0][i], max=bb[1][i], atol=atol) for i in dirs ]
    return stack(test).all(axis=0)


def origin():
    """Return a single point with coordinates [0.,0.,0.].

    Returns a :class:`Coords` object with shape(3,) holding three zero
    coordinates.
    """
    return Coords(zeros((3), dtype=Float))


def pattern(s,aslist=False):
    """Return a series of points lying on a regular grid.

    This function creates a series of points that lie on a regular grid
    with unit step. These points are created from a string input, interpreting
    each character as a code specifying how to move to the next point.
    The start position is always the origin (0.,0.,0.).

    Currently the following codes are defined:

    - 0 or +: goto origin (0.,0.,0.)
    - 1..8: move in the x,y plane
    - 9 or .: remain at the same place (i.e. duplicate the last point)
    - A..I: same as 1..9 plus step +1. in z-direction
    - a..i: same as 1..9 plus step -1. in z-direction
    - /: do not insert the next point

    Any other character raises an error.

    When looking at the x,y-plane with the x-axis to the right and the
    y-axis up, we have the following basic moves:
    1 = East, 2 = North, 3 = West, 4 = South, 5 = NE, 6 = NW, 7 = SW, 8 = SE.

    Adding 16 to the ordinal of the character causes an extra move of +1. in
    the z-direction. Adding 48 causes an extra move of -1. This means that
    'ABCDEFGHI', resp. 'abcdefghi', correspond with '123456789' with an extra
    z +/-= 1. This gives the following schema::

                 z+=1             z unchanged            z -= 1

             F    B    E          6    2    5         f    b    e
                  |                    |                   |
                  |                    |                   |
             C----I----A          3----9----1         c----i----a
                  |                    |                   |
                  |                    |                   |
             G    D    H          7    4    8         g    d    h

    The special character '/' can be put before any character to make the
    move without inserting the new point. You need to start
    the string with a '0' or '9' to include the origin in the output.

    Parameters:

    - `s`: string: with the characters generating subsequent points.
    - `aslist`: bool: if True, the points are returned as lists of
      integer coordinates instead of a :class:`Coords` object.

    Returns a :class:`Coords` with the generated points (default) or a list
    of tuples with 3 integer coordinates (if `aslist` is True).

    Example:

    >>> print(pattern('0123'))
    [[ 0.  0.  0.]
     [ 1.  0.  0.]
     [ 1.  1.  0.]
     [ 0.  1.  0.]]

    """
    x = y = z = 0
    l = []
    insert = True
    for c in s:
        if c == '/':
            insert = False
            continue
        elif c == '0' or c == '+':
            x = y = z = 0
        elif c == '.':
            pass
        else:
            j, i = divmod(ord(c), 16)
            if j == 3:
                pass
            elif j == 4:
                z += 1
            elif j == 6:
                z -= 1
            else:
                raise RuntimeError("Unknown character '%c' in pattern input" % c)
            if i == 1:
                x += 1
            elif i == 2:
                y += 1
            elif i == 3:
                x -= 1
            elif i == 4:
                y -= 1
            elif i == 5:
                x += 1
                y += 1
            elif i == 6:
                x -= 1
                y += 1
            elif i == 7:
                x -= 1
                y -= 1
            elif i == 8:
                x += 1
                y -= 1
            elif i == 9:
                pass
            else:
                raise RuntimeError("Unknown character '%c' in pattern input" % c)
        if insert:
            l.append((x, y, z))
        insert = True
    if not aslist:
        l = Coords(l)
    return l


def xpattern(s,nplex=1):
    """Create a Coords object from a string pattern.

    This is like pattern, but allows grouping the points into elements.
    First, the string is expanded to a list of points by calling pattern(s).
    Then the resulting list of points is transformed in a 2D table of points
    where each row has the length `nplex`.

    If the number of points produced by `s` is not a multiple of `nplex`,
    an error is raised.

    Example:

    >>> print(xpattern('.12.34',3))
    [[[ 0.  0.  0.]
      [ 1.  0.  0.]
      [ 1.  1.  0.]]
    <BLANKLINE>
     [[ 1.  1.  0.]
      [ 0.  1.  0.]
      [ 0.  0.  0.]]]
    """
    x = Coords(pattern(s))
    try:
        return x.reshape(-1, nplex, 3)
    except:
        raise ValueError("Could not reshape points list to plexitude %s" % nplex)


def align(L,align,offset=[0., 0., 0.]):
    """Align a list of geometrical objects.

    L is a list of geometrical objects (Coords or Geometry or subclasses
    thereof) and thus having an appropriate ``align`` method.
    align is a string of three characters, one for each coordinate direction,
    defining how the subsequent objects have to be aligned in that direction:

    - ``-`` : align on the minimal coordinate value
    - ``+`` : align on the maximal coordinate value
    - ``0`` : align on the middle coordinate value
    - ``|`` : align the minimum value on the maximal value of the previous item

    E.g., the string ``'|--'`` will juxtapose the objects in the x-direction,
    while aligning them on their minimal coordinates in the y- and z- direction.

    An offset may be specified to create a space between the object, instead
    of juxtaposing them.

    Returns: a list with the aligned objects.

    See also the :meth:`Coords.align` method for aligning a single object
    with respect to a point.
    """
    r = L[:1]
    al = am =''
    for i in range(3):
        if align[i] == '|':
            al += '-'
            am += '+'
        else:
            al += align[i]
            am += align[i]
    for o in L[1:]:
        r.append(o.align(al, r[-1].bboxPoint(am)+offset))
    return r


def positionCoordsObj(objects,path,normal=0,upvector=2,avgdir=False,enddir=None):
    """ Position a list of Coords objects along a path.

    At each point of the curve, a copy of the Coords object is created, with
    its origin in the curve's point, and its normal along the curve's direction.
    In case of a PolyLine, directions are pointing to the next point by default.
    If avgdir==True, average directions are taken at the intermediate points
    avgdir can also be an array like sequence of shape (N,3) to explicitely set
    the directions for ALL the points of the path

    Missing end directions can explicitely be set by enddir, and are by default
    taken along the last segment.
    enddir is a list of 2 array like values of shape (3). one of the two can
    also be an empty list.
    If the curve is closed, endpoints are treated as any intermediate point,
    and the user should normally not specify enddir.

    The return value is a sequence of the repositioned Coords objects.
    """
    points = path.coords
    if isinstance(avgdir, bool):
        if avgdir:
            directions = path.avgDirections()
        else:
            directions = path.directions()
    else:
        directions=asarray(avgdir).reshape(len(avgdir), -1)

    missing = points.shape[0] - directions.shape[0]
    if missing == 1:
        lastdir = (points[-1] - points[-2]).reshape(1, 3)
        directions = concatenate([directions, lastdir], axis=0)
    elif missing == 2:
        lastdir = (points[-1] - points[-2]).reshape(1, 3)
        firstdir = (points[1] - points[0]).reshape(1, 3)
        directions = concatenate([firstdir, directions, lastdir], axis=0)

    if enddir:
        for i, j in enumerate([0, -1]):
            if enddir[i]:
                directions[j] = Coords(enddir[i])

    directions = normalize(directions)

    if isinstance(normal, int):
        normal = Coords(unitVector(normal))

    if isinstance(upvector, int):
        upvector = Coords(unitVector(upvector))

    sequence = [ object.rotate(vectorRotation(normal, d, upvector)).translate(p)
                 for object, d, p in zip(objects, directions, points)
                 ]

    return sequence


def sweepCoords(self,path,origin=[0.,0.,0.],scalex=None,scaley=None,scalez=None,**kwargs):
    """ Sweep a Coords object along a path, returning a series of copies.

    origin and normal define the local path position and direction on the mesh.

    At each point of the curve, a copy of the Coords object is created, with
    its origin in the curve's point.

    At each point of the curve, the original Coords object can be scaled in x
    and y direction by specifying scalex and scaley. The number of values
    specified in scalex and scaly should be equal to the number of points on
    the curve.
    All the kwargs parameters are used to set `positionCoordsObj` function.

    The return value is a sequence of the transformed Coords objects.
    """

    if scalex is not None:
        if len(scalex) != path.ncoords():
            raise ValueError("The number of scale values in x-direction differs from the number of copies that will be created.")
    else:
        scalex = ones(path.ncoords())

    if scaley is not None:
        if len(scaley) != path.ncoords():
            raise ValueError("The number of scale values in y-direction differs from the number of copies that will be created.")
    else:
        scaley = ones(path.ncoords())

    if scalez is not None:
        if len(scalez) != path.ncoords():
            raise ValueError("The number of scale values in y-direction differs from the number of copies that will be created.")
    else:
        scalez = ones(path.ncoords())

    base = self.translate(-Coords(origin))
    sequence = [ base.scale([scx, scy, scz]) for scx, scy, scz in zip(scalex, scaley, scalez) ]
    sequence = positionCoordsObj(sequence,path,**kwargs)

    return sequence


##############################################################################
#
#  Testing
#

if __name__ == '__main__':

    def testX(X):
        """Run some tests on:class:`Coords` X."""

        def prt(s, v):
            """Print a statement 's = v' and return v"""
            if isinstance(v, ndarray):
                sep = '\n'
            else:
                sep = ' '
            print("%s =%s%s" % (s, sep, v))
            return v

        prt("###################################\nTests for Coords X", X)

        # Info
        prt("points", X.points())
        prt("pshape", X.pshape())
        prt("npoints", X.npoints())
        prt("y", X.y())
        prt("bbox", X.bbox())
        prt("center", X.center())
        prt("centroid", X.centroid())
        prt("sizes", X.sizes())
        prt("dsize", X.dsize())
        prt("bsphere", X.bsphere())
        prt("distanceFromPlane", X.distanceFromPlane([0., 0., 1.], [0., 0., 1.]))
        prt("distanceFromLine", X.distanceFromLine([0., 0., 1.], [0., 0., 1.]))
        prt("distanceFromPoint", X.distanceFromPoint([0., 0., 1.]))
        prt("test", X.test(dir=1, min=0.5, max=1.5))
        prt("test2", X.test(dir=[1., 1., 0.], min=[0., 0.5, 0.], max=[0., 1.5, 0.]))

        # Transforms
        prt("X_scl", X.scale(2, False))
        prt("X", X)
        prt("X_scl", X.scale(2, True))
        prt("X", X)
        prt("X_scl2", X.scale([0.5, 1., 0.]))
        prt("X_trl", X.copy().translate(0, 6))
        prt("X_trl2", X.translate([10., 100., 1000.]))
        prt("X_rot", X.rotate(90.))
        prt("X_rot2", X.rotate(90., 0))

        Y=prt("Y = X_reflect", X.reflect(1, 2))
        prt("X_bbox", X.bbox())
        prt("Y_bbox", Y.bbox())
        prt("(X+Y)bbox", bbox([X, Y]))
        Z = X.copy().reflect(1, 1.5).translate(1, 2)
        prt("X", X)
        prt("Y", Y)
        prt("Z", Z)
        G = Coords.concatenate([X, Z, Y, Z], axis=0)
        prt("X+Z+Y+Z", G)
        prt("Points with y > 4.5", where(G.test(dir=1, min=4.5))[0])
        return


    def test_module():
        """Run the tests.

        This is intended for tests during development and can be
        changed at will.
        """
        testX(Coords([[1, 0, 0], [0, 1, 0]]))
        testX(Coords([[[0, 0, 0], [1, 0, 0]], [[0, 1, 0], [1, 1, 0]]]))
        testX(Coords([1, 0, 0]))
        try:
            testX(Coords())
        except:
            print("Some test(s) failed for an empty Coords")
            print("But that surely is no surprise")
        return


    test_module()

### End
