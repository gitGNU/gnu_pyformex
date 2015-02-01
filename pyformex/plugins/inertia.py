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
"""inertia.py

Compute inertia related quantities of a Formex.
This comprises: center of gravity, inertia tensor, principal axes

Currently, these functions work on arrays of nodes, not on Formices!
Use func(F,f) to operate on a Formex F.
"""
from __future__ import print_function


import numpy as np
from pyformex import arraytools as at


class Tensor2(object):
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

    Example:

        >>> t = Tensor2([1,2,3,4,5,6])
        >>> print(t.contracted)
        [ 1.  2.  3.  4.  5.  6.]
        >>> print(t.tensor)
        [[ 1.  6.  5.]
         [ 6.  2.  4.]
         [ 5.  4.  3.]]
        >>> s = Tensor2(t.tensor)
        >>> print(s)
        [ 1.  2.  3.  4.  5.  6.]

    """

    _contracted_order = ( (0,0), (1,1), (2,2), (1,2), (2,0), (0,1) )


    def __init__(self,data):
        """Initialize the Tensor2."""
        try:
            data = at.checkArray(data,shape=(6,),kind='f',allow='if')
        except:
            try:
                data = at.checkArray(data,shape=(3,3),kind='f',allow='if')
            except:
                raise ValueError("Data should have shape (6,) or (3,3)")
            # Force symmetry
            data = (data + data.T) / 2
            data = data[zip(*Tensor2._contracted_order)]

        self._data = data


    @property
    def xx(self):
        return self._data[0]
    @property
    def yy(self):
        return self._data[1]
    @property
    def zz(self):
        return self._data[2]
    @property
    def yz(self):
        return self._data[3]
    @property
    def zx(self):
        return self._data[4]
    @property
    def xy(self):
        return self._data[5]

    zy = yz
    xz = zx
    yx = xy

    @property
    def contracted(self):
        return self._data

    @property
    def tensor(self):
        return np.array([
            [ self.xx, self.xy, self.xz ],
            [ self.yx, self.yy, self.yz ],
            [ self.zx, self.zy, self.zz ],
            ])


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
        - `axes`: is a (3,3) array in which each column is a unit vector
          along the corresponding principal axis.

        Example:

        >>> t = Tensor2([-19., 4.6, -8.3, 11.8, 6.45, -4.7 ])
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


    def __str__(self):
        return self._data.__str__()


class Tensor3(object):
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

    Properties: a Tensor3 T has the following properties:

    - T.xx, T.xy, T.xz, T.yx, T.yy, T.yz, T.zx, T.zy, T.zz: aliases for
      the nine components of the tensor
    - T.contracted: the (6,) shaped contracted array with independent
      values of the tensor
    - T.tensor: the full tensor as an (3,3) array

    Discuss:

    - inertia and stres/strain tensors transform in the same way
      on rotations of axes. But differently on translations! Should we
      therefore store the purpose of the tensor??
    - should we allow non-symmetrical tensors? Then what with principal?

    Example:

        >>> t = Tensor3([1,2,3,4,5,6])
        >>> print(t.contracted)
        [ 1.  2.  3.  4.  5.  6.]
        >>> print(t.tensor)
        [[ 1.  6.  5.]
         [ 6.  2.  4.]
         [ 5.  4.  3.]]
        >>> s = Tensor3(t.tensor)
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


    def __init__(self,data,symmetric=True):
        """Initialize the Tensor3."""
        try:
            data = at.checkArray(data,shape=(3,3),kind='f',allow='if')
        except:
            try:
                data = at.checkArray(data,shape=(6,),kind='f',allow='if')
            except:
                raise ValueError("Data should have shape (3,3) or (6,)")
            data = data[Tensor3._contracted_index]

        self._data = data
        if symmetric:
            self._data = self.sym


    @property
    def xx(self):
        return self._data[0,0]
    @property
    def yy(self):
        return self._data[1,1]
    @property
    def zz(self):
        return self._data[2,2]
    @property
    def yz(self):
        return self._data[1,2]
    @property
    def zx(self):
        return self._data[0,2]
    @property
    def xy(self):
        return self._data[0,1]

    zy = yz
    xz = zx
    yx = xy


    @property
    def contracted(self):
        return self.sym[zip(*Tensor3._contracted_order)]

    @property
    def tensor(self):
        return self._data

    @property
    def sym(self):
        """Return the symmetric part of the tensor."""
        return (self._data+self._data.T) / 2
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
        - `axes`: is a (3,3) array in which each column (or row?) is a
          unit(?) vector along the corresponding principal axis.

        Example:

        >>> t = Tensor3([-19., 4.6, -8.3, 11.8, 6.45, -4.7 ])
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


    def transform(self,rot=None,trl=None):
        """Transform the tensor with the given rotation and/or translation.

        Example:

        >>> t = Tensor3([-19., 4.6, -8.3, 11.8, 6.45, -4.7 ])
        >>> p,a = t.principal()
        >>> print(t.transform(np.linalg.linalg.inv(a)))
        [[ 11.62   0.     0.  ]
         [ -0.    -9.    -0.  ]
         [  0.    -0.   -25.32]]

        """
        data = self.tensor
        if rot is not None:
            rot = at.checkArray(rot,shape=(3,3),kind='f')
            data = at.abat(rot,data)
        return data


    def __str__(self):
        return self._data.__str__()


# Removed, as this is provided by Formex or Mesh

## def centroids(X):
##     """Compute the centroids of the points of a set of elements.

