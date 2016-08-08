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
"""eigen.py: Solving large eigenproblems.

This module contains some functions that can be used to compute
the eigenpairs (eigenvalues and eigenvectors) of generalized
eigenproblem problems with large positive definite matrices.

The standard eigenproblem consists in finding the solutions (x,e)
satisfying the equation A.x = e.x, where A is an (n,n) matrix,
x is an (n) vector and e is a scalar. There are n solutions.

In structural mechanics often a generalized eigenproblem is
encountered, with the following form: A.x = e.B.x, where B is
also a positive definite matrix of size (n,n). Moreover, due
to the discretization process (e.g. finite elements), the
value of n can be very high. Therefore specialized solution methods
are required, and only a small number of solutions can practaically
be computed.

This module contains some Python function to solve such large
eigenproblems for the lowest p eigenvalues. Most of the alogrithms
were based on the book "Finite Element Procedures in Engineering Analysis"
by K-J Bathe (Prentice-Hall 1982).

(C) 2016 Benedict Verhegghe (benedict.verhegghe@feops.com)
This code is distributed under the GNU-GPL v 1.3 or later.

The only non-standard Python module used is numpy (http://www.numpy.org/).

Available functions for solving eigenproblems:
- tjacobi: for small standard symmetric problems
- gjacobi: for small generalized symmetric positive definite problems
- inverse: for medium size generalized problems (discouraged)
- subspace: for large generalized problems
- lanczos: for large generalized problems

"""
from __future__ import print_function

# Notes with subspace:
# - size of vector space:  min (2p, p+8) is p eigenvectors required
# - all eigenvalues are upper bounds, lowest has highest accuracy
# - typically 10 iterations for 6 digit precision in largest eigenvalue

from numpy import *

# Set precision for printing arrays
prec = 6
set_printoptions(precision=prec,linewidth=132)


def vector(x):
    """Convert a single column matrix into a vector."""
    return asarray(x).squeeze()


def interleave(l1,l2):
    """Interleave two lists"""
    from itertools import chain
    return list(chain(*zip(l1,l2)))


def lu_decomp(A,ptol=1.e-20):
    """Perform an LU decomposition of A.

    The LU decomposition of a matrix A is a set of two matrices L and U,
    where L is a lower triangular matrix with unit diagonal elements, and
    U is an upper triangular matrix, such that L * U = A.

    Unlike scipy's lu_factor function, this function does not perform any
    pivoting. Instead, as soon as a zero diagonal element is encountered,
    the function aborts.
    """
    m,n = shape(A)
    for i in arange(0,n):
        pivot = A[i,i]
        if abs(pivot) < ptol:
            print('zero pivot encountered')
            break
        for k in arange(i+1,n):
            A[k,i] = A[k,i]/pivot
            A[k,i+1:n] = A[k,i+1:n] - A[k,i]*A[i,i+1:n]
            L = eye(n)+tril(A,-1)
            U = triu(A)
    return L,U


def count_neg_diag(a):
    """Compute the number of negative diagonal elements in LDLt decomposition

    Constructs the LDLt (or LU) decomposition of k and returns the number
    of negative diagonal elements.
    """
    return (lu_decomp(a)[1].diagonal() < 0.0).sum()


def sturm_check(k,m,e,bound='lu',group=True,tol=0.01,verbose=False):
    """Performs a Sturm sequence check on the eigenvalues e.

    When applying a shift s: ks = k - s * m, the number of negative diagonal
    in the LDLt decomposition (or the LU decomposition) is equal to the
    number of eigenvalues lower than s.
    This function uses this property to check the obtained eigenvalues.

    e: the eigenvalues found for the eigenproblem (k,m)
    bound: either 'l', 'u' or 'lu': specifies if a shift at the lower bound,
      the upper bound, or both is to be performed.
    group: if True, a check around all eigenvalues as a group is done.
      If False, a check around each individual eigenvalue is performed.
    boundtol: accuracy used to compute bounds around an eigenvalue. This
      value should be larger than the accuracy of the obtained eigenvalues.
    verbose: if True, prints report.

    Returns True if all checks pass, else False.

    Note that the function currently does not check for clustered eigenvalues,
    and therefore might be slighlty off the correct values if values are
    clustered.
    """
    e = asarray(e)
    p = len(e)
    lb = (1.0 - tol) * e
    ub = (1.0 + tol) * e
    ln = arange(p)
    un = arange(1,p+1)
    if bound == 'l':
        shift,count = lb,ln
    elif bound == 'u':
        shift,count = ub,un
    else:
        shift,count = interleave(lb,ub),interleave(ln,un)
    if group:
        if bound == 'l':
            shift,count = shift[:1],count[:1]
        elif bound == 'u':
            shift,count = shift[-1:],count[-1:]
        else:
            shift,count = shift[[1,-1]],count[[1,-1]]

    ok = True
    for s,c in zip(shift,count):
        ks = k - s * m
        n = count_neg_diag(ks)
        if n != c:
            ok = False
        if n != c or verbose:
            print("Shift %.6f: %s expected, %s found, %s missing" % (s,n,c,n-c))
    return ok


