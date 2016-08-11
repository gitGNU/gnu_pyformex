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

"""Unittests for the pyformex.plugins.fe_abq module

These unittest are based on the pytest framework.

"""
from __future__ import print_function
import pyformex as pf
import numpy as np
from pyformex.plugins.fe import *

from pyformex.mesh import Mesh
# Create a Mesh of 2 line elements
A = Mesh([[0.],[1.],[2.]],[[0,1],[1,2]])
B = Mesh([[0.,0.],[1.,0.],[2.,0.],[2.,1.]],[[0,1,3],[1,2,3]])
M = Model(meshes=[A,B])


def test_Model_init():
    """Test initialization of Model class"""
    #assert (M.coords == [[0,0.0],[1,0,0],[2,0,0],[3,0,0],[4,0,0]]).all()

def test_Model_nnodes():
    assert M.nnodes() == 4

def test_Model_nelems():
    assert M.nelems() == 4

def test_Model_ngroups():
    assert M.ngroups() == 2

def test_Model_mplex():
    assert M.mplex() == [2,3]

def test_Model_splitElems():
    glob,loc = M.splitElems([1,3,2])
    assert (glob[0] == [1]).all()
    assert (glob[1] == [2,3]).all()
    assert (loc[0] == [1]).all()
    assert (loc[1] == [0,1]).all()

def test_elemNrs():
    assert (M.elemNrs(1) == [2,3]).all()
    assert (M.elemNrs(1,[1,0]) == [3,2]).all()

def test_getElems():
    g = M.getElems([[0,1],[1]])
    assert len(g) == 2
    assert g[0].shape == (2,2)
    assert g[1].shape == (1,3)
    assert (g[0] == [[0,1],[1,2]]).all()
    assert (g[1] == [[1,2,3]]).all()


print(__name__)
if __name__ == "__script__":
    test_getElems()


# End
