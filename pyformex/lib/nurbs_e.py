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
#
"""Python equivalents of the functions in lib.nurbs_

The functions in this module should be exact emulations of the
external functions in the compiled library. Currently however this
module only contains a few of the functions in lib.nurbs_, making
nurbs functionality in pyFormex currently only available when using
the compiled lib.
"""
from __future__ import absolute_import, print_function


# There should be no other imports here but numpy
import numpy as np

# And Set the version from pyformexld be defined
import pyformex
__version__ = pyformex.__version__
accelerated = False

# Since binomial is already defined in plugins.curve, we can just import it here.
from pyformex.plugins.curve import binomial


def length(A):
    """Return the length of an ndim vector."""
    return np.linalg.norm(A)


def Bernstein(n,i,u):
    """Compute the value of the Bernstein polynomial Bi,n at u.

    Parameters:

    - `n`: int: degree of the polynomials
    - `i`: int: degree of the polynomials
    - `u`: float, parametric value where the polynomials are evaluated

    Returns: an (n+1,) shaped float array with the value of all n-th
    degree Bernstein polynomials B(i,n) at parameter value u.

    Algorithm A1.3 from 'The NURBS Book' p20.

    >>> Bernstein(5,2,0.4)
    0.34560000000000002
    """
    # THIS IS NOT OPTIMIZED !
    return allBernstein(n,u)[i]


def allBernstein(n, u):
    """Compute the value of all n-th degree Bernstein polynomials.

    Parameters:

    - `n`: int, degree of the polynomials
    - `u`: float, parametric value where the polynomials are evaluated

    Returns: an (n+1,) shaped float array with the value of all n-th
    degree Bernstein polynomials B(i,n) at parameter value u.

    Algorithm A1.3 from 'The NURBS Book' p20.
    """
    # THIS IS NOT OPTIMIZED FOR PYTHON.
    B = np.zeros(n+1)
    B[0] = 1.0
    u1 = 1.0-u
    for j in range(1, n+1):
        saved = 0.0
        for k in range(j):
            temp = B[k]
            B[k] = saved + u1*temp
            saved = u * temp
        B[j] = saved
    return B