def flip(x):
    """Flip vectors in x to make largest component positive.

    x: a set of coumn vectors (n,p)

    Returns the set x (n,p) with possibly some vector(s) flipped.
    """
    for j in range(x.shape[1]):
        ind = argmax(abs(x[:,j]))
        if x[ind,j] < 0.0:
            x[:,j] = -x[:,j]
    return x


def reorder(e,x):
    """Reorder eigenvalues and eigenvectors in ascending order."""
    ind = argsort(abs(e))
    return e[ind], x[:,ind]


def orthonormalize(x,m=None,i=0):
    """Orthonormalize the vectors of x with respect to m.

    x: a set of p column vectors (n,p), p <= n
    m: mass matrix (n,n). Defaults to an identity matrix.
    i: the first vector to be orthonormalized, i <= p. This can be used
      to speed up the operations in case the first i-1 vectors are already
      orthonormal. The operations will only be performed for vectors i..p.

    Returns the orthogonalized vectors (n,p-i) and their length factors (p-i).
    """
    l = []
    for j in range(i,x.shape[1]):
        xj = x[:,j]
        if m is None:
            xm = xj.copy()
        else:
            xm = m * xj
        # Orthogonalize to the previous j vectors
        for k in range(j):
            xk = x[:,k]
            a = xk.T * xm
            xj -= float(a) * xk
        # Normalize vector j with respect to m
        a = float(xj.T * xm)
        a = sqrt(a)
        l.append(a)
        x[:,j] /= a
    return flip(x[:,i:]),array(l)


def compare(x,y):
    """Compare the column vectors of x and y.

    Returns the maximum 2-norm of the difference between
    columns vectors in the matrices x and y.
    """
    d = asarray(x) - asarray(y)
    return linalg.norm(d,axis=0).max()


def initial_vectors(k,m,p,randx=False):
    """Compute initial values for p eigenvectors of k,m.

    The first vector contains the diagonal of the mass matrix.
    The following vectors are unit vectors corresponding with the
    smallest kii/mii values (which would produce the smallest eigenvalues
    if all DOFs were uncoupled).

    As an option, a random vector may be used as the last one, to enforce
    all DOFs being sollicited.
    """
    n = k.shape[0]
    x = zeros((n,p))
    # First vector: the diagonal of the mass matrix
    x[:,0] = m.diagonal()

    if p > 1:
        # Remainder are the dofs with the smallest kii/mii ratio:
        # they will likely be close to the lowest eigenvalue vectors
        # First check where mii != 0
        ok = where(x[:,0] != 0.)[0]
        # compute ratios k/m
        km = asarray(k).diagonal()[ok] / x[:,0][ok]
        # find p-1 smallest values
        ind = argsort(km)[:p-1]
        ind = ok[ind]
        # create unit vectors
        for i in range(p-1):
            x[ind[i],i+1] = 1.0

        if randx:
            # Last vector is random (to allow all dofs to be engaged)
            x[:,-1] = random.rand((n))

    return x


