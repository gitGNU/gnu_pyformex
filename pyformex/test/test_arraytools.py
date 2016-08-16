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

"""Unittests for the pyformex.arraytools module

These unittest are based on the pytest framework.

"""
from __future__ import print_function
import pyformex as pf
import numpy as np
from pyformex.arraytools import *

def test_isInt():
    """Test that argument is an integer number"""
    assert isInt(1) is True
    assert isInt(1.1) is False
    assert isInt(np.arange(1)[0]) is True
    assert isInt(np.ones((1,))[0]) is False

def test_isFloat():
    """Test that argument is a float number"""
    assert isFloat(1) is False
    assert isFloat(1.1) is True
    assert isFloat(np.arange(1)[0]) is False
    assert isFloat(np.ones((1,))[0]) is True

def test_isNum():
    """Test that argument is a number"""
    assert isNum(1) is True
    assert isNum(1.1) is True
    assert isNum('a') is False
    assert isNum([0,1]) is False

def test_powers():
    assert powers(2,5) == [ 1,2,4,8,16,32 ]

def test_cumsum0():
    assert (cumsum0([2,4,3]) == [0, 2, 6, 9]).all()

def test_sind():
    assert isclose(sind(30), 0.5)
    assert isclose(sind(30,DEG), 0.5)
    assert isclose(sind(pi/6,RAD), 0.5)

def test_cosd():
    assert isclose(cosd(60), 0.5)
    assert isclose(cosd(60,DEG), 0.5)
    assert isclose(cosd(pi/3,RAD), 0.5)

def test_tand():
    assert isclose(tand(45), 1.)
    assert isclose(tand(45,DEG), 1.)
    assert isclose(tand(pi/4,RAD), 1.)

def test_arcsind():
    assert isclose(arcsind(0.5), 30)
    assert isclose(arcsind(0.5,DEG), 30)
    assert isclose(arcsind(0.5,RAD), pi/6)

def test_arcsind():
    assert isclose(arccosd(0.5), 60)
    assert isclose(arccosd(0.5,DEG), 60)
    assert isclose(arccosd(0.5,RAD), pi/3)

def test_arctand():
    assert isclose(arctand(1.), 45)
    assert isclose(arctand(1.,DEG), 45)
    assert isclose(arctand(1.,RAD), pi/4)

def test_arctand2():
    assert isclose(arctand2(0.5,sqrt(3)/2), 30)
    assert isclose(arctand2(0.5,sqrt(3)/2,DEG), 30)
    assert isclose(arctand2(0.5,sqrt(3)/2,RAD), pi/6)

def test_niceLogSize():
    assert niceLogSize(1.3) == 1
    assert niceLogSize(35679.23) == 5
    assert niceLogSize(0.4) == 0
    assert niceLogSize(0.00045676) == -3


def test_nodalSum_Avg():
    val = np.array([
        [[ 0.,  0.],
         [ 2., 20.],
         [ 3., 30.],
         [ 1., 10.]],
        [[ 2., 20.],
         [ 4., 40.],
         [ 5., 50.],
         [ 3., 30.]]])
    elems = np.array([
        [0, 2, 3, 1],
        [2, 4, 5, 3]])
    sum,cnt = nodalSum(val,elems)
    assert isclose(sum,[[0,0],[1,10],[4,40],[6,60],[4,40],[5,50]]).all()
    assert (cnt == [1, 1, 2, 2, 1, 1]).all()
    avg = nodalAvg(val,elems)
    print(avg)
    assert isclose(avg,[[0,0],[1,10],[2,20],[3,30],[4,40],[5,50]]).all()

# End
