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
#

"""Polynomials

This module defines the class Polynomial, representing a polynomial
in n variables.
"""

from __future__ import print_function
from future_builtins import zip

import numpy as np
import arraytools as at


class Polynomial(object):
    """A polynomial in ndim dimensions.

    Parameters:

    - `exp`: (nterms,ndim) int array with the exponents of each of
      the ndim variables in the nterms terms of the polynomial.
    - `coeff`: (nterms,) float array with the coefficients of the terms.
      If not specified, all coeeficients are set to 1.

    Example:

    >>> p = Polynomial([(0,0),(1,0),(1,1),(0,2)],(2,3,-1,-1))
    >>> print(p.atoms())
    ['1', 'x', 'x*y', 'y**2']
    >>> print(p.human())
    2.0 + 3.0*x -1.0*x*y -1.0*y**2
    >>> print(p.evalAtoms([[1,2],[3,0],[2,1]]))
    [[ 1.  1.  2.  4.]
     [ 1.  3.  0.  0.]
     [ 1.  2.  2.  1.]]
    >>> print(p.eval([[1,2],[3,0],[2,1]]))
    [ -1.  11.   5.]
    """

    def __init__(self,exp,coeff=None):
        """Create an n-d polynomial"""
        self.exp = at.checkArray(exp, kind='i', ndim=2)
        if coeff is None:
            self.coeff = np.ones(self.nterms)
        else:
            self.coeff = at.checkArray(coeff, (self.nterms,), 'f', 'i')


    @property
    def nterms(self):
        return self.exp.shape[0]


    @property
    def ndim(self):
        return self.exp.shape[1]


    def degrees(self):
        """Return the degree of the polynomial in each of the dimensions.

        The degree is the maximal exponent for each of the dimensions.
        """
        return self.exp.max(axis=0)

    def degree(self):
        """Return the total degree of the polynomial.

        The degree is the sum of the degrees for all dimensions.
        """
        return self.degrees().sum()


    def evalAtoms1(self, x):
        """Evaluate the monomials at the given points

        x is an (npoints,ndim) array of points where the polynomial is to
        be evaluated. The result is an (npoints,nterms) array of values.
        """
        x = at.checkArray(x, (-1, self.ndim), 'f', 'i')
        maxd = self.degrees()
        mon = [ at.powers(x[:, j], maxd[j]) for j in range(self.ndim) ]
        terms = [[mon[j][e[j]] for j in range(self.ndim)] for e in self.exp]
        terms = np.dstack([np.column_stack([mon[j][e[j]] for j in range(self.ndim)]) for e in self.exp])
        return terms.prod(axis=1)


    #### ALTERNATIVE evalAtoms
    # This implementation first computes the monomial strings and
    #    then evals the strins. It is currrently faster than evalAtoms.
    def evalAtoms(self, x):
        """Evaluate the monomials at the given points

        x is an (npoints,ndim) array of points where the polynomial is to
        be evaluated. The result is an (npoints,nterms) array of values.
        """
        x = at.checkArray(x, (-1, self.ndim), 'f', 'i')
        symbol = 'xyz'
        g = dict([(symbol[i], x[:, i]) for i in range(self.ndim) ])
        atoms = self.atoms(symbol)
        aa = np.zeros((len(x), len(atoms)), at.Float)
        for k, a in enumerate(atoms):
            aa[:, k] = eval(a, g)
        return aa


    def eval(self, x):
        """Evaluate the polynomial at the given points

        x is an (npoints,ndim) array of points where the polynomial is to
        be evaluated. The result is an (npoints,) array of values.
        """
        terms = self.evalAtoms(x)
        return (self.coeff*terms).sum(axis=-1)


    def atoms(self,symbol='xyz'):
        """Return a human representation of the monomials"""
        return [ monomial(e, symbol) for e in self.exp ]


    def human(self,symbol='xyz'):
        """Return a human representation"""
        mon = self.atoms(symbol)
        mon = [ str(c)+'*'+m if c != 1 else m for c, m in zip(self.coeff, mon)]
        return ' + '.join(mon).replace('*1', '').replace('+ -', '-')


def polynomial(atoms,x,y=0,z=0):
    """Build a matrix of functions of coords.

    - `atoms`: a list of text strings representing a mathematical function of
      `x`, and possibly of `y` and `z`.
    - `x`, `y`, `z`: a list of x- (and optionally y-, z-) values at which the
      `atoms` will be evaluated. The lists should have the same length.

    Returns a matrix with `nvalues` rows and `natoms` colums.
    """
    aa = np.zeros((len(x), len(atoms)), Float)
    for k, a in enumerate(atoms):
        aa[:, k] = eval(a)
    return aa


def monomial(exp,symbol='xyz'):
    """Compute the monomials for the given exponents

    - `exp`: a tuple of integer exponents
    - `symbol`: a string of at least the same length as `exp`

    Returns a string representation of a monomial created by raising
    the symbols to the corresponding exponent.

    Example:

    >>> monomial((2,1))
    'x**2*y'

    """
    factor = lambda sym, exp: '1' if exp == 0 else sym if exp == 1 else sym+'**'+str(exp)
    factors = [ factor(symbol[i], j) for i, j in enumerate(exp) ]
    # Join and sanitize (note we do not have '**1')
    return '*'.join(factors).replace('1*', '').replace('*1', '')

# End