def tjacobi(k,tol=1.e-6,maxsweeps=20,verbose=False):
    """Compute eigenvalues of a symmetric matrix using threshold jacobi method.

    Solves the standard eigenproblem k.x = e.x, where k is a symmetric matrix.

    The jacobi method consists in zeroing the off-diagonal elements by
    subsequent rotations. In this variant only elements larger that a
    given threshold are zeroed.

    Returns e,x: the eigenvalues and eigenvectors in order of increasing
    eigenvalue.
    """
    k = k.copy()    # avoid changing the input
    n = k.shape[0]
    x = eye(n,n)
    e = asarray(k).diagonal()
    # Execute a number of sweeps
    for m in range(maxsweeps):
        thres = 10.**(-2*(m+1))
        conv2 = 0.0
        # Loop over upper triangular off-diagonal elements
        for i in range(n-1):
            for j in range(i+1,n):
                coupling = sqrt( k[i,j]*k[i,j] / k[i,i]*k[j,j])
                if coupling > conv2:
                    conv2 = coupling
                if coupling > thres:
                    # Zero this element.
                    theta = arctan(2*k[i,j]/(k[i,i]-k[j,j])) / 2 if k[i,i] != k[j,j] else pi/4
                    co, si = cos(theta), sin(theta)
                    #print("theta = %s, co = %s, si = %s" % (theta,co,si))
                    Pi = matrix([[co, -si], [si, co]])
                    k[[i,j]] = Pi.T * k[[i,j]]
                    k[:,[i,j]] = k[:,[i,j]] * Pi
                    x[:,[i,j]] = x[:,[i,j]] * Pi
        #print(k)
        #print(x)
        ei = asarray(k).diagonal()
        # Compute convergence
        conv1 = max(abs((e-ei)/e))
        e = ei
        if verbose:
            print("Sweep %s: convergence: %s, %s" % (m,conv1,conv2))
        if conv1 < tol and conv2 < tol:
            break

    return (reorder(e,x))


def gjacobi(k,m,tol=1.e-6,maxsweeps=20,verbose=False):
    """Compute eigenvalues of (k,m) using generalized jacobi method.

    Solves for all eigenpairs of the generalized eigenproblem k.x = e.m.x

    Parameters:
    k: stiffness matrix (n,n), positive definite
    m: mass matrix (n,n), positive definite

    The method consists in zeroing the off-diagonal elements of k and m
    by subsequent rotations. Only elements larger than the given threshold
    are zeroed.

    The method is very efficient for small systems, as it converges
    quadratically, and can be used as part of the subspace iteration method.

    Returns e,x: the eigenvalues e(n) and eigenvectors x(,n,) in order of
    increasing eigenvalue.
    """
    k, m = k.copy(), m.copy()    # avoid changing the input matrices
    n = k.shape[0]
    # If k and m were diagonal, these would be the solutions:
    e = asarray(k).diagonal() / asarray(m).diagonal()
    x = eye(n,n)
    # Execute a number of sweeps: a sweep loops over all off-diagonal
    # elements larger than the threshold. It zeroes the element by
    # a single rotation in the plane of the two involved DOFs.
    # As any such rotation will change other off-diagonal elements as well,
    # previously zeroed elements become nonzero again.
    # Therefore, a number of sweeps is required, until all elements have
    # become smaller than the threshold value.
    for sw in range(maxsweeps):
        thres = 10.**(-2*(sw+1))
        conv2 = 0.0
        # Loop over upper triangular off-diagonal elements
        for i in range(n-1):
            for j in range(i+1,n):
                kii, kij, kjj = k[i,i], k[i,j], k[j,j]
                mii, mij, mjj = m[i,i], m[i,j], m[j,j]
                kcoupling = sqrt( kij*kij / kii*kjj )
                mcoupling = sqrt( mij*mij / mii*mjj )
                conv2 = max(conv2,kcoupling,mcoupling)
                if kcoupling > thres or mcoupling > thres:
                    # Zero this element in both k and m
                    # Note that e[i] == kii/mii and e[j] == kjj/mjj
                    if mij > 0.0 and e[i] == e[j] == kij/mij:
                        # Trivial case
                        alpha = 0
                        gamma = -kij/kjj
                    else:
                        # General case
                        ka = kii*mij - mii*kij
                        kc = kjj*mij - mjj*kij
                        kb = kii*mjj - kjj*mii
                        xb = kb/2 + copysign(1,kb) * sqrt((kb/2)**2+ka*kc)
                        alpha = kc / xb
                        gamma = -ka / xb
                    #print("alpha = %s, gamma = %s" % (alpha,gamma))
                    # Construct the rotation matrix for dofs i,j
                    Pi = matrix([[1., alpha], [gamma, 1.]])
                    # Computes the products Pt * k * P and Pt * m * P
                    # where P is the (n,n) rotation matrix with the
                    # elements of Pi on positions (i,j)
                    k[[i,j]] = Pi.T * k[[i,j]]
                    m[[i,j]] = Pi.T * m[[i,j]]
                    k[:,[i,j]] = k[:,[i,j]] * Pi
                    m[:,[i,j]] = m[:,[i,j]] * Pi
                    x[:,[i,j]] = x[:,[i,j]] * Pi

        # Compute new approximations for the eigenvalues
        # and evaluate their convergence
        ei = asarray(k).diagonal() / asarray(m).diagonal()
        conv1 = max(abs((e-ei)/e))
        # Store new approximations
        e = ei
        if verbose:
            print("Sweep %s: convergence: %s, %s" % (sw,conv1,conv2))
        if conv1 < tol and conv2 < tol:
            # Eigenvalues have converged AND all off-diagonals are small
            break

    # Compute eigenvectors
    x = x / sqrt(m.diagonal())

    return reorder(e,x)


