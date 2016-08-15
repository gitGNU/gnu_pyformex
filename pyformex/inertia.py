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
"""Compute inertia related quantities of geometrical models.

Inertia related quantities of a geometrical model comprise: the total mass,
the center of mass, the inertia tensor, the principal axes of inertia.

This module defines some classes to store the inertia data:

- :class:`Tensor`: a general second order tensor
- :class:`Inertia`: a specialized second order tensor for inertia data

This module also provides the basic functions to compute the inertia data
of collections of simple geometric data: points, lines, triangles, tetrahedrons.

The prefered way to compute inertia data of a geometric model is through the
:meth:`Geometry.inertia` methods.
"""
from __future__ import print_function

from pyformex import arraytools as at
from pyformex.coords import Coords
from pyformex.formex import Formex
from pyformex.coordsys import CoordSys

import numpy as np

class Tensor(np.ndarray):
    """A second order symmetric(!) shaped tensor in 3D vector space.

    This is a new class under design. Only use for developemnt!

    The Tensor class provides conversion between full matrix (3,3) shape
    and contracted vector (6,) shape.
    It can e.g. be used to store an inertia tensor or a stress or strain
    tensor.
    It provides methods to transform the tensor to other (cartesian)
    axes.

    Parameters:

    - `data`: array-like (float) of shape (3,3) or (6,)
    - `symmetric`: bool. If True (default), the tensor is forced to be
      symmetric by averaging the off-diagonal elements.
    - `cs`: CoordSys. The coordinate system of the tensor.

    Properties: a Tensor T has the following properties:

    - T.xx, T.xy, T.xz, T.yx, T.yy, T.yz, T.zx, T.zy, T.zz: aliases for
      the nine components of the tensor
    - T.contracted: the (6,) shaped contracted array with independent
      values of the tensor
    - T.tensor: the full tensor as an (3,3) array

    Discussion:

    - inertia and stres/strain tensors transform in the same way
      on rotations of axes. But differently on translations! Should we
      therefore store the purpose of the tensor??

      * Propose to leave it to the user to know what he is doing.
      * Propose to have a separate class Inertia derived from Tensor,
        which implements computing the inertia tensor and translation.

    - should we allow non-symmetrical tensors? Then what with principal?

      * Propose to silently allow non-symm. Result of functions is what it is.
        Again, suppose the user knows what he is doing.

    Example:

        >>> t = Tensor([1,2,3,4,5,6])
        >>> print(t)
        [[ 1.  6.  5.]
         [ 6.  2.  4.]
         [ 5.  4.  3.]]
        >>> print(t.contracted)
        [ 1.  2.  3.  4.  5.  6.]
        >>> s = Tensor(t)
        >>> print(s)
        [[ 1.  6.  5.]
         [ 6.  2.  4.]
         [ 5.  4.  3.]]

    """

    _contracted_order = ( (0,0), (1,1), (2,2), (1,2), (2,0), (0,1) )
    _contracted_index = np.array([
        [ 0, 5, 4],
        [ 5, 1, 3],
        [ 4, 3, 2],
        ])


    def __new__(clas,data=None,symmetric=True,cs=None):
        """Create a new Tensor instance"""
        try:
            data = at.checkArray(data,shape=(3,3),kind='f',allow='if')
        except:
            try:
                data = at.checkArray(data,shape=(6,),kind='f',allow='if')
            except:
                raise ValueError("Data should have shape (3,3) or (6,)")
            data = data[Tensor._contracted_index]
        ar = data.view(clas)
        if cs is None:
            cs = CoordSys()
        if not(isinstance(cs,CoordSys)):
            raise ValueError('Wrong Coordinate System')
        ar.CS = cs
        return ar


    def __array_finalize__(self, obj):
        """Finalize the new Matrix object.

        When a class is derived from numpy.ndarray and the constructor (the
        :meth:`__new__` method) defines new attributes, these atttributes
        need to be reset in this method.
        """
        if obj is None: return
        self.CS = getattr(obj, 'cs', CoordSys())
        #~ pass  # currently no new attributes defined in __new__
        # self._newattr = getattr(obj, '_newattr', None)

    @property
    def xx(self):
        return self[0,0]
    @property
    def yy(self):
        return self[1,1]
    @property
    def zz(self):
        return self[2,2]
    @property
    def yz(self):
        return self[1,2]
    @property
    def zx(self):
        return self[0,2]
    @property
    def xy(self):
        return self[0,1]

    zy = yz
    xz = zx
    yx = xy


    @property
    def contracted(self):
        """Returned the symmetric tensor data as a numpy array with shape (6,)

        """
        return self.sym[zip(*Tensor._contracted_order)]

    @property
    def tensor(self):
        """Returned the tensor data as a numpy array with shape (3,3)"""
        return np.asarray(self)

    @property
    def sym(self):
        """Return the symmetric part of the tensor."""
        return (self+self.T) / 2
    @property
    def asym(self):
        """Return the antisymmetric part of the tensor."""
        return (self-self.T) / 2


    def principal(self,sort=True,right_handed=True):
        """Returns the principal values and axes of the inertia tensor.

        Parameters:

        - `sort`: bool. If True (default), the return values are sorted
          in order of decreasing principal values. Otherwise they are
          unsorted.
        - `right_handed`: bool. If True (default), the returned axis vectors
          are guaranteed to form a right-handed coordinate system.
          Otherwise, lef-handed systems may result)

        Returns a tuple (prin,axes) where

        - `prin`: is a (3,) array with the principal values,
        - `axes`: is a (3,3) array with the rotation matrix that
          rotates the global axes to the principal axes. This also
          means that the columns of axes are the unit vectors along
          the principal directions.

        Example:

        >>> t = Tensor([-19., 4.6, -8.3, 11.8, 6.45, -4.7 ])
        >>> p,a = t.principal()
        >>> print(p)
        [ 11.62  -9.   -25.32]
        >>> print(a)
        [[-0.03 -0.62 -0.78]
         [ 0.86  0.38 -0.33]
         [ 0.5  -0.69  0.53]]

        """
        prin, axes = np.linalg.eig(self.tensor)
        if sort:
            s = prin.argsort()[::-1]
            prin = prin[s]
            axes = axes[:, s]
        if right_handed and not at.allclose(at.normalize(np.cross(axes[:, 0], axes[:, 1])), axes[:, 2]):
            axes[:, 2] = -axes[:, 2]
        return prin, axes


    def rotate(self,rot):
        """Transform the tensor on coordinate system rotation.

        Note: for an inertia tensor, the inertia should have been
        computed around axes through the center of mass.
        See also translate.

        Example:

        >>> t = Tensor([-19., 4.6, -8.3, 11.8, 6.45, -4.7 ])
        >>> p,a = t.principal()
        >>> print(t.rotate(np.linalg.linalg.inv(a)))
        [[ 11.62   0.     0.  ]
         [ -0.    -9.    -0.  ]
         [  0.    -0.   -25.32]]

        """
        rot = at.checkArray(rot,shape=(3,3),kind='f')
        return Tensor(at.abat(rot,self),self.CS.rotate(rot))


