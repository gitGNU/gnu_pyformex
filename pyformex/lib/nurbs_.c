/* $Id$ */
//
//  This file is part of pyFormex 1.0.2  (Thu Jun 18 15:35:31 CEST 2015)
//  pyFormex is a tool for generating, manipulating and transforming 3D
//  geometrical models by sequences of mathematical operations.
//  Home page: http://pyformex.org
//  Project page:  http://savannah.nongnu.org/projects/pyformex/
//  Copyright 2004-2015 (C) Benedict Verhegghe (benedict.verhegghe@feops.com)
//  Distributed under the GNU General Public License version 3 or later.
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.
//
//  This program is distributed in the hope that it will be useful,
//  but WITHOUT ANY WARRANTY; without even the implied warranty of
//  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//  GNU General Public License for more details.
//
//  You should have received a copy of the GNU General Public License
//  along with this program.  If not, see http://www.gnu.org/licenses/.
//

//
// This module is partly inspired by the Nurbs toolbox Python port by
// Runar Tenfjord (http://www.aria.uklinux.net/nurbs.php3)
//

#include "Python.h"
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include "numpy/arrayobject.h"
#include <math.h>

// cast pointers to avoid warnings
#define PYARRAY_DATA(p) PyArray_DATA((PyArrayObject *)p)
#define PYARRAY_DIMS(p) PyArray_DIMS((PyArrayObject *)p)
#define PYARRAY_FROM_OTF(p,q,r) (PyArrayObject *) PyArray_FROM_OTF(p,q,r)

/****************** LIBRARY VERSION AND DOCSTRING *******************/

static char *__version__ = "1.0.3-a2";
static char *__doc__ = "pyformex.lib.nurbs_ module\n\
\n\
This module provides accelerated versions of the pyFormex NURBS\n\
functions.\n\
";


/****** INTERNAL FUNCTIONS (not callable from Python) ********/

int min(int a, int b)
{
  if (b < a) a = b;
  return a;
}

int max(int a, int b)
{
  if (b > a) a = b;
  return a;
}

/* cumsum of a list of integer values */
/* v and cs have same length */
static void cumsum(int *v, int nv, int *cs)
{
  int i, sum = 0;
  for (i=0; i<nv; ++i) {
    sum += v[i];
    cs[i] = sum;
  }
}

/* Dot product of two vectors of length n */
/* ia and ib are the strides of the elements addressed starting from a, b */
static double dotprod(double *a, int ia, double *b, int ib, int n)
{
  int i;
  double t;
  t = 0.0;
  for (i=0; i<n; i++) {
    t += (*a)*(*b);
    a += ia;
    b += ib;
  }
  return t;
}

/* Distance between two points in n dimensions */
/* p and q are n-dimensional points. */
static double distance4d(double *a, double *b, int n)
{
  int i;
  double s,t;
  t = 0.0;
  for (i=0; i<n; i++) {
    s = (*a)-(*b);
    t += s*s;
    ++a;
    ++b;
  }
  return t;
}


/* Turn an array into a matrix */
/* An array here is a contiguous memory space of (nrows*ncols) doubles,
   stored in row first order. This function creates an array of pointers
   to the start of each row. As a result the array elements can be addressed
   as p[i][j], and operations can be done on the whole row.
*/
/* static double **matrix(double*a, int nrows, int ncols)  */
/* { */
/*   int row; */
/*   double **mat; */

/*   mat = (double**) malloc (nrows*sizeof(double*)); */
/*   mat[0] = a; */
/*   for (row = 1; row < nrows; row++) */
/*     mat[row] = mat[row-1] + ncols;   */
/*   return mat; */
/* } */

static double **newmatrix(int nrows, int ncols)
{
  int row;
  double **mat;

  mat = (double**) malloc (nrows*sizeof(double*));
  mat[0] = (double*) malloc (nrows*ncols*sizeof(double));
  for (row = 1; row < nrows; row++)
    mat[row] = mat[row-1] + ncols;
  return mat;
}

static void freematrix(double **mat)
{
  free(mat[0]);
  free(mat);
}

static void print_mat(double *mat,int nrows,int ncols)
{
  int i,j;
  for (i=0;  i<nrows; i++) {
    for (j=0; j<ncols; j++) printf(" %e",mat[i*ncols+j]);
    printf("\n");
  }
}

// Compute logarithm of the gamma function
// Algorithm from 'Numerical Recipes in C, 2nd Edition' pg214.
static double _gammaln(double xx)
{
  double x,y,tmp,ser;
  static double cof[6] = {76.18009172947146,-86.50532032291677,
                          24.01409824083091,-1.231739572450155,
                          0.12086650973866179e-2, -0.5395239384953e-5};
  int j;
  y = x = xx;
  tmp = x + 5.5;
  tmp -= (x+0.5) * log(tmp);
  ser = 1.000000000190015;
  for (j=0; j<=5; j++) ser += cof[j]/++y;
  return -tmp+log(2.5066282746310005*ser/x);
}

// computes ln(n!)
// Algorithm from 'Numerical Recipes in C, 2nd Edition' pg215.
static double _factln(int n)
{
  static int ntop = 0;
  static double a[101];

  if (n <= 1) return 0.0;
  while (n > ntop)
  {
    ++ntop;
    a[ntop] = _gammaln(ntop+1.0);
  }
  return a[n];
}

//Computes the binomial coefficient.
//
//  ( n )      n!
//  (   ) = --------
//  ( k )   k!(n-k)!
// Algorithm from 'Numerical Recipes in C, 2nd Edition' pg215.

static double _binomial(int n, int k)
{
  return floor(0.5+exp(_factln(n)-_factln(k)-_factln(n-k)));
}


/* _horner

Compute the value of a polynomial using Horner's rule.

Input:
- a: double(n+1), coefficients of the polynomial, starting
     from lowest degree
- n: int, degree of the polynomial
- u: double, parametric value where the polynomial is evaluated

Returns:
double, the value of the polynomial

Algorithm A1.1 from 'The NURBS Book' p7.
*/

static double _horner(double *a, int n, double u)
{
  double c = a[n];
  int i;
  for (i = n-1; i>=0; --i) c = c * u + a[i];
  return c;
}

/* _bernstein */
/*
Compute the value of a Bernstein polynomial.

Input:
- i: int, index of the polynomial
- n: int, degree of the polynomial
- u: double, parametric value where the polynomial is evaluated

Returns:
The value of the Bernstein polynomial B(i,n) at parameter value u.

Algorithm A1.2 from 'The NURBS Book' p20.
*/

static double _bernstein(int i, int n, double u)
{
  int j, k;
  double u1;
  double *temp  = (double*) malloc((n+1)*sizeof(double));
  for (j=0; i<+n; j++) temp[j] = 0.0;
  temp[n-i] = 1.0;
  u1 = 1.0-u;
  for (k=1; k<=n; k++)
    for (j=n; j<=k; j--)
      temp[j] = u1*temp[j] + u*temp[j-1];
  return temp[n];
}


/* all_bernstein */
/*
Compute the value of all n-th degree Bernstein polynomials.

Input:
- n: int, degree of the polynomials
- u: double, parametric value where the polynomials are evaluated

Output:
- B: double(n+1), the value of all n-th degree Bernstein polynomials B(i,n)
at parameter value u.

Algorithm A1.3 from 'The NURBS Book' p20.
*/

static void all_bernstein(int n, double u, double *B)
{
  int j, k;
  double u1, temp, saved;
  B[0] = 1.0;
  u1 = 1.0-u;
  for (j=1; j<=n; j++) {
    saved = 0.0;
    for (k=0; k<j; k++) {
      temp = B[k];
      B[k] = saved + u1*temp;
      saved = u * temp;
    }
    B[j] = saved;
  }
}



/* /\* Find last occurrence of u in U *\/ */
/* static int find_last_occurrence(double *U, double u) */
/* { */
/*   int i = 0; */
/*   while (U[i] <= u + 1.e-5) ++i; */
/*   return i-1; */
/* } */

/* /\* Find multiplicity of u in U, where r is the last occurrence of u in U*\/ */
/* static int find_multiplicity(double *U, double u, int r) */
/* { */
/*   int i = r; */
/*   while (U[i] >= u - 1.e-5) --i; */
/*   return r-i; */
/* } */


/* find_span */
/*
Find the knot span index of the parametric point u.

Input:

- U: knot sequence: U[0] .. U[m]
- u: parametric value: U[0] <= u <= U[m]
- p: degree of the B-spline basis functions
- n: number of control points - 1 = m - p - 1

Returns:

- index of the knot span

Algorithm A2.1 from 'The NURBS Book' pg68.
*/
static int find_span(double *U, double u, int p, int n)
{
  int low, high, mid;
  int cnt=0;

  // special case
  if (u == U[n+1]) return(n);

  // do binary search
  low = p;
  high = n + 1;
  mid = (low + high) / 2;
  while (u < U[mid] || u >= U[mid+1]) {
    if (u < U[mid])
      high = mid;
    else
      low = mid;
    mid = (low + high) / 2;
    cnt ++;
    if (cnt > 20) break;
  }
  return(mid);
}

/* basis_funs */
/*
Compute the nonvanishing B-spline basis functions for index span i.

Input:

- U: knot sequence: U[0] .. U[m]
- u: parametric value: U[0] <= u <= U[m]
- p: degree of the B-spline basis functions
- i: index of the knot span for value u (from find_span())

Output:
- N: (p+1) values of nonzero basis functions at u

Algorithm A2.2 from 'The NURBS Book' pg70.
*/
static void basis_funs(double *U, double u, int p, int i, double *N)
{
  int j,r;
  double saved, temp;

  // work space
  double *left  = (double*) malloc((p+1)*sizeof(double));
  double *right = (double*) malloc((p+1)*sizeof(double));

  N[0] = 1.0;
  for (j = 1; j <= p; j++) {
    left[j]  = u - U[i+1-j];
    right[j] = U[i+j] - u;
    saved = 0.0;
    for (r = 0; r < j; r++) {
      temp = N[r] / (right[r+1] + left[j-r]);
      N[r] = saved + right[r+1] * temp;
      saved = left[j-r] * temp;
    }
    N[j] = saved;
  }

  free(left);
  free(right);
}