def inverse(k,m,p=None,x=None,tol=1.e-3,maxit=20,verbose=True):
    """Find the eigenvectors and eigenvalues of k,m by inverse iteration

    Solves for the p smallest eigenvalues (and corresponding eigenvectors)
    of the generalized eigenproblem k.x = e.m.x using simultaneous
    inverse iteration.

    Parameters:
    k: stiffness matrix (n,n)
    m: mass matrix (n,n)
    p: number of eigenvalues to compute. Can be omitted if x is specified.
    x: initial guesses for the first p eigenvectors (n,p). If not specified,
       proper initial values are constructed automatically.
    tol: required accuracy on the eigenvalues
    maxit: maximum number of subspace iterations. Avoids runaway on badly
       converging problems
    verbose: bool. If True, the convergence trace is printed

    Returns e,x: the p smallest eigenvalues e(p) and corresponding
    eigenvectors x(n,p) in order of increasing absolute eigenvalue.
    """
    k = matrix(k)
    m = matrix(m)
    n = k.shape[0]
    if x is None:
        # Construct optimal initial vectors
        x = initial_vectors(k,m,p)
    # Perform simultaneous inverse iteration over all eigenvectors
    for i in range(maxit):
        # Solve for new approximations
        # NOTE: the speed of this method can drastically be improved
        # by moving the LDLt decomposition of k outside of the loop.
        xi = linalg.solve(k,m*x)
        # Orthonormalize the vectors with respect to the mass matrix
        # This also delivers the reciprocals of the eigenvalues
        xi,ei = orthonormalize(xi,m)
        ei = 1.0 / ei
        # Evaluate convergence
        conv = compare(xi,x)
        if verbose:
            print("  Inverse iteration %s: convergence: %s" % (i,conv))
        # Store new approximations
        e,x = ei,xi
        if conv < tol:
            # Accuracy obtained: we're done
            break

    return reorder(e,x)


