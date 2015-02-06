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
"""Utility functions for finite elements applications

This module contains some functions, data and classes for assist
finite element modelling.
You need to import this module in your scripts to have access to its
contents.
"""

from __future__ import print_function

from pyformex.arraytools import checkArray


# Note: this could be combined with convertUnits function from
# plugins.units to do things like this:
#
#  mat = IsotropicElasticity(E='21GPa',K='7000kN/cm**2')
#  mat.E('Mpa')  # would give value in MPa
#
class IsotropicElasticity(object):
    """Material constants for an isotropic linear elastic material.

       Exactly 2 out of the following need to be specified:

       E, G, nu, K, lmbda, mu, D
    """

    def __init__(self,E=None,G=None,nu=None,K=None,lmbda=None,mu=None,D=None):

        # convert None values to float
        E,G,nu,K,lmbda,mu,D = [ float(var) if var is not None else None for var in  [E,G,nu,K,lmbda,mu,D] ]

        if G is None and mu is not None:
            G = mu

        if K is None and D is not None:
            K = 2./D

        # Set the young modulus E (checked for combinations with K, lamba, G)
        if K is not None:

            if lmbda is not None:
                E = (9.*K*(K-lmbda))/(3.*K-lmbda)

            if G is not None:
                E=(9.*K*G)/(3.*K+G)

            if nu is not None:
                E = 3.*K*(1.-2.*nu)

        if lmbda is not None:

            if G is not None:
                E = (G* (3.*lmbda + 2.*G))/(lmbda + G)

            if nu is not None:
                E = (lmbda*(1.+nu)*(1-2*nu))/nu

        if G is not None:
            if nu is not None:
                E = 2.*G*(1.+nu)

        # After setting the young modulus E computes G only the few checks below are needed
        if lmbda is not None:
            R = (E**2.+9.*lmbda**2.+2.*E*lmbda)**0.5
            G = (E-3.*lmbda+R)/4.

        if nu is not None:
            G = E / (2*(1+nu))

        if K is not None:
            G = (3.*K*E)/(9*K-E)

        self._E, self._G = E,G


    @property
    def E(self):
        return self._E

    @property
    def G(self):
        return self._G

    @property
    def nu(self):
        return self._E / (2*self._G) - 1.0

    @property
    def K(self):
        return self._G * self._E / (3*(3*self._G-self._E))

    @property
    def D(self):
        return 2./self.K

    @property
    def lmbda(self):
        E,G = self._E,self._G
        return G*(E-2*G) / (3*G-E)

    @property
    def mu(self):
        return self._G

    def __str__(self):
        return "E = %s; G=mu=%s; nu=%s; K=%s; lmbda=%s; D=%s" % (self.E,self.G,self.nu,self.K,self.lmbda,self.D)


class UniaxialStrain(object):
    """Uniaxial finite deformation strain measures.

    This class provides a way to store finite deformation strain measures
    and to convert between different strain measure definitions.

    Parameters:

    - `data`: array-like float (n,): strain values
    - `type`: one of 'stretch', 'log', 'nominal', 'green', 'almansi'.
      Defines the type of strain measure:

      - 'stretch': stretch (ratio) or extension ratio,
      - 'nominal': nominal or engineering strain,
      - 'log': logarithmic or true strain,
      - 'green': Green strain (values should be >= -0.5),
      - 'almansi': Almansi strain (values should be <= 0.5).

      The default is to interprete the data as nominal strains.

    Internally, the data are stored as stretch values.
    """

    def __init__(self,data,type):
        """Initialize the UniaxialStrain"""

        data = checkArray(data,shape=(-1,),kind='f')
        if type == 'nominal':
            data = data + 1.
        elif type == 'log':
            data = exp(data)
        elif type == 'green':
            data = sqrt(2*data + 1.)
        elif type == 'almansi':
            data = 1. / sqrt(1. - 2*data)
        elif type != 'stretch':
            raise valueError("Invalid strain type: %s" % type)

        self.data = data


    def stretch(self):
        """Return the strain data as stretch ratios"""
        return self.data

    def log(self):
        """Return the strain data as logarithmic (true) strains"""
        return log(self.data)

    def nominal(self):
        """Return the strain data as nominal (engineering) strains"""
        return self.data - 1.

    def green(self):
        """Return the strain data as Green strains"""
        return 0.5 * ( self.data * self.data - 1.0 )

    def almansi(self):
        """Return the strain data as Almansi strains"""
        return 0.5 * ( 1. - 1. / (self.data * self.data) )