/* basis_derivs */
/*
Compute the nonvanishing B-spline basis functions and their derivatives.

Input:

- U: knot sequence: U[0] .. U[m]
- u: parametric value: U[0] <= u <= U[m]
- p: degree of the B-spline basis functions
- i: index of the knot span for value u (from find_span())
- n: number of derivatives to compute (n <= p)

Output:
- dN: (n+1,p+1) values of the nonzero basis functions and their first n
      derivatives at u

Algorithm A2.3 from 'The NURBS Book' pg72.
*/
static void basis_derivs(double *U, double u, int p, int i, int n, double *dN)
{
  int j,k,r,s1,s2,rk,pk,j1,j2;
  double temp, saved, der;
  double **ndu, *a, *left, *right;

  ndu = newmatrix(p+1, p+1);
  a = (double *) malloc(2*(p+1)*sizeof(double));
  left = (double *) malloc((p+1)*sizeof(double));
  right = (double *) malloc((p+1)*sizeof(double));

  ndu[0][0] = 1.0;
  for (j=1; j<=p; j++) {
    left[j] = u - U[i+1-j];
    right[j] = U[i+j]-u;
    saved = 0.0;
    for (r=0; r<j; r++) {
      /* Lower triangle */
      ndu[j][r] = right[r+1] + left[j-r];
      temp = ndu[r][j-1]/ndu[j][r];
      /* Upper Triangle */
      ndu[r][j] = saved + right[r+1]*temp;
      saved = left[j-r]*temp;
    }
    ndu[j][j] = saved;
  }
  /* Load the basis functions */
  for (j=0; j<=p; j++) dN[j] = ndu[j][p];

  /* Compute the derivatives (Eq. 2.9) */
  for (r=0; r<=p; r++) {   /* Loop over function index */
    s1 = 0; s2 = p+1;      /* Alternate rows in array a */
    a[0] = 1.0;

    /* Loop to compute kth derivative */
    for (k=1; k<=n; k++) {
      der = 0.0;
      rk = r-k;  pk = p-k;
      if (r >= k) {
        a[s2] = a[s1] / ndu[pk+1][rk];
        der = a[s2] * ndu[rk][pk];
      }
      if (rk >= -1) j1 = 1;
      else j1 = -rk;
      if (r-1 <= pk) j2 = k-1;
      else j2 = p-r;
      for (j=j1; j<=j2; j++) {
        a[s2+j] = (a[s1+j] - a[s1+j-1]) / ndu[pk+1][rk+j];
        der += a[s2+j] * ndu[rk+j][pk];
      }
      if (r <= pk) {
        a[s2+k] = -a[s1+k-1] / ndu[pk+1][r];
        der += a[s2+k] * ndu[r][pk];
      }
      dN[k*(p+1)+r] = der;
      /* Switch rows */
      j = s1; s1 = s2; s2 = j;
    }
  }

  /* Multiply by the correct factors */
  r = p;
  for (k=1; k<=n; k++) {
    for (j=0; j<=p; j++) dN[k*(p+1)+j] *= r;
    r *= (p-k);
  }

  freematrix(ndu);
  free(a);
  free(left);
  free(right);
}


/********************************************************/
/************************ CURVE *************************/
/********************************************************/


/* curve_points */
/*
Compute points on a B-spline curve.

Input:

- P: control points P(nc,nd)
- nc: number of control points
- nd: dimension of the points (3 or 4)
- U: knot sequence: U[0] .. U[m]
- nk: number of knot values = m+1
- u: parametric values: U[0] <= ui <= U[m]
- nu: number of parametric values

Output:
- pnt: (nu,nd) points on the B-spline

Modified algorithm A3.1 from 'The NURBS Book' pg82.
*/
static void curve_points(double *P, int nc, int nd, double *U, int nk, double *u, int nu, double *pnt)
{
  int i, j, p, s, t;

  /* degree of the spline */
  p = nk - nc - 1;

  /* space for the basis functions */
  double *N = (double*) malloc((p+1)*sizeof(double));

  /* for each parametric point j */
  for (j=0; j<nu; ++j) {

    /* find the span index of u[j] */
    s = find_span(U,u[j],p,nc-1);
    basis_funs(U,u[j],p,s,N);

    t = (s-p) * nd;
    for (i=0; i<nd; ++i) {
      pnt[j*nd+i] = dotprod(N,1,P+t+i,nd,p+1);
    }
  }
  free(N);
}


/* curve_derivs */
/*
Compute derivatives of a B-spline curve.

Input:

- n: number of derivatives to compute
- P: control points P(nc,nd)
- nc: number of control points
- nd: dimension of the points (3 or 4)
- U: knot sequence: U[0] .. U[m]
- nk: number of knot values = m+1
- u: parametric values: U[0] <= ui <= U[m]
- nu: number of parametric values

Output:
- pnt: (n+1,nu,nd) points and derivatives on the B-spline

Modified algorithm A3.2 from 'The NURBS Book' pg93.
*/
static void curve_derivs(int n, double *P, int nc, int nd, double *U, int nk, double *u, int nu, double *pnt)
{
  int i, j, l, p, s, t;

  /* degree of the spline */
  p = nk - nc - 1;

  /* number of nonzero derivatives to compute */
  int du = min(p,n);

  /* space for the basis functions and derivs (du+1,p+1) */
  double *dN = (double *) malloc((du+1)*(p+1)*sizeof(double));
  for (i = 0; i < (du+1)*(p+1); i++) dN[i] = 0.0;

  /* for each parametric point r */
  for (j = 0; j < nu; j++) {
    s = find_span(U,u[j],p,nc-1);
    basis_derivs(U,u[j],p,s,du,dN);

    /* for each nonzero dervative */
    for (l = 0; l <= du; l++) {

      t = (s-p) * nd;
      for (i = 0; i < nd; i++) {
	pnt[(l*nu+j)*nd+i] = dotprod(dN+l*(p+1),1,P+t+i,nd,p+1);
      }
    }
  }
  /* clear remainder */
  for (l = du+1; l <= n; l++)
    for (j = 0; j < nu; j++)
      for (i = 0; i < nd; i++)
	pnt[(l*nu+j)*nd+i] = 0.0;
  free(dN);
}


/* curve_knot_refine */
/*
Refine curve knot vector.

Input:

- p: degree of the B-spline
- P: control points P(nc,nd)
- nc: number of control points = n+1
- nd: dimension of the points (3 or 4)
- U: knot sequence: U[0] .. U[m]   m = n+p+1 = nc+p
- u: (nu) parametric values of new knots: U[0] <= u[i] <= U[m]
- nu: number of knots to insert

Output:
- newP: (nc+nu,nd) new control points
- newU: (nc+p+nu) new knot vector

Modified algorithm A5.4 from 'The NURBS Book' pg164.
*/
static void curve_knot_refine(double *P, int nc, int nd, double *U, int nk, double *u, int nu, double *newP, double *newU)
{
  int a, b, r, l, i, j, k, n, p, q, ind;
  double alfa;

  p = nk - nc - 1;
  n = nc - 1;
  r = nu - 1;

  a = find_span(U,u[0],p,n);
  b = find_span(U,u[r],p,n) + 1;

  for (j = 0; j < a-p; j++)
    for (q=0; q<nd; q++) newP[j*nd+q] = P[j*nd+q];
  for (j = b-1; j <= n; j++)
    for (q=0; q<nd; q++) newP[(j+r+1)*nd+q] = P[j*nd+q];

  for (j = 0; j <= a; j++)   newU[j] = U[j];
  for (j = b+p; j < nk; j++) newU[j+r+1] = U[j];

  i = b + p - 1;
  k = b + p + r;
  for (j = r; j >= 0; j--) {
    while (u[j] <= U[i] && i > a) {
      for (q=0; q<nd; q++) newP[(k-p-1)*nd+q] = P[(i-p-1)*nd+q];
      newU[k] = U[i];
      --k;
      --i;
    }
    for (q=0; q<nd; q++) newP[(k-p-1)*nd+q] = newP[(k-p)*nd+q];
    for (l = 1; l <= p; l++) {
      ind = k - p + l;
      alfa = newU[k+l] - u[j];
      if (fabs(alfa) == 0.0)
        for (q=0; q<nd; q++) newP[(ind-1)*nd+q] = newP[ind*nd+q];
      else {
        alfa /= (newU[k+l] - U[i-p+l]);
        for (q=0; q<nd; q++)
	  newP[(ind-1)*nd+q] = alfa*newP[(ind-1)*nd+q] + (1.0-alfa)*newP[ind*nd+q];
      }
    }

    newU[k] = u[j];
    --k;
  }
}

/* curve_decompose */
/*
Decompose a Nurbs curve in Bezier segments.

Input:

- p: degree of the B-spline
- P: control points P(nc,nd)
- nc: number of control points = n+1
- nd: dimension of the points (3 or 4)
- U: knot sequence: U[0] .. U[m]   m = n+p+1 = nc+p
- nk: number of knot values = m+1

Output:

- newP: (nb*p+1,nd) new control points
- nb: number of Bezier segments

Modified algorithm A5.6 from 'The NURBS Book' pg173.
*/
static void curve_decompose(double *P, int nc, int nd, double *U, int nk, double *newP)
{
  int i, j, k, p, s, m, r, a, b, mult, n, nb, ii, save;
  double numer, alpha, *alfa;

  n = nc - 1;
  m = nk - 1;
  p = m - n - 1;

  alfa = (double *) malloc(p*sizeof(double));

  a = p;
  b = p+1;
  nb = 0;

  /* First bezier segment */
  for (i = 0; i < (p+1)*nd; i++) newP[i] = P[i];

  // Loop through knot vector

  // INITIALIZE r in case it would not happen below.
  // To AVOID COMPILER WARNING
  // we should check this with the Nurbs book
  r = 0;

  while (b < m) {
    i = b;
    while (b < m && U[b] == U[b+1]) b++;
    mult = b-i+1;

    if (mult < p) {
      //printf("mult at %d is %d < %d\n",b,mult,p);
      /* compute alfas */
      numer = U[b] - U[a];
      for (k = p; k > mult; k--)
        alfa[k-mult-1] = numer / (U[a+k]-U[a]);

      /* Insert knot U[b] r times */
      r = p - mult;
      for (j = 1; j <= r; j++) {
        save = r - j;
        s = mult + j; 	/* Number of new points */
        for (k = p; k >= s; k--) {
	  alpha = alfa[k-s];
	  //printf("alpha = %f\n",alpha);
          for (ii = 0; ii < nd; ii++) {
            newP[(nb+k)*nd+ii] = alpha*newP[(nb+k)*nd+ii] + (1.0-alpha)*newP[(nb+k-1)*nd+ii];
	    //printf("Setting element %d to %f\n",(nb+k)*nd+ii,newP[(nb+k)*nd+ii]);
	  }
	}
	if (b < m)
	  /* Control point of next segment */
	  for (ii = 0; ii < nd; ii++) {
	    newP[(nb+p+save)*nd+ii] = newP[(nb+p)*nd+ii];
	    //printf("Copying element %d to %f\n",(nb+p+save)*nd+ii,newP[(nb+p+save)*nd+ii]);
	  }
      }
    }
    /* NOTE: if mult >= p, r is not initialized */
    /* Bezier segment completed */
    nb += p;
    if (b < m) {
      /* Initialize for next segment */
      for (i = r; i <= p; i++)
        for (ii = 0; ii < nd; ii++) {
          newP[(nb+i)*nd+ii] = P[(b-p+i)*nd+ii];
	  //printf("Initializing element %d to %f\n",(nb+i)*nd+ii,newP[(nb+i)*nd+ii]);
	}
      a = b;
      b++;
    }
  }

  free(alfa);
}