def curveDegreeElevate(Pw,U,t):
    """Elevate the degree of the Nurbs curve.

    Parameters:

    - `Pw`: float array (nk,nd): nk=n+1 control points
    - `U`: int array(nu): nu=m+1 knot values
    - `t`: int: how much to elevate the degree

    Returns a tuple:

    - `Qw`: nh+1 new control points
    - `Uh`: mh+1 new knot values
    - `nh`: highest control point index
    - `mh`: highest knot index

    This is based on algorithm A5.9 from 'The NURBS Book' pg206.

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

    # Compute Bezier degree elevation coefficients
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
    # Initialize first Bezier segment
    for i in range(p+1):
        bpts[i] = Pw[i]
#    print("bpts =\n%s" % bpts[:p+1])

    # Big loop thru knot vector
    while b < m:
#        print("Big loop b = %s < m = %s" % (b,m))
        i = b
        while b < m and U[b] == U[b+1]:
            b += 1;
        mul = b-i+1
        mh += mul+t
        ub = U[b]
        oldr = r
        r = p-mul

        # Insert knot ub r times
        lbz = (oldr+2)//2 if oldr > 0 else 1
        rbz = ph-(r+1)//2 if r > 0 else ph

        if r > 0:
            # Insert knot to get Bezier segment
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

        # Degree elevate Bezier
        for i in range(lbz,ph+1):
            # Only points lbz..ph are used below
            ebpts[i] = 0.0
            mpi = min(p,i)
            for j in range(max(0,i-t),mpi+1):
                ebpts[i] += bezalfs[i,j]*bpts[j]
#        print("ebpts =\n%s" % ebpts[lbz:ph+1])

        if oldr > 1:
            # Must remove knot U[a] oldr times
            first = kind-2
            last = kind
            den = ub-ua
            bet = (ub-Uh[kind-1]/den)
            for tr in range(1,oldr):
                # Knot removal loop
                i = first
                j = last
                kj = j-kind+1
                while j-i > tr:
                    # Compute new control points
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
            # Load the knot ua
            for i in range(ph-oldr):
                Uh[kind] = ua
                kind += 1

        for j in range(lbz,rbz+1):
            # Load control points into Qw
            Qw[cind] = ebpts[j]
            cind += 1
#        print(Qw[:cind])

#        print("Now b=%s, m=%s" % (b,m))
        if b < m:
            # Set up for next passcthru loop
            for j in range(r):
                bpts[j] = Nextbpts[j]
            for j in range(r,p+1):
                bpts[j] = Pw[b-p+j]
            a = b
            b += 1
            ua = ub
        else:
            # End knot
            for i in range(ph+1):
                Uh[kind+i] = ub

    nh = mh - ph - 1
    Uh = Uh[:mh+1]
    Qw = Qw[:nh+1]

    return np.array(Pw), np.array(Uh), nh, mh


def BezDegreeReduce(Q,return_errfunc=False):
    """Degree reduce a Bezier curve.

    Parameters:

    - `Q`: float array (nk,nd): control points of a Bezier curve of degree
      p = nk-1
    - `return_errfunc`: bool: if True, also returns a function to evaluate the
      error along the parametric values.

    Returns a tuple:

    - `P`: float array (nk-1,nd): control points of a Bezier curve of
      degree p-1
    - `maxerr`: float: an upper bound on the error introduced by the degree
      reduction

    Based on The NURBS Book.
    """
    nk,nd = Q.shape
    p = nk - 1
    r = (p-1) // 2
    alfs = np.arange(p) / float(p)
    print("Bezier alfs: %s" % alfs)
    print("Input Q")
    print(Q)
    P = np.zeros((p,nd))
    P[0] = Q[0]
    for i in range(1,r+1):
        P[i] = ( Q[i] - alfs[i]*P[i-1] ) / (1.0-alfs[i])
    P[p-1] = Q[p]
    for i in range(p-2,r,-1):
        P[i] = ( Q[i+1] - (1-alfs[i+1])*P[i+1] ) / alfs[i+1]
    if p % 2 == 1:
        PrR = ( Q[r+1] - (1-alfs[r+1])*P[r+1] ) / alfs[r+1]
        Err = 0.5 * (1.0-alfs[r]) * length( P[r] - PrR )
        P[r] = 0.5 * (P[r] + PrR)
    else:
        Err = length(Q[r+1]-0.5*(P[r]+P[r+1]))
    #print("Err = %s" % Err)

    # Max error
    # Note that maximum of Bernstein polynom (i,p) is at i/p
    if p % 2 == 0:
        errfunc = lambda u: Err * Bernstein(p,r+1,u)
        # Note that maximum of Bernstein polynom (i,p) is at i/p
        #print("Bernstein(%s,%s,%s) = %s" %(p,r+1,(r+1.)/p,errfunc((r+1.)/p)))
        maxerr = errfunc((r+1.)/p)
    else:
        #print("Bernstein(%s,%s,%s) = %s" %(p,r+1,(r+1.)/p,Bernstein(p,r+1,(r+1.)/p)))
        #print("Bernstein(%s,%s,%s) = %s" %(p,r+1,(r+0.)/p,Bernstein(p,r+1,(r+0.)/p)))
        #print("Bernstein(%s,%s,%s) = %s" %(p,r,(r+1.)/p,Bernstein(p,r,(r+1.)/p)))
        #print("Bernstein(%s,%s,%s) = %s" %(p,r,(r+0.)/p,Bernstein(p,r,(r+0.)/p)))
        errfunc = lambda u: Err * abs(Bernstein(p,r,u) - Bernstein(p,r+1,u))
        # We guess that maximum is close to middle of r/p and r+1/p
        maxerr = max(errfunc(float(r)/p),errfunc(float(r+1)/p))

    #print("maxerr = %s" % maxerr)
    print("Output P")
    print(P)
    if return_errfunc:
        return P,maxerr,errfunc
    else:
        return P,maxerr


from pyformex.coords import Coords
from pyformex.gui.draw import pause
def curveDegreeReduce(Qw,U):
    """Reduce the degree of the Nurbs curve.

    Parameters:

    - `Qw`: float array (nc,nd): nc=n+1 control points
    - `U`: int array(nu): nu=m+1 knot values

    Returns a tuple:

    - `Pw`: nh+1 new control points
    - `Uh`: mh+1 new knot values
    - `nh`: highest control point index
    - `mh`: highest knot index
    - `err`: error vector

    This is based on algorithm A5.11 from 'The NURBS Book' pg223.

    """
    nc,nd = Qw.shape
    n = nc-1
    m = U.shape[0]-1
    p = m-n-1
    print("Reduce degree of curve from %s to %s" % (p,p-1))
    # Workspace for return arrays
    Uh = np.zeros((2*m+1,))
    Pw = np.zeros((2*nc+1,nd))
    # Set up workspaces
    bpts = np.zeros((p+1,nd)) # Bezier control points of current segment
    Nextbpts = np.zeros((p-1,nd)) # leftmost control points of next Bezier segment
    rbpts = np.zeros((p,nd)) # degree reduced Bezier control points
    alfs = np.zeros((p-1,)) # knot insertion alphas
    err = np.zeros((m,)) # error vector

    # Initialize some variables
    ph = p-1
    mh = ph
    kind = p
    r = -1
    a = p
    b = p+1
    cind = 1
    mult = p
    Pw[0] = Qw[0]
    # Compute left end of knot vector
    Uh[:ph+1] = U[0]
    # Initialize first Bezier segment
    bpts[:p+1] = Qw[:p+1]

    print("Initial Uh")
    print(Uh[:ph+1])
     # Loop through the knot vector
    while b < m:
        # Compute knot multiplicity
        i = b
        while b < m and U[b] == U[b+1]:
            b += 1;
        mult = b-i+1
        mh += mult-1
        print("Big loop b=%s < m=%s (mult=%s, mh=%s, )" % (b,m,mult,mh))
        print("a=%s;b=%s;u[a]..u[b]=%s" % (a,b,U[a:b+1]))
        print("Initial bpts\n",bpts)
        oldr = r
        r = p-mult
        lbz = (oldr+2)//2 if oldr > 0 else 1
        print("oldr=%s; r=%s; lbz=%s" % (oldr,r,lbz))
#
#        ua = U[a]
#        ub = U[b]

        # Insert knot U[b] r times
        if r > 0:
            # Insert knot to get Bezier segment
            print("Insert knot %s %s times" % (U[b],r))
            numer = U[b]-U[a]
            for k in range(p,mult-1,-1):
                alfs[k-mult-1] = numer / (U[a+k] - U[a])
            print("alfs = %s" % alfs[:p])
            for j in range(1,r+1):
                save = r-j
                s = mult+j
                for k in range(p,s-1,-1):
                    bpts[k] = alfs[k-s]*bpts[k] + (1.0-alfs[k-s])*bpts[k-1]
                Nextbpts[save] = bpts[p]
                print("Nextbpts %s = %s" %(save,Nextbpts[save]))

        print("Bezier segment degree reduction")
        print("bpts =\n",bpts)
        # Degree reducee Bezier segment
        rbpts,maxErr = BezDegreeReduce(bpts)
        from pyformex.plugins.curve import PolyLine
        from pyformex.gui.draw import draw
        draw(PolyLine(rbpts[:,:3]),color='darkgreen')
        draw(Coords(rbpts[:,:3]),color='black',marksize=5)
        print("Reduced ctrl points: \n",rbpts[:p])
        print("Degree reduce error = %s"%maxErr)
        err[a] += maxErr
#        if err[a] > TOL:
#            return None  # Curve not degree reducible

        if oldr > 0:
            print("Remove knot %s %s times" % (U[a],oldr))
            first = kind
            last = kind
            for k in range(oldr):
                i = first
                j = last
                kj = j-kind
                while j-i > k:
                    alfa = (U[a]-Uh[i-1]) / (U[b]-Uh[i-1])
                    beta = (U[a]-Uh[j-k-1]) / (U[b]-Uh[j-k-1])
                    Pw[i-1] = (Pw[i-1] - (1.0-alfa)*Pw[i-2]) / alfa
                    rbpts[kj] = (rbpts[kj] - beta*rbpts[kj+1])/(1.0-beta)
                    i += 1
                    j -= 1
                    kj -= 1

                # Compute knot removal error bounds (Br)
                if j-i < k:
                    Br = length(Pw[i-2] - rbpts[kj+1])
                else:
                    delta = (U[a]-Uh[i-1]) / (U[b]-Uh[i-1])
                    A = delta*rbpts[kj+1] + (1.0-delta)*Pw[i-2]
                    Br = length(Pw[i-1] - A)
                print("Knot removal error = %s" % Br)
                # Update the error vector
                K = a+oldr-k
                q = (2*p-k+1)//2
                L = K-q
                for ii in range(L,a+1): # These knot spans were affected
                    err[ii] += Br
#                    if err[ii] > TOL:
#                        return None

                first -= 1
                last +=1

            cind = i-1

        if a != p:
            # Load the knot U[a]
            for i in range(ph-oldr+1):
                print("Load the knot ua=%s in Uh[%s]" % (U[a],kind))
                Uh[kind] = U[a]
                kind += 1
        print("Uh is now (%s)" % kind)
        print(Uh[:kind])

        for i in range(lbz,ph+1):
            # Load control points into Pw
            print("Load control point %s from rbpts %s = %s" % (cind,i,rbpts[i]))
            Pw[cind] = rbpts[i]
            cind += 1
        print("Pw is now (%s)" % cind)
        print(Pw[:cind])
        pause()
        draw(Coords(Pw[:cind,:3]),color='black',marksize=5)

        pause()
        if b < m:
            print("%s < %s: Set up for next pass thru loop" % (b,m))
            for i in range(r):
                bpts[i] = Nextbpts[i]
            for i in range(r,p+1):
                bpts[i] = Qw[b-p+i]
            a = b
            b += 1

        else:
            # End knot
            for i in range(ph+1):
                Uh[kind] = U[b]
                kind += 1

    print("cind = %s; kind = %s; mh=%s; ph=%s" % (cind,kind,mh,ph))
    mh = kind-1
    nh = mh - ph - 1
    print("nh = %s" % nh)
    Uh = Uh[:mh+1]
    Pw = Pw[:nh+1]

    draw(PolyLine(Pw[:,:3]),color='red',linewidth=3)
    print("New control points:\n",Pw)
    print("New knot vector:\n",Uh)
    return Pw, Uh, nh, mh, err


def curveUnclamp(P,U):
    """Unclamp a clamped curve.

    Input: P,U
    Output: P,U

    Note: this changes P and U inplace.

    Based on algorithm A12.1 of The NURBS Book.
    """
#    print("CURVE UNCLAMP INPUT")
#    print(P)
#    print(U)
    n = P.shape[0] - 1
    m = U.shape[0] - 1
    p = m - n - 1
    # Unclamp at left end
    for i in range(p):
        U[p-i-1] = U[p-i] - (U[n-i+1]-U[n-i])
        if i == p-1:
            break
        k = p-1
        for j in range(i,-1,-1):
            alfa = (U[p]-U[k]) / (U[p+j+1]-U[k])
            P[j] = (P[j] - alfa*P[j+1]) / (1.0-alfa)
            k -= 1
    # Unclamp at right end
    for i in range(p):
        U[n+i+2] = U[n+i+1] + (U[p+i+1]-U[p+i])
        if i == p-1:
            break
        for j in range(i,-1,-1):
            alfa = (U[n+1]-U[n-j]) / (U[n-j+i+2]-U[n-j])
            P[n-j] = (P[n-j] - (1.0-alfa)*P[n-j-1]) / alfa

#    print("CURVE UNCLAMP OUTPUT")
#    print(P)
#    print(U)
    return P,U



# End
