# $Id$
##
##  This file is part of pyFormex 0.9.0  (Mon Mar 25 13:52:29 CET 2013)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2012 (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
##  Distributed under the GNU General Public License version 3 or later.
##
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

from coords import *


def evaluate(atoms,x,y=0,z=0):
    """Build a matrix of functions of coords.

    - `atoms`: a list of text strings representing a mathematical function of
      `x`, and possibly of `y` and `z`.
    - `x`, `y`, `z`: a list of x- (and optionally y-, z-) values at which the
      `atoms` will be evaluated. The lists should have the same length.

    Returns a matrix with `nvalues` rows and `natoms` colums.
    """
    aa = zeros((len(x),len(atoms)),Float)
    for k,a in enumerate(atoms):
        aa[:,k] = eval(a)
    return aa


def exponents(n,layout='lag'):
    """Create tuples of polynomial exponents.

    This function creates the exponents of polynomials in 1 to 3 dimensions
    which can be used to construct interpolation function over lagrangian,
    triangular or serendipity grids.

    Parameters:

    - `n`: a tuple of 1 to 3 integers, specifying the number of points in
      the x up to z directions.
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
    - serendipity:

    """
    n = checkArray(n,(-1,),'i')
    ndim = n.shape[0]
    if ndim < 1 or ndim > 3:
        raise RuntimeError,"Expected a 1..3 length tuple"

    layout = layout[:3]
    if layout == 'tri':
        if not (n == n[0]).all():
            raise RuntimeError,"For triangular grids, all axes should have the same number of points"


    # First create the full lagrangian set
    exp = indices(n).reshape(ndim,-1).transpose()

    if layout == 'lag':
        # We're done
        pass
    elif layout == 'tri':
        # Select by total maximal degree
        deg = n[0]-1
        ok = exp.sum(axis=-1) <= deg
        exp = exp[ok]
    elif layout == 'bor':
        # Select if any value is not higher than 1
        ok = (exp <= 1).any(axis=-1)
        exp = exp[ok]

    return exp


def monomial(exp,symbol='xyz'):
    """Compute the monomials for the given exponents

    exp is a tuple of 1 to 3 exponents
    """
    factor = lambda sym,exp: '1' if exp == 0 else sym if exp == 1 else sym+'**'+str(exp)
    factors = [ factor(symbol[i],j) for i,j in enumerate(exp) ]
    # Join and sanitize (note we do not have '**1')
    return '*'.join(factors).replace('1*','').replace('*1','')


def monomials(n,layout='lag'):
    """Create the list of monomials for an element

    Returns a tuple (ndim,list of monomials), like the values in
    isodata below
    """
    exp = exponents(n,layout)
    mon = map(monomial,exp)
    return (len(n),mon)


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

    # REM: We started to create some more general functions to generate
    # interpolation polynomials (see above)
    # As a result, the comments below is somewhat obsolete

    # LAGRANGIAN : 1,2,3 dim (LINE, QUAD, HEX)
    # TRIANGLE : 2,3 dim (TRI,TET)
    # SERENDIPITY : list ???

    # lagrangian(nx,ny,nz)
    #                type   ndim   degree+1
    #  'line2': ('lagrangian',1,(1))
    #  'quad9': ('lagrangian',2,(2,2))
    #  'quad6': ('lagrangian',2,(3,2))
    #  'quad6': 'lag-2-3-2'
    #  'quad8' : ('direct', 2, ('1','x','y','x*x','y*y','x*y','x*x*y','x*y*y')),
    #
    # generic name:
    #
    #   'lag-2-2-3' : ('lagrangian',2,(2,3))
    #   'tri-2-2' : ('triangular',2,(2))

    #   'lag-i-j-k'


    #
    # Currently, we still use a static list of string monomials
    # This will be replaced later
    #
    isodata = {
        'line2' : monomials((2,)),
        'line3' : monomials((3,)),
        'line4' : monomials((4,)),
        'tri3'  : monomials((2,2),'tri'),
        'tri6'  : monomials((3,3),'tri'),
        'tri10' : monomials((4,4),'tri'),
        'quad4' : monomials((2,2)),
        'quad9' : monomials((3,3)),
        'quad16': monomials((4,4)),
        'quad8' : monomials((3,3),'bor'),
        'quad12': monomials((4,4),'bor'),
        'tet4'  : monomials((2,2,2),'tri'),
        'tet10' : monomials((3,3,3),'tri'),
        'hex8'  : monomials((2,2,2)),
        'hex27' : monomials((3,3,3)),
        'hex36' : monomials((3,3,4)),
        'hex64' : monomials((4,4,4)),
        # Serendipity still needs to be done
        'quad13': (2, ('1','x','y','x*x','x*y','y*y',
                       'x*x*x','x*x*y','x*y*y','y*y*y',
                       'x*x*x*y','x*x*y*y','x*y*y*y')),
        'hex20' : (3, ('1','x','y','z','x*x','y*y','z*z','x*y','x*z','y*z',
                       'x*x*y','x*x*z','x*y*y','y*y*z','x*z*z','y*z*z','x*y*z',
                       'x*x*y*z','x*y*y*z','x*y*z*z')),
        }


    def __init__(self,eltype,coords,oldcoords):
        """Create an isoparametric transformation.

        """
        ndim,atoms = Isopar.isodata[eltype]
        coords = coords.view().reshape(-1,3)
        oldcoords = oldcoords.view().reshape(-1,3)
        x = oldcoords[:,0]
        if ndim > 1:
            y = oldcoords[:,1]
        else:
            y = 0
        if ndim > 2:
            z = oldcoords[:,2]
        else:
            z = 0
        aa = evaluate(atoms,x,y,z)
        ab = linalg.solve(aa,coords)
        self.eltype = eltype
        self.trf = ab


    def transform(self,X):
        """Apply isoparametric transform to a set of coordinates.

        Returns a Coords array with same shape as X
        """
        if not isinstance(X,Coords):
            try:
                X = Coords(X)
            except:
                raise ValueError,"Expected a Coords object as argument"

        ndim,atoms = Isopar.isodata[self.eltype]
        aa = evaluate(atoms,X.x().ravel(),X.y().ravel(),X.z().ravel())
        xx = dot(aa,self.trf).reshape(X.shape)
        if ndim < 3:
            xx[...,ndim:] += X[...,ndim:]
        return X.__class__(xx)


# End