class Inertia(Tensor):
    """A class for storing the inertia tensor of an array of points.

    Parameters:

    - `X`: a Coords with shape (npoints,3). Shapes (...,3) are accepted
      but will be reshaped to (npoints,3).
    - `mass`: optional, (npoints,) float array with the mass of the points.
      If omitted, all points have mass 1.

      The result is a tuple of two float arrays:

      - the center of gravity: shape (3,)
      - the inertia tensor: shape (6,) with the following values (in order):
        Ixx, Iyy, Izz, Iyz, Izx, Ixy

    Example:

    >>> from .elements import Tet4
    >>> X = Tet4.vertices
    >>> print(X)
    [[ 0.  0.  0.]
     [ 1.  0.  0.]
     [ 0.  1.  0.]
     [ 0.  0.  1.]]
    >>> I = X.inertia()
    >>> print(I)
    [[ 1.5   0.25  0.25]
     [ 0.25  1.5   0.25]
     [ 0.25  0.25  1.5 ]]
    >>> print(I.ctr)
    [ 0.25  0.25  0.25]
    >>> print(I.mass)
    4.0
    >>> print(I.translate(-I.ctr))
    [[ 2.  0.  0.]
     [ 0.  2.  0.]
     [ 0.  0.  2.]]

    """

    def __new__(clas,data,mass,ctr):
        """Create a new Tensor instance"""
        ar = Tensor.__new__(clas,data)
        # We need mass and ctr!
        ar.mass = float(mass)
        ar.ctr = Coords(at.checkArray(ctr,shape=(3,),kind='f'))
        return ar


    def translate(self,trl,toG=False):
        """Return the inertia tensor around axes translated over vector trl.

        Parameters:

        - `trl`: arraylike (3,). Distance vector from the center of mass
          to the new reference point.
        - `toG`: bool. If False (default) the inertia tensor is translated to the
          the  new reference point, otherwise it will be translated to its center
          of mass

        """
        trl = at.checkArray(trl,shape=(3,),kind='f')
        trf = -np.dot(trl.reshape(3,-1),trl.reshape(-1,3))
        ind = np.diag_indices(3)
        trf[ind] += np.dot(trl,trl.T)
        if toG:
            trf = -trf
        return self.tensor + self.mass * trf


    def translateTo(self,ref,toG=False):
        """Return the inertia tensor around axes translated to the reference
        point ref.

        Parameters:

        - `ref`: arraylike (3,). The new reference point coordinates.
        - `toG`: bool. If False (default) the inertia tensor is translated to the
          the  new reference point, otherwise it will be translated to its center
          of mass

        """

        trl = at.checkArray(ref,shape=(3,),kind='f') - self.ctr
        return self.translate(self,trl,toG=toG)



    def toCS(self,cs):
        """Transform the coordinates to another CoordSys.

        """
        return self.tensor.translateTo(cs.trl) + self.tensor.rotate(np.dot(self.CS.rot.T,cs.rot))


