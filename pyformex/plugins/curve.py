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

"""Definition of curves in pyFormex.

This module defines classes and functions specialized for handling
one-dimensional geometry in pyFormex. These may be straight lines, polylines,
higher order curves and collections thereof. In general, the curves are 3D,
but special cases may be created for handling plane curves.
"""
from __future__ import absolute_import, division, print_function
from pyformex import zip

import pyformex as pf
from pyformex.coords import *
from pyformex.coordsys import CoordSys
from pyformex.geometry import Geometry
from pyformex.formex import Formex, connect
from pyformex.mesh import Mesh
from pyformex import geomtools as gt
from pyformex import arraytools
from pyformex import utils
from pyformex.varray import Varray

import math

##############################################################################

class Curve(Geometry):
    """Base class for curve type classes.

    This is a virtual class intended to be subclassed.
    It defines the common definitions for all curve types.
    The subclasses should at least define the following attributes and methods
    or override them if the defaults are not suitable.

    Attributes:

    - `coords`: coordinates of points defining the curve
    - `parts`:  number of parts (e.g. straight segments of a polyline)
    - `closed`: is the curve closed or not
    - `range`: [min,max], range of the parameter: default 0..1

    Methods:

    - `sub_points(t,j)`: returns points at parameter value t,j
    - `sub_directions(t,j)`: returns direction at parameter value t,j
    - `pointsOn()`: the defining points placed on the curve
    - `pointsOff()`: the defining points placeded off the curve (control points)
    - `parts(j,k)`:
    - `approx(nseg=None,ndiv=None,chordal=None)`:

    Furthermore it may define, for efficiency reasons, the following methods:

    - `sub_points_2`
    - `sub_directions_2`

    """

    def __init__(self):
        Geometry.__init__(self)
        self.prop = None

    def pointsOn(self):
        return self.coords

    def pointsOff(self):
        return Coords()

    def ncoords(self):
        return self.coords.shape[0]

    def npoints(self):
        return self.pointsOn().shape[0]

    def endPoints(self):
        """Return start and end points of the curve.

        Returns a Coords with two points, or None if the curve is closed.
        """
        if self.closed:
            #return self.coords[[0,0]]
            return None
        else:
            return self.coords[[0, -1]]

    def sub_points(self, t, j):
        """Return the points at values t in part j

        t can be an array of parameter values, j is a single segment number.
        """
        raise NotImplementedError

    def sub_points_2(self, t, j):
        """Return the points at values,parts given by zip(t,j)

        t and j can both be arrays, but should have the same length.
        """
        raise NotImplementedError

    def sub_directions(self, t, j):
        """Return the directions at values t in part j

        t can be an array of parameter values, j is a single segment number.
        """
        raise NotImplementedError

    def sub_directions_2(self, t, j):
        """Return the directions at values,parts given by zip(t,j)

        t and j can both be arrays, but should have the same length.
        """
        raise NotImplementedError

    def lengths(self):
        raise NotImplementedError


    def charLength(self):
        try:
            return self.lengths().mean()
        except:
            return self.bbox().dsize()


    def localParam(self, t):
        """Split global parameter value in part number and local parameter

        Parameter values are floating point values. Their integer part
        is interpreted as the curve segment number, and the decimal part
        goes from 0 to 1 over the segment.

        Returns a tuple of arrays i,t, where i are the (integer) part
        numbers and t the local parameter values (between 0 and 1).
        """
        # Do not use asarray here! We change it, so need a copy!
        t = array(t).astype(Float).ravel()
        ti = floor(t).clip(min=0, max=self.nparts-1)
        t -= ti
        i = ti.astype(int)
        return i, t


    def pointsAt(self,t,return_position=False):
        """Return the points at parameter values t.

        Parameter values are floating point values. Their integer part
        is interpreted as the curve segment number, and the decimal part
        goes from 0 to 1 over the segment.

        Returns a Coords with the coordinates of the points.

        If return_position is True, also returns the part numbers on which
        the point are lying and the local parameter values.
        """
        t = array(t)
        i, t = self.localParam(t)
        try:
            allX = self.sub_points_2(t, i)
        except:
            allX = concatenate([ self.sub_points(tj, ij) for tj, ij in zip(t, i)])
        X = Coords(allX)
        if return_position:
            return X, i, t
        else:
            return X


    def directionsAt(self, t):
        """Return the directions at parameter values t.

        Parameter values are floating point values. Their integer part
        is interpreted as the curve segment number, and the decimal part
        goes from 0 to 1 over the segment.
        """
        i, t = self.localParam(t)
        try:
            allX = self.sub_directions_2(t, i)
        except:
            allX = concatenate([ self.sub_directions(tj, ij) for tj, ij in zip(t, i)])
        return Coords(allX)


    def subPoints(self,div=10,extend=[0., 0.]):
        """Return a sequence of points on the Curve.

        - `div`: int or a list of floats (usually in the range [0.,1.])
          If `div` is an integer, a list of floats is constructed by dividing
          the range [0.,1.] into `div` equal parts.
          The list of floats then specifies a set of parameter values for which
          points at in each part are returned. The points are returned in a
          single Coords in order of the parts.


        The extend parameter allows to extend the curve beyond the endpoints.
        The normal parameter space of each part is [0.0 .. 1.0]. The extend
        parameter will add a curve with parameter space [-extend[0] .. 0.0]
        for the first part, and a curve with parameter space
        [1.0 .. 1 + extend[0]] for the last part.
        The parameter step in the extensions will be adjusted slightly so
        that the specified extension is a multiple of the step size.
        If the curve is closed, the extend parameter is disregarded.
        """
        # Subspline parts (without end point)
        if isInt(div):
            u = arange(div) / float(div)

        else:
            u = array(div).ravel()
            div = len(u)

        parts = [ self.sub_points(u, j) for j in range(self.nparts) ]

        if not self.closed:
            nstart, nend = round_(asarray(extend)*div, 0).astype(Int)

            # Extend at start
            if nstart > 0:
                u = arange(-nstart, 0) * extend[0] / float(nstart)
                parts.insert(0, self.sub_points(u, 0))

            # Extend at end
            if nend > 0:
                u = 1. + arange(0, nend+1) * extend[1] / float(nend)
            else:
                # Always extend at end to include last point
                u = array([1.])
            parts.append(self.sub_points(u, self.nparts-1))

        X = concatenate(parts, axis=0)
        return Coords(X)


    def split(self,split=None):
        """Split a curve into a list of partial curves

        split is a list of integer values specifying the node numbers
        where the curve is to be split. As a convenience, a single int may
        be given if the curve is to be split at a single node, or None
        to split at all nodes.

        Returns a list of open curves of the same type as the original.
        """
        if split is None:
            split = list(range(1, self.nparts))
        elif isinstance(split, int):
            split = [split]
        start = [0] + split
        end = split + [self.nparts]
        return [ self.parts(j, k) for j, k in zip(start, end) ]


    def length(self):
        """Return the total length of the curve.

        This is only available for curves that implement the 'lengths'
        method.
        """
        return self.lengths().sum()


    def atApproximate(self,nseg=None,ndiv=None,equidistant=False,npre=None):
        """Return parameter values for approximating a Curve with a PolyLine.

        Parameters:

        - `nseg`: number of segments of the resulting PolyLine. The number
          of returned parameter values is `nseg` if the curve is closed,
          else `nseg+1`. Only used if `ndiv` is not specified.
        - `ndiv`: positive integer or a list thereof. If a single integer,
          it specifies the number of straight segments in each part of the
          curve, and is thus equivalent with `nseg = ndiv * self.nparts`.
          If a list of integers, its length should be equal to the number
          of parts in the curve and each integer in the list specifies the
          number of segments the corresponding part.
        - `equidistant`: bool, only used if ndiv is not specified.
          If True, the points are spaced almost equidistantly
          over the curve. If False (default), the points are spread
          equally over the parameter space.
        - `npre`: integer: only used when `equidistant` is True:
          number of segments per part of the curve used in the
          pre-approximation. This pre-approximation is currently
          required to compute curve lengths.

        """
        if ndiv is not None:
            if isInt(ndiv):
                nseg = ndiv * self.nparts
                ndiv = None
            equidistant = False
        if equidistant:
            if npre is None:
                npre = 100
            S = self.approx(ndiv=npre)
            at = S.atLength(nseg) / npre

        elif ndiv is not None:
            at = concatenate([[ 0. ]] + [ i + unitDivisor(n,1) for i,n in enumerate(ndiv) ])

        else:
            if nseg is None:
                nseg = self.nparts
            at = arange(nseg+1) * float(self.nparts) / nseg

        return at


    def atChordal(self,chordal,at=None):
        """Return parameter values to approximate within given chordal error.

        Parameters:

        - chordal: relative tolerance on the distance of the chord to the
          curve. The tolerance is relative to the curve's charLength().
        - at: list of floats: list of parameter values that need to be
          included in the result. The list should contain increasing values
          in the curve's parameter range. If not specified, a default is
          set assuring that the curve is properly approximated. If you
          specify this yourself, you may end up with bad approximations due
          to bad choice of the initial values.

        Returns a list of parameter values that create a PolyLine
        approximate for the curve, such that the chordal error is
        everywhere smaller than the give value. The chordal error
        is defined as the distance from a point of the curve to the
        chord.
        """
        # Create first approximation
        if at is None:
            if hasattr(self,'degree'):
                ndiv = self.degree
            else:
                ndiv = 1
            at = self.atApproximate(nseg=ndiv*self.nparts)
        charlen = self.approxAt(at).charLength()

        # Split in handled and to-be-handled
        at,bt = list(at[:1]),list(at[1:])

        # Handle segment by segment
        #
        # THIS SHOULD BE CHANGED:
        #    insert NO points of degree 1 (always correct)
        #    insert 1 point at 1/2 for degree 2  (current implementation)
        #    insert 2 points at 1/3 and 2/3 for degree 3
        #    etc...
        #
        while len(bt) > 0:
            c0,c2 = at[-1],bt[0]
            if c2 > c0:
                c1 = 0.5*(c0+c2)
                X = self.pointsAt([c0,c1,c2])
                XM = 0.5*(X[0]+X[2])
                d = length(X[1]-XM) / charlen

                if d >= chordal:
                    # need refinement: put new point in front of todo list
                    bt = [c1] + bt
                    continue

            # move on
            at.append(bt.pop(0))

        return at


    def approxAt(self,at):
        """Create a PolyLine approximation with specified parameter values.

        Parameters:

        - `at`: a list of parameter values in the curve parameter range.
          The Curve points at these parameter values are connected with
          straight segments to form a PolyLine approximation.
        """
        X = self.pointsAt(at)

        PL = PolyLine(X, closed=self.closed)
        return PL.setProp(self.prop)


    def approx(self,nseg=None,ndiv=None,chordal=0.02,equidistant=False,npre=None):
        """Approximate a Curve with a PolyLine of n segments

        If neither `nseg` nor `ndiv` are specified (default), a chordal method
        is used limiting the chordal distance of the curve to the PolyLine
        segments.

        Parameters:

        - `nseg`: integer: number of straight segments of the resulting
          PolyLine. Only used if `ndiv` is not specified.
        - `ndiv`: positive integer or a list thereof. If a single integer,
          it specifies the number of straight segments in each part of the
          curve, and is thus equivalent with `nseg = ndiv * self.nparts`.
          If a list of integers, its length should be equal to the number
          of parts in the curve and each integer in the list specifies the
          number of segments the corresponding part.
        - `chordal`: float: accuracy of the approximation when using the
          'chordal error' method. This is the case if neither `nseg` nor
          `ndiv` are specified (the default). The value is relative to the
          curve's :func:`charLength`.
        - `equidistant`: bool, only used if `nseg` is specified and `ndiv`
          is not. If True the `nseg+1` points are spaced almost equidistantly
          over the curve. If False (default), the points are spread equally
          over the parameter space.
        - `npre`: integer, only used if the `chordal` method is used or if
          `nseg` is not None and `equidistant` is True: the number of segments
          per part of the curve (like `ndiv`) used in a pre-approximation.
          If not specified, it is set to the degree of the curve for the
          `chordal` method (1 for PolyLine), and to 100 in the `equidistant`
          method (where the pre-approximation is currently used to compute
          accurate curve lengths).

        """
        if nseg or ndiv or equidistant:
            at = self.atApproximate(nseg,ndiv,equidistant,npre)
        else:
            at = self.atChordal(chordal)
        if self.closed and at[-1] == float(self.nparts):
            at = at[:-1]
        return self.approxAt(at)


    # For compatibility/convenience
    approximate = approx


    def frenet(self,ndiv=None,nseg=None,chordal=0.01,upvector=None,avgdir=True,compensate=False):
        """Return points and Frenet frame along the curve.

        A PolyLine approximation for the curve is constructed, using the
        :meth:`Curve.approx()` method with the arguments `ndiv`, `nseg`
        and `chordal`.
        Then Frenet frames are constructed with :meth:`PolyLine._movingFrenet`
        using the remaining arguments.
        The resulting PolyLine points and Frenet frames are returned.

        Parameters:

        - `upvector`: (3,) vector: a vector normal to the (tangent,normal)
          plane at the first point of the curve. It defines the binormal at
          the first point. If not specified it is set to the shorted distance
          through the set of 10 first points.
        - `avgdir`: bool or array.
          If True (default), the tangential vector is set to
          the average direction of the two segments ending at a node.
          If False, the tangent vectors will be those of the line segment
          starting at the points.
          The tangential vector can also be set by the user by specifying
          an array with the matching number of vectors.
        - `compensate`: bool: If True, adds a compensation algorithm if the
          curve is closed. For a closed curve the moving Frenet
          algorithm can be continued back to the first point. If the resulting
          binormial does not coincide with the starting one, some torsion is
          added to the end portions of the curve to make the two binormals
          coincide.

          This feature is off by default because it is currently experimental
          and is likely to change in future.
          It may also form the base for setting the starting as well as the
          ending binormal.

        Returns:

        - `X`: a Coords with `npts` points on the curve
        - `T`: normalized tangent vector to the curve at `npts` points
        - `N`: normalized normal vector to the curve at `npts` points
        - `B`: normalized binormal vector to the curve at `npts` points
        """
        PL = self.approx(ndiv=ndiv, nseg=nseg, chordal=chordal)
        X = PL.coords
        T, N, B = PL._movingFrenet(upvector=upvector, avgdir=avgdir, compensate=compensate)
        return X, T, N, B


    def position(self,geom,csys=None):
        """ Position a Geometry object along a path.

        Parameters:

        - `geom`: Geometry or Coords.
        - `csys`: CoordSys.

        For each point of the curve, a copy of the Geometry/Coords object
        is created, and positioned thus that the specified csys (default
        the global axes) coincides with the curve's frenet axes at that
        point.

        Returns a list of Geometry/Coords objects.
        """
        X,T,N,B = self.frenet()
        if csys:
            geom = geom.fromCS(csys)
        return [ geom.fromCS(CoordSys(rot=row_stack([t,n,b]),trl=x)) for x,t,n,b in zip(X,T,N,B) ]


    def sweep(self,mesh,eltype=None,csys=None):
        """Sweep a mesh along the curve, creating an extrusion.

        Parameters:

        - `mesh`: Mesh-like object. This is usually a planar object
          that is swept in the direction normal to its plane.
        - `eltype`: string. Name of the element type on the
          returned Meshes.
        - `**kargs`: keyword arguments that are passed to
          func:`coords.sweepCoords`, with the same meaning.
          Usually, you will need to at least set the `normal` parameter.

        Returns a Mesh obtained by sweeping the given Mesh over a path.
        The returned Mesh has double plexitude of the original.
        If `path` is a closed Curve connect back to the first.

        .. note:: Sweeping nonplanar objects and/or sweeping along very curly
           curves may result in physically impossible geometries.
        """
        loop = self.closed
        mesh = mesh.toMesh()
        seq = self.position(mesh.coords,csys)
        return mesh.connect(seq, eltype=eltype,loop=loop)


    def toFormex(self,*args,**kargs):
        """Convert a curve to a Formex.

        This creates a polyline approximation as a plex-2 Formex.
        This is mainly used for drawing curves that do not implement
        their own drawing routines.

        The method can be passed the same arguments as the `approx` method.
        """
        return self.approx(*args,**kargs).toFormex()


    def toNurbs(self):
        """Convert a curve to a NurbsCurve.

        This is currently only implemented for BezierSpline and
        PolyLine
        """
        from pyformex.plugins.nurbs import NurbsCurve
        if isinstance(self,(BezierSpline, PolyLine)):
            return NurbsCurve(self.coords, degree=self.degree, closed=self.closed, blended=False)
        else:
            raise ValueError("Can not convert a curve of type %s to NurbsCurve" % self.__class__.__name__)


    def setProp(self,p=None):
        """Create or destroy the property number for the Curve.

        A curve can have a single integer as property number.
        If it is set, derived curves and approximations will inherit it.
        Use this method to set or remove the property.

        Parameters:

        - `p`: integer or None. If a value None is given, the property is
          removed from the Curve.
        """
        try:
            self.prop = int(p)
        except:
            self.prop = None
        return self


