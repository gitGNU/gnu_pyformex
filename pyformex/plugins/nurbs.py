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

"""Using NURBS in pyFormex.

The :mod:`nurbs` module defines functions and classes to manipulate
NURBS curves and surface in pyFormex.
"""
from __future__ import print_function


from pyformex import arraytools as at
from pyformex.coords import Coords
from pyformex.lib import nurbs
from pyformex.plugins import curve
#from pyformex import options
from pyformex import utils
from pyformex import olist

from numpy import *
import numpy as np


###########################################################################
##
##   class Coords4
##
#########################
#
class Coords4(np.ndarray):
    """A collection of points represented by their homogeneous coordinates.

    While most of the pyFormex implementation is based on the 3D Cartesian
    coordinates class :class:`Coords`, some applications may benefit from using
    homogeneous coordinates. The class :class:`Coords4` provides some basic
    functions and conversion to and from cartesian coordinates.
    Through the conversion, all other pyFormex functions, such as
    transformations, are available.

    :class:`Coords4` is implemented as a float type :class:`numpy.ndarray`
    whose last axis has a length equal to 4.
    Each set of 4 values (x,y,z,w) along the last axis represents a
    single point in 3D space. The cartesian coordinates of the point
    are obtained by dividing the first three values by the fourth:
    (x/w, y/w, z/w). A zero w-value represents a point at infinity.
    Converting such points to :class:`Coords` will result in Inf or NaN
    values in the resulting object.

    The float datatype is only checked at creation time. It is the
    responsibility of the user to keep this consistent throughout the
    lifetime of the object.

    Just like :class:`Coords`, the class :class:`Coords4` is derived from
    :class:`numpy.ndarray`.

    Parameters:

    `data`: array_like
      If specified, data should evaluate to an array of floats, with the
      length of its last axis not larger than 4. When equal to four, each
      tuple along the last axis represents a ingle point in homogeneous
      coordinates.
      If smaller than four, the last axis will be expanded to four by adding
      values zero in the second and third position and values 1 in the last
      position.
      If no data are given, a single point (0.,0.,0.) will be created.

    `w`: array_like
      If specified, the w values are used to denormalize the homogeneous
      data such that the last component becomes w.

    `dtyp`: data-type
      The datatype to be used. It not specified, the datatype of `data`
      is used, or the default :data:`Float` (which is equivalent to
      :data:`numpy.float32`).

    `copy`: boolean
      If ``True``, the data are copied. By default, the original data are
      used if possible, e.g. if a correctly shaped and typed
      :class:`numpy.ndarray` is specified.
    """

    def __new__(cls, data=None, w=None, dtyp=at.Float, copy=False):
        """Create a new instance of :class:`Coords4`."""
        if data is None:
            # create an empty array
            ar = ndarray((0, 4), dtype=dtyp)
        else:
            # turn the data into an array, and copy if requested
            ar = array(data, dtype=dtyp, copy=copy)

        if ar.shape[-1] in [3, 4]:
            pass
        elif ar.shape[-1] in [1, 2]:
            # make last axis length 3, adding 0 values
            ar = at.growAxis(ar, 3-ar.shape[-1], -1)
        elif ar.shape[-1] == 0:
            # allow empty coords objects
            ar = ar.reshape(0, 3)
        else:
            raise ValueError("Expected a length 1,2,3 or 4 for last array axis")

        # Make sure dtype is a float type
        if ar.dtype.kind != 'f':
            ar = ar.astype(at.Float)

        # We should now have a float array with last axis 3 or 4
        if ar.shape[-1] == 3:
            # Expand last axis to length 4, adding values 1
            ar = at.growAxis(ar, 1, -1, 1.0)

        # Denormalize if w is specified
        if w is not None:
            self.deNormalize(w)

        # Transform 'subarr' from an ndarray to our new subclass.
        ar = ar.view(cls)

        return ar


    def normalize(self):
        """Normalize the homogeneous coordinates.

        Two sets of homogeneous coordinates that differ only by a
        multiplicative constant refer to the same points in cartesian space.
        Normalization of the coordinates is a way to make the representation
        of a single point unique. Normalization is done so that the last
        component (w) is equal to 1.

        The normalization of the coordinates is done in place.

        .. warning:: Normalizing points at infinity will result in Inf or
           NaN values.
        """
        self /= self[..., 3:]


    def deNormalize(self, w):
        """Denormalizes the homogeneous coordinates.

        This multiplies the homogeneous coordinates with the values w.
        w normally is a constant or an array with shape
        self.shape[:-1] + (1,).
        It then multiplies all 4 coordinates of a point with the same
        value, thus resulting in a denormalization while keeping the
        position of the point unchanged.

        The denormalization of the coordinates is done in place.
        If the Coords4 object was normalized, it will have precisely w as
        its 4-th coordinate value after the call.
        """
        self *= w


    def toCoords(self):
        """Convert homogeneous coordinates to cartesian coordinates.

        Returns:

        A :class:`Coords` object with the cartesian coordinates
        of the points. Points at infinity (w=0) will result in
        Inf or NaN value. If there are no points at infinity, the
        resulting :class:`Coords` point set is equivalent to the
        :class:`Coords4` one.
        """
        return Coords(self[..., :3] / self[..., 3:])


    def npoints(self):
        """Return the total number of points."""
        return np.asarray(self.shape[:-1]).prod()


    ncoords = npoints


    def x(self):
        """Return the x-plane"""
        return self[..., 0]
    def y(self):
        """Return the y-plane"""
        return self[..., 1]
    def z(self):
        """Return the z-plane"""
        return self[..., 2]
    def w(self):
        """Return the w-plane"""
        return self[..., 3]


    def bbox(self):
        """Return the bounding box of a set of points.

        Returns the bounding box of the cartesian coordinates of
        the object.
        """
        return self.toCoords().bbox()


    def actor(self,**kargs):
        """Graphical representation"""
        return self.toCoords().actor()