/* curve_knot_remove */
/*
Refine curve knot vector.

Input:

- p: degree of the B-spline
- P: control points P(nc,nd)
- nc: number of control points = n+1
- nd: dimension of the points (3 or 4)
- U: knot sequence: U[0] .. U[m]   m = n+p+1 = nc+p
- nk: number of knot values = m+1
- u: knot value to remove: U[0] <= u <= U[m]
- num: number of times to remove u
- r: index of last knot of value u
- s: multiplicity of knot value u
- tol: allowable tolerance for deviation of the curve. See NURBS book, p. 185

Output:
- t: actual number of times that u was removed
P and U are replaced with the new control points and knot vector

Modified algorithm A5.8 from 'The NURBS Book' pg185.
*/
static int curve_knot_remove(double *P, int nc, int nd, double *U, int nk, double u, int num, int r, int s, double tol)
{
  int n,m,p,ord,fout,last,first,t,off,i,j,ii,jj,k,kk,remflag;
  double alfi,alfj;

  n = nc - 1;
  m = nk - 1;
  p = m - n - 1;

  double *temp = (double*) malloc((2*p+1)*nd*sizeof(double));
  double *xtemp = (double*) malloc(nd*sizeof(double));


  /* printf("Knots: "); */
  /* for (i=0; i<nk; ++i) printf("%f, ",U[i]); */
  /* printf("\n"); */
  /* printf("Remove knot value %f, index %d, multiplicity %d\n",u,r,s); */
  /* r = find_last_occurrence(U,u); */
  /* s = find_multiplicity(U,u,r); */
  /* printf("Remove knot value %f, index %d, multiplicity %d\n",u,r,s); */

  ord = p+1;
  fout = (2*r-s-p)/2;  /* First control point out */
  last = r-s;
  first = r-p;
  for (t=0; t<num; t++) {
    /* This loop is Eq. (5.28) */
    off = first-1; /* Diff in index between temp and P */
    for (k=0; k<nd; ++k) temp[0*nd+k] = P[off*nd+k];
    for (k=0; k<nd; ++k) temp[(last+1-off)*nd+k] = P[(last+1)*nd+k];
    i = first;
    j = last;
    ii = 1;
    jj = last-off;
    remflag = 0;
    while (j-i > t) {
      /* Compute new control points for one removal step */
      alfi = (u-U[i])/(U[i+ord+t]-U[i]);
      alfj = (u-U[j-t])/(U[j+ord]-U[j-t]);
      for (k=0; k<nd; ++k) temp[ii*nd+k] = (P[i*nd+k]-(1.0-alfi)*temp[(ii-1)*nd+k])/alfi;
      for (k=0; k<nd; ++k) temp[jj*nd+k] = (P[j*nd+k]-alfj*temp[(jj+1)*nd+k])/(1.0-alfj);
      ++i; ++ii;
      --j; --jj;
    }
    /* Check if knot removable */
    if (j-i < t) {
      if (distance4d(temp+(ii-1)*nd,temp+(jj+1)*nd,nd) <= tol)
    	remflag = 1;
      }
    else {
      alfi = (u-U[i])/(U[i+ord+t]-U[i]);
      for (k=0; k<nd; ++k) xtemp[k] = alfi*temp[(ii+t+1)*nd+k] + (1.0-alfi)*temp[(ii-1)*nd+k];
      if (distance4d(P+i*nd,xtemp,nd) <= tol)
	    remflag = 1;
    }
    if (remflag == 0) {
      /* Cannot remove any more knots */
      /* Get out of for-loop */
      break;
    } else {
      /* Succesful removal. Save new control points */
      i = first;
      j = last;
      while (j-i > t) {
	    for (k=0; k<nd; ++k) P[i*nd+k] = temp[(i-off)*nd+k];
	    for (k=0; k<nd; ++k) P[j*nd+k] = temp[(j-off)*nd+k];
	    ++i;
	    --j;
      }
    }
    --first;
    ++last;
  }
  if (t>0) {
    /* Shift knots */
    for (k=r+1; k<= m; ++k) U[k-t] = U[k];
    /* Pj thru Pi will be overwritten */
    j = fout;
    i = j;
    for (k=1; k<t; ++k) {
      if (k % 2 == 1)
        ++i;
      else
        --j;
    }
    for (k=i+1; k<=n; ++k) { /* Shift */
      for (kk=0; kk<nd; ++kk) P[j*nd+kk] = P[k*nd+kk];
      ++j;
    }
  }

  free(temp);
  free(xtemp);

  return t;
}


/* curve_degree_elevate */
/*
Degree elevate a curve t times.

Input:

- P: control points P(nc,nd)
- nc: number of control points = n+1
- nd: dimension of the points (3 or 4)
- U: knot sequence: U[0] .. U[m]   m = n+p+1 = nc+p
- nk: number of knot values = m+1
- t: degree elevation
- Pw: work space for new control points:
- Uw: work space for new knots

Output:
- Pw: new control points Pw(nq,nd)
- Uw: new knot sequence: Uw[0] .. Uw[mh]   mh = nh+p+t+1 = nq+p+t
- nq: number of new control points = nh+1
- nu: number of new knots = mh+1

Modified algorithm A5.9 from 'The NURBS Book' pg206.
*/
static void curve_degree_elevate(double *P, int nc, int nd, double *U, int nk, int t, double *Pw, double* Uw, int *nq, int *nu)
{
  int n,m,p,mh,ph,ph2,i,j,mpi,kind,r,a,b,cind,kk,oldr,mul,lbz,rbz,k,save,s,first,last,tr,kj;
  double inv,ua,ub,den,alf,bet,gam,numer;

  n = nc - 1;
  m = nk - 1;
  p = m - n - 1;

  ph = p+t;
  ph2 = ph/2;

  /* Create local storage */
  double **bezalfs = newmatrix(ph+1,p+1);
  double *bpts = (double *) malloc((p+1)*nd*sizeof(double));
  double *ebpts = (double *) malloc((ph+1)*nd*sizeof(double));
  double *nbpts = (double *) malloc((p-1)*nd*sizeof(double));
  double *alfs = (double *) malloc((p-1)*sizeof(double));

  /* Compute Bezier degree elevation coefficients */
  //printf("Bezier degree elevation coefficients\n");
  // Added for testing
  for (i=0;i<=ph;++i) for (j=0;j<=p;++j) bezalfs[i][j] = 0.0;
  bezalfs[0][0] = bezalfs[ph][p] = 1.0;

  for (i=1; i<=ph2; ++i) {
    inv = 1.0 / _binomial(ph,i);
    mpi = min(p,i);

    for (j=max(0,i-t); j<=mpi; ++j)
      bezalfs[i][j] = inv * _binomial(p,j) * _binomial(t,i-j);
  }
  for (i=ph2+1; i<=ph-1; ++i) {
    mpi = min(p, i);
    for (j=max(0,i-t); j<=mpi; ++j)
      bezalfs[i][j] = bezalfs[ph-i][p-j];
  }
//  for (i=0; i<=ph;++i)
//    print_mat(bezalfs[i],1,p+1);

//  printf("U\n");
//  print_mat(U,1,nk);
  mh = ph;
  kind = ph+1;
  r = -1;
  a = p;
  b = p+1;
  cind = 1;
  ua = U[0];
  for (kk=0; kk<nd; ++kk) Pw[0*nd+kk] = P[0*nd+kk];
  for (i=0; i<=ph; ++i) Uw[i] = ua;

  /* Initialize first bezier segment */
  for (i=0; i<=p; ++i)
    for (kk=0; kk<nd; ++kk) bpts[i*nd+kk] = P[i*nd+kk];

  /* Big loop thru knot vector */
  while (b < m) {
//    printf("Big loop b = %d < m = %d\n",b,m);
    i = b;
    while (b < m && U[b] == U[b+1]) ++b;

    mul = b-i+1;
    mh += mul+t;
    ub = U[b];
    oldr = r;
    r = p-mul;

    /* Insert knot u(b) r times */
//    printf("Insert knot %f %d times (oldr=%d)\n",ub,r,oldr);
    if (oldr > 0)
      lbz = (oldr+2)/2;
    else
      lbz = 1;

    if (r > 0)
      rbz = ph-(r+1)/2;
    else
      rbz = ph;

    if (r > 0) {
      /* Insert knot to get bezier segment */
//      printf("Insert knot to get bezier segment of degree %d mul %d\n",p,mul);
      numer = ub-ua;
//      printf("numer = %f\n",numer);
      for (k=p; k>mul; --k) {
        alfs[k-mul-1] = numer / (U[a+k]-ua);
//        printf("alfs %d = %f\n",k-mul-1,alfs[k-mul-1]);
      }
//      printf("alfs = \n");
//      print_mat(alfs,1,2);

      for (j=1; j<=r; ++j) {
        save = r-j;
        s = mul+j;
        for (k=p; k>=s; --k)
          for (kk=0; kk<nd; ++kk)
            bpts[k*nd+kk] = alfs[k-s]*bpts[k*nd+kk]+(1.0-alfs[k-s])*bpts[(k-1)*nd+kk];
        for (kk=0; kk<nd; ++kk)
          nbpts[save*nd+kk] = bpts[p*nd+kk];
      }
//      printf("bpts =\n");
//      print_mat(bpts,p,nd);
    }

    /* Degree elevate bezier */
//    printf("Degree elevate bezier %d..%d\n",lbz,ph);
    for (i=lbz; i<=ph; ++i) {
      /* Only points lbz..ph are used below */
      for (kk=0; kk<nd; ++kk) ebpts[i*nd+kk] = 0.0;
      mpi = min(p,i);
      for (j=max(0,i-t); j<=mpi; ++j)
        for (kk=0; kk<nd; ++kk)
          ebpts[i*nd+kk] += bezalfs[i][j]*bpts[j*nd+kk];
    }

    if (oldr > 1) {
      /* Must remove knot u=U[a] oldr times */
      first = kind-2;
      last = kind;
      den = ub-ua;
      bet = (ub-Uw[kind-1]) / den;

      /* Knot removal loop */
      for (tr=1; tr<oldr; ++tr) {
        i = first;
        j = last;
        kj = j-kind+1;
        while (j-i > tr) {
          /* Loop and compute the new control points for one removal step */
          if (i < cind) {
            alf = (ub-Uw[i])/(ua-Uw[i]);
  	    for (kk=0; kk<nd; ++kk)
              Pw[i*nd+kk] = alf * Pw[i*nd+kk] + (1.0-alf) * Pw[(i-1)*nd+kk];
          }
          if (j >= lbz) {
            if (j-tr <= kind-ph+oldr) {
              gam = (ub-Uw[j-tr]) / den;
  	      for (kk=0; kk<nd; ++kk)
                ebpts[kj*nd+kk] = gam*ebpts[kj*nd+kk] + (1.0-gam)*ebpts[(kj+1)*nd+kk];
            } else {
  	      for (kk=0; kk<nd; ++kk)
                ebpts[kj*nd+kk] = bet*ebpts[kj*nd+kk] + (1.0-bet)*ebpts[(kj+1)*nd+kk];
            }
          }
          i++;
          j--;
          kj--;
        }
        first--;
        last++;
      }
    }

    if (a != p)
      /* Load the knot ua */
      for (i=0; i<ph-oldr; ++i) {
        Uw[kind] = ua;
        ++kind;
      }

    /* Load ctrl pts into Pw */
    for (j=lbz; j<=rbz; ++j) {
      for (kk=0; kk<nd; ++kk)
        Pw[cind*nd+kk] = ebpts[j*nd+kk];
      ++cind;
    }

    if (b < m) {
      /* Set up for next pass thru loop */
      for (j=0; j<r; ++j)
        for (kk=0; kk<nd; ++kk)
          bpts[j*nd+kk] = nbpts[j*nd+kk];
      for (j=r; j<=p; ++j)
        for (kk=0; kk<nd; ++kk)
          bpts[j*nd+kk] = P[(b-p+j)*nd+kk];
      a = b;
      ++b;
      ua = ub;
    } else {
      /* End knot */
      for (i=0; i<=ph; ++i)
        Uw[kind+i] = ub;
    }

  } /* end of big while loop */

  *nq = mh-ph;
  *nu = kind+ph+1;
//  print_mat(Pw,*nq,nd);
//  print_mat(Uw,1,*nu);

//  printf("Free the work spaces\n");
  freematrix(bezalfs);
  free(bpts);
  free(ebpts);
  free(nbpts);
  free(alfs);
}


