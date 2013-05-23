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
    - serendipity:

    """
    n = checkArray(n,(-1,),'i')
    ndim = n.shape[0]
    if ndim < 1 or ndim > 3:
        raise RuntimeError,"Expected a 1..3 length tuple"

    layout = layout[:3]
    if layout in ['tri','ser']:
        if not (n == n[0]).all():
            raise RuntimeError,"For triangular and serendipity grids, all axes should have the same number of points"


    # First create the full lagrangian set
    exp = indices(n+1).reshape(ndim,-1).transpose()

    if layout != 'lag':
        if layout == 'tri':
            # Select by total maximal degree
            ok = exp.sum(axis=-1) <= n[0]
        elif layout == 'bor':
            # Select if any value is not higher than 1
            ok = (exp <= 1).any(axis=-1)
        elif layout == 'ser':
            if len(n) > 2:
                raise RuntimeError,"Serendipy layout for 3D not yet implemented"
            deg = n[0]-1
            #print(exp.sum(axis=-1))
            ok = exp.sum(axis=-1) <= n[0] + len(n) - 1
        else:
            raise RuntimeError,"Unknown layout %s" % layout
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
    #
    # The static list of string monomials has now been replaced with
    # on-demand generation for most element types
    #
    # TODO: The monomials need to be replaced with use of the exponents
    #
    isodata = {
        # 3D Serendipity still needs to be done
        'hex20' : (3, ('1','x','y','z','x*x','y*y','z*z','x*y','x*z','y*z',
                       'x*x*y','x*x*z','x*y*y','y*y*z','x*z*z','y*z*z','x*y*z',
                       'x*x*y*z','x*y*y*z','x*y*z*z')),
        }

    isodata_alias = {
        'line2' : 'lag-1',
        'line3' : 'lag-2',
        'line4' : 'lag-3',
        'tri3'  : 'tri-1-1',
        'tri6'  : 'tri-2-2',
        'tri10' : 'tri-3-3',
        'quad4' : 'lag-1-1',
        'quad9' : 'lag-2-2',
        'quad16': 'lag-3-3',
        'quad8' : 'bor-2-2',
        'quad12': 'bor-3-3',
        'quad13': 'ser-3-3',
        'tet4'  : 'tri-1-1-1',
        'tet10' : 'tri-2-2-2',
        'hex8'  : 'lag-1-1-1',
        'hex27' : 'lag-2-2-2',
        'hex36' : 'lag-2-2-3',
        'hex64' : 'lag-3-3-3',
        }

    def __init__(self,eltype,coords,oldcoords):
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
                n = map(int,s[1:])
                Isopar.isodata[eltype] = monomials(n,s[0])
            else:
                raise RuntimeError,"Unknown eltype %s"

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