class Geometry4(object):
    def scale(self,*args,**kargs):
        self.coords[..., :3] = Coords(self.coords[..., :3]).scale(*args,**kargs)
        return self


#######################################################
## NURBS CURVES ##

#    nctrl = nparts * degree + 1
#    nknots = nctrl + degree + 1
#    nknots = (nparts+1) * degree + 2
#

class KnotVector(object):

    """A knot vector

    A knot vector is sequence of float values sorted in ascending order.
    Values can occur multiple times. In they typical use case for this
    class (Nurbs) most values do indeed occur multiple times, and the
    multiplicity of the values is an important quantity.
    Therefore, the knot vector is stored in two arrays of the same length:

    - `v`: the unique float values, a strictly ascending sequence
    - `m`: the multiplicity of each of the values

    Example:

    >>> K = KnotVector([0.,0.,0.,0.5,0.5,1.,1.,1.])
    >>> print(K.val)
    [ 0.   0.5  1. ]
    >>> print(K.mul)
    [3 2 3]
    >>> print(K)
    KnotVector: 0.0(3), 0.5(2), 1.0(3)
    >>> print(K.knots())
    [(0.0, 3), (0.5, 2), (1.0, 3)]
    >>> print(K.values())
    [ 0.   0.   0.   0.5  0.5  1.   1.   1. ]

    """

    def __init__(self,data=None,val=None,mul=None):
        """Initialize a KnotVector"""
        if data is not None:
            data = at.checkArray(data,(-1,),'f','i')
            val,inv = np.unique(data,return_inverse=True)
            mul,bins = at.multiplicity(inv)
        else:
            val = at.checkArray(val,(-1,),'f','i')
            mul = at.checkArray(mul,val.shape,'i')
        self.val = val#.astype(at.float64)
        self.mul = mul.astype(at.Int)


    def nknots(self):
        """Return the total number of knots"""
        return self.mul.sum()


    def knots(self):
        """Return the knots as a list of tuples (value,multiplicity)"""
        return zip(self.val,self.mul)


    def values(self):
        """Return the full list of knot values"""
        return np.concatenate([ [v]*m for v,m in self.knots()])


    def __str__(self):
        """Format the knot vector as a string."""
        return "KnotVector: " + ", ".join(["%s(%s)" % (v,m) for v,m in self.knots()])


    def reverse(self):
        """Return the reverse knot vector.

        Example:

        >>> print(KnotVector([0,0,0,1,3,6,6,8,8,8]).reverse().values())
        [ 0.  0.  0.  2.  2.  5.  7.  8.  8.  8.]

        """
        val = self.val.min() + self.val.max() - self.val
        return KnotVector(val=val[::-1],mul=self.mul[::-1])





def genKnotVector(nctrl,degree,blended=True,closed=False):
    """Compute sensible knot vector for a Nurbs curve.

    A knot vector is a sequence of non-decreasing parametric values. These
    values define the `knots`, i.e. the points where the analytical expression
    of the Nurbs curve may change. The knot values are only meaningful upon a
    multiplicative constant, and they are usually normalized to the range
    [0.0..1.0].

    A Nurbs curve with ``nctrl`` points and of given ``degree`` needs a knot
    vector with ``nknots = nctrl+degree+1`` values. A ``degree`` curve needs
    at least ``nctrl = degree+1`` control points, and thus at least
    ``nknots = 2*(degree+1)`` knot values.

    To make an open curve start and end in its end points, it needs knots with
    multiplicity ``degree+1`` at its ends. Thus, for an open blended curve, the
    default policy is to set the knot values at the ends to 0.0, resp. 1.0,
    both with multiplicity ``degree+1``, and to spread the remaining
    ``nctrl - degree - 1`` values equally over the interval.

    For a closed (blended) curve, the knots are equally spread over the
    interval, all having a multiplicity 1 for maximum continuity of the curve.

    For an open unblended curve, all internal knots get multiplicity ``degree``.
    This results in a curve that is only one time continuously derivable at
    the knots, thus the curve is smooth, but the curvature may be discontinuous.
    There is an extra requirement in this case: ``nctrl`` should be a multiple
    of ``degree`` plus 1.

    Returns a KnotVector instance.

    Example:

    >>> print(genKnotVector(7,3))
    KnotVector: 0.0(4), 0.25(1), 0.5(1), 0.75(1), 1.0(4)
    >>> print(genKnotVector(7,3,blended=False))
    KnotVector: 0.0(4), 1.0(3), 2.0(4)
    >>> print(genKnotVector(3,2,closed=True))
    KnotVector: 0.0(1), 0.2(1), 0.4(1), 0.6(1), 0.8(1), 1.0(1)
    """
    nknots = nctrl+degree+1
    if closed or blended:
        nval = nknots
        if not closed:
            nval -= 2*degree
        val = at.uniformParamValues(nval-1) # Returns nval values!
        mul = ones(nval,dtype=at.Int)
        if not closed:
            mul[0] = mul[-1] = degree+1
        return KnotVector(val=val,mul=mul)
    else:
        nparts = (nctrl-1) / degree
        if nparts*degree+1 != nctrl:
            raise ValueError("Discrete knot vectors can only be used if the number of control points is a multiple of the degree, plus one.")
        knots = [0.] + [ [float(i)]*degree for i in range(nparts+1) ] + [float(nparts)]
        knots = olist.flatten(knots)
        return KnotVector(knots)