/* bezier_degree_reduce */
/*
Degree reduce a Bezier curve.

Input:

- Q: control points Q(nc,nd)
- nc: number of control points = p+1
- nd: dimension of the points (3 or 4)

Output:
- P: new control points P(nc-1,nd)
- maxerr: error bound for the degree reduction

Based on eqs. 5.41 .. 5.46 from 'The NURBS Book' pg220.
*/
static void bezier_degree_reduce(double* Q, int nc, int nd, double* P, double *maxerr)
{
  int p, r, i, kk;
  double PrR[4];

  p = nc - 1;
  r = (p-1) / 2;

  /* Degree elevation coeffs for p-1 -> p */
  double *alfs = (double *) malloc(p*sizeof(double));
  for (i=0; i<p; ++i) alfs[i] = (double) i / p;
  printf("Bezier alfs; p = %d; r = %d\n",p,r);
  print_mat(alfs,1,p);
  printf("Input Q\n");
  print_mat(Q,nc,nd);
  for (kk=0; kk<nd; ++kk)
    P[0*nd+kk] = Q[0*nd+kk];
  for (i=0; i<=r; ++i)
    for (kk=0; kk<nd; ++kk)
      P[i*nd+kk] = ( Q[i*nd+kk] - alfs[i]*P[(i-1)*nd+kk] ) / (1.0-alfs[i]);
  for (kk=0; kk<nd; ++kk)
    P[(p-1)*nd+kk] = Q[p*nd+kk];
  for (i=p-2; i>r; --i)
    for (kk=0; kk<nd; ++kk)
      P[i*nd+kk] = ( Q[(i+1)*nd+kk] - (1-alfs[i+1])*P[(i+1)*nd+kk] ) / alfs[i+1];
  if (p % 2 == 1) {
    for (kk=0; kk<nd; ++kk) {
      PrR[kk] = ( Q[(r+1)*nd+kk] - (1-alfs[r+1])*P[(r+1)*nd+kk] ) / alfs[r+1];
    }
    //Err = 0.5 * (1.0-alfs[r]) * length( P[r] - PrR );
    for (kk=0; kk<nd; ++kk) {
      P[r*nd+kk] = 0.5 * (P[r*nd+kk] + PrR[kk]);
    }
  } else {
      //Err = length(Q[r+1]-0.5*(P[r]+P[r+1]));
  }
  printf("Output P\n");
  print_mat(P,p,nd);

}

/* curve_degree_reduce */
/*
Degree reduce a curve.

Input:

- P: control points P(nc,nd)
- nc: number of control points = n+1
- nd: dimension of the points (3 or 4)
- U: knot sequence: U[0] .. U[m]   m = n+p+1 = nc+p
- nk: number of knot values = m+1
- Pw: work space for new control points:
- Uw: work space for new knots

Output:
- Pw: new control points Pw(nq,nd)
- Uw: new knot sequence: Uw[0] .. Uw[mh]   mh = nh+p+t+1 = nq+p+t
- nq: number of new control points = nh+1
- nu: number of new knots = mh+1

Modified algorithm A5.9 from 'The NURBS Book' pg206.
*/
static void curve_degree_reduce(double *P, int nc, int nd, double *U, int nk, double *Pw, double* Uw, int *nq, int *nu)
{
  int n,m,p,mh,ph,i,j,kind,r,a,b,cind,kk,oldr,mul,lbz,k,save,s,first,last,kj;
  double ua,ub,alfa,beta,numer,maxerr;

  n = nc - 1;
  m = nk - 1;
  p = m - n - 1;

  ph = p-1;

  /* Create local storage */
  double *bpts = (double *) malloc((p+1)*nd*sizeof(double));
  double *rbpts = (double *) malloc(p*nd*sizeof(double));
  double *nbpts = (double *) malloc((p-1)*nd*sizeof(double));
  double *alfs = (double *) malloc((p-1)*sizeof(double));
  double *err = (double *) malloc(m*sizeof(double));

  /* Initialize some variables */
  mh = ph;
  kind = ph+1;
  r = -1;
  a = p;
  b = p+1;
  cind = 1;
  mul = p;
  ua = U[0];
  for (kk=0; kk<nd; ++kk) Pw[0*nd+kk] = P[0*nd+kk];
  for (i=0; i<=ph; ++i) Uw[i] = ua;

  /* Initialize first bezier segment */
  for (i=0; i<=p; ++i)
    for (kk=0; kk<nd; ++kk) bpts[i*nd+kk] = P[i*nd+kk];
  /* Initialize error vector */
  for (i=0; i<m; ++i) err[i] = 0.0;

  /* Big loop thru knot vector */
  while (b < m) {
//    printf("Big loop b = %d < m = %d\n",b,m);
    /* Compute knot multiplicity */
    i = b;
    while (b < m && U[b] == U[b+1]) ++b;

    mul = b-i+1;
    mh += mul+1;
    ub = U[b];
    oldr = r;
    r = p-mul;

    /* Insert knot u(b) r times */
    if (oldr > 0)
      lbz = (oldr+2)/2;
    else
      lbz = 1;

    if (r > 0) {
      /* Insert knot to get bezier segment */
//      printf("Insert knot to get bezier segment of degree %d mul %d\n",p,mul);
      numer = ub-ua;
      for (k=p; k>mul; --k) {
        alfs[k-mul-1] = numer / (U[a+k]-ua);
      }

      for (j=1; j<=r; ++j) {
        save = r-j;
        s = mul+j;
        for (k=p; k>=s; --k)
          for (kk=0; kk<nd; ++kk)
            bpts[k*nd+kk] = alfs[k-s]*bpts[k*nd+kk]+(1.0-alfs[k-s])*bpts[(k-1)*nd+kk];
        for (kk=0; kk<nd; ++kk)
          nbpts[save*nd+kk] = bpts[p*nd+kk];
      }
      printf("bpts =\n");
      print_mat(bpts,p,nd);
    }

    /* Degree reduce bezier */
    bezier_degree_reduce(bpts,p+1,nd,rbpts,&maxerr);


    if (oldr > 1) {
      /* Remove knot u=U[a] oldr times */
      first = kind;
      last = kind;

      /* Knot removal loop */
      for (k=0; k<oldr; ++k) {
        i = first;
        j = last;
        kj = j-kind;
        while (j-i > k) {
          /* Loop and compute the new control points for one removal step */
          alfa = (ua-Uw[i-1]) / (U[b]-Uw[i-1]);
          beta = (ua-Uw[j-k-1]) / (U[b]-Uw[j-k-1]);
          for (kk=0; kk<nd; ++kk)
            Pw[(i-1)*nd+kk] = (Pw[(i-1)*nd+kk] - (1.0-alfa) * Pw[(i-2)*nd+kk]) / alfa;
  	      for (kk=0; kk<nd; ++kk)
            rbpts[kj*nd+kk] = (rbpts[kj*nd+kk] - beta * rbpts[(kj+1)*nd+kk]) / (1.0-beta);
          i++;
          j--;
          kj--;
        }
        first--;
        last++;
      }
      cind = i-1;
    }

    if (a != p)
      /* Load the knot ua */
      for (i=0; i<ph-oldr; ++i) {
        Uw[kind] = ua;
        ++kind;
      }

    /* Load ctrl pts into Pw */
    for (i=lbz; i<=ph-oldr; ++i) {
      for (kk=0; kk<nd; ++kk)
        Pw[cind*nd+kk] = rbpts[i*nd+kk];
      ++cind;
    }

    if (b < m) {
      /* Set up for next pass thru loop */
      for (i=0; i<r; ++i)
        for (kk=0; kk<nd; ++kk)
          bpts[i*nd+kk] = nbpts[i*nd+kk];
      for (i=r; i<=p; ++i)
        for (kk=0; kk<nd; ++kk)
          bpts[i*nd+kk] = P[(b-p+i)*nd+kk];
      a = b;
      ++b;
      ua = ub;
    } else {
      /* End knot */
      for (i=0; i<=ph; ++i) {
        Uw[kind] = ub;
	++kind;
      }
    }

  } /* end of big while loop */

  //  *nq = mh-ph;
  //*nu = kind+ph+1;
  *nu = kind;
  *nq = *nu - ph - 1;

  printf("Return arrays\n");
  print_mat(Pw,*nq,nd);
  print_mat(Uw,1,*nu);

  printf("Free the work spaces\n");
  free(bpts);
  free(rbpts);
  free(nbpts);
  free(alfs);
  free(err);
}




/* curve_global_interp_mat */
/*
Compute the global curve interpolation matrix.

Input:

- p: degree of the B-spline
- Q: points through which the curve should pass (nc,nd)
- nc: number of points = number of control points = n+1
- nd: dimension of the points (3 or 4)
- u: parameter values at the points (nc)
strategies:
  0 : equally spaced (not recommended)
  1 : chord length
  2 : centripetal (recommended)

Output:
- P: control points P(nc,nd)
- U: knot sequence: U[0] .. U[m]   m = n+p+1 = nc+p
- A: coefficient matrix (nc,nc)

Modified algorithm A9.1 from 'The NURBS Book' pg369.
*/

static void curve_global_interp_mat(int p, double *Q, int nc, int nd, double *u, double *U, double *A)
{
  int n,m,i,j,s;

  n = nc - 1;
  m = nc + p;

  /* Compute the knot vector U by averaging (9.8) */
  for (i=0; i<m-p; ++i) U[i] = 0.0;
  for (i=m-p; i<=m; ++i) U[i] = 1.0;
  for (j=1; j<=n-p; ++j) {
    for (i=j; i<j+p; ++i) U[j+p] += u[i];
    U[j+p] /= p;
  }
  /* Set up coefficient matrix A */
  for (i=0; i<nc*nc; ++i) A[i] = 0.0;
  for (i=0; i<nc; ++i) {
    s = find_span(U,u[i],p,nc-1);
    basis_funs(U,u[i],p,s,A+i*nc+s-p); /* i-th row */
  }
}


/********************************************************/
/*********************** SURFACE ************************/
/********************************************************/