def point_inertia(X,mass=None,center_only=False):
    """Compute the total mass, center of mass and inertia tensor mass points.

    Parameters:

    - `X`: a Coords with shape (npoints,3). Shapes (...,3) are accepted
      but will be reshaped to (npoints,3).
    - `mass`: optional, (npoints,) float array with the mass of the points.
      If omitted, all points have mass 1.
    - `center_only`: bool: if True, only returns the total mass and center
      of mass.

    Returns a tuple (M,C,I) where M is the total mass of all points, C is
    the center of mass, and I is the inertia tensor in the central coordinate
    system, i.e. a coordinate system with axes paralle to the global axes
    but origin at the (computed) center of mass. If `center_only` is True,
    returns the tuple (M,C) only. On large models this is more effective
    in case you do not need the inertia tensor.

    """
    X = Coords(X).reshape(-1, 3)
    npoints = X.shape[0]
    if mass is not None:
        mass = at.checkArray(mass,shape=(npoints,),kind='f')
        mass = mass.reshape(-1,1)
        M = mass.sum()
        C = (X*mass).sum(axis=0) / M
    else:
        M = float(npoints)
        C = X.mean(axis=0)
    if center_only:
        return M,C

    Xc = X - C
    x, y, z = Xc[:, 0], Xc[:, 1], Xc[:, 2]
    xx, yy, zz, yz, zx, xy = x*x, y*y, z*z, y*z, z*x, x*y
    I = np.column_stack([ yy+zz, zz+xx, xx+yy, -yz, -zx, -xy ])
    if mass is not None:
        I *= mass
    I = I.sum(axis=0)
    return M,C,I


def surface_volume(x,pt=None):
    """Return the volume inside a 3-plex Formex.

    - `x`: an (ntri,3,3) shaped float array, representing ntri triangles.
    - `pt`: a point in space. If unspecified, it is taken equal to the
      origin of the global coordinate system ([0.,0.,0.]).

    Returns an (ntri) shaped array with the volume of the tetrahedrons formed
    by the triangles and the point `pt`. Triangles with an outer normal
    pointing away from `pt` will generate positive tetrahral volumes, while
    triangles having `pt` at the side of their positive normal will generate
    negative volumes. In any case, if `x` represents a closed surface,
    the algebraic sum of all the volumes is the total volume inside the surface.
    """
    x = at.checkArray(x,shape=(-1,3,3),kind='f')
    if pt is not None:
        x -= pt
    a, b, c = [ x[:,i,:] for i in range(3) ]
    d = np.cross(b, c)
    e = (a*d).sum(axis=-1)
    return e / 6


def surface_volume_inertia(x,center_only=False):
    """Return the inertia of the volume inside a 3-plex Formex.

    - `x`: an (ntri,3,3) shaped float array, representing ntri triangles.

    This uses the same algorithm as tetrahedral_inertia using [0.,0.,0.]
    as the 4-th point for each tetrahedron.

    Returns a tuple (V,C,I) where V is the total volume,
    C is the center of mass (3,) and I is the inertia tensor (6,) of the
    tetrahedral model.

    Example:

    >>> from .simple import sphere
    >>> S = sphere(4).toFormex()
    >>> V,C,I = surface_volume_inertia(S.coords)
    >>> print(V,C,I)
    4.04701 [-0. -0. -0.] [ 1.58  1.58  1.58 -0.    0.    0.  ]

    """
    def K(x,y):
        x1,x2,x3 = x[:,0], x[:,1], x[:,2]
        y1,y2,y3 = y[:,0], y[:,1], y[:,2]
        return x1 * (y1+y2+y3) + \
               x2 * (   y2+y3) + \
               x3 * (      y3)

    x = at.checkArray(x,shape=(-1,3,3),kind='f')
    v = surface_volume(x)
    V = v.sum()
    c = x.sum(axis=1) / 4.  # 4-th point is 0.,0.,0.
    C = (c*v[:,np.newaxis]).sum(axis=0) / V
    if center_only:
        return V,C

    x -= C
    aa = 2 * K(x,x) * v.reshape(-1,1)
    aa = aa.sum(axis=0)
    a0 = aa[1] + aa[2]
    a1 = aa[0] + aa[2]
    a2 = aa[0] + aa[1]
    x0,x1,x2 = x[...,0],x[...,1],x[...,2]
    a3 = (( K(x1,x2) + K(x2,x1) ) * v).sum(axis=0)
    a4 = (( K(x2,x0) + K(x0,x2) ) * v).sum(axis=0)
    a5 = (( K(x0,x1) + K(x1,x0) ) * v).sum(axis=0)
    I = np.array([a0,a1,a2,a3,a4,a5]) / 20.
    return V,C,I