def subspace(k,m,p,q=None,x=None,tol=1.e-6,maxit=20,verbose=False,check=True):
    """Find some eigenvectors and eigenvalues of k,m by subspace iteration.

    Solves for the p smallest eigenvalues (and corresponding eigenvectors)
    of the generalized eigenproblem k.x = e.m.x using subspace iteration.

    Parameters:
    k: stiffness matrix (n,n)
    m: mass matrix (n,n)
    p: number of eigenpairs to compute (p <= n)
    q: size of the subspace (p <= q <= n). If not specified and neither is
       x, it is set to min(2p,p+8,n), else to the number of columns in x.
    x: initial guesses for the first q eigenvectors (n,q). If not specified,
       proper initial values are constructed automatically.
    tol: required accuracy on the eigenvalues
    maxit: maximum number of subspace iterations. Avoids runaway on badly
       converging problems
    verbose: bool. If True, the convergence trace is printed

    Returns e,x: the p smallest eigenvalues e(p) and corresponding
    eigenvectors x(n,p) in order of increasing absolute eigenvalue.
    """
    k = matrix(k)
    m = matrix(m)
    n = k.shape[0]
    if q is None and x is None:
        # Sensible choice of subspace size
        q = min(2*p,p+8,n)
    if q is None:
        # x was spcified, acknowledge it
        mx = m*x
        q = mx.shape[1]
    else:
        # Construct optimal initial vectors
        if verbose: print('Size of subspace: %s' % q)
        mx = initial_vectors(k,m,q)

    for i in range(maxit):
        # Compute q vectors to reduce space
        # NOTE: just like for inverse iteration, performing LDLt decomposition
        # of k before starting the loop can dramatically improve performance
        xi = linalg.solve(k,mx)
        # Project k,m on a smaller vector space
        ki = xi.T * k * xi
        mi = xi.T * m * xi
        # Solve reduced eigenproblem for all q eigenpairs
        ei,qi = gjacobi(ki,mi,tol=tol)
        # New full eigenvector approximations
        xi = xi * qi
        # Compute convergence
        if i > 0:
            # Only use p vectors here!
            econv = abs((e-ei[:p])/e)
            # We could also check convergence of x
            #xconv = compare(xi,x)
            if verbose:
                print("  Subspace iteration %s: convergence: %s" % (i,econv.max()))
        # Store eigenpair approximations
        e,x = ei[:p],xi[:,:p]
        # Prepare for next iteration: use q vectors here
        mx = m * xi[:,:q]
        # Check convergence
        if i > 0 and (econv < tol).all():
            break
        if verbose and i == maxit-1:
            print("  Convergence not reached after %s iterations" % maxit)

    # Note that the results are already ordered by the gjacobi
    if check:
        # Perform a sturm check
        sturm_check(k,m,e,group=True,bound='u',verbose=False)

    return e,flip(x)


def lanczos(k,m,p,q=None,randx=False,check=True):
    """Solves a generalized eigenproblem using lanczos vectors.

    Solves for the p smallest eigenvalues (and corresponding eigenvectors)
    of the generalized eigenproblem k.x = e.m.x using lanczos vectors.

    Parameters:
    k: stiffness matrix (n,n)
    m: mass matrix (n,n)
    p: number of eigenpairs to compute (p <= n)
    q: number of lanczos vectors to be used. Default q == p. Since each
       following eigenvalue is obtained with smaller accuracy, this should be
       set larger than p (e.g. 2*p) if p accurate values are required.
    randx: use a random starting vector instead of all ones.

    Returns e,x: the p smallest eigenvalues e(p) and corresponding
    eigenvectors x(n,p) in order of increasing absolute eigenvalue.

    """
    n = k.shape[0]
    if q is None:
        q = min(2*p,p+8,n)
    # Construct start vector
    if randx:
        # arbitrary
        xi = matrix(random.rand(n,1))
    else:
        # all ones
        xi = matrix(ones((n,1)))
    # Initialize associated problem matrix and fill in first vector
    t = zeros((q,q))
    x = matrix(zeros((n,q)))
    x[:,0],dummy = orthonormalize(xi,m)
    # iteratively create next vectors and fill t matrix of the
    # associated problem
    for i in range(1,q+1):
        mx = m * matrix(x[:,i-1])
        xbar = linalg.solve(k,mx)
        alpha = float(xbar.T * mx)
        t[i-1,i-1] = alpha
        if i == q:
            break
        xtilde = xbar - alpha * x[:,i-1]
        if i > 1:
            xtilde = xtilde - beta * x[:,i-2]
        #x[:,i],beta = orthonormalize(xtilde,m)
        x[:,i] = xtilde
        x[:,i],beta = orthonormalize(x[:,:i+1],m,i)
        beta = float(beta)
        t[i-1,i] = t[i,i-1] = beta
    # Now find the eigenvalues of the associated problem
    e,xt = tjacobi(t)
    # And compute approximations for full problem
    e = 1/e
    x = x * xt
    e,x = reorder(e,x)
    if p < q:
        e = e[:p]
        x = x[:,:p]

    if check:
        # Perform a sturm check
        sturm_check(k,m,e,group=True,bound='u',verbose=False)

    return e,flip(x)


# End