/* surface_points */
/*
Compute points on a B-spline surface.

Input:

- P: control points P(ns,nt,nd)
- ns,nt: number of control points
- nd: dimension of the points (3 or 4)
- U: knot sequence: U[0] .. U[m]
- nU: number of knot values U = m+1
- V: knot sequence: V[0] .. V[n]
- nV: number of knot values V = n+1
- u: parametric values (nu,2): U[0] <= ui[0] <= U[m], V[0] <= ui[1] <= V[m]
- nu: number of parametric values

Output:
- pnt: (nu,nd) points on the B-spline

Modified algorithm A3.5 from 'The NURBS Book' pg103.
*/
static void surface_points(double *P, int ns, int nt, int nd, double *U, int nU, double *V, int nV, double *u, int nu, double *pnt)
{
  int i, j, p, q, r, su, sv, iu, iv;
  double S;

  /* degrees of the spline */
  p = nU - ns - 1;
  q = nV - nt - 1;

  /* space for the basis functions */
  double *Nu = (double*) malloc((p+1)*sizeof(double));
  double *Nv = (double*) malloc((q+1)*sizeof(double));

  /* for each parametric point j */
  for (j=0; j<nu; ++j) {

    /* find the span index of u[j] */
    su = find_span(U,u[2*j],p,ns-1);
    basis_funs(U,u[2*j],p,su,Nu);

    /* find the span index of v[j] */
    sv = find_span(V,u[2*j+1],q,nt-1);
    basis_funs(V,u[2*j+1],q,sv,Nv);

    iu = su-p;
    iv = sv-q;
    for (i=0; i<nd; ++i) {
      S = 0.0;
      for (r=0; r<=p; ++r) {
	S += Nu[r] * dotprod(Nv,1,P+((iu+r)*nt+iv)*nd+i,nd,q+1);
      }
      pnt[j*nd+i] = S;
    }
  }
  free(Nu);
  free(Nv);
}


/* surface_derivs */
/*
Compute derivatives of a B-spline surface.

Input:

- mu,mv: number of derivatives to compute in u,v direction
- P: control points P(ns,nt,nd)
- ns,nt: number of control points
- nd: dimension of the points (3 or 4)
- U: knot sequence: U[0] .. U[m]
- nU: number of knot values U = m+1
- V: knot sequence: V[0] .. V[n]
- nV: number of knot values V = n+1
- u: parametric values (nu,2): U[0] <= ui[0] <= U[m], V[0] <= ui[1] <= V[m]
- nu: number of parametric values

Output:

- pnt: (mu+1,mv+1,nu,nd) points and derivatives on the B-spline surface

Modified algorithm A3.6 from 'The NURBS Book' pg111.
*/
static void surface_derivs(int mu, int mv, double *P,int ns, int nt, int nd, double *U, int nU, double *V, int nV, double *u, int nu, double *pnt)
{
  int p,q,du,dv,su,sv,i,j,k,l,iu,iv,r;
  double S, *qnt;

  /* degrees of the spline */
  p = nU - ns - 1;
  q = nV - nt - 1;

  /* number of nonzero derivatives to compute */
  du = min(p,mu);
  dv = min(q,mv);

  /* space for the basis functions and derivatives */
  double *Nu = (double*) malloc((du+1)*(p+1)*sizeof(double));
  double *Nv = (double*) malloc((dv+1)*(q+1)*sizeof(double));

  /* clear everything */
  for (i=0; i<(mu+1)*(mv+1)*nu*nd; ++i) pnt[i] = 0;

  /* for each parametric point j */
  for (j=0; j<nu; ++j) {

    /* find the span index of u[j] */
    su = find_span(U,u[2*j],p,ns-1);
    basis_derivs(U,u[2*j],p,su,du,Nu);
    //printf("Nu (%d,%d)\n",du+1,p+1);
    //print_mat(Nu,du+1,p+1);

    /* find the span index of v[j] */
    sv = find_span(V,u[2*j+1],q,nt-1);
    basis_derivs(V,u[2*j+1],q,sv,dv,Nv);
    //printf("Nv (%d,%d)\n",du+1,p+1);
    //print_mat(Nv,dv+1,q+1);

    /* for each nonzero derivative */
    for (k=0; k<=du; ++k) {
      for (l=0; l<=dv; ++l) {
	qnt = pnt + (k*(mv+1) + l) *nu*nd;

	iu = su-p;
	iv = sv-q;
	//printf("k=%d, l=%d\n",k,l);
	//printf("offset %d\n", (k*(mv+1) + l) *nu*nd);
	for (i=0; i<nd; ++i) {
	  S = 0.0;
	  for (r=0; r<=p; ++r) {
	    S += Nu[k*(p+1)+r] * dotprod(Nv+l*(q+1),1,P+((iu+r)*nt+iv)*nd+i,nd,q+1);
	  }
	  //printf("S = %f\n",S);
	  qnt[j*nd+i] = S;
	}
	//print_mat(pnt,(mu+1)*(mv+1)*nu,nd);
      }
    }
  }
  free(Nu);
  free(Nv);
}


/* surfaceDecompose */
/*
Decompose a Nurbs surface in Bezier patches.

Input:

- p: degree of the B-spline
- P: control points P(nc,nd)
- nc: number of control points = n+1
- nd: dimension of the points (3 or 4)
- U: knot sequence: U[0] .. U[m]   m = n+p+1 = nc+p

Output:

- newP: (nb*p+1,nd) new control points
- nb: number of Bezier segments

Modified algorithm A5.7 from 'The NURBS Book' pg177.
*/


/* static void surfaceDecompose(double *P, int nc, int nd, double *U, int nk, double *newP) */
/* { */
/*   int i, j, k, p, s, m, r, a, b, mult, n, nb, ii, save; */
/*   double numer, alpha, *alfa; */

/*   n = nc - 1; */
/*   m = nk - 1; */
/*   p = m - n - 1; */

/*   alfa = (double *) malloc(p*sizeof(double)); */

/*   a = p; */
/*   b = p+1; */
/*   nb = 0; */

/*   /\* First bezier segment *\/ */
/*   for (i = 0; i < (p+1)*nd; i++) newP[i] = P[i]; */

/*   // Loop through knot vector *\/ */
/*   while (b < m) { */
/*     i = b; */
/*     while (b < m && U[b] == U[b+1]) b++; */
/*     mult = b-i+1; */

/*     if (mult < p) { */
/*       printf("mult at %d is %d < %d\n",b,mult,p); */
/*       /\* compute alfas *\/ */
/*       numer = U[b] - U[a]; */
/*       for (k = p; k > mult; k--) */
/*         alfa[k-mult-1] = numer / (U[a+k]-U[a]); */

/*       /\* Insert knot U[b] r times *\/ */
/*       r = p - mult; */
/*       for (j = 1; j <= r; j++) { */
/*         save = r - j; */
/*         s = mult + j; 	/\* Number of new points *\/ */
/*         for (k = p; k >= s; k--) { */
/* 	  alpha = alfa[k-s]; */
/* 	  printf("alpha = %f\n",alpha); */
/*           for (ii = 0; ii < nd; ii++) { */
/*             newP[(nb+k)*nd+ii] = alpha*newP[(nb+k)*nd+ii] + (1.0-alpha)*newP[(nb+k-1)*nd+ii]; */
/* 	    printf("Setting element %d to %f\n",(nb+k)*nd+ii,newP[(nb+k)*nd+ii]); */
/* 	  } */
/* 	} */
/* 	if (b < m) */
/* 	  /\* Control point of next segment *\/ */
/* 	  for (ii = 0; ii < nd; ii++) { */
/* 	    newP[(nb+p+save)*nd+ii] = newP[(nb+p)*nd+ii]; */
/* 	    printf("Copying element %d to %f\n",(nb+p+save)*nd+ii,newP[(nb+p+save)*nd+ii]); */
/* 	  } */
/*       } */
/*     } */
/*     /\* Bezier segment completed *\/ */
/*     nb += p; */
/*     if (b < m) { */
/*       /\* Initialize for next segment *\/ */
/*       for (i = r; i <= p; i++) */
/*         for (ii = 0; ii < nd; ii++) { */
/*           newP[(nb+i)*nd+ii] = P[(b-p+i)*nd+ii]; */
/* 	  printf("Initializing element %d to %f\n",(nb+i)*nd+ii,newP[(nb+i)*nd+ii]); */
/* 	} */
/*       a = b; */
/*       b++; */
/*     } */
/*   } */

/*   free(alfa); */
/* } */




/********************************************************/
/****** EXPORTED FUNCTIONS (callable from Python ********/
/********************************************************/


static char binomial_doc[] =
"Computes the binomial coefficient.\n\
\n\
 ( n )      n!\n\
 (   ) = --------\n\
 ( k )   k!(n-k)!\n\
\n\
 Algorithm from 'Numerical Recipes in C, 2nd Edition' pg215.\n\
";

static PyObject * binomial(PyObject *self, PyObject *args)
{
  int n, k;
  double ret;
  if(!PyArg_ParseTuple(args, "ii", &n, &k))
    return NULL;
  ret = _binomial(n, k);
  return Py_BuildValue("d",ret);
}


static char horner_doc[] =
"Compute points on a power base curve using Horner's rule.\n\
\n\
Input:\n\
- a: double(nd,n+1), nd-dimensional coefficients of the polynom of\n\
     degree n, starting from lowest degree\n\
- u: double(nu), parametric values where the polynom is evaluated\n\
\n\
Returns: double(nu,nd), nu nd-dimensonal points\n\
\n\
Extended algorithm A1.1 from 'The NURBS Book' p7.\n\
";

static PyObject * horner(PyObject *self, PyObject *args)
{
  int n, nd, nu;
  npy_intp *a_dim, *u_dim, dim[2];
  double *a, *u, *pnt;
  PyObject *arg1, *arg2;
  PyObject *arr1=NULL, *arr2=NULL, *ret=NULL;

  if (!PyArg_ParseTuple(args, "OO", &arg1, &arg2))
    return NULL;
  arr1 = PyArray_FROM_OTF(arg1, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr1 == NULL)
    return NULL;
  arr2 = PyArray_FROM_OTF(arg2, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr2 == NULL)
    goto fail;

  /* We suppose the dimensions are correct*/
  a_dim = PYARRAY_DIMS(arr1);
  u_dim = PYARRAY_DIMS(arr2);
  n = a_dim[1];
  nd = a_dim[0];
  nu = u_dim[0];
  a = (double *)PYARRAY_DATA(arr1);
  u = (double *)PYARRAY_DATA(arr2);

  /* Create the return array */
  dim[0] = nu;
  dim[1] = nd;
  ret = PyArray_SimpleNew(2,dim, NPY_DOUBLE);
  pnt = (double *)PYARRAY_DATA(ret);

  /* Compute */
  int i,j;
  for (i=0; i<nu; ++i)
    for (j=0; j<nd; ++j)
      *pnt++ = _horner(a+n*i, n-1, *u++);
  //printf("pnt(%d,%d)\n",nu,nd);
  //print_mat(pnt,nu,nd);

  /* Clean up and return */
  Py_DECREF(arr1);
  Py_DECREF(arr2);
  return ret;

 fail:
  printf("error cleanup and return\n");
  Py_XDECREF(arr1);
  Py_XDECREF(arr2);
  return NULL;
}


static char bernstein_doc[] =
"Compute the value of a Bernstein polynomial.\n\
\n\
Input:\n\
- i: int, index of the polynomial\n\
- n: int, degree of the polynomial\n\
- u: double, parametric value where the polynomial is evaluated\n\
\n\
Returns:\n\
  The value of the Bernstein polynomial B(i,n) at parameter value u.\n\
\n\
Algorithm A1.2 from 'The NURBS Book' p20.\n\
";