def tetrahedral_volume(x):
    """Compute the volume of tetrahedrons.

    - `x`: an (ntet,4,3) shaped float array, representing ntet tetrahedrons.

    Returns an (ntet,) shaped array with the volume of the tetrahedrons.
    Depending on the ordering of the points, this volume may be positive
    or negative. It will be positive if point 4 is on the side of the positive
    normal formed by the first 3 points.
    """
    x = at.checkArray(x,shape=(-1,4,3),kind='f')
    a, b, c = [ x[:,i,:] - x[:,3,:] for i in range(3) ]
    d = np.cross(b, c)
    e = (a*d).sum(axis=-1)
    return -e / 6


def tetrahedral_inertia(x,density=None,center_only=False):
    """Return the inertia of the volume of a 4-plex Formex.

    Parameters:

    - `x`: an (ntet,4,3) shaped float array, representing ntet tetrahedrons.
    - `density`: optional mass density (ntet,) per tetrahedron
    - `center_only`: bool. If True, returns only the total volume, total mass
      and center of gravity. This may be used on large models when only these
      quantities are required.

    Returns a tuple (V,M,C,I) where V is the total volume, M is the total mass,
    C is the center of mass (3,) and I is the inertia tensor (6,) of the
    tetrahedral model.

    Formulas for inertia were based on F. Tonon, J. Math & Stat, 1(1):8-11,2005

    Example:

    >>> x = Coords([
    ...     [  8.33220, -11.86875,  0.93355 ],
    ...     [  0.75523,   5.00000, 16.37072 ],
    ...     [ 52.61236,   5.00000, -5.38580 ],
    ...     [  2.000000,  5.00000,  3.00000 ],
    ...     ])
    >>> F = Formex([x])
    >>> print(tetrahedral_center(F.coords))
    [ 15.92   0.78   3.73]
    >>> print(tetrahedral_volume(F.coords))
    [ 1873.23]
    >>> print(*tetrahedral_inertia(F.coords))
    1873.23 1873.23 [ 15.92   0.78   3.73] [  43520.32  194711.28  191168.77    4417.66  -46343.16   11996.2 ]

    """
    def K(x,y):
        x1,x2,x3,x4 = x[:,0], x[:,1], x[:,2], x[:,3]
        y1,y2,y3,y4 = y[:,0], y[:,1], y[:,2], y[:,3]
        return x1 * (y1+y2+y3+y4) + \
               x2 * (   y2+y3+y4) + \
               x3 * (      y3+y4) + \
               x4 * (         y4)

    x = at.checkArray(x,shape=(-1,4,3),kind='f')
    v = tetrahedral_volume(x)
    V = v.sum()
    if density:
        v *= density
    c = Formex(x).centroids()
    M = v.sum()
    C = (c*v[:,np.newaxis]).sum(axis=0) / M
    if center_only:
        return V,M,C

    x -= C
    aa = 2 * K(x,x) * v.reshape(-1,1)
    aa = aa.sum(axis=0)
    a0 = aa[1] + aa[2]
    a1 = aa[0] + aa[2]
    a2 = aa[0] + aa[1]
    x0,x1,x2 = x[...,0],x[...,1],x[...,2]
    a3 = (( K(x1,x2) + K(x2,x1) ) * v).sum(axis=0)
    a4 = (( K(x2,x0) + K(x0,x2) ) * v).sum(axis=0)
    a5 = (( K(x0,x1) + K(x1,x0) ) * v).sum(axis=0)
    I = np.array([a0,a1,a2,a3,a4,a5]) / 20.
    return V,M,C,I


def tetrahedral_center(x,density=None):
    """Compute the center of mass of a collection of tetrahedrons.

    - `x`: an (ntet,4,3) shaped float array, representing ntet tetrahedrons.
    - `density`: optional mass density (ntet,) per tetrahedron. Default 1.

    Returns a (3,) shaped array with the center of mass.
    """
    return tetrahedral_inertia(x,density=None,center_only=True)[2]


# Kept for compatibility
inertia = point_inertia


# End