class NurbsCurve(Geometry4):

    """A NURBS curve

    The Nurbs curve is defined by nctrl control points, a degree (>= 1) and
    a knot vector with nknots = nctrl+degree+1 parameter values.

    Parameters:

    - `control`: Coords-like (nctrl,3): the vertices of the control polygon.
    - `degree`: int: the degree of the Nurbs curve.
    - `wts`: float array (nctrl): weights to be attributed to the control
      points. Default is toattribute a weight 1.0 to all points. Using
      different weights allows for more versatile modeling (like perfect
      circles and arcs.)
    - `knots`: KnotVector or an ascending list of nknots float values.
      The values are only defined upon a multiplicative constant and will
      be normalized to set the last value to 1.
      If `degree` is specified, default values are constructed automatically
      by calling :func:`genKnotVector`.
      If no knots are given and no degree is specified, the degree is set to
      the nctrl-1 if the curve is blended. If not blended, the degree is not
      set larger than 3.
    - `closed`: bool: determines whether the curve is closed. Default
      False. The use of closed NurbsCurves is currently very limited.
    - `blended`: bool: determines that the curve is blended. A nonblended
      curve is a chain of independent curves (Bezier curves if the weights
      are all ones). The number of control points should be a multiple of the
      degree, plus one.
      See also :meth:`decompose`.

    """

    N_approx = 100
#
#    order (2,3,4,...) = degree+1 = min. number of control points
#    ncontrol >= order
#    nknots = order + ncontrol >= 2*order
#
#    convenient solutions:
#    OPEN:
#      nparts = (ncontrol-1) / degree
#      nintern =
#
    def __init__(self,control,degree=None,wts=None,knots=None,closed=False,blended=True):
        self.closed = closed
        nctrl = len(control)
        if knots is not None:
            if not isinstance(knots,KnotVector):
                knots = KnotVector(knots)
            nknots = knots.nknots()

        if degree is None:
            if knots is None:
                degree = nctrl-1
                if not blended:
                    degree = min(degree, 3)
            else:
                degree = nknots - nctrl -1
                if degree <= 0:
                    raise ValueError("Length of knot vector (%s) must be at least number of control points (%s) plus 2" % (nknots, nctrl))

        order = degree+1
        control = Coords4(control)
        if wts is not None:
            control.deNormalize(wts.reshape(wts.shape[-1], 1))

        if closed:
            if knots is None:
                nextra = degree
            else:
                nextra = nknots - nctrl - order
            nextra1 = (nextra+1) // 2
            nextra2 = nextra-nextra1
            print("extra %s = %s + %s" % (nextra, nextra1, nextra2))
            control = Coords4(concatenate([control[-nextra1:], control, control[:nextra2]], axis=0))

        nctrl = control.shape[0]

        if nctrl < order:
            raise ValueError("Number of control points (%s) must not be smaller than order (%s)" % (nctrl, order))

        if knots is None:
            knots = genKnotVector(nctrl, degree, blended=blended, closed=closed)
            nknots = knots.nknots()

        if nknots != nctrl+order:
            raise ValueError("Length of knot vector (%s) must be equal to number of control points (%s) plus order (%s)" % (nknots, nctrl, order))


        self.coords = control
        self.knotv = knots
        self.degree = degree
        self.closed = closed


    @property
    def knots(self):
        """Return the full list of knot values"""
        return self.knotv.values()

    # This is commented out because there is only 1 place where we set
    # the knots: __init__