static PyObject * bernstein(PyObject *self, PyObject *args)
{
  int n, k;
  double u, ret;
  if(!PyArg_ParseTuple(args, "iid", &n, &k, &u))
    return NULL;
  ret = _bernstein(n,k,u);
  return Py_BuildValue("d",ret);
}


static char allBernstein_doc[] =
"Compute the value of all n-th degree Bernstein polynomials.\n\
\n\
Input:\n\
- n: int, degree of the polynomials\n\
- u: double, parametric value where the polynomials are evaluated\n\
\n\
Returns:\n\
double(n+1), the value of all n-th degree Bernstein polynomials B(i,n)\n\
at parameter value u.\n\
\n\
Algorithm A1.3 from The NURBS Book.\n\
";

static PyObject * allBernstein(PyObject *self, PyObject *args)
{
  int n;
  npy_intp dim[1];
  double u, *B;
  PyObject *ret=NULL;

  if (!PyArg_ParseTuple(args, "id", &n, &u))
    return NULL;

  /* Create the return array */
  dim[0] = n+1;
  ret = PyArray_SimpleNew(1,dim, NPY_DOUBLE);
  B = (double *)PYARRAY_DATA(ret);

  /* Compute */
  all_bernstein(n,u,B);

  /* Return */
  return ret;
}


static char curvePoints_doc[] =
"Compute a point on a B-spline curve.\n\
\n\
Input:\n\
\n\
- p: degree of the B-spline\n\
- P: control points P(nc,nd)\n\
- nc: number of control points\n\
- nd: dimension of the points (3 or 4)\n\
- U: knot sequence: U[0] .. U[m]\n\
- u: parametric values: U[0] <= ui <= U[m]\n\
- nu: number of parametric values\n\
\n\
Output:\n\
- pnt: (nu,nd) points on the B-spline\n\
\n\
Modified algorithm A3.1 from 'The NURBS Book' pg82.\n\
";

static PyObject * curvePoints(PyObject *self, PyObject *args)
{
  int nd, nc, nk, nu;
  npy_intp *P_dim, *U_dim, *u_dim, dim[2];
  double *P, *U, *u, *pnt;
  PyObject *a1, *a2, *a3;
  PyObject *arr1=NULL, *arr2=NULL, *arr3=NULL, *ret=NULL;

  if (!PyArg_ParseTuple(args, "OOO", &a1, &a2, &a3))
    return NULL;
  arr1 = PyArray_FROM_OTF(a1, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr1 == NULL)
    return NULL;
  arr2 = PyArray_FROM_OTF(a2, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr2 == NULL)
    goto fail;
  arr3 = PyArray_FROM_OTF(a3, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr3 == NULL)
    goto fail;

  P_dim = PYARRAY_DIMS(arr1);
  U_dim = PYARRAY_DIMS(arr2);
  u_dim = PYARRAY_DIMS(arr3);
  nc = P_dim[0];
  nd = P_dim[1];
  nk = U_dim[0];
  nu = u_dim[0];
  P = (double *)PYARRAY_DATA(arr1);
  U = (double *)PYARRAY_DATA(arr2);
  u = (double *)PYARRAY_DATA(arr3);

  /* Create the return array */
  dim[0] = nu;
  dim[1] = nd;
  ret = PyArray_SimpleNew(2,dim, NPY_DOUBLE);
  pnt = (double *)PYARRAY_DATA(ret);

  /* Compute */
  curve_points(P, nc, nd, U, nk, u, nu, pnt);

  /* Clean up and return */
  Py_DECREF(arr1);
  Py_DECREF(arr2);
  Py_DECREF(arr3);
  return ret;

 fail:
  //printf("error cleanup and return\n");
  Py_XDECREF(arr1);
  Py_XDECREF(arr2);
  Py_XDECREF(arr3);
  return NULL;
}


static char curveDerivs_doc[] =
"Compute derivatives of a B-spline curve.\n\
\n\
Input:\n\
\n\
- p: degree of the B-spline\n\
- P: control points P(nc,nd)\n\
- nc: number of control points\n\
- nd: dimension of the points (3 or 4)\n\
- U: knot sequence: U[0] .. U[m]\n\
- u: parametric values: U[0] <= ui <= U[m]\n\
- nu: number of parametric values\n\
- n: number of derivatives to compute\n\
\n\
Output:\n\
- pnt: (n+1,nu,nd) points and derivatives on the B-spline\n\
\n\
Modified algorithm A3.2 from 'The NURBS Book' pg93.\n\
";

static PyObject * curveDerivs(PyObject *self, PyObject *args)
{
  int nc, nd, nk, nu, n;
  npy_intp *P_dim, *U_dim, *u_dim, dim[3];
  double *P, *U, *u, *pnt;
  PyObject *a1, *a2, *a3;
  PyObject *arr1=NULL, *arr2=NULL, *arr3=NULL, *ret=NULL;

  if(!PyArg_ParseTuple(args, "OOOi", &a1, &a2, &a3, &n))
    return NULL;
  arr1 = PyArray_FROM_OTF(a1, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr1 == NULL)
    return NULL;
  arr2 = PyArray_FROM_OTF(a2, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr2 == NULL)
    goto fail;
  arr3 = PyArray_FROM_OTF(a3, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr3 == NULL)
    goto fail;

  P_dim = PYARRAY_DIMS(arr1);
  U_dim = PYARRAY_DIMS(arr2);
  u_dim = PYARRAY_DIMS(arr3);
  nc = P_dim[0];
  nd = P_dim[1];
  nk = U_dim[0];
  nu = u_dim[0];
  P = (double *)PYARRAY_DATA(arr1);
  U = (double *)PYARRAY_DATA(arr2);
  u = (double *)PYARRAY_DATA(arr3);

  /* Create the return array */
  dim[0] = n+1;
  dim[1] = nu;
  dim[2] = nd;
  ret = PyArray_SimpleNew(3,dim, NPY_DOUBLE);
  pnt = (double *)PYARRAY_DATA(ret);

  /* Compute */
  curve_derivs(n, P, nc, nd, U, nk, u, nu, pnt);

  /* Clean up and return */
  Py_DECREF(arr1);
  Py_DECREF(arr2);
  Py_DECREF(arr3);
  return ret;

 fail:
  Py_XDECREF(arr1);
  Py_XDECREF(arr2);
  Py_XDECREF(arr3);
  return NULL;
}


static char curveKnotRefine_doc[] =
"Refine curve knot vector.\n\
\n\
Input:\n\
\n\
- P: control points P(nc,nd)\n\
- U: knot sequence: U(nk) (nk = nc+p+1)\n\
- u: (nu) parametric values of new knots: U[0] <= u[i] <= U[m]\n\
\n\
Output:\n\
- newP: (nc+nu,nd) new control points\n\
- newU: (m+nu) new knot vector\n\
\n\
Modified algorithm A5.4 from 'The NURBS Book' pg164.\n\
";

static PyObject * curveKnotRefine(PyObject *self, PyObject *args)
{
  int nd, nc, nk, nu;
  npy_intp *P_dim, *U_dim, *u_dim, dim[2];
  double *P, *U, *u, *newP, *newU;
  PyObject *a1, *a2, *a3;
  PyObject *arr1=NULL, *arr2=NULL, *arr3=NULL, *ret1=NULL, *ret2=NULL;

  if(!PyArg_ParseTuple(args, "OOO", &a1, &a2, &a3))
    return NULL;
  arr1 = PyArray_FROM_OTF(a1, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr1 == NULL)
    return NULL;
  arr2 = PyArray_FROM_OTF(a2, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr2 == NULL)
    goto fail;
  arr3 = PyArray_FROM_OTF(a3, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr3 == NULL)
    goto fail;

  P_dim = PYARRAY_DIMS(arr1);
  U_dim = PYARRAY_DIMS(arr2);
  u_dim = PYARRAY_DIMS(arr3);
  nc = P_dim[0];
  nd = P_dim[1];
  nk = U_dim[0];
  nu = u_dim[0];
  P = (double *)PYARRAY_DATA(arr1);
  U = (double *)PYARRAY_DATA(arr2);
  u = (double *)PYARRAY_DATA(arr3);

  /* Create the return arrays */
  dim[0] = nc+nu;
  dim[1] = nd;
  ret1 = PyArray_SimpleNew(2,dim, NPY_DOUBLE);
  newP = (double *)PYARRAY_DATA(ret1);
  dim[0] = nk+nu;
  ret2 = PyArray_SimpleNew(1,dim, NPY_DOUBLE);
  newU = (double *)PYARRAY_DATA(ret2);

  /* Compute */
  curve_knot_refine(P, nc, nd, U, nk, u, nu, newP, newU);

  /* Clean up and return */
  Py_DECREF(arr1);
  Py_DECREF(arr2);
  Py_DECREF(arr3);
  return Py_BuildValue("(OO)", ret1, ret2);

 fail:
  Py_XDECREF(arr1);
  Py_XDECREF(arr2);
  Py_XDECREF(arr3);
  return NULL;
}


static char curveDecompose_doc[] =
"Decompose a Nurbs curve in Bezier segments.\n\
\n\
Input:\n\
\n\
- P: control points P(nc,nd)\n\
- nc: number of control points = n+1\n\
- nd: dimension of the points (3 or 4)\n\
- U: knot sequence U(nk) with nk = nc+p+1 = nc+p\n\
\n\
Returns:\n\
\n\
- newP: (nb*p+1,nd) new control points defining nb Bezier segments\n\
\n\
Modified algorithm A5.6 from 'The NURBS Book' pg173.\n\
";

static PyObject * curveDecompose(PyObject *self, PyObject *args)
{
  int nd, nc, nk;
  npy_intp *P_dim, *U_dim, dim[2];
  double *P, *U, *newP;
  PyObject *a1, *a2;
  PyObject *arr1=NULL, *arr2=NULL, *ret=NULL;

  if(!PyArg_ParseTuple(args, "OO", &a1, &a2))
    return NULL;
  arr1 = PyArray_FROM_OTF(a1, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr1 == NULL)
    return NULL;
  arr2 = PyArray_FROM_OTF(a2, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr2 == NULL)
    goto fail;

  P_dim = PYARRAY_DIMS(arr1);
  U_dim = PYARRAY_DIMS(arr2);
  nc = P_dim[0];
  nd = P_dim[1];
  nk = U_dim[0];
  P = (double *)PYARRAY_DATA(arr1);
  U = (double *)PYARRAY_DATA(arr2);

  /* Compute number of knots to insert */
  int count = 0;
  int m = nk - 1;
  int p = nk - nc - 1;
  int b = p + 1;
  int i,mult;
  while (b < m) {
    i = b;
    while (b < m && U[b] == U[b+1]) b++;
    mult = b-i+1;
    if (mult < p) {
      count += (p-mult);
    }
    b++;
  }

  /* Create the return arrays */
  dim[0] = nc+count;
  dim[1] = nd;
  ret = PyArray_SimpleNew(2,dim, NPY_DOUBLE);
  newP = (double *)PYARRAY_DATA(ret);

  /* Compute */
  curve_decompose(P, nc, nd, U, nk, newP);
  //print_mat(newP,nc+count,nd);

  /* Clean up and return */
  Py_DECREF(arr1);
  Py_DECREF(arr2);
  return ret;

 fail:
  Py_XDECREF(arr1);
  Py_XDECREF(arr2);
  return NULL;
}


