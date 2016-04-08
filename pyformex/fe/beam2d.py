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
"""beam2d: A 2d beam finite element

"""

from numpy import *

class Beam2d:

    @staticmethod
    def mass(rho,A,l):
        l = float(l)
        l2 = l*l
        M = array([
            [ 156  , 22*l ,  54  , -13*l  ],
            [  22*l,  4*l2,  13*l,  -3*l2 ],
            [  54  , 13*l , 156  , -22*l  ],
            [ -13*l, -3*l2, -22*l,   4*l2 ]])
        M *= rho * A * l / 420
        return M

    @staticmethod
    def stiff(E,I,l):
        l = float(l)
        EIl = E*I/l
        b4 = 2 * EIl
        b3 = 2 * b4
        b2 = 3 * b4 / l
        b1 = 2 * b2 / l
        K = array([
            [  b1,  b2, -b1,  b2 ],
            [  b2,  b3, -b2,  b4 ],
            [ -b1, -b2,  b1, -b2 ],
            [  b2,  b4, -b2,  b3 ]])
        return K

# units are N, m, kg, s

class steel(object):
    E = 210.e9

class IPE100(object):
    rho = 8.26 # kg/m
    A = 1032.e-6
    I = 171.e-12


def cantilever_frequencies(rho,A,l,E,I):
    """First 6 eigenfrequencies of cantilever beam

    These are high precision results from analytical formulas.
    """
    c = sqrt(E*I/(rho*A)) / (l*l)
    coeffs = array([
        1.875104069,
        4.694091133,
        7.854757438,
        10.99554073,
        14.13716839,
        17.27875953])
    return c * coeffs**2 / 2 / pi


def assemble(Ke,Me,ne):
    """Assemble beam of ne identical elements Ke,Me"""
    n = 2*(ne+1)
    K = zeros((n,n))
    M = zeros((n,n))
    for ie in range(ne):
        i = 2*ie
        K[i:i+4,i:i+4] += Ke
        M[i:i+4,i:i+4] += Me
    return K,M


def createBeam(lt,nel,addbc=True):
    """Create stiffness and mass matrices of a simple beam.

    lt: length of the beam (m)
    nel: number of element to use along the beam length
    addbc: if True, add cantilever boundary conditions
    """
    # element length
    l = lt / nel
    # create element stiffness and mass matrix
    Ke = Beam2d.stiff(steel.E,IPE100.I,l)
    Me = Beam2d.mass(IPE100.rho,IPE100.A,l)
    # assemble the global stiffness and mass matrix
    K,M = assemble(Ke,Me,nel)
    if addbc:
        # Impose cantilever boundary conditions
        # This is done by adding a very stiff translational
        #   and rotational spring to the first node:
        VERY_STIFF = 1.e4
        K[0,0] *= (1.+VERY_STIFF)
        K[1,1] *= (1.+VERY_STIFF)

    return K,M


# End