##############################################################################
#
#  Curves that can be transformed by Coords Transforms
#
##############################################################################
#
class PolyLine(Curve):
    """A class representing a series of straight line segments.

    coords is a (npts,3) shaped array of coordinates of the subsequent
    vertices of the polyline (or a compatible data object).
    If closed == True, the polyline is closed by connecting the last
    point to the first. This does not change the vertex data.

    The `control` parameter has the same meaning as `coords` and is added
    for symmetry with other Curve classes. If specified, it will override
    the `coords` argument.
    """

    degree = 1

    def __init__(self,coords=[],control=None,closed=False):
        """Initialize a PolyLine from a coordinate array."""
        Curve.__init__(self)

        if control is not None:
            coords = control
        if isinstance(coords, Formex):
            if coords.nplex() == 1:
                coords = coords.points()
            elif coords.nplex() == 2:
                coords = Coords.concatenate([coords.coords[:, 0,:], coords.coords[-1, 1,:]])
            else:
                raise ValueError("Only Formices with plexitude 1 or 2 can be converted to PolyLine")

        else:
            coords = Coords(coords)

        if coords.ndim != 2 or coords.shape[1] != 3 or coords.shape[0] < 2:
            raise ValueError("Expected an (npoints,3) shaped coordinate array with npoints >= 2, got shape " + str(coords.shape))
        self.coords = coords
        self.nparts = self.coords.shape[0]
        if not closed:
            self.nparts -= 1
        self.closed = closed


    def close(self,atol=0.):
        """Close a PolyLine.

        If the PolyLine is already closed, this does nothing.
        Else it is closed by one of two methods, depending on the distance
        between the start and end points of the PolyLine:

        - if the distance is smaller than atol, the last point is removed and
          the last segment now connects the penultimate point with the first
          one, leaving the number of segments unchanged and the number of points
          decreased by one;
        - if the distance is not smaller than atol, a new segment is added
          connecting the last point with the first, resulting in a curve with
          one more segment and the number of points unchanged.
          Since the default value for atol is 0.0, this is the default
          behavior for all PolyLines.

        Returns True if the PolyLine was closed without adding a segment.

        The return value can be used to reopen the PolyLine while keeping all
        segments (see :meth:`open`).

        .. warning:: This method changes the PolyLine inplace.
        """
        if not self.closed:
            d = arraytools.length(self.coords[0]-self.coords[-1])
            if d < atol:
                self.coords = self.coords[:-1]
                ret = True
            else:
                self.nparts += 1
                ret = False
            self.closed = True
            return ret


    def open(self,keep_last=False):
        """Open a closed PolyLine.

        If the PolyLine is not closed, this does nothing.

        Else, the PolyLine is opened in one of two ways:

        - if keep_last is True, the PolyLine is opened by adding a last
          point equal to the first, and keeping the number of segments
          unchanged;
        - if False, the PolyLine is opened by removing the last segment,
          keeping the number of points unchanged. This is the default
          behavior.

        There is no return value.

        If a closed PolyLine is opened with keep_last=True, the first and
        last point will coincide. In order to close it again, a positive
        atol value needs to be used in :meth:`close`.

        .. warning:: This method changes the PolyLine inplace.

        """
        if self.closed:
            if keep_last:
                self.coords = Coords.concatenate([self.coords,self.coords[0]])
            else:
                self.nparts -= 1
            self.closed = False


    def nelems(self):
        return self.nparts


    def toFormex(self):
        """Return the PolyLine as a Formex."""
        x = self.coords
        F = connect([x, x], bias=[0, 1], loop=self.closed)
        return F.setProp(self.prop)


    def toMesh(self):
        """Convert the PolyLine to a plex-2 Mesh.

        The returned Mesh is equivalent with the PolyLine.
        """
        e1 = arange(self.ncoords())
        elems = column_stack([e1, roll(e1, -1)])
        if not self.closed:
            elems = elems[:-1]
        return Mesh(self.coords, elems, eltype='line2').setProp(self.prop)


    def sub_points(self, t, j):
        """Return the points at values t in part j"""
        j = int(j)
        t = asarray(t).reshape(-1, 1)
        n = self.coords.shape[0]
        X0 = self.coords[j % n]
        X1 = self.coords[(j+1) % n]
        X = (1.-t) * X0 + t * X1
        return X


    def sub_points_2(self, t, j):
        """Return the points at value,part pairs (t,j)"""
        j = int(j)
        t = asarray(t).reshape(-1, 1)
        n = self.coords.shape[0]
        X0 = self.coords[j % n]
        X1 = self.coords[(j+1) % n]
        X = (1.-t) * X0 + t * X1
        return X


    def sub_directions(self, t, j):
        """Return the unit direction vectors at values t in part j."""
        j = int(j)
        t = asarray(t).reshape(-1, 1)
        return self.directions()[j].reshape(len(t), 3)


    def vectors(self):
        """Return the vectors of each point to the next one.

        The vectors are returned as a Coords object.
        If the curve is not closed, the number of vectors returned is
        one less than the number of points.
        """
        x = self.coords
        if self.closed:
            x1 = x
            x2 = roll(x, -1, axis=0) # NEXT POINT
        else:
            x1 = x[:-1]
            x2 = x[1:]
        return x2-x1


    def directions(self,return_doubles=False):
        """Returns unit vectors in the direction of the next point.

        This directions are returned as a Coords object with the same
        number of elements as the point set.

        If two subsequent points are identical, the first one gets
        the direction of the previous segment. If more than two subsequent
        points are equal, an invalid direction (NaN) will result.

        If the curve is not closed, the last direction is set equal to the
        penultimate.

        If return_doubles is True, the return value is a tuple of the direction
        and an index of the points that are identical with their follower.
        """
        d = normalize(self.vectors())
        w = where(isnan(d).any(axis=-1))[0]
        d[w] = d[w-1]
        if not self.closed:
            d = concatenate([d, d[-1:]], axis=0)
        if return_doubles:
            return d, w
        else:
            return d


    def avgDirections(self,return_doubles=False):
        """Returns the average directions at points.

        For each point the returned direction is the average of the direction
        from the preceding point to the current, and the direction from the
        current to the next point.

        If the curve is open, the first and last direction are equal to the
        direction of the first, resp. last segment.

        Where two subsequent points are identical, the average directions
        are set equal to those of the segment ending in the first and the
        segment starting from the last.
        """
        d, w = self.directions(True)
        d1 = d
        d2 = roll(d, 1, axis=0) # PREVIOUS DIRECTION
        w = concatenate([w, w+1])
        if not self.closed:
            w = concatenate([[0, self.npoints()-1], w])
        w = setdiff1d(arange(self.npoints()), w)
        d[w] = 0.5 * (d1[w]+d2[w])
        if return_doubles:
            return d, w
        else:
            return d


    def _compensate(self,end=0,cosangle=0.5):
        """_Compensate an end discontinuity over a piece of curve.

        An end discontinuity in the curve is smeared out over a part of
        the curve where no sharp angle occur with cosangle < 0.5
        """
        v = self.vectors()
        print("VECTORS", v)
        cosa = vectorPairCosAngle(roll(v, 1, axis=0), v)
        print("COSA", cosa)
        L = self.lengths()
        if end < 0:
            L = L[::-1]
            cosa = roll(cosa, -1)[::-1]
        print(len(L), L)
        for i in range(1, len(L)):
            if cosa[i] <= cosangle:
                break
        print("HOLDING AT i=%s" % i)
        L = L[:i]
        print(len(L), L)
        L = L[::-1].cumsum()
        comp = L / L[-1]
        comp = comp[::-1]
        print("COMP", comp)
        return comp


    def _movingFrenet(self,upvector=None,avgdir=True,compensate=False):
        """Return a Frenet frame along the curve.

        ..note : The recommended way to use this method is through the
                 :meth:`frenet` method.

        The Frenet frame consists of a system of three orthogonal vectors:
        the tangent (T), the normal (N) and the binormal (B).
        These vectors define a coordinate system that re-orients while walking
        along the polyline.
        The _movingFrenet method tries to minimize the twist angle.

        Parameters:

        - `upvector`: (3,) vector: a vector normal to the (tangent,normal)
          plane at the first point of the curve. It defines the binormal at
          the first point. If not specified it is set to the shorted distance
          through the set of 10 first points.
        - `avgdir`: bool or array.
          If True (default), the tangential vector is set to
          the average direction of the two segments ending at a node.
          If False, the tangent vectors will be those of the line segment
          starting at the points.
          The tangential vector can also be set by the user by specifying
          an array with the matching number of vectors.
        - `compensate`: bool: If True, adds a compensation algorithm if the
          curve is closed. For a closed curve the moving Frenet
          algorithm can be continued back to the first point. If the resulting
          binormial does not coincide with the starting one, some torsion is
          added to the end portions of the curve to make the two binormals
          coincide.

          This feature is off by default because it is currently experimental
          and is likely to change in future.
          It may also form the base for setting the starting as well as the
          ending binormal.

        Returns:

        - `T`: normalized tangent vector to the curve at `npts` points
        - `N`: normalized normal vector to the curve at `npts` points
        - `B`: normalized binormal vector to the curve at `npts` points
        """
        if isinstance(avgdir, ndarray):
            T = checkArray(avgdir, (self.ncoords(), 3), 'f')
        elif avgdir:
            T = self.avgDirections()
        else:
            T = self.directions()
        B = zeros(T.shape)
        if upvector is None:
            upvector = gt.smallestDirection(self.coords[:10])

        B[-1] = normalize(upvector)
        for i, t in enumerate(T):
            B[i] = cross(t, cross(B[i-1], t))
            if isnan(B[i]).any():
                # if we can not compute binormal, keep previous
                B[i] = B[i-1]

        T = normalize(T)
        B = normalize(B)

        if self.closed and compensate:
            from pyformex import arraytools as at
            from pyformex.gui.draw import drawVectors
            print(len(T))
            print(T[0], B[0])
            print(T[-1], B[-1])
            P0 = self.coords[0]
            if avgdir:
                T0 = T[0]
            else:
                T0 = T[-1]
            B0 = cross(T0, cross(B[-1], T0))
            N0 = cross(B0, T0)
            drawVectors(P0, T0, size=2., nolight=True, color='magenta')
            drawVectors(P0, N0, size=2., nolight=True, color='yellow')
            drawVectors(P0, B0, size=2., nolight=True, color='cyan')
            print("DIFF", B[0], B0)
            if length(cross(B[0], B0)) < 1.e-5:
                print("NO NEED FOR COMPENSATION")
            else:
                PM, BM = gt.intersectionLinesPWP(P0, T[0], P0, T0, mode='pair')
                PM = PM[0]
                MB = BM[0]
                if length(BM) < 1.e-5:
                    print("NORMAL PLANES COINCIDE")
                    BM = (B0 + B[0])/2

                print("COMPENSATED B0: %s" % BM)
                print("Compensate at start")
                print(BM, B[0])
                a = at.vectorPairAngle(B[0], BM) / DEG
                print("ANGLE to compensate: %s" % a)
                sa = sign(at.projection(cross(B[0], BM), T[0]))
                print("Sign of angle: %s" % sa)
                a *= sa
                torsion = a * self._compensate(0)
                print("COMPENSATION ANGLE", torsion)
                for i in range(len(torsion)):
                    B[i] = Coords(B[i]).rotate(torsion[i], axis=T[i])

                print("Compensate at end")
                print(BM, B0)
                a = at.vectorPairAngle(B0, BM) / DEG
                print("ANGLE to compensate: %s" % a)
                sa = sign(at.projection(cross(BM, B0), T[-1]))
                print("Sign of angle: %s" % sa)
                a *= sa
                torsion = a * self._compensate(-1)
                print("COMPENSATION ANGLE", torsion)
                for i in range(len(torsion)):
                    B[-i] = Coords(B[-i]).rotate(torsion[i], axis=T[-i])

        N = cross(B, T)
        return T, N, B


    def roll(self, n):
        """Roll the points of a closed PolyLine."""
        if self.closed:
            return PolyLine(roll(self.coords, n, axis=0), closed=True)
        else:
            raise ValueError("""Can only roll a closed PolyLine""")


    def lengths(self):
        """Return the length of the parts of the curve."""
        return length(self.vectors())


    def atLength(self, div):
        """Returns the parameter values at given relative curve length.

        ``div`` is a list of relative curve lengths (from 0.0 to 1.0).
        As a convenience, a single integer value may be specified,
        in which case the relative curve lengths are found by dividing
        the interval [0.0,1.0] in the specified number of subintervals.

        The function returns a list with the parameter values for the points
        at the specified relative lengths.
        """
        lens = self.lengths().cumsum()
        rlen = concatenate([[0.], lens/lens[-1]]) # relative length
        if isInt(div):
            div = arange(div+1) / float(div)
        else:
            div = asarray(div)
        z = rlen.searchsorted(div)
        # we need interpolation
        wi = where(z>0)[0]
        zw = z[wi]
        L0 = rlen[zw-1]
        L1 = rlen[zw]
        ai = zw + (div[wi] - L1) / (L1-L0)
        at = zeros(len(div))
        at[wi] = ai
        return at


    def reverse(self):
        """Return the same curve with the parameter direction reversed."""
        return PolyLine(reverseAxis(self.coords, axis=0), closed=self.closed)


    def parts(self, j, k):
        """Return a PolyLine containing only segments j to k (k not included).

        The resulting PolyLine is always open.
        """
        start = j
        end = k + 1
        return PolyLine(control=self.coords[start:end], closed=False)


    def cutWithPlane(self,p,n,side=''):
        """Return the parts of the PolyLine at one or both sides of a plane.

        If side is '+' or '-', return a list of PolyLines with the parts at
        the positive or negative side of the plane.

        For any other value, returns a tuple of two lists of PolyLines,
        the first one being the parts at the positive side.

        p is a point specified by 3 coordinates.
        n is the normal vector to a plane, specified by 3 components.
        """
        n = asarray(n)
        p = asarray(p)

        d = self.coords.distanceFromPlane(p, n)
        t = d > 0.0
        cut = t != roll(t, -1)
        if not self.closed:
            cut = cut[:-1]
        w = where(cut)[0]   # segments where side switches

        res = [[], []]
        i = 0        # first point to include in next part
        if t[0]:
            sid = 0  # start at '+' side
        else:
            sid = 1  # start at '-' side
        Q = Coords() # new point from previous cutting (None at start)

        for j in w:
            #print("%s -- %s" % (i,j))
            if self.closed:
                pts = self.coords.take(range(j,j+2),axis=0,mode='wrap')
            else:
                pts = self.coords[j:j+2]
            #print("Points: %s" % pts)
            P = gt.intersectionPointsSWP(pts, p, n, mode='pair')[0]
            #print("%s -- %s cuts at %s" % (j,j+1,P))
            x = Coords.concatenate([Q, self.coords[i:j+1], P])
            #print("Save part of length %s + %s + %s = %s" % (Q.shape[0],j-i,P.shape[0],x.shape[0]))
            res[sid].append(PolyLine(x))
            sid = 1-sid
            i = j+1
            Q = P

        # Remaining points
        x = Coords.concatenate([Q, self.coords[i:]])
        #print("%s + %s = %s" % (Q.shape[0],self.nparts-i,x.shape[0]))
        if not self.closed:
            # append the remainder as an extra PolyLine
            res[sid].append(PolyLine(x))
        else:
            # append remaining points to the first
            #print(res)
            #print(len(res[sid]))
            if len(res[sid]) > 0:
                x = Coords.concatenate([x, res[sid][0].coords])
                res[sid][0] = PolyLine(x)
            else:
                res[sid].append(PolyLine(x))
            #print([len(r) for r in res])
            if len(res[sid]) == 1 and len(res[1-sid]) == 0:
                res[sid][0].closed = True

        # Do not use side in '+-', because '' in '+-' returns True
        if side in ['+', '-']:
            return res['+-'.index(side)]
        else:
            return res


    def append(self,PL,fuse=True,smart=False,**kargs):
        """Concatenate two open PolyLines.

        This combines two open PolyLines into a single one. Closed PolyLines
        cannot be concatenated.

        Parameters:

        - `PL`: an open PolyLine, to be appended at the end of the current.
        - `fuse`: bool. If True, the last point of `self` and the first point
          of `PL` will be fused to a single point if they are close. Extra
          parameters may be added to tune the fuse operation. See the
          :meth:`Coords.fuse` method. The `ppb` parameter is not allowed.
        - `smart`: bool. If True, `PL` will be connected to `self` by the
          endpoint that is closest to the last point of self, thus possibly
          reversing the sense of PL.

        The same result (with the default parameter values) can also be
        achieved using operator syntax: `PolyLine1 + PolyLine2`.
        """
        if self.closed or PL.closed:
            raise RuntimeError("Closed PolyLines cannot be concatenated.")
        if smart:
            d = PL.coords[[0,-1]].distanceFromPoint(self.coords[-1])
            print("Dist: %s" % d)
            if d[1] < d[0]:
                PL = PL.reverse()
        X = PL.coords
        if fuse:
            x = Coords.concatenate([self.coords[-1], X[0]])
            x, e = x.fuse(ppb=3) # !!! YES ! > 2 !!!
            if e[0] == e[1]:
                X = X[1:]
        return PolyLine(Coords.concatenate([self.coords, X]))


    # allow syntax PL1 + PL2
    __add__ = append


    @staticmethod
    def concatenate(PLlist,**kargs):
        """Concatenate a list of :class:`PolyLine` objects.

        Parameters:

        - `PLlist`: a list of open PolyLines.
        - Other parameters are like in :meth:`append`

        Returns a PolyLine which is the concatenation of all the PolyLines
        in `PLlist`

        """
        PL = PLlist[0]
        for pl in PLlist[1:]:
            PL = PL.append(pl,**kargs)
        return PL


    def insertPointsAt(self,t,return_indices=False):
        """Insert new points at parameter values t.

        Parameter values are floating point values. Their integer part
        is interpreted as the curve segment number, and the decimal part
        goes from 0 to 1 over the segment.

        Returns a PolyLine with the new points inserted. Note that the
        parameter values of the points will have changed.
        If return_indices is True, also returns the indices of the
        inserted points in the new PolyLine.
        """
        t = sorted(t)
        X, i, t = self.pointsAt(t, return_position=True)
        Xc = self.coords.copy()
        if return_indices:
            ind = -ones(len(Xc))
        # Loop in descending order to avoid recomputing parameters
        for j in range(len(i))[::-1]:
            Xi, ii = X[j].reshape(-1, 3), i[j]+1
            Xc = Coords.concatenate([Xc[:ii], Xi, Xc[ii:]])
            if return_indices:
                ind = concatenate([ind[:ii], [j], ind[ii:]])
        PL = PolyLine(Xc, closed=self.closed)
        if return_indices:
            ind = ind.tolist()
            ind = [ ind.index(i) for i in arange(len(i)) ]
            return PL, ind
        else:
            return PL


    def splitAt(self,t):
        """Split a PolyLine at parametric values t

        Parameter values are floating point values. Their integer part
        is interpreted as the curve segment number, and the decimal part
        goes from 0 to 1 over the segment.

        Returns a list of open Polylines.
        """
        PL, t = self.insertPointsAt(t, return_indices=True)
        return PL.split(t)


    def splitAtLength(self, L):
        """Split a PolyLine at relative lenghts L.

        This is a convenience function equivalent with::

           self.splitAt(self.atLength(L))
        """
        return self.splitAt(self.atLength(L))


    def refine(self,maxlen):
        """Insert extra points in the PolyLine to reduce the segment length.

        Parameters:

        - `maxlen`: float: maximum length of the segments. The value is
          relative to the total curve length.

        Returns a PolyLine which is geometrically equivalent to the
        input PolyLine.
        """
        maxlen *= self.length()
        ndiv = ceil(self.lengths() / maxlen).astype(Int)
        return self.approx(ndiv=ndiv)


    def vertexReductionDP(self,tol,maxlen=None,keep=[0,-1]):
        """Douglas-Peucker vertex reduction.

        For any subpart of the PolyLine, if the distance of all its vertices to
        the line connecting the endpoints is smaller than `tol`, the internal
        points are removed.

        Returns a bool array flagging the vertices to be kept in the reduced
        form.
        """
        x = self.coords
        n = len(x)
        _keep = zeros(n,dtype=bool)
        _keep[keep] = 1

        def decimate(i,j):
            """Recursive vertex decimation.

            This will remove all the vertices in the segment i-j that
            are closer than tol to any chord.
            """
            # Find point farthest from line through endpoints
            d = x[i+1:j].distanceFromLine(x[i], x[j]-x[i])
            k = argmax(d)
            dmax = d[k]
            k += i+1
            if dmax > tol:
                # Keep the farthest vertex, split the polyline at that vertex
                # and recursively decimate the two parts
                _keep[k] = 1
                if k > i+1:
                  decimate(i,k);
                if k < j-1:
                  decimate(k,j);

        def reanimate(i,j):
            """Recursive vertex reanimation.

            This will revive vertices in the segment i-j if the
            segment is longer than maxlen.
            """
            if j > i+1 and length(x[i]-x[j]) > maxlen:
                # too long: revive a point
                d = length(x[i+1:j]-x[i])
                w = where(d>maxlen)[0]
                if len(w) > 0:
                    k = w[0] + i+1
                    _keep[k] = 1
                    reanimate(k+1,j)


        # Compute vertices to keep
        decimate(0,n-1)

        # Reanimate some vertices if maxlen specified
        if maxlen is not None:
            w = where(_keep)[0]
            for i,j in zip(w[:-1],w[1:]):
                reanimate(i,j)

        return _keep


    def coarsen(self,tol=0.01,maxlen=None,keep=[0,-1]):
        """ Reduce the number of points of the PolyLine.

        Parameters:

        - `tol`: maximum relative distance of vertices to remove from the
          chord of the segment. The value is relative to the total curve
          length.
        - `keep`: list of vertices to keep during the coarsening process.
          (Not implemented yet).

        Retuns a Polyline with a reduced number of points.
        """
        atol = tol*self.length()
        if maxlen:
            maxlen *= self.length()
        keep = self.vertexReductionDP(tol=atol,maxlen=maxlen,keep=keep)
        return PolyLine(self.coords[keep],closed=self.closed)