#    @knots.setter
#    def knots(self,value):
#        """Set the knot values"""
#        self.knotv = KnotVector(knots)


    def nctrl(self):
        """Return the number of control points"""
        return self.coords.shape[0]

    def nknots(self):
        """Return the number of knots"""
        return self.knotv.nknots()

    def order(self):
        """Return the order of the Nurbs curve"""
        return self.nknots()-self.nctrl()

    def bbox(self):
        """Return the bounding box of the NURBS curve.

        """
        return self.coords.toCoords().bbox()


    def __str__(self):
        return """NURBS Curve, degree = %s, nctrl = %s, nknots = %s
  Control points:
%s,
  knots = %s
"""  % ( self.degree, len(self.coords), self.nknots(), self.coords, self.knotv)


    def pointsAt(self, u):
        """Return the points on the Nurbs curve at given parametric values.

        Parameters:

        - `u`: (nu,) shaped float array, parametric values at which a point
          is to be placed.

        Returns (nu,3) shaped Coords with nu points at the specified
        parametric values.

        """
        ctrl = self.coords.astype(double)
        knots = self.knotv.values().astype(double)
        u = atleast_1d(u).astype(double)

        try:
            pts = nurbs.curvePoints(ctrl, knots, u)
            if isnan(pts).any():
                print("We got a NaN")
                raise RuntimeError
        except:
            raise RuntimeError("Some error occurred during the evaluation of the Nurbs curve")

        if pts.shape[-1] == 4:
            pts = Coords4(pts).toCoords()
        else:
            pts = Coords(pts)
        return pts


    def derivs(self,u,d=1):
        """Returns the points and derivatives up to d at parameter values at

        Parameters:

        - `u`: either of:

          - int: number of points (npts) at which to evaluate the points
            andderivatives. The points will be equally spaced in parameter space.

          - float array (npts): parameter values at which to compute points
            and derivatives.

        - `d`: int: highest derivative to compute.

        Returns a float array of shape (d+1,npts,3).
        """
        if isinstance(u, int):
            u = at.uniformParamValues(u, self.knotv.val[0], self.knotv.val[-1])
        else:
            u = at.checkArray(u, (-1,), 'f', 'i')

        # sanitize arguments for library call
        ctrl = self.coords.astype(double)
        knots = self.knotv.values().astype(double)
        u = atleast_1d(u).astype(double)
        d = int(d)

        try:
            pts = nurbs.curveDerivs(ctrl, knots, u, d)
            if isnan(pts).any():
                print("We got a NaN")
                print(pts)
                raise RuntimeError
        except:
            raise RuntimeError("Some error occurred during the evaluation of the Nurbs curve")

        if pts.shape[-1] == 4:
            pts = Coords4(pts)
            # When using no weights, ctrl points are Coords4 normalized points,
            # and the derivatives all have w=0: the points represent directions
            # We just strip off the w=0.
            # HOWEVER, if there are weights, not sure what to do.
            # Points themselves could be just normalized and returned.
            pts[0].normalize()
            pts = Coords(pts[..., :3])
        else:
            pts = Coords(pts)
        return pts


    def knotPoints(self,multiple=False):
        """Returns the points at the knot values.

        If multiple is True, points are returned with their multiplicity.
        The default is to return all points just once.
        """
        if multiple:
            val = self.knotv.knots
        else:
            val = self.knotv.val
        return self.pointsAt(val)


    def insertKnots(self, u):
        """Insert a set of knots in the Nurbs curve.

        u is a vector with knot parameter values to be inserted into the
        curve. The control points are adapted to keep the curve unchanged.

        Returns:

        A Nurbs curve equivalent with the original but with the
        specified knot values inserted in the knot vector, and the control
        points adapted.
        """
        if self.closed:
            raise ValueError("insertKnots currently does not work on closed curves")
        # sanitize arguments for library call
        ctrl = self.coords.astype(double)
        knots = self.knotv.values().astype(double)
        u = asarray(u).astype(double)
        newP, newU = nurbs.curveKnotRefine(ctrl, knots, u)
        return NurbsCurve(newP, degree=self.degree, knots=newU, closed=self.closed)


    def decompose(self):
        """Decomposes a curve in subsequent Bezier curves.

        Returns an equivalent unblended Nurbs.
        """
        # sanitize arguments for library call
        ctrl = self.coords
        knots = self.knotv.values().astype(double)
        X = nurbs.curveDecompose(ctrl, knots)
        return NurbsCurve(X, degree=self.degree, blended=False)


    def removeKnot(self, u, m, tol=1.e-5):
        """Remove a knot from the knot vector of the Nurbs curve.

        u: knot value to remove
        m: how many times to remove (if negative, remove maximally)

        Returns:

        A Nurbs curve equivalent with the original but with a knot vector
        where the specified value has been removed m times, if possible,
        or else as many times as possible. The control points are adapted
        accordingly.

        """
        if self.closed:
            raise ValueError("removeKnots currently does not work on closed curves")
        P = self.coords.astype(double)
        Uv = self.knotv.val.astype(double)
        Um = self.knotv.mul.astype(at.Int)
        w = where(isclose(Uv,u))[0]
        if len(w) > 0:
            i = w[0]
        else:
            print("No such knot value: %s" % u)
            return self

        if m < 0:
            m = Um[i]

        t,newP,newU = nurbs.curveKnotRemove(P,Uv,Um,i,m,tol)

        if t > 0:
            print("Removed the knot value %s %s times" % (u,t))
            return NurbsCurve(newP, degree=self.degree, knots=newU, closed=self.closed)
        else:
            print("Can not remove the knot value %s" % u)
            return self


    def removeAllKnots(self,tol=1.e-5):
        """Remove all removable knots"""
        N = self
        print(N)
        while True:
            print(N)
            for u in N.knotv.val:
                print("Removing %s" % u)
                NN = N.removeKnot(u,m=-1,tol=tol)
                if NN is N:
                    print("Can not remove")
                    continue
                else:
                    break
            if NN is N:
                print("Done")
                break
            else:
                print("Cycle")
                N = NN
        return N


    def elevateDegree(self, t):
        """Elevate the degree of the Nurbs curve.

        t: how much to elevate the degree

        Returns:

        A Nurbs curve equivalent with the original but of a higher degree.

        """
        if self.closed:
            raise ValueError("elevateDegree currently does not work on closed curves")

        P = self.coords.astype(double)
        #Uv = self.knotv.val.astype(double)
        #Um = self.knotv.mul.astype(at.Int)
        newP,newU,nh,mh = nurbs.curveDegreeElevate(P, self.knots, t)

        #Pw = self.coords
        #newP,newU,nh,mh = curveDegreeElevate(Pw, self.knots, t)

        return NurbsCurve(newP, degree=self.degree+t, knots=newU, closed=self.closed)


    def reduceDegree(self, nd):
        """Reduce the degree of the Nurbs curve.

        nd: how much to reduce the degree

        Returns:

        A Nurbs curve approximating the original but of a lower degree.

        """
        pass


    # TODO: This might be implemented in C for efficiency
    def projectPoint(self, P, eps1=1.e-5, eps2=1.e-5, maxit=20, nseed=20):
        """Project a given point on the Nurbs curve.

        This can also be used to determine the parameter value of a point
        lying on the curve.

        Parameters:

        - `P`: Coords-like (npts,3): one or more points is space.

        Returns a tuple (u,X):

        - `u`: float: parameter value of the base point X of the projection
          of P on the NurbsCurve.
        - `X`: Coords (3,): the base point of the projection of P
          on the NurbsCurve.

        The algorithm is based on the from The Nurbs Book.

        """
        P = at.checkArray(P,(3,),'f','i')

        # Determine start value from best match of nseed+1 points
        umin,umax = self.knotv.val[[0,-1]]
        u = at.uniformParamValues(nseed+1,umin,umax)
        pts = self.pointsAt(u)
        i = pts.distanceFromPoint(P).argmin()
        u0,P0 = u[i],pts[i]
        #print("Start at point %s : %s" % (u0,P0))

        # Apply Newton's method to minimize distance
        i = 0
        ui = u0
        while i < maxit:
            i += 1
            C = self.derivs([ui],2)
            C0,C1,C2 = C[:,0]
            CP = (C0-P)
            CPxCP = dot(CP,CP)
            C1xCP = dot(C1,CP)
            C1xC1 = dot(C1,C1)
            eps1sq = eps1*eps1
            eps2sq = eps2*eps2
            # Check convergence
            chk1 = CPxCP <= eps1sq
            chk2 = C1xCP / C1xC1 / CPxCP <= eps2sq

            uj = ui - dot(C1,CP) / ( dot(C2,CP) + dot(C1,C1) )
            # ensure that parameter stays in range
            if self.closed:
                while uj < umin:
                    uj += umax - umin
                while uj > umax:
                    uj -= umax - umin
            else:
                if uj < umin:
                    uj = umin
                if uj > umax:
                    uj = umax

            # Check convergence
            chk4 = (uj-ui)**2 * C1xC1 <= eps1sq
            P0 = self.pointsAt([uj])[0]
            #print("u[%s] = %s (P=%s) conv=%s" % (i,uj,P0,(chk1,chk2,chk4)))

            if (chk1 or chk2) and chk4:
                # Converged!
                break
            else:
                # Prepare for next it
                ui = uj

        if i == maxit:
            print("Convergence not reached after %s iterations" % maxit)

        return u0,P0


    def approx(self,ndiv=None,nseg=None,**kargs):
        """Return a PolyLine approximation of the Nurbs curve

        If no `nseg` is given, the curve is approximated by a PolyLine
        through equidistant `ndiv+1` point in parameter space. These points
        may be far from equidistant in Cartesian space.

        If `nseg` is given, a second approximation is computed with `nseg`
        straight segments of nearly equal length. The lengths are computed
        based on the first approximation with `ndiv` segments.
        """
        from pyformex.plugins.curve import PolyLine
        if ndiv is None:
            ndiv = self.N_approx
        u = arange(ndiv+1)*1.0/ndiv
        PL = PolyLine(self.pointsAt(u))
        if nseg is not None:
            u = PL.atLength(nseg)
            PL = PolyLine(PL.pointsAt(u))
        return PL


    def actor(self,**kargs):
        """Graphical representation"""
        from pyformex.legacy.actors import NurbsActor
        from pyformex.opengl.actors import Actor
        if self.degree <= 7:
            return NurbsActor(self,**kargs)
        else:
            #B = self.decompose()
            return Actor(self.approx(ndiv=100).toFormex(),**kargs)


    def reverse(self):
        """Return the reversed Nurbs curve.

        The reversed curve is geometrically identical, but start and en point
        are interchanged and parameter values increase in the opposite direction.
        """
        return NurbsCurve(control=self.coords[::-1], knots=self.knotv.reverse(), degree=self.degree, closed=self.closed)