##     X (nelems,nplex,3)
##     """
##     return X.sum(axis=1) / X.shape[1]


def center(X,mass=None):
    """Compute the center of gravity of an array of points.

    mass is an optional array of masses to be atributed to the
    points. The default is to attribute a mass=1 to all points.

    If you also need the inertia tensor, it is more efficient to
    use the inertia() function.
    """
    X = X.reshape((-1, X.shape[-1]))
    if mass is not None:
        mass = np.array(mass)
        ctr = (X*mass).sum(axis=0) / mass.sum()
    else:
        ctr = X.mean(axis=0)
    return ctr


def inertia(X,mass=None):
    """Compute the inertia tensor of an array of points.

    mass is an optional array of masses to be atributed to the
    points. The default is to attribute a mass=1 to all points.

    The result is a tuple of two float arrays:

      - the center of gravity: shape (3,)
      - the inertia tensor: shape (6,) with the following values (in order):
        Ixx, Iyy, Izz, Iyz, Izx, Ixy
    """
    X = X.reshape((-1, X.shape[-1]))
    if mass is not None:
        mass = np.array(mass)
        ctr = (X*mass).sum(axis=0) / mass.sum()
    else:
        ctr = X.mean(axis=0)
    Xc = X - ctr
    x, y, z = Xc[:, 0], Xc[:, 1], Xc[:, 2]
    xx, yy, zz, yz, zx, xy = x*x, y*y, z*z, y*z, z*x, x*y
    I = np.column_stack([ yy+zz, zz+xx, xx+yy, -yz, -zx, -xy ])
    if mass is not None:
        I *= mass
    return ctr, I.sum(axis=0)


def principal(inertia,sort=False,right_handed=False):
    """Returns the principal values and axes of the inertia tensor.

    If sort is True, they are sorted (maximum comes first).
    If right_handed is True, the axes define a right-handed coordinate system.
    """
    Ixx, Iyy, Izz, Iyz, Izx, Ixy = inertia
    Itensor = np.array([ [Ixx, Ixy, Izx], [Ixy, Iyy, Iyz], [Izx, Iyz, Izz] ])
    Iprin, Iaxes = np.linalg.eig(Itensor)
    if sort:
        s = Iprin.argsort()[::-1]
        Iprin = Iprin[s]
        Iaxes = Iaxes[:, s]
    if right_handed and not at.allclose(normalize(cross(Iaxes[:, 0], Iaxes[:, 1])), Iaxes[:, 2]):
        Iaxes[:, 2] = -Iaxes[:, 2]
    return Iprin, Iaxes



# End