static char curveKnotRemove_doc[] =
"Coarsen curve knot vector.\n\
\n\
Input:\n\
\n\
- P: control points P(nc,nd)\n\
- Uv: knot values (nv)\n\
- Um: knot multiplicities (nv): sum(Um) =  m = n+p+1 = nc+p\n\
- iv: knot value index to remove: 0 <= iv < nv\n\
- num: number of times to remove u\n\
- tol: allowable tolerance for deviation of the curve. See NURBS book, p. 185\n\
\n\
Output:\n\
- t: actual number of times that u was removed\n\
P and U are replaced with the new control points and knot vector\n\
\n\
Modified algorithm A5.8 from 'The NURBS Book' pg185.\n\
";

static PyObject * curveKnotRemove(PyObject *self, PyObject *args)
{
  int *Um, iv, num, nd, nc, nv, nk, t, i, j, k, r, s;
  npy_intp *P_dim, *U_dim, dim[2];
  double *P, *Uv, tol, u, *newP, *newU;
  PyObject *a1, *a2, *a3;
  PyObject *arr1=NULL, *arr2=NULL, *arr3=NULL, *ret1 = NULL, *ret2 = NULL;

  if(!PyArg_ParseTuple(args, "OOOiid", &a1, &a2, &a3, &iv, &num, &tol))
    return NULL;
  arr1 = PyArray_FROM_OTF(a1, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr1 == NULL)
    return NULL;
  arr2 = PyArray_FROM_OTF(a2, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr2 == NULL)
    goto fail;
  arr3 = PyArray_FROM_OTF(a3, NPY_INT, NPY_ARRAY_IN_ARRAY);
  if(arr3 == NULL)
    goto fail;

  P_dim = PYARRAY_DIMS(arr1);
  nc = P_dim[0];
  nd = P_dim[1];
  U_dim = PYARRAY_DIMS(arr2);
  nv = U_dim[0];
  P = (double *)PYARRAY_DATA(arr1);
  Uv = (double *)PYARRAY_DATA(arr2);
  Um = (int *)PYARRAY_DATA(arr3);

  /* Compute derived data as needed by curve_knot_remove */
  int *Sm = (int*) malloc(nv*sizeof(int));
  cumsum(Um,nv,Sm);
  /* printf("Cumsum: "); */
  /* for (i=0; i<nv; ++i) printf("%d, ",Sm[i]); */
  /* printf("\n"); */
  nk = Sm[nv-1];
  double *U = (double*) malloc(nk*sizeof(double));
  k = 0;
  for (i=0; i<nv; ++i)
    for (j=0; j<Um[i]; ++j)
      U[k++] = Uv[i];
  u = Uv[iv];
  r = Sm[iv]-1;
  s = Um[iv];

  /* Compute */
  /* printf("Knots: "); */
  /* for (i=0; i<nk; ++i) printf("%f, ",U[i]); */
  /* printf("\n"); */
  /* printf("Remove knot value %f, index %d, multiplicity %d\n",u,r,s); */
  t = curve_knot_remove(P, nc, nd, U, nk, u, num, r, s, tol);

  /* Create the return arrays */
  dim[0] = nc-t;
  dim[1] = nd;
  ret1 = PyArray_SimpleNew(2,dim, NPY_DOUBLE);
  newP = (double *)PYARRAY_DATA(ret1);
  for (i=0; i<dim[0]*dim[1]; ++i) newP[i] = P[i];
  dim[0] = nk-t;
  ret2 = PyArray_SimpleNew(1,dim, NPY_DOUBLE);
  newU = (double *)PYARRAY_DATA(ret2);
  for (i=0; i<dim[0]; ++i) newU[i] = U[i];

  /* Clean up and return */
  free(U);
  free(Sm);
  Py_DECREF(arr1);
  Py_DECREF(arr2);
  return Py_BuildValue("iOO",t,ret1,ret2);

 fail:
  Py_XDECREF(arr1);
  Py_XDECREF(arr2);
  return NULL;
}


static char curveDegreeElevate_doc[] =
"Degree elevate a curve t times.\n\
\n\
Input:\n\
\n\
- P: control points P(nc,nd)\n\
- U: knot sequence: U[0] .. U[m]   m = n+p+1 = nc+p\n\
- t: degree elevation\n\
\n\
Output:\n\
- newP: new control points newP(nq,nd)\n\
- nq: number of new control points = nh+1\n\
- newU: new knot sequence: newU[0] .. newU[mh]   mh = nh+p+t+1 = nq+p+t\n\
- nu: number of new knots = mh+1\n\
\n\
Modified algorithm A5.9 from 'The NURBS Book' pg206.\n\
";

static PyObject * curveDegreeElevate(PyObject *self, PyObject *args)
{
  int nd, nc, nk, t, nq, nu, i;
  npy_intp *P_dim, *U_dim, dim[2];
  double *P, *U, *newP, *newU;
  PyObject *a1, *a2;
  PyObject *arr1=NULL, *arr2=NULL, *ret1 = NULL, *ret2 = NULL;

  if(!PyArg_ParseTuple(args, "OOi", &a1, &a2, &t))
    return NULL;
  arr1 = PyArray_FROM_OTF(a1, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr1 == NULL)
    return NULL;
  arr2 = PyArray_FROM_OTF(a2, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr2 == NULL)
    goto fail;

  P_dim = PYARRAY_DIMS(arr1);
  U_dim = PYARRAY_DIMS(arr2);
  nc = P_dim[0];
  nd = P_dim[1];
  nk = U_dim[0];
  P = (double *)PYARRAY_DATA(arr1);
  U = (double *)PYARRAY_DATA(arr2);

  /* Create thework spaces */
  nq = nc*(t+1);
  nu = (t+1)*nk;
  printf("Create work spaces for %d new control points and %d new knots\n",nq,nu);
  double *Pw = (double*) malloc(nq*nd*sizeof(double));
  double *Uw = (double*) malloc(nu*sizeof(double));

  /* Compute */
  curve_degree_elevate(P, nc, nd, U, nk, t, Pw, Uw, &nq, &nu);
  printf("Computed %d new control points\n",nq);
  print_mat(Pw,nq,nd);
  printf("Computed %d new knots\n",nu);
  print_mat(Uw,1,nu);

  /* Create the return arrays */
  dim[0] = nq;
  dim[1] = nd;
  printf("Create space for %d new control points\n",nq);
  ret1 = PyArray_SimpleNew(2,dim, NPY_DOUBLE);
  newP = (double *)PYARRAY_DATA(ret1);
  dim[0] = nu;
  ret2 = PyArray_SimpleNew(1,dim, NPY_DOUBLE);
  printf("Create space for %d new knots\n",nu);
  newU = (double *)PYARRAY_DATA(ret2);
  for (i=0; i<nq*nd; ++i) newP[i] = Pw[i];
  for (i=0; i<nu; ++i) newU[i] = Uw[i];

  /* free thw work spaces */
  free(Pw);
  free(Uw);

  /* Clean up and return */
  Py_DECREF(arr1);
  Py_DECREF(arr2);
  return Py_BuildValue("OOii",ret1,ret2, nq-1, nu-1);

 fail:
  Py_XDECREF(arr1);
  Py_XDECREF(arr2);
  return NULL;
}


static char curveDegreeReduce_doc[] =
"Degree reducee a curve.\n\
\n\
Input:\n\
\n\
- P: control points P(nc,nd)\n\
- U: knot sequence: U[0] .. U[m]   m = n+p+1 = nc+p\n\
\n\
Output:\n\
- newP: new control points newP(nq,nd)\n\
- nq: number of new control points = nh+1\n\
- newU: new knot sequence: newU[0] .. newU[mh]   mh = nh+p+t+1 = nq+p+t\n\
- nu: number of new knots = mh+1\n\
\n\
Modified algorithm A5.9 from 'The NURBS Book' pg206.\n\
";

static PyObject * curveDegreeReduce(PyObject *self, PyObject *args)
{
  int nd, nc, nk, nq, nu, i;
  npy_intp *P_dim, *U_dim, dim[2];
  double *P, *U, *newP, *newU;
  PyObject *a1, *a2;
  PyObject *arr1=NULL, *arr2=NULL, *ret1 = NULL, *ret2 = NULL;

  if(!PyArg_ParseTuple(args, "OO", &a1, &a2))
    return NULL;
  arr1 = PyArray_FROM_OTF(a1, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr1 == NULL)
    return NULL;
  arr2 = PyArray_FROM_OTF(a2, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr2 == NULL)
    goto fail;

  P_dim = PYARRAY_DIMS(arr1);
  U_dim = PYARRAY_DIMS(arr2);
  nc = P_dim[0];
  nd = P_dim[1];
  nk = U_dim[0];
  P = (double *)PYARRAY_DATA(arr1);
  U = (double *)PYARRAY_DATA(arr2);

  /* Create the work spaces */
  nq = nc*2;
  nu = 2*nk;
  printf("Create work spaces for %d new control points and %d new knots\n",nq,nu);
  double *Pw = (double*) malloc(nq*nd*sizeof(double));
  double *Uw = (double*) malloc(nu*sizeof(double));

  /* Compute */
  curve_degree_reduce(P, nc, nd, U, nk, Pw, Uw, &nq, &nu);
  printf("Computed %d new control points\n",nq);
  print_mat(Pw,nq,nd);
  printf("Computed %d new knots\n",nu);
  print_mat(Uw,1,nu);

  /* Create the return arrays */
  dim[0] = nq;
  dim[1] = nd;
  printf("Create space for %d new control points\n",nq);
  ret1 = PyArray_SimpleNew(2,dim, NPY_DOUBLE);
  newP = (double *)PYARRAY_DATA(ret1);
  dim[0] = nu;
  ret2 = PyArray_SimpleNew(1,dim, NPY_DOUBLE);
  printf("Create space for %d new knots\n",nu);
  newU = (double *)PYARRAY_DATA(ret2);
  for (i=0; i<nq*nd; ++i) newP[i] = Pw[i];
  for (i=0; i<nu; ++i) newU[i] = Uw[i];

  /* free thw work spaces */
  free(Pw);
  free(Uw);

  /* Clean up and return */
  Py_DECREF(arr1);
  Py_DECREF(arr2);
  return Py_BuildValue("OOii",ret1,ret2, nq-1, nu-1);

 fail:
  Py_XDECREF(arr1);
  Py_XDECREF(arr2);
  return NULL;
}


static char curveGlobalInterpolationMatrix_doc[] =
"Compute the global curve interpolation matrix.\n\
\n\
Input:\n\
\n\
- Q: points through which the curve should pass (nc,nd), where\n\
  nc is the number of points = number of control points = n+1 and\n\
  nd is the dimension of the points (3 or 4)\n\
- u: parameter values at the points (nc)\n\
- p: degree of the B-spline\n\
strategies:\n\
  0 : equally spaced (not recommended)\n\
  1 : chord length\n\
  2 : centripetal (recommended)\n\
\n\
Output:\n\
- P: control points P(nc,nd)\n\
- U: knot sequence: U[0] .. U[m]   m = n+p+1 = nc+p\n\
- A: coefficient matrix (nc,nc)\n\
\n\
Modified algorithm A9.1 from 'The NURBS Book' pg369.\n\
";