from pyformex.plugins.curve import binomial
def curveDegreeElevate(Pw,U,t):
    """Elevate the degree of the Nurbs curve.

    t: how much to elevate the degree

    Returns:

    A Nurbs curve equivalent with the original but of a higher degree.

    """
    nk,nd = Pw.shape
    n = nk-1
    m = U.shape[0]-1
    p = m-n-1
    # Workspace for return arrays
    Uh = np.zeros((U.shape[0]*(t+1)))
    Qw = np.zeros((Pw.shape[0]*(t+1),nd))
    # Workspaces
    bezalfs = np.zeros((p+t+1,p+1))
    bpts = np.zeros((p+1,nd))
    ebpts = np.zeros((p+t+1,nd))
    Nextbpts = np.zeros((p-1,nd))
    alfs = np.zeros((p-1,))

    ph = p+t
    ph2 = ph//2
#    print("New degree: %s" % ph)

    bezalfs[0,0] = bezalfs[ph,p] = 1.0
    for i in range(1,ph2+1):
        inv = 1.0 / binomial(ph,i)
        mpi = min(p,i)
        for j in range(max(0,i-t),mpi+1):
            bezalfs[i,j] = inv * binomial(p,j) * binomial(t,i-j)
    for i in range(ph2+1,ph):
        mpi = min(p,i)
        for j in range(max(0,i-t),mpi+1):
            bezalfs[i,j] = bezalfs[ph-i,p-j]
