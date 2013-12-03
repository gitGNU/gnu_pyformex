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

"""Isoparametric transformations

"""
from __future__ import print_function


from pyformex.coords import *
from pyformex.plugins.polynomial import *


#
# This should probably be moved to polynomial
#
def evaluate(atoms,x,y=0,z=0):
    """Build a matrix of functions of coords.

    - `atoms`: a list of text strings representing a mathematical function of
      `x`, and possibly of `y` and `z`.
    - `x`, `y`, `z`: a list of x- (and optionally y-, z-) values at which the
      `atoms` will be evaluated. The lists should have the same length.

    Returns a matrix with `nvalues` rows and `natoms` colums.
    """
    aa = zeros((len(x), len(atoms)), Float)
    for k, a in enumerate(atoms):
        aa[:, k] = eval(a)
    return aa


def exponents(n,layout='lag'):
    """Create tuples of polynomial exponents.

    This function creates the exponents of polynomials in 1 to 3 dimensions
    which can be used to construct interpolation function over lagrangian,
    triangular or serendipity grids.

    Parameters:

    - `n`: a tuple of 1 to 3 integers, specifying the degree of the polynomials
      in the x up to z directions. For a lagrangian layout, this is one less
      than the number of points in each direction.
    - `layout`: string, specifying the layout of grid and the selection of
      monomials to be used. Should be one of 'lagrangian', 'triangular',
      'serendipity' or 'border'. The string can be abbreviated to its
      first 3 characters.

    Returns an integer array of shape (ndim,npoints), where ndim = len(n)
    and npoints depends on the layout:

    - lagrangian: npoints = prod(n). The point layout is a rectangular
      lagrangian grid form by n[i] points in direction i. As an example,
      specifying n=(3,2) uses a grid of 3 points in x-direction and 2 points
      in y-direction.
    - triangular: requires that all values in n are equal. For ndim=2, the
      number of points is n*(n+1)/2.
    - border: this is like the lagrangian grid with all internal points
      removed. For ndim=2, we have npoints = 2 * sum(n) - 4. For ndim=3 we
      have npoints = 2 * sum(nx*ny+ny*nz+nz*nx) - 4 * sum(n) + 8.
      Thus n=(3,3,3) will yield 2*3*3*3 - 4*(3+3+3) + 8 = 26
    - serendipity: tries to use only the corner and edge nodes, but uses
      a convex domain of the monomials. This may require some nodes inside
      the faces or the volume. Currently works up to (4,4) in 2D or (3,3,3)
      in 3D.

    """
    n = checkArray(n, (-1,), 'i')
    ndim = n.shape[0]
    if ndim < 1 or ndim > 3:
        raise RuntimeError("Expected a 1..3 length tuple")

    layout = layout[:3]
    if layout in ['tri', 'ser']:
        if not (n == n[0]).all():
            raise RuntimeError("For triangular and serendipity grids, all axes should have the same number of points")


    # First create the full lagrangian set
    exp = indices(n+1).reshape(ndim, -1).transpose()

    if layout != 'lag':
        if layout == 'tri':
            # Select by total maximal degree
            ok = exp.sum(axis=-1) <= n[0]
        elif layout == 'bor':
            # Select if any value is not higher than 1
            ok = (exp <= 1).any(axis=-1)
        elif layout == 'ser':
            if len(n) > 2:
                #print(exp.sum(axis=-1))
                #print(n[0] + len(n) - 1)
                np = 8 + 12*(n[0] - 1) # minimal number of points
                sdeg = n[0] + 1
                ok = exp.sum(axis=-1) <= sdeg
                if ok.sum() < np:
                    #print("Need at least %s" % np)
                    sdeg += 1
                    ok = exp.sum(axis=-1) <= sdeg
                    ok1 = (exp == n[0]).sum(axis=-1) <= 1
                    ok = ok*ok1
            else:
                np = 4 + 4*(n[0] - 1) # minimal number of points
                ok = exp.sum(axis=-1) <= n[0] + 1
            if ok.sum() < np:
                raise ValueError("No solution for eltype %s %s" % (layout, n))
        else:
            raise RuntimeError("Unknown layout %s" % layout)
        exp = exp[ok]
    return exp


def interpoly(n,layout='lag'):
    """Create an interpolation polynomial

    parameters are like for exponents.

    Returns a Polynomial that can be used for interpolation over
    the element.
    """
    exp = exponents(n, layout)
    return Polynomial(exp)


class Isopar(object):
    """A class representing an isoparametric transformation

        eltype is one of the keys in Isopar.isodata
        coords and oldcoords can be either arrays, Coords or Formex instances,
        but should be of equal shape, and match the number of atoms in the
        specified transformation type

    The following three formulations are equivalent ::

       trf = Isopar(eltype,coords,oldcoords)
       G = F.isopar(trf)

       trf = Isopar(eltype,coords,oldcoords)
       G = trf.transform(F)

       G = isopar(F,eltype,coords,oldcoords)

    """
    # Store the interpolation polynomials corresponding with
    # some element
    isodata = {
        }

    isodata_alias = {
        'line2': 'lag-1',
        'line3': 'lag-2',
        'line4': 'lag-3',
        'tri3': 'tri-1-1',
        'tri6': 'tri-2-2',
        'tri10': 'tri-3-3',
        'quad4': 'lag-1-1',
        'quad9': 'lag-2-2',
        'quad16': 'lag-3-3',
        'quad8': 'bor-2-2',
        'quad12': 'bor-3-3',
        'quad13': 'ser-3-3',
        'tet4': 'tri-1-1-1',
        'tet10': 'tri-2-2-2',
        'hex8': 'lag-1-1-1',
        'hex20': 'ser-2-2-2',
        'hex27': 'lag-2-2-2',
        'hex36': 'lag-2-2-3',
        'hex64': 'lag-3-3-3',
        }

    def __init__(self, eltype, coords, oldcoords):
        """Create an isoparametric transformation.

        `eltype`: string: either one of the keys in the isodata dictionary,
          or a string in the following format: layout-nx-ny-nz

        """
        if eltype not in Isopar.isodata:
            if eltype in Isopar.isodata_alias:
                eltype = Isopar.isodata_alias[eltype]
        if eltype not in Isopar.isodata:
            s = eltype.split('-')
            if s[0] in [ 'lag', 'tri', 'bor', 'ser' ]:
                n = [int(v) for v in s[1:]]
                #
                # It might be better to just store (ndim,atoms)
                # if we use string atoms to evaluate
                #
                Isopar.isodata[eltype] = interpoly(n, s[0])
            else:
                raise RuntimeError("Unknown eltype %s")

        poly = Isopar.isodata[eltype]
        coords = coords.view().reshape(-1, 3)
        oldcoords = oldcoords.view().reshape(-1, 3)
        aa = poly.evalAtoms(oldcoords[:, :poly.ndim])
        ab = linalg.solve(aa, coords)
        self.eltype = eltype
        self.trf = ab


    def transform(self, X):
        """Apply isoparametric transform to a set of coordinates.

        Returns a Coords array with same shape as X
        """
        if not isinstance(X, Coords):
            try:
                X = Coords(X)
            except:
                raise ValueError("Expected a Coords object as argument")

        poly = Isopar.isodata[self.eltype]
        ndim = poly.ndim
        aa = poly.evalAtoms(X.reshape(-1, 3)[:, :ndim])
        xx = dot(aa, self.trf).reshape(X.shape)
        if ndim < 3:
            xx[..., ndim:] += X[..., ndim:]
        return X.__class__(xx)


# End