##############################################################################
#
class Line(PolyLine):
    """A Line is a PolyLine with exactly two points.

    Parameters:

    - `coords`: compatible with (2,3) shaped float array

    """

    def __init__(self, coords):
        """Initialize the Line."""
        PolyLine.__init__(self, coords)
        if self.coords.shape[0] != 2:
            raise ValueError("Expected exactly two points, got %s" % coords.shape[0])


    def dxftext(self):
        return "Line(%s,%s,%s,%s,%s,%s)" % tuple(self.coords.ravel().tolist())


##############################################################################
#
class BezierSpline(Curve):
    """A class representing a Bezier spline curve of degree 1, 2 or 3.

    A Bezier spline of degree `d` is a continuous curve consisting of `nparts`
    successive parts, where each part is a Bezier curve of the same degree.
    Currently pyFormex can model linear, quadratic and cubic BezierSplines.
    A linear BezierSpline is equivalent to a PolyLine, which has more
    specialized methods than the BezierSpline, so it might be more
    sensible to use a PolyLine instead of the linear BezierSpline.

    A Bezier curve of degree `d` is determined by `d+1` control points,
    of which the first and the last are on the curve, while the intermediate
    `d-1` points are not.
    Since the end point of one part is the begin point of the next part,
    a BezierSpline is described by `ncontrol=d*nparts+1` control points if the
    curve is open, or `ncontrol=d*nparts` if the curve is closed.

    The constructor provides different ways to initialize the full set of
    control points. In many cases the off-curve control points can be
    generated automatically.

    Parameters:

    - `coords` : array_like (npoints,3)
      The points that are on the curve. For an open curve, npoints=nparts+1,
      for a closed curve, npoints = nparts.
      If not specified, the on-curve points should be included in the
      `control` argument.
    - `deriv` : array_like (npoints,3) or (2,3) or a list of 2 values
      one of which can be None and the other is a shape(3,) arraylike.
      If specified, it gives the direction of the curve at all points or at
      the endpoints only for a shape (2,3) array or only at one of the
      endpoints for a list of shape(3,) arraylike and a None type.
      For points where the direction is left unspecified or where the
      specified direction contains a `NaN` value, the direction
      is calculated as the average direction of the two
      line segments ending in the point. This will also be used
      for points where the specified direction contains a value `NaN`.
      In the two endpoints of an open curve however, this average
      direction can not be calculated: the two control points in these
      parts are set coincident.
    - `curl` : float
      The curl parameter can be set to influence the curliness of the curve
      in between two subsequent points. A value curl=0.0 results in
      straight segments. The higher the value, the more the curve becomes
      curled.
    - `control` : array(nparts,d-1,3) or array(ncontrol,3)
      If `coords` was specified and d > 1, this should be a (nparts,d-1,3) array with
      the intermediate control points, `d-1` for each part.
      If `coords` was not specified, this should be the full array of
      `ncontrol` control points for the curve.

      If not specified, the control points are generated automatically from
      the `coords`, `deriv` and `curl` arguments.
      If specified, they override these parameters.
    - `closed` : boolean
      If True, the curve will be continued from the last point back
      to the first to create a closed curve.

    - `degree`: int (1, 2 or 3)
      Specfies the degree of the curve. Default is 3.

    - `endzerocurv` : boolean or tuple of two booleans.
      Specifies the end conditions for an open curve.
      If True, the end curvature will be forced to zero. The default is
      to use maximal continuity of the curvature.
      The value may be set to a tuple of two values to specify different
      conditions for both ends.
      This argument is ignored for a closed curve.

    """