#    print("bezalfs:",bezalfs)

    mh = ph
    kind = ph+1
    r = -1
    a = p
    b = p+1
    cind = 1
    ua = U[0]
    Qw[0] = Pw[0]
    for i in range(ph+1):
        Uh[i] = ua
    for i in range(p+1):
        bpts[i] = Pw[i]
#    print("bpts =\n%s" % bpts[:p+1])

    while (b < m):
#        print("Big loop b = %s < m = %s" % (b,m))
        i = b
        while b < m and U[b] == U[b+1]:
            b += 1;
        mul = b-i+1
        mh = mh+mul+t
        ub = U[b]
        oldr = r
        r = p-mul

#        print("Insert knot %s r=%s times (oldr=%s)" % (ub,r,oldr))
        lbz = (oldr+2)//2 if oldr > 0 else 1
        rbz = ph-(r+1)//2 if r > 0 else ph

        if r > 0:
#            print("Insert knot to get Bezier segment of degree %s mul %s" % (p,mul))
            numer = ub-ua
            for k in range(p,mul,-1):
                alfs[k-mul-1] = numer / (U[a+k] - ua)
#            print("alfs = %s" % alfs[:p])
            for j in range(1,r+1):
                save = r-j
                s = mul+j
                for k in range(p,s-1,-1):
                    bpts[k] = alfs[k-s]*bpts[k] + (1.0-alfs[k-s])*bpts[k-1]
                Nextbpts[save] = bpts[p]
#                print("Nextbpts %s = %s" %(save,Nextbpts[save]))
#            print("bpts =\n%s" % bpts[:p+1])
            #X = Coords(bpts[:p+1,:3])
            #draw(PolyLine(X))
            #draw(X)

#        print("Degree elevate Bezier")
        for i in range(lbz,ph+1):
            ebpts[i] = 0.0
            mpi = min(p,i)
            for j in range(max(0,i-t),mpi+1):
                ebpts[i] += bezalfs[i,j]*bpts[j]
#        print("ebpts =\n%s" % ebpts[lbz:ph+1])
        #X = Coords(ebpts[lbz:ph+1,:3])
        #draw(PolyLine(X),color='red')
        #draw(X,color='red')

        if oldr > 1:
#            print("Must remove knot %s %s times" % (ua,oldr))
            first = kind-2
            last = kind
            den = ub-ua
            bet = (ub-Uh[kind-1]/den)
            for tr in range(1,oldr):
#                print("Knot removal loop %s, (first=%s, last=%s)" % (tr,first,last))
                i = first
                j = last
                kj = j-kind+1
                while j-i > tr:
#                    print("Compute new control points (i=%s, j=%s)" % (i,j))
                    if i < cind:
                        alf = (ub-Uh[i]) / (ua-Uh[i])
                        Qw[i] = alf*Qw[i] + (1.0-alf)*Qw[i-1]
                    if j >= lbz:
                        if j-tr <= kind-ph+oldr:
                            gam = (ub-Uh[j-tr]) / den
                            ebpts[kj] = gam*ebpts[kj] + (1.0-gam)*ebpts[kj+1]
                        else:
                            ebpts[kj] = bet*ebpts[kj] + (1.0-bet)*ebpts[kj+1]
                    i += 1
                    j -= 1
                    kj -= 1
                first -= 1
                last +=1

        if a != p:
#            print("Load the knot ua")
            for i in range(ph-oldr):
                Uh[kind] = ua
                kind += 1

        for j in range(lbz,rbz+1):
#            print("Load control point %s into Qw %s)" % (j,cind))
            Qw[cind] = ebpts[j]
            cind += 1
#        print(Qw[:cind])

#        print("Now b=%s, m=%s" % (b,m))
        if b < m:
#            print("Set up for next pass")
            for j in range(r):
                bpts[j] = Nextbpts[j]
            for j in range(r,p+1):
                bpts[j] = Pw[b-p+j]
            a = b
            b += 1
            ua = ub
        else:
#            print("End knot")
            for i in range(ph+1):
                Uh[kind+i] = ub

    nh = mh - ph - 1
    Uh = Uh[:mh+1]
    Qw = Qw[:nh+1]
    return np.array(Qw), np.array(Uh), nh, mh



#######################################################
## NURBS Surface ##