class UniaxialStress(object):
    """Uniaxial finite deformation stress measures.

    This class provides a way to store finite deformation stress measures
    and to convert between different stress measure definitions.

    Parameters:

    - `data`: array-like float (n,): stress values
    - `type`: one of 'cauchy', 'nominal', 'pk2'.
      Defines the type of stress measure:

      - 'cauchy': Cauchy or true stress,
      - 'nominal': nominal, engineering or first Piola-Kirchhoff stress,
      - 'pk2': second Piola-Kirchhoff stress.

      The default is to interprete the data as nominal stresses.

    - `strain`: a :class:`UniaxialStrain` instance of matching size (n,),
      or array-like float (n,) with the strain values. In the latter case
      also `straintype` should be specified.
    - `straintype`: if `strain` is specified as a :class:`UniaxialStrain`
      instance, this argument is not used. Else it specifies the strain type
      (see :class:`UniaxialStrain`).

    Internally, the data are stored as Cauchy stress.
    """

    def __init__(self,data,type,strain,straintype=None):
        """Initialize the UniaxialStress"""

        data = checkArray(data,shape=(-1,),kind='f')
        if not isinstance(strain,UniaxialStrain):
            strain = UniaxialStrain(strain,straintype)
        stretch = strain.stretch()
        if type == 'nominal':
            data = data * stretch
        elif type == 'pk2':
            data = data * stretch**2
        elif type != 'cauchy':
            raise valueError("Invalid stress type: %s" % type)

        self.data = data
        self.strain = strain

    def cauchy(self):
        return self.data

    def nominal(self):
        return self.data / self.strain.stretch()

    def pk2(self):
        return self.data / self.strain.stretch()**2





# maybe move this to the amplitude class?
def smoothAmp(a,n=50):
    """ Compute a single abaqus smooth amplitude.

    Parameters:
    -`a`: arraylike of floats of shape(2,2) storing  initial and final amplitudes/time pairs
    -`n`: int. number of of intervals for the time variable
    """

    tc=linspace(a[0,0],a[1,0],n)
    eps=(tc-a[0,0])/ (a[1,0]-a[0,0])
    amp= a[0,1] + (a[1,1]-a[0,1]) *  eps**3 * (10.-15.*eps+6.*eps**2.)
    return column_stack([tc,amp])


def ampSequence(a,n=100,f=smoothAmp):
    """ Compute a single abaqus smooth amplitude.

    Parameters:
    -`a`: arraylike of floats. every row is a pair of subsequent initial and final amplitudes/time value
    -`n`: int. number of of intervals for the time variable
    -`f`: function of the amplitude
    """

    amp= empty((0,2))
    for i  in range(len(a)-1):
        amp=concatenate([amp,f(a[i:i+2],n=n)],axis=0)
    return amp


def transverseShear(E,nu,c,type='generalized'):
    """ Compute the shear stiffness for beam and shell element theory
    for a homogeneous beams/shells made of a linear, orthotropic elastic material.

    Parameters:

    -`E`: float or arraylike of shape (2,). Elastic modulus in the two directions.
        If float the values in each directions are considerd the same.
    -`nu`: float. Poisson modulus
    -`c`: float. Characteristic dimension. For beam elements is the cross-
        sectional area, for shell elements is the thickness of the element
    -`type`: str. Can assume value 'shell' or one of the allowed beam cross
        section names as defined in abaqus.

    Return a list of 3 values for the transverse shear. If `type` == 'shell' returns a list
    [shear stiffness in the 1st direction, shear stiffness in the 2nd direction,coupling term ]
    where the coupling term is assumed to be 0. In all the other cases refers to beam
    sections and returns a list [shear stiffness, shear stiffness,  slenderness compensation factor ]
    (See abaqus documentation for meanings and usage).
    """
    k = {'arbitrary':1.0,\
        'box':0.44,\
        'circular':0.89,\
        'elbow':0.85,\
        'generalized':1.0,\
        'hexagonal':0.53,\
        'i' :0.44,\
        't' :0.44,\
        'l':1.0,\
        'meshed':1.0,\
        'nonlinear':1.0,\
        'pipe':0.53,\
        'rectangular':0.85,\
        'thick pipe1':0.53,\
        'thick pipe2':0.89,\
        'trapezoidal':0.822,\
        'shell': 5/6.}

    if asarray(E).size == 1:
        E = [E,E]

    sh = []
    for  em in E:
        G = IsotropicElasticity(E=em,nu=nu).G
        sh.append(k[type]*c*G) # Actual transverse shear stiffness

    if type != 'shell':
        sh.append(k[type]/(2.*(1.+nu)))  # default slenderness compensation factor, has sense only for beam elements
    else:
        sh.append(0.)
    return sh


## if __name__ == "script" or __name__ == "draw":

##     # Testing ampSequence
##     t= [0.,0.1,1.1,1.3,1.8,5];a = [0.,0.,1,2,2,1]

##     a=column_stack([t,a])
##     amp=ampSequence(a)

##     from matplotlib import pyplot

##     x = numpy.arange(10)
##     y = numpy.array([5,3,4,2,7,5,4,6,3,2])

##     fig = pyplot.figure()
##     ax = fig.add_subplot(111)
##     off=abs((amp[:,1].max()-amp[:,1].min())/50.)
##     ax.set_ylim(amp[:,1].min()-off,amp[:,1].max()+off)
##     pyplot.plot(amp[:,0],amp[:,1])
##     for i,j in a:
##         ax.annotate(str(j),xy=(i,j))

##     #~ pyplot.show()

##     # Testing isotropicelasticity
##     mat = IsotropicElasticity(E=210000,nu=0.3)
##     print(mat)
##     mat1 = IsotropicElasticity(K=mat.K,G=mat.G)
##     print(mat1)
##     mat2 = IsotropicElasticity(lmbda=mat1.lmbda,nu=mat1.nu)
##     print(mat2)


##     # Testing shearStiffness
##     sh = transverseShear(type='shell',c=0.3,E=210000,nu=0.3)
##     print(sh)
# End