static PyObject * curveGlobalInterpolationMatrix(PyObject *self, PyObject *args)
{
  int p,nc,nd,nu;
  npy_intp *Q_dim, *u_dim, dim[2];
  double *Q, *u, *U, *A;
  PyObject *a1, *a2;
  PyObject *arr1=NULL, *arr2=NULL, *ret1=NULL, *ret2=NULL;

  if (!PyArg_ParseTuple(args, "OOi", &a1, &a2, &p))
    return NULL;
  arr1 = PyArray_FROM_OTF(a1, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr1 == NULL)
    return NULL;
  arr2 = PyArray_FROM_OTF(a2, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr2 == NULL)
    goto fail;

  Q_dim = PYARRAY_DIMS(arr1);
  u_dim = PYARRAY_DIMS(arr2);
  nc = Q_dim[0];
  nd = Q_dim[1];
  nu = u_dim[0];
  if (nu != nc) goto fail;

  Q = (double *)PYARRAY_DATA(arr1);
  u = (double *)PYARRAY_DATA(arr2);

  /* Create the return arrays */
  dim[0] = nc+p+1;
  ret1 = PyArray_SimpleNew(1,dim, NPY_DOUBLE);
  U = (double *)PYARRAY_DATA(ret1);
  dim[0] = nc;
  dim[1] = nc;
  ret2 = PyArray_SimpleNew(2,dim, NPY_DOUBLE);
  A = (double *)PYARRAY_DATA(ret2);

  /* Compute */
  curve_global_interp_mat(p, Q, nc, nd, u, U, A);

  /* Clean up and return */
  Py_DECREF(arr1);
  Py_DECREF(arr2);
  //return ret1;
  return Py_BuildValue("(OO)", ret1, ret2);

 fail:
  //printf("error cleanup and return\n");
  Py_XDECREF(arr1);
  Py_XDECREF(arr2);
  return NULL;
}


static char surfacePoints_doc[] =
"Compute points on a B-spline surface.\n\
\n\
Input:\n\
\n\
- P: control points P(ns,nt,nd)\n\
- ns,nt: number of control points\n\
- nd: dimension of the points (3 or 4)\n\
- U: knot sequence: U[0] .. U[m]\n\
- nU: number of knot values U = m+1\n\
- V: knot sequence: V[0] .. V[n]\n\
- nV: number of knot values V = n+1\n\
- u: parametric values (nu,2): U[0] <= ui[0] <= U[m], V[0] <= ui[1] <= V[m]\n\
- nu: number of parametric values\n\
\n\
Output:\n\
- pnt: (nu,nd) points on the B-spline\n\
\n\
Modified algorithm A3.5 from 'The NURBS Book' pg103.\n\
";


static PyObject * surfacePoints(PyObject *self, PyObject *args)
{
  int ns,nt,nd,nU,nV,nu;
  npy_intp *P_dim, *U_dim, *V_dim, *u_dim, dim[2];
  double *P, *U, *V, *u, *pnt;
  PyObject *a1, *a2, *a3, *a4;
  PyObject *arr1=NULL, *arr2=NULL, *arr3=NULL, *arr4=NULL, *ret=NULL;

  if (!PyArg_ParseTuple(args, "OOOO", &a1, &a2, &a3, &a4))
    return NULL;
  arr1 = PyArray_FROM_OTF(a1, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr1 == NULL)
    return NULL;
  arr2 = PyArray_FROM_OTF(a2, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr2 == NULL)
    goto fail;
  arr3 = PyArray_FROM_OTF(a3, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr3 == NULL)
    goto fail;
  arr4 = PyArray_FROM_OTF(a4, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr4 == NULL)
    goto fail;

  P_dim = PYARRAY_DIMS(arr1);
  U_dim = PYARRAY_DIMS(arr2);
  V_dim = PYARRAY_DIMS(arr3);
  u_dim = PYARRAY_DIMS(arr4);
  ns = P_dim[0];
  nt = P_dim[1];
  nd = P_dim[2];
  nU = U_dim[0];
  nV = V_dim[0];
  nu = u_dim[0];
  P = (double *)PYARRAY_DATA(arr1);
  U = (double *)PYARRAY_DATA(arr2);
  V = (double *)PYARRAY_DATA(arr3);
  u = (double *)PYARRAY_DATA(arr4);

  /* Create the return array */
  dim[0] = nu;
  dim[1] = nd;
  ret = PyArray_SimpleNew(2,dim, NPY_DOUBLE);
  pnt = (double *)PYARRAY_DATA(ret);

  /* Compute */
  surface_points(P,ns,nt,nd,U,nU,V,nV,u,nu,pnt);

  /* Clean up and return */
  Py_DECREF(arr1);
  Py_DECREF(arr2);
  Py_DECREF(arr3);
  Py_DECREF(arr4);
  return ret;

 fail:
  //printf("error cleanup and return\n");
  Py_XDECREF(arr1);
  Py_XDECREF(arr2);
  Py_XDECREF(arr3);
  Py_XDECREF(arr4);
  return NULL;
}


static char surfaceDerivs_doc[] =
"Compute derivatives of a B-spline surface.\n\
\n\
Input:\n\
\n\
- n: number of derivatives to compute\n\
- P: control points P(ns,nt,nd)\n\
- ns,nt: number of control points\n\
- nd: dimension of the points (3 or 4)\n\
- U: knot sequence: U[0] .. U[m]\n\
- nU: number of knot values U = m+1\n\
- V: knot sequence: V[0] .. V[n]\n\
- nV: number of knot values V = n+1\n\
- u: parametric values (nu,2): U[0] <= ui[0] <= U[m], V[0] <= ui[1] <= V[m]\n\
- nu: number of parametric values\n\
\n\
Output:\n\
- pnt: (n+1,nu,nd) points and derivatives on the B-spline surface\n\
\n\
Modified algorithm A3.6 from 'The NURBS Book' pg111.\n\
";

static PyObject * surfaceDerivs(PyObject *self, PyObject *args)
{
  int ns, nt, nd, nU, nV, nu, mu, mv;
  npy_intp *P_dim, *U_dim, *V_dim, *u_dim, dim[4];
  double *P, *U, *V, *u, *pnt;
  PyObject *a1, *a2, *a3, *a4;
  PyObject *arr1=NULL, *arr2=NULL, *arr3=NULL, *arr4=NULL;
  PyObject *ret=NULL;

  if(!PyArg_ParseTuple(args, "OOOOii", &a1, &a2, &a3, &a4, &mu, &mv))
    return NULL;
  arr1 = PyArray_FROM_OTF(a1, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr1 == NULL)
    return NULL;
  arr2 = PyArray_FROM_OTF(a2, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr2 == NULL)
    goto fail;
  arr3 = PyArray_FROM_OTF(a3, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr3 == NULL)
    goto fail;
  arr4 = PyArray_FROM_OTF(a4, NPY_DOUBLE, NPY_ARRAY_IN_ARRAY);
  if(arr4 == NULL)
    goto fail;

  P_dim = PYARRAY_DIMS(arr1);
  U_dim = PYARRAY_DIMS(arr2);
  V_dim = PYARRAY_DIMS(arr3);
  u_dim = PYARRAY_DIMS(arr4);
  ns = P_dim[0];
  nt = P_dim[1];
  nd = P_dim[2];
  nU = U_dim[0];
  nV = V_dim[0];
  nu = u_dim[0];
  P = (double *)PYARRAY_DATA(arr1);
  U = (double *)PYARRAY_DATA(arr2);
  V = (double *)PYARRAY_DATA(arr3);
  u = (double *)PYARRAY_DATA(arr4);

  /* Create the return array */
  dim[0] = mu+1;
  dim[1] = mv+1;
  dim[2] = nu;
  dim[3] = nd;
  ret = PyArray_SimpleNew(4,dim, NPY_DOUBLE);
  pnt = (double *)PYARRAY_DATA(ret);

  /* Compute */
  surface_derivs(mu,mv,P,ns,nt,nd,U,nU,V,nV,u,nu,pnt);

  /* Clean up and return */
  Py_DECREF(arr1);
  Py_DECREF(arr2);
  Py_DECREF(arr3);
  Py_DECREF(arr4);
  return ret;

 fail:
  //printf("error cleanup and return\n");
  Py_XDECREF(arr1);
  Py_XDECREF(arr2);
  Py_XDECREF(arr3);
  Py_XDECREF(arr4);
  return NULL;
}


static PyMethodDef extension_methods[] =
{
	{"binomial", binomial, METH_VARARGS, binomial_doc},
	{"horner", horner, METH_VARARGS, horner_doc},
	{"bernstein", bernstein, METH_VARARGS, bernstein_doc},
	{"allBernstein", allBernstein, METH_VARARGS, allBernstein_doc},
	{"curvePoints", curvePoints, METH_VARARGS, curvePoints_doc},
	{"curveDerivs", curveDerivs, METH_VARARGS, curveDerivs_doc},
	{"curveKnotRefine", curveKnotRefine, METH_VARARGS, curveKnotRefine_doc},
	{"curveDecompose", curveDecompose, METH_VARARGS, curveDecompose_doc},
	{"curveKnotRemove", curveKnotRemove, METH_VARARGS, curveKnotRemove_doc},
	{"curveDegreeElevate", curveDegreeElevate, METH_VARARGS, curveDegreeElevate_doc},
	{"curveDegreeReduce", curveDegreeReduce, METH_VARARGS, curveDegreeReduce_doc},
	{"curveGlobalInterpolationMatrix", curveGlobalInterpolationMatrix, METH_VARARGS, curveGlobalInterpolationMatrix_doc},
	{"surfacePoints", surfacePoints, METH_VARARGS, surfacePoints_doc},
	{"surfaceDerivs", surfaceDerivs, METH_VARARGS, surfaceDerivs_doc},
	{NULL, NULL, 0, NULL}        /* Sentinel */
};

/* Initialize the module */
#if PY_MAJOR_VERSION >= 3

static struct PyModuleDef moduledef = {
        PyModuleDef_HEAD_INIT,
        "misc_",   // module name
        NULL,      // module doc
        -1,        //sizeof(struct module_state),
        extension_methods,
        NULL,
        NULL, //myextension_traverse,
        NULL, //myextension_clear,
        NULL
};


#define INITERROR return NULL
PyMODINIT_FUNC PyInit_nurbs_(void)
#else
#define INITERROR return
void initnurbs_(void)
#endif
{
  PyObject* m;
#if PY_MAJOR_VERSION >= 3
  m = PyModule_Create(&moduledef);
#else
  m = Py_InitModule3("nurbs_", extension_methods, NULL);
#endif
  if (m == NULL)
    INITERROR;
  PyModule_AddStringConstant(m,"__version__",__version__);
  PyModule_AddStringConstant(m,"__doc__",__doc__);
  PyModule_AddIntConstant(m,"accelerated",1);
  import_array(); /* Get access to numpy array API */

#if PY_MAJOR_VERSION >= 3
  return m;
#endif
}

/* End */