class NurbsSurface(Geometry4):

    """A NURBS surface

    The Nurbs surface is defined as a tensor product of NURBS curves in two
    parametrical directions u and v. The control points form a grid of
    (nctrlu,nctrlv) points. The other data are like those for a NURBS curve,
    but need to be specified as a tuple for the (u,v) directions.

    The knot values are only defined upon a multiplicative constant, equal to
    the largest value. Sensible default values are constructed automatically
    by a call to the :func:`genKnotVector` function.

    If no knots are given and no degree is specified, the degree is set to
    the number of control points - 1 if the curve is blended. If not blended,
    the degree is not set larger than 3.

    .. warning:: This is a class under development!

    """

    def __init__(self,control,degree=(None, None),wts=None,knots=(None, None),closed=(False, False),blended=(True, True)):

        self.closed = closed

        control = Coords4(control)
        if wts is not None:
            control.deNormalize(wts.reshape(wts.shape[-1], 1))

        for d in range(2):
            nctrl = control.shape[1-d] # BEWARE! the order of the nodes
            deg = degree[d]
            kn = knots[d]
            bl = blended[d]
            cl = closed[d]

            if deg is None:
                if kn is None:
                    deg = nctrl-1
                    if not bl:
                        deg = min(deg, 3)
                else:
                    deg = len(kn) - nctrl -1
                    if deg <= 0:
                        raise ValueError("Length of knot vector (%s) must be at least number of control points (%s) plus 2" % (len(knots), nctrl))
                # make degree changeable
                degree = list(degree)
                degree[d] = deg

            order = deg+1

            if nctrl < order:
                raise ValueError("Number of control points (%s) must not be smaller than order (%s)" % (nctrl, order))

            if kn is None:
                kn = genKnotVector(nctrl, deg, blended=bl, closed=cl).values()
            else:
                kn = asarray(kn).ravel()

            nknots = kn.shape[0]

            if nknots != nctrl+order:
                raise ValueError("Length of knot vector (%s) must be equal to number of control points (%s) plus order (%s)" % (nknots, nctrl, order))

            if d == 0:
                self.uknots = kn
            else:
                self.vknots = kn

        self.coords = control
        self.degree = degree
        self.closed = closed


    def order(self):
        return (self.uknots.shape[0]-self.coords.shape[1],
                self.vknots.shape[0]-self.coords.shape[0])

    def bbox(self):
        """Return the bounding box of the NURBS surface.

        """
        return self.coords.toCoords().bbox()


    def pointsAt(self, u):
        """Return the points on the Nurbs surface at given parametric values.

        Parameters:

        - `u`: (nu,2) shaped float array: `nu` parametric values (u,v) at which
          a point is to be placed.

        Returns (nu,3) shaped Coords with `nu` points at the specified
        parametric values.

        """
        ctrl = self.coords.astype(double)
        U = self.vknots.astype(double)
        V = self.uknots.astype(double)
        u = asarray(u).astype(double)

        try:
            pts = nurbs.surfacePoints(ctrl, U, V, u)
            if isnan(pts).any():
                print("We got a NaN")
                raise RuntimeError
        except:
            raise RuntimeError("Some error occurred during the evaluation of the Nurbs curve")

        if pts.shape[-1] == 4:
            pts = Coords4(pts).toCoords()
        else:
            pts = Coords(pts)
        return pts


    def derivs(self, u, m):
        """Return points and derivatives at given parametric values.

        Parameters:

        - `u`: (nu,2) shaped float array: `nu` parametric values (u,v) at which
          the points and derivatives are evaluated.
        - `m`: tuple of two int values (mu,mv). The points and derivatives up
          to order mu in u direction and mv in v direction are returned.

        Returns:

        (nu+1,nv+1,nu,3) shaped Coords with `nu` points at the
        specified parametric values. The slice (0,0,:,:) contains the
        points.

        """
        # sanitize arguments for library call
        ctrl = self.coords.astype(double)
        U = self.vknots.astype(double)
        V = self.uknots.astype(double)
        u = asarray(u).astype(double)
        mu, mv = m
        mu = int(mu)
        mv = int(mv)

        try:
            pts = nurbs.surfaceDerivs(ctrl, U, V, u, mu, mv)
            if isnan(pts).any():
                print("We got a NaN")
                raise RuntimeError
        except:
            raise RuntimeError("Some error occurred during the evaluation of the Nurbs surface")

        if pts.shape[-1] == 4:
            pts = Coords4(pts)
            pts[0][0].normalize()
            pts = Coords(pts[..., :3])
        else:
            pts = Coords(pts)
        return pts


    def actor(self,**kargs):
        """Graphical representation"""
        from pyformex.legacy.actors import NurbsActor
        return NurbsActor(self,**kargs)


################################################################