#    coeffs = {
#        1: matrix([
#            [ 1.,  0.],
#            [-1.,  1.],
#            ]),
#        2: matrix([
#            [ 1.,  0.,  0.],
#            [-2.,  2.,  0.],
#            [ 1., -2.,  1.],
#            ]),
#        3: matrix([
#            [ 1.,  0.,  0.,  0.],
#            [-3.,  3.,  0.,  0.],
#            [ 3., -6.,  3.,  0.],
#            [-1.,  3., -3.,  1.],
#            ]),
#        4: matrix([
#            [ 1.,  0.,  0.,  0.,  0.],
#            [-4.,  4.,  0.,  0.,  0.],
#            [ 6., -12.,  6.,  0.,  0.],
#            [-4., 12., -12.,  4.,  0.],
#            [ 1., -4.,  6., -4.,  1.],
#            ]),
#        }

    def __init__(self,coords=None,deriv=None,curl=1./3.,control=None,closed=False,degree=3,endzerocurv=False):
        """Create a BezierSpline curve."""
        Curve.__init__(self)

        if not degree > 0:
            raise ValueError("Degree of BezierSpline should be >= 0!")

        if endzerocurv in [False, True]:
            endzerocurv = (endzerocurv, endzerocurv)

        if coords is None:
            # All control points are given, in a single array
            control = Coords(control)
            if len(control.shape) != 2 or control.shape[-1] != 3:
                raise ValueError("If no coords argument given, the control parameter should have shape (ncontrol,3), but got %s" % str(control.shape))

            if closed:
                control = Coords.concatenate([control, control[:1]])

            ncontrol = control.shape[0]
            nextra = (ncontrol-1) % degree
            if nextra != 0:
                nextra = degree - nextra
                control = Coords.concatenate([control,]+[control[:1]]*nextra)
                ncontrol = control.shape[0]

            nparts = (ncontrol-1) // degree

        else:
            # Oncurve points are specified separately

            if degree > 3:
                raise ValueError("BezierSpline of degree > 3 can only be specified by a full set of control points")

            coords = Coords(coords)
            ncoords = nparts = coords.shape[0]
            if ncoords < 2:
                raise ValueError("Need at least two points to define a curve")
            if not closed:
                nparts -= 1

            if control is None:

                if degree == 1:
                    control = coords[:nparts]

                elif degree == 2:
                    if ncoords < 3:
                        control = 0.5*(coords[:1] + coords[-1:])
                        if closed:
                            control =  Coords.concatenate([control, control])
                    else:
                        if closed:
                            P0 = 0.5 * (roll(coords, 1, axis=0) + roll(coords, -1, axis=0))
                            P1 = 2*coords - P0
                            Q0 = 0.5*(roll(coords, 1, axis=0) + P1)
                            Q1 = 0.5*(roll(coords, -1, axis=0) + P1)
                            Q = 0.5*(roll(Q0, -1, axis=0)+Q1)
                            control = Q
                        else:
                            P0 = 0.5 * (coords[:-2] + coords[2:])
                            P1 = 2*coords[1:-1] - P0
                            Q0 = 0.5*(coords[:-2] + P1)
                            Q1 = 0.5*(coords[2:] + P1)
                            Q = 0.5*(Q0[1:]+Q1[:-1])
                            control = Coords.concatenate([Q0[:1], Q, Q1[-1:]], axis=0)

                elif degree == 3:
                    P = PolyLine(coords, closed=closed)
                    ampl = P.lengths().reshape(-1, 1)
                    if deriv is None:
                        deriv = array([[nan, nan, nan]]*ncoords)
                    else:
                        for id, d in enumerate(deriv):
                            if d is None:
                                deriv[id] = [nan, nan, nan]
                        deriv = Coords(deriv)
                        nderiv = deriv.shape[0]
                        if nderiv < ncoords:
                            if nderiv !=2 :
                                raise ValueError("Either all or at least the initial and/or the final directions expected (got %s)" % nderiv)
                            deriv = concatenate([
                                deriv[:1],
                                [[nan, nan, nan]]*(ncoords-2),
                                deriv[-1:]])

                    undefined = isnan(deriv).any(axis=-1)
                    if undefined.any():
                        deriv[undefined] = P.avgDirections()[undefined]

                    if closed:
                        p1 = coords + deriv*curl*ampl
                        p2 = coords - deriv*curl*roll(ampl, 1, axis=0)
                        p2 = roll(p2, -1, axis=0)
                    else:
                        # Fix the first and last derivs if they were autoset
                        if undefined[0]:
                            if endzerocurv[0]:
                                # option curvature 0:
                                deriv[0] =  [nan, nan, nan]
                            else:
                                # option max. continuity
                                deriv[0] = 2.*deriv[0] - deriv[1]
                        if undefined[-1]:
                            if endzerocurv[1]:
                                # option curvature 0:
                                deriv[-1] =  [nan, nan, nan]
                            else:
                                # option max. continuity
                                deriv[-1] = 2.*deriv[-1] - deriv[-2]

                        p1 = coords[:-1] + deriv[:-1]*curl*ampl
                        p2 = coords[1:] - deriv[1:]*curl*ampl
                        if isnan(p1[0]).any():
                            p1[0] = p2[0]
                        if isnan(p2[-1]).any():
                            p2[-1] = p1[-1]
                    control = concatenate([p1, p2], axis=1)

            if control is not None and degree > 1:
                try:
                    control = asarray(control).reshape(nparts, degree-1, 3)
                    control = Coords(control)
                except:
                    print("coords array has shape %s" % str(coords.shape))
                    print("control array has shape %s" % str(control.shape))
                    raise ValueError("Invalid control points for BezierSpline of degree %s" % degree)

                # Join the coords and controls in a single array
                control = Coords.concatenate([coords[:nparts, newaxis,:], control], axis=1).reshape(-1, 3)

            if control is not None:
                # We now have a multiple of degree coordinates, add the last:
                if closed:
                    last = 0
                else:
                    last = -1
                control = Coords.concatenate([control, coords[last]])

        self.degree = degree
        self.coeffs = matrix(bezierPowerMatrix(degree))
        self.coords = control
        self.nparts = nparts
        self.closed = closed


    def report(self):
        return """BezierSpline: degree=%s; nparts=%s, ncoords=%s
  Control points:
%s
""" % (self.degree, self.nparts, self.coords.shape[0], self.coords)


    __repr__ = report
    __str__ = report


    def pointsOn(self):
        """Return the points on the curve.

        This returns a Coords object of shape [nparts+1]. For a closed curve,
        the last point will be equal to the first.
        """
        return self.coords[::self.degree]


    def pointsOff(self):
        """Return the points off the curve (the control points)

        This returns a Coords object of shape [nparts,ndegree-1], or
        an empty Coords if degree <= 1.
        """
        if self.degree > 1:
            return self.coords[:-1].reshape(-1, self.degree, 3)[:, 1:]
        else:
            return Coords()


    def part(self, j, k=None):
        """Returns the points defining parts [j:k] of the curve.

        If k is None, it is set equal to j+1, resulting in a single
        part with degree+1 points.
        """
        if k is None:
            k = j+1
        start = self.degree * j
        end = self.degree * k + 1
        return self.coords[start:end]


    def sub_points(self, t, j):
        """Return the points at values t in part j."""
        P = self.part(j)
        C = self.coeffs * P
        U = [ t**d for d in range(0, self.degree+1) ]
        U = column_stack(U)
        X = dot(U, C)
        return X


    def sub_directions(self, t, j):
        """Return the unit direction vectors at values t in part j."""
        P = self.part(j)
        C = self.coeffs * P
        U = [ d*(t**(d-1)) if d >= 1 else zeros_like(t) for d in range(0, self.degree+1) ]
        U = column_stack(U)
        T = dot(U, C)
        T = normalize(T)
        return T


    def sub_curvature(self, t, j):
        """Return the curvature at values t in part j."""
        P = self.part(j)
        C = self.coeffs * P
        U1 = [ d*(t**(d-1)) if d >= 1 else zeros_like(t) for d in range(0, self.degree+1) ]
        U1 = column_stack(U1)
        T1 = dot(U1, C)
        U2 = [ d*(d-1)*(t**(d-2)) if d >=2 else zeros_like(t) for d in range(0, self.degree+1) ]
        U2 = column_stack(U2)
        T2 = dot(U2, C)
        K = length(cross(T1, T2))/(length(T1)**3)
        return K


    def length_intgrnd(self, t, j):
        """Return the arc length integrand at value t in part j."""
        P = self.part(j)
        C = self.coeffs * P
        U = [ d*(t**(d-1)) if d >= 1 else 0. for d in range(0, self.degree+1) ]
        U = array(U)
        T = dot(U, C)
        T = array(T).reshape(3)
        return length(T)


    def lengths(self):
        """Return the length of the parts of the curve."""
        try:
            from scipy.integrate import quad
        except:
            pf.warning("""..

**The **lengths** function is not available.
Most likely because 'python-scipy' is not installed on your system.""")
            return
        L = [ quad(self.length_intgrnd, 0., 1., args=(j,))[0] for j in range(self.nparts) ]
        return array(L)


    def parts(self, j, k):
        """Return a curve containing only parts j to k (k not included).

        The resulting curve is always open.
        """
        return BezierSpline(control=self.part(j,k), degree=self.degree, closed=False)


    def atLength(self, l, approx=20):
        """Returns the parameter values at given relative curve length.

        Parameters:

        - `l`: list of relative curve lengths (from 0.0 to 1.0).
          As a convenience, a single integer value may be specified,
          in which case the relative curve lengths are found by dividing
          the interval [0.0,1.0] in the specified number of subintervals.

        - `approx`: int or None. If not None, an approximate result is
          returned obtained by approximating the curve first by a
          PolyLine with `approx` number of line segments per curve segment.
          This is currently the only implemented method, and specifying
          None will fail.

        The function returns a list with the parameter values for the points
        at the specified relative lengths.
        """
        if isInt(approx) and approx > 0:
            P = self.approx(ndiv=approx)
            return P.atLength(l) / approx
        else:
            raise ValueError("approx should be int and > 0")



    def insertPointsAt(self,t,split=False):
        """Insert new points on the curve at parameter values t.

        Parameters:

        - `t`: float: parametric value where the new points will be
          inserted. Parameter values are floating point values.
          Their integer part is interpreted as the curve segment number,
          and the decimal part goes from 0 to 1 over the segment.

          * Currently there can only be one new point in each segment *

        - `split`: bool: if True, this method behaves like the
          :func:`split` method. Users should use the latter method instead
          of the `split` parameter.

        Returns a single BezierSpline (default). The result is equivalent
        with the input curve, but has more points on the curve (and more
        control points.
        If `split` is True, the behavior is that of the :func:`split` method.
        """
        from pyformex.plugins.nurbs import splitBezierCurve
        # Loop in descending order to avoid recomputing parameters
        X = []
        k = self.nparts # last full part
        points = [] # points of left over parts
        for i in argsort(t)[::-1]:
            j, uu = self.localParam(t[i])
            j = j[0]
            uu = uu[0]
            if j==k:
                raise ValueError("Currently you can only have one split point per curve part!")
            # Push the tail beyond current part
            if k > j+1:
                points[0:1] = self.part(j+1,k).tolist()
            L,R = splitBezierCurve(self.part(j),uu)
            # Push the right part
            points[0:1] = R.tolist()
            # Save the new segment
            X.insert(0,Coords.concatenate(points))
            # Save left part
            points = L.tolist()
            k = j

        if j >0:
            points = self.part(0,j).tolist()[:-1]+points
        X.insert(0,Coords.concatenate(points))

        if split:
            return [ BezierSpline(control=x, degree=self.degree, closed=False) for x in X ]
        else:
            X = Coords.concatenate([X[0]] + [xi[1:] for xi in X[1:]])
            return BezierSpline(control=X, degree=self.degree, closed=self.closed)


    def splitAt(self,t):
        """Split a BezierSpline at parametric values.

        Parameters:

        - `t`: float: parametric value where the new points will be
          inserted. Parameter values are floating point values.
          Their integer part is interpreted as the curve segment number,
          and the decimal part goes from 0 to 1 over the segment.

          * Currently there can only be one new point in each segment *

        Returns a list of len(t)+1 open BezierSplines of the same degree
        as the input.
        """
        return self.insertPointsAt(t,split=True)


    def toMesh(self):
        """Convert the BezierSpline to a Mesh.

        For degrees 1 or 2, the returned Mesh is equivalent with the
        BezierSpline, and will have element type 'line1', resp. 'line2'.

        For degree 3, the returned Mesh will currently be a quadratic
        approximation with element type 'line2'.
        """
        if self.degree == 1:
            return self.approx(ndiv=1).toMesh()
        else:
            coords = self.subPoints(2)
            e1 = 2*arange(len(coords)//2)
            elems = column_stack([e1, e1+1, e1+2])
            if self.closed:
                elems[-1][-1] = 0
            return Mesh(coords, elems, eltype='line3')


        # This is not activated (yet) because it would be called for
        # drawing curves.
    ## def toFormex(self):
    ##     """Convert the BezierSpline to a Formex.

    ##     This is notational convenience for::
    ##       self.toMesh().toFormex()
    ##     """
    ##     return self.toMesh().toFormex()


    def extend(self,extend=[1., 1.]):
        """Extend the curve beyond its endpoints.

        This function will add a Bezier curve before the first part and/or
        after the last part by applying de Casteljau's algorithm on this part.
        """
        if self.closed:
            return
        if extend[0] > 0.:
            # get the control points
            P = self.part(0)
            # apply de Casteljau's algorithm
            t = -extend[0]
            M = [ P ]
            for i in range(self.degree):
                M.append( (1.-t)*M[-1][:-1] + t*M[-1][1:] )
            # compute control points
            Q = stack([ Mi[0] for Mi in M[::-1] ], axis=0)
            self.coords = Coords.concatenate([Q[:-1], self.coords])
            self.nparts += 1
        if extend[1] > 0.:
            # get the control points
            P = self.part(self.nparts-1)
            # apply de Casteljau's algorithm
            t = 1.+extend[1]
            M = [ P ]
            for i in range(self.degree):
                M.append( (1.-t)*M[-1][:-1] + t*M[-1][1:] )
            # compute control points
            Q = stack([ Mi[-1] for Mi in M ], axis=0)
            self.coords = Coords.concatenate([self.coords, Q[1:]])
            self.nparts += 1


    def reverse(self):
        """Return the same curve with the parameter direction reversed."""
        control = reverseAxis(self.coords, axis=0)
        return BezierSpline(control=control, closed=self.closed, degree=self.degree)


##############################################################################
#

class Contour(Curve):
    """A class for storing a contour.

    The contour class stores a continuous (usually closed) curve which consists of
    a sequence of strokes, each stroke either being a straight segment or a quadratic
    or cubic Bezier curve. A stroke is thus defined by 2, 3 or 4 points.
    The contour is defined by a list of points and a Varray of element connectivity.
    This format is well suited to store contours of scalable fonts. The contours are
    in that case usually 2D.
    """
    def __init__(self,coords,elems):
        Geometry.__init__(self)
        self.prop = None
        self.coords = Coords(checkArray(coords,(-1,3),'f'))
        self.elems = Varray(elems)
        first = self.elems.col(0)
        last = self.elems.col(-1)
        if (first[1:] != last[:-1]).any():
            raise ValueError("elems do not form a continuous contour")
        self.nparts = self.elems.shape[0]
        self.closed = self.elems[0][0] == self.elems[-1][-1]

    def pointsOn(self):
        ind = self.elems.col(0)
        if not self.closed:
            ind = concatenate([ind,[self.elems[-1][-1]]])
        return self.coords[ind]

    def pointsOff(self):
        ind = unique(concatenate([r[1:-1] for  r in self.elems]))
        return self.coords[ind]

    def ncoords(self):
        return self.coords.shape[0]

    def npoints(self):
        return self.pointsOn().shape[0]

    def endPoints(self):
        """Return start and end points of the curve.

        Returns a Coords with two points, or None if the curve is closed.
        """
        if self.closed:
            return None
        else:
            return self.coords[[0, -1]]


    def part(self, i):
        """Returns the points defining part j of the curve."""
        return self.coords[self.elems[i]]


    def stroke(self,i):
        """Return curve for part i"""
        X = self.part(i)
        degree = len(X) - 1
        if len(X) == 1:
            return PolyLine(X)
        else:
            return BezierSpline(control=X,degree=degree)


    def sub_points(self, t, j):
        """Return the points at values t in part j

        t can be an array of parameter values, j is a single segment number.
        """
        j = int(j)
        t = asarray(t).reshape(-1, 1)
        return self.stroke(j).sub_points(t,0)


    def sub_directions(self, t, j):
        """Return the directions at values t in part j

        t can be an array of parameter values, j is a single segment number.
        """
        j = int(j)
        t = asarray(t).reshape(-1, 1)
        return self.stroke(j).sub_points(t,0)


    def lengths(self):
        return [ self.stroke(i).length() for i in range(self.nparts) ]


    def atChordal(self,chordal=0.01,at=None):
        # Define specialized preapproximation
        if at is None:
            at = self.atApproximate(ndiv=self.elems.lengths)
        return Curve.atChordal(self,chordal,at)


    def toMesh(self):
        """Convert the Contour to a Mesh."""
        #print("Convert to mesh")
        return [ self.stroke(i).toMesh() for i in range(self.nparts) ]

##############################################################################
#
class CardinalSpline(BezierSpline):
    """A class representing a cardinal spline.

    Create a natural spline through the given points.

    The Cardinal Spline with given tension is a Bezier Spline with curl
    :math: `curl = ( 1 - tension) / 3`
    The separate class name is retained for compatibility and convenience.
    See CardinalSpline2 for a direct implementation (it misses the end
    intervals of the point set).
    """

    def __init__(self,coords,tension=0.0,closed=False,endzerocurv=False):
        """Create a natural spline through the given points."""
        curl = (1.-tension)/3.
        BezierSpline.__init__(self, coords, curl=(1.-tension)/3., closed=closed, endzerocurv=endzerocurv)


##############################################################################
#
class CardinalSpline2(Curve):
    """A class representing a cardinal spline."""

    def __init__(self,coords,tension=0.0,closed=False):
        """Create a natural spline through the given points.

        This is a direct implementation of the Cardinal Spline.
        For open curves, it misses the interpolation in the two end
        intervals of the point set.
        """
        Curve.__init__(self)
        coords = Coords(coords)
        self.coords = coords
        self.nparts = self.coords.shape[0]
        if not closed:
            self.nparts -= 3
        self.closed = closed
        self.tension = float(tension)
        s = (1.-self.tension)/2.
        self.coeffs = matrix([[-s, 2-s, s-2., s], [2*s, s-3., 3.-2*s, -s], [-s, 0., s, 0.], [0., 1., 0., 0.]])#pag.429 of open GL


    def sub_points(self, t, j):
        n = self.coords.shape[0]
        i = (j + arange(4)) % n
        P = self.coords[i]
        C = self.coeffs * P
        U = column_stack([t**3., t**2., t, ones_like(t)])
        X = dot(U, C)
        return X


##############################################################################

class NaturalSpline(Curve):
    """A class representing a natural spline."""

    def __init__(self,coords,closed=False,endzerocurv=False):
        """Create a natural spline through the given points.

        coords specifies the coordinates of a set of points. A natural spline
        is constructed through this points.

        closed specifies whether the curve is closed or not.

        endzerocurv specifies the end conditions for an open curve.
        If True, the end curvature will forced to be zero. The default is
        to use maximal continuity (up to the third derivative) between
        the first two splines. The value may be set to a tuple of two
        values to specify different end conditions for both ends.
        This argument is ignored for a closed curve.
        """
        Curve.__init__(self)
        coords = Coords(coords)
        if closed:
            coords = Coords.concatenate([coords, coords[:1]])
        self.nparts = coords.shape[0] - 1
        self.closed = closed
        if not closed:
            if endzerocurv in [False, True]:
                self.endzerocurv = (endzerocurv, endzerocurv)
            else:
                self.endzerocurv = endzerocurv
        self.coords = coords
        self.compute_coefficients()


    def _set_coords(self, coords):
        C = self.copy()
        C._set_coords_inplace(coords)
        C.compute_coefficients()
        return C


    def compute_coefficients(self):
        n = self.nparts
        M = zeros([4*n, 4*n])
        B = zeros([4*n, 3])

        # constant submatrix
        m = array([[0., 0., 0., 1., 0., 0., 0., 0.],
                   [1., 1., 1., 1., 0., 0., 0., 0.],
                   [3., 2., 1., 0., 0., 0., -1., 0.],
                   [6., 2., 0., 0., 0., -2., 0., 0.]])

        for i in range(n-1):
            f = 4*i
            M[f:f+4, f:f+8] = m
            B[f:f+2] = self.coords[i:i+2]

        # the last spline passes through the last 2 points
        f = 4*(n-1)
        M[f:f+2, f:f+4] = m[:2, :4]
        B[f:f+2] = self.coords[-2:]

        #add the appropriate end constrains
        if self.closed:
            # first and second derivatives at starting and last point
            # (that are actually the same point) are the same
            M[f+2, f:f+4] = m[2, :4]
            M[f+2, 0:4] = m[2, 4:]
            M[f+3, f:f+4] = m[3, :4]
            M[f+3, 0:4] = m[3, 4:]

        else:
            if self.endzerocurv[0]:
                # second derivatives at start is zero
                M[f+2, 0:4] = m[3, 4:]
            else:
                # third derivative is the same between the first 2 splines
                M[f+2,  [0, 4]] = array([6., -6.])

            if self.endzerocurv[1]:
                # second derivatives at end is zero
                M[f+3, f:f+4] = m[3, :4]
            else:
                # third derivative is the same between the last 2 splines
                M[f+3, [f-4, f]] = array([6., -6.])

        #calculate the coefficients
        C = linalg.solve(M, B)
        self.coeffs = array(C).reshape(-1, 4, 3)


    def sub_points(self, t, j):
        C = self.coeffs[j]
        U = column_stack([t**3., t**2., t, ones_like(t)])
        X = dot(U, C)
        return X

##############################################################################


def circle():
    """Create a spline approximation of a circle.

    The returned circle lies in the x,y plane, has its center at (0,0,0)
    and has a radius 1.

    In the current implementation it is approximated by a bezier spline
    with curl 0.375058 through 8 points.
    """
    pts = Formex([1.0, 0.0, 0.0]).rosette(8, 45.).coords.reshape(-1, 3)
    return BezierSpline(pts, curl=0.375058, closed=True)


class Arc3(Curve):
    """A class representing a circular arc."""
    ##approx returns a PolyLine that does not start from coords[0]. Why?
    def __init__(self, coords):
        """Create a circular arc.

        The arc is specified by 3 non-colinear points.
        """
        Curve.__init__(self)
        self.nparts = 1
        self.closed = False
        self.coords = Coords(coords)##GDS. This line is needed?
        self._set_coords(Coords(coords))


    def _set_coords(self, coords):
        C = self.copy()
        C._set_coords_inplace(coords)
        if self.coords.shape != (3, 3):
            raise ValueError("Expected 3 points")

        r, C, n = gt.triangleCircumCircle(self.coords.reshape(-1, 3, 3))
        self.radius, self.center, self.normal = r[0], C[0], n[0]
        self.angles = vectorPairAngle(Coords([1., 0., 0.]), self.coords-self.center)
        print("Radius %s, Center %s, Normal %s" % (self.radius, self.center, self.normal))
        print("ANGLES=%s" % (self.angles))
        return C


    def sub_points(self, t, j):
        a = t*(self.angles[-1]-self.angles[0])
        X = Coords(column_stack([cos(a), sin(a), zeros_like(a)]))
        X = X.scale(self.radius).rotate(self.angles[0]/DEG).translate(self.center)
        return X


class Arc(Curve):
    """A class representing a circular arc.

    The arc can be specified by 3 points (begin, center, end)
    or by center, radius and two angles. In the latter case, the arc
    lies in a plane parallel to the x,y plane.
    If specified by 3 colinear points, the plane of the circle will be
    parallel to the x,y plane if the points are in such plane, else the
    plane will be parallel to the z-axis.
    """

    def __init__(self,coords=None,center=None,radius=None,angles=None,angle_spec=DEG):
        """Create a circular arc."""
        # Internally, we store the coords
        Curve.__init__(self)
        self.nparts = 1
        self.closed = False
        if coords is not None:
            self.coords = Coords(coords)
            if self.coords.shape != (3, 3):
                raise ValueError("Expected 3 points")

            self._center = self.coords[1]
            v = self.coords-self._center
            self.radius = length(self.coords[0]-self.coords[1])
            try:
                self.normal = unitVector(cross(v[0], v[2]))
            except:
                pf.warning("The three points defining the Arc seem to be colinear: I will use a random orientation.")
                self.normal = gt.anyPerpendicularVector(v[0])
            self._angles = gt.rotationAngle(Coords([1., 0., 0.]).rotate(vectorRotation([0., 0., 1.], self.normal)), self.coords[[0, 2]]-self._center, self.normal, RAD)
        else:
            if center is None:
                center = [0., 0., 0.]
            if radius is None:
                radius = 1.0
            if angles is None:
                angles = (0., 360.)
            try:
                self._center = center
                self.radius = radius
                self.normal = [0., 0., 1.]
                self._angles = [ a * angle_spec for a in angles ]
                while self._angles[1] < self._angles[0]:
                    self._angles[1] += 2*pi
                while self._angles[1] > self._angles[0] + 2*pi:
                    self._angles[1] -= 2*pi
                begin, end = self.sub_points(array([0.0, 1.0]), 0)
                self.coords = Coords([begin, self._center, end])
            except:
                print("Invalid data for Arc")
                raise

    def getCenter(self):
        return self._center

    def getAngles(self,angle_spec=DEG):
        return (self._angles[0]/angle_spec, self._angles[1]/angle_spec)

    def getAngleRange(self,angle_spec=DEG):
        return ((self._angles[1]-self._angles[0])/angle_spec)



    def _set_coords(self, coords):
        if isinstance(coords, Coords) and coords.shape == self.coords.shape:
            return self.__class__(coords)
        else:
            raise ValueError("Invalid reinitialization of %s coords" % self.__class__)


    def __str__(self):
        return """ARC
  Center %s, Radius %s, Normal %s
  Angles=%s
  Pt0=%s; Pt1=%s; Pt2=%s
"""  % ( self._center, self.radius, self.normal,
         self.getAngles(),
         self.coords[0], self.coords[1], self.coords[2]
       )


    def dxftext(self):
        return "Arc(%s,%s,%s,%s,%s,%s)" % tuple(list(self._center)+[self.radius]+list(self.getAngles()))


    def sub_points(self, t, j):
        a = t*(self._angles[-1]-self._angles[0])
        X = Coords(column_stack([cos(a), sin(a), zeros_like(a)]))
        X = X.scale(self.radius).rotate(self._angles[0]/DEG).rotate(vectorRotation([0., 0., 1.], self.normal)).translate(self._center)
        return X


    def sub_directions(self, t, j):
        a = t*(self._angles[-1]-self._angles[0])
        X = Coords(column_stack([-sin(a), cos(a), zeros_like(a)]))
        X = X.rotate(self._angles[0]/DEG).rotate(vectorRotation([0., 0., 1.], self.normal))
        return X


    def approx(self,ndiv=None,chordal=0.001):
        """Return a PolyLine approximation of the Arc.

        Approximates the Arc by a sequence of inscribed straight line
        segments.

        If `ndiv` is specified, the arc is divided in precisely `ndiv`
        segments.

        If `ndiv` is not given, the number of segments is determined
        from the chordal distance tolerance. It will guarantee that the
        distance of any point of the arc to the chordal approximation
        is less or equal than `chordal` times the radius of the arc.
        """
        if ndiv is None:
            phi = 2.*arccos(1.-chordal)
            rng = abs(self._angles[1] - self._angles[0])
            ndiv = int(ceil(rng/phi))
        return Curve.approx(self, ndiv=ndiv)


def arc2points(x0,x1,R,pos='-'):
    """Create an arc between two points

    Given two points x0 and x1, this constructs an arc with radius R
    through these points. The two points should have the same z-value.
    The arc will be in a plane parallel with the x-y plane and wind
    positively around the z-axis when moving along the arc from x0 to x1.

    If pos == '-', the center of the arc will be at the left when going
    along the chord from x0 to x1, creating an arc smaller than a half-circle.
    If pos == '+', the center of the arc will be at the right when going
    along the chord from x0 to x1, creating an arc larger than a half-circle.

    If R is too small, an exception is raised.
    """
    if x0[2] != x1[2]:
        raise ValueError("The points should b in a plane // xy plane")
    xm = (x0+x1) / 2  # center of points
    xd = (x0-x1) / 2  # half length vector
    do = normalize([xd[1], -xd[0], 0])  # direction of center
    xl = dot(xd, xd)    # square length
    if R**2 < xl:
        raise ValueError("The radius should at least be %s" % sqrt(xl))
    dd = sqrt(R**2 - xl)   # distance of center to xm
    if pos == '+':
        xc = xm - dd * do  # Center is to the left when going from x0 to x1
    else:
        xc = xm + dd * do

    xx = [1., 0., 0.]
    xz = [0., 0., 1.]
    angles = gt.rotationAngle([xx, xx], [x0-xc, x1-xc], m=[xz, xz])
    if dir == '-':
        angles = reversed(angles)
    xc[2] = x0[2]
    return Arc(center=xc, radius=R, angles=angles)


class Spiral(Curve):
    """A class representing a spiral curve."""

    def __init__(self,turns=2.0,nparts=100,rfunc=None):
        Curve.__init__(self)
        if rfunc is None:
            rfunc = lambda x:x
        self.coords = Coords([0., 0., 0.]).replic(npoints+1).hypercylindrical()
        self.nparts = nparts
        self.closed = False


##############################################################################
# Other functions

def binomial(n, k):
    """Compute the binomial coefficient Cn,k.

    This computes the binomial coefficient Cn,k = fac(n) // fac(k) // fac(n-k).

    Example:

    >>> print([ binomial(3,i) for i in range(4) ])
    [1, 3, 3, 1]
    """
    f = math.factorial
    return f(n) // f(k) // f(n-k)


_binomial_coeffs = {}
_bezier_power_matrix = {}

def binomialCoeffs(p):
    """Compute all binomial coefficients for a given degree p.

    Returns an array of p+1 values.

    For efficiency reasons, the computed values are stored in the module,
    in a dict with p as key. This allows easy and fast lookup of already
    computed values.

    Example:

    >>> print(binomialCoeffs(4))
    [1 4 6 4 1]

    """
    if p not in _binomial_coeffs:
        _binomial_coeffs[p] = array([ binomial(p,i) for i in range(p+1) ])
    return _binomial_coeffs[p]


def bezierPowerMatrix(p):
    """Compute the Bezier to power curve transformation matrix for degree p.

    Bezier curve representations can be converted to power curve representations
    using the coefficients in this matrix.

    Returns a (p+1,p+1) shaped array with a zero upper triangular part.

    For efficiency reasons, the computed values are stored in the module,
    in a dict with p as key. This allows easy and fast lookup of already
    computed values.

    Example:

    >>> print(bezierPowerMatrix(4))
    [[  1.   0.   0.   0.   0.]
     [ -4.   4.   0.   0.   0.]
     [  6. -12.   6.   0.   0.]
     [ -4.  12. -12.   4.   0.]
     [  1.  -4.   6.  -4.   1.]]

    >>> 4 in _bezier_power_matrix
    True

    """
    if p in _bezier_power_matrix:
        return _bezier_power_matrix[p]

    M = zeros((p+1,p+1))
    # Set corner elements
    M[0,0] = M[p,p] = 1.0
    M[p,0] = -1.0 if p % 2 else 1.0
    # Compute first column, last row and diagonal
    sign = -1.0
    for i in range(1,p):
        M[i,i] = binomialCoeffs(p)[i]
        M[i,0] = M[p,p-i] = sign*M[i,i]
        sign = -sign
    # Compute remaining elements
    k1 = (p+1)//2
    pk = p-1
    for k in range(1,k1):
        sign = -1.0
        for j in range(k+1,pk+1):
            M[j,k] = M[pk,p-j] = sign * binomialCoeffs(p)[k] * binomialCoeffs(p-k)[j-k]
            sign = -sign
        pk -= 1

    _bezier_power_matrix[p] = M
    return M


def convertFormexToCurve(self,closed=False):
    """Convert a Formex to a Curve.

    The following Formices can be converted to a Curve:
    - plex 2 : to PolyLine
    - plex 3 : to BezierSpline with degree=2
    - plex 4 : to BezierSpline
    """
    if closed:
        points = self.coords[:, 0,:]
    else:
        points = Coords.concatenate([self.coords[:, 0,:], self.coords[-1:, -1,:]], axis=0)
    if self.nplex() == 2:
        curve = PolyLine(points, closed=closed)
    elif self.nplex() == 3:
        control = self.coords[:, 1,:]
        curve = BezierSpline(points, control=control, closed=closed, degree=2)
    elif self.nplex() == 4:
        control = self.coords[:, 1:3,:]
        curve = BezierSpline(points, control=control, closed=closed)
    else:
        raise ValueError("Can not convert %s-plex Formex to a Curve" % self.nplex())
    return curve

Formex.toCurve = convertFormexToCurve


# End