def globalInterpolationCurve(Q,degree=3,strategy=0.5):
    """Create a global interpolation NurbsCurve.

    Given an ordered set of points Q, the globalInterpolationCurve
    is a NURBS curve of the given degree, passing through all the
    points.

    Returns:

    A NurbsCurve through the given point set. The number of
    control points is the same as the number of input points.

    .. warning:: Currently there is the limitation that two consecutive
      points should not coincide. If they do, a warning is shown and
      the double points will be removed.

    The procedure works by computing the control points that will
    produce a NurbsCurve with the given points occurring at predefined
    parameter values. The strategy to set this values uses a parameter
    as exponent. Different values produce (slighly) different curves.
    Typical values are:

    0.0: equally spaced (not recommended)
    0.5: centripetal (default, recommended)
    1.0: chord length (often used)
    """
    from pyformex.plugins.curve import PolyLine
    # set the knot values at the points
    #nc = Q.shape[0]
    #n = nc-1

    # chord length
    d = PolyLine(Q).lengths()
    if (d==0.0).any():
        utils.warn("warn_nurbs_gic")
        Q = concatenate([Q[d!=0.0], Q[-1:]], axis=0)
        d = PolyLine(Q).lengths()
        if (d==0.0).any():
            raise ValueError("Double points in the data set are not allowed")
    # apply strategy
    d = d ** strategy
    d = d.cumsum()
    d /= d[-1]
    u = concatenate([[0.], d])
    #print "u = ",u
    U, A = nurbs.curveGlobalInterpolationMatrix(Q, u, degree)
    #print "U = ",U
    #print "A = ",A
    P = linalg.solve(A, Q)
    #print "P = ",P
    return NurbsCurve(P, knots=U, degree=degree)


def toCoords4(x):
    """Convert cartesian coordinates to homogeneous

    `x`: :class:`Coords`
      Array with cartesian coordinates.

    Returns a Coords4 object corresponding to the input cartesian coordinates.
    """
    return Coords4(x)

Coords.toCoords4 = toCoords4


def pointsOnBezierCurve(P, u):
    """Compute points on a Bezier curve

    Parameters:

    P is an array with n+1 points defining a Bezier curve of degree n.
    u is a vector with nu parameter values between 0 and 1.

    Returns:

    An array with the nu points of the Bezier curve corresponding with the
    specified parametric values.
    ERROR: currently u is a single paramtric value!

    See also:
    examples BezierCurve, Casteljau
    """
    u = asarray(u).ravel()
    n = P.shape[0]-1
    return Coords.concatenate([
        (nurbs.allBernstein(n, ui).reshape(1, -1, 1) * P).sum(axis=1)
        for ui in u ], axis=0)


def deCasteljau(P, u):
    """Compute points on a Bezier curve using deCasteljau algorithm

    Parameters:

    P is an array with n+1 points defining a Bezier curve of degree n.
    u is a single parameter value between 0 and 1.

    Returns:

    A list with point sets obtained in the subsequent deCasteljau
    approximations. The first one is the set of control points, the last one
    is the point on the Bezier curve.

    This function works with Coords as well as Coords4 points.
    """
    n = P.shape[0]-1
    C = [P]
    for k in range(n):
        Q = C[-1]
        Q = (1.-u) * Q[:-1] + u * Q[1:]
        C.append(Q)
    return C


def splitBezierCurve(P, u):
    """Split a Bezier curve at parametric values

    Parameters:

    P is an array with n+1 points defining a Bezier curve of degree n.
    u is a single parameter value between 0 and 1.

    Returns two arrays of n+1 points, defining the Bezier curves of degree n
    obtained by splitting the input curve at parametric value u. These results
    can be used with the control argument of BezierSpline to create the
    corresponding curve.

    """
    C = deCasteljau(P, u)
    L = stack([x[0] for x in C])
    R = stack([x[-1] for x in C[::-1]])
    return L,R



def curveToNurbs(B):
    """Convert a BezierSpline to NurbsCurve"""
    return NurbsCurve(B.coords, degree=B.degree, closed=B.closed, blended=False)

curve.BezierSpline.toNurbs = curveToNurbs

def polylineToNurbs(B):
    """Convert a PolyLine to NurbsCurve"""
    return NurbsCurve(B.coords, degree=1, closed=B.closed, blended=False)

curve.PolyLine.toNurbs = polylineToNurbs


def frenet(d1,d2,d3=None):
    """Returns the 3 Frenet vectors and the curvature.

    Parameters:

    - `d1`: first derivative at `npts` points of a nurbs curve
    - `d2`: second derivative at `npts` points of a nurbs curve
    - `d3`: (optional) third derivative at `npts` points of a nurbs curve

    The derivatives of the nurbs curve are normally obtained from
    :func:`NurbsCurve.deriv`.

    Returns:

    - `T`: normalized tangent vector to the curve at `npts` points
    - `N`: normalized normal vector to the curve at `npts` points
    - `B`: normalized binormal vector to the curve at `npts` points
    - `k`: curvature of the curve at `npts` points
    - `t`: (only if `d3` was specified) torsion of the curve at `npts` points

    """
    l = length(d1)
    # What to do when l is 0? same as with k?
    if l.min() == 0.0:
        print("l is zero at %s" % where(l==0.0)[0])
    e1 = d1 / l.reshape(-1, 1)
    e2 = d2 - dotpr(d2, e1).reshape(-1, 1)*e1
    k = length(e2)
    if k.min() == 0.0:
        w = where(k==0.0)[0]
        print("k is zero at %s" % w)
    # where k = 0: set e2 to mean of previous and following
    e2 /= k.reshape(-1, 1)
    #e3 = normalize(ddd - dotpr(ddd,e1)*e1 - dotpr(ddd,e2)*e2)
    e3 = cross(e1, e2)
    m = dotpr(cross(d1, d2), e3)
    #print "m",m
    k = m / l**3
    if d3 is None:
        return e1, e2, e3, k
    # compute torsion
    t = dotpr(d1, cross(d2, d3)) / dotpr(d1, d2)
    return e1, e2, e3, k, t


### End
