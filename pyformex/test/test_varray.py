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

"""Unittests for the pyformex.varray module

These unittest are based on the pytest framework.

"""
from __future__ import print_function
import pyformex as pf
import numpy as np
from pyformex.varray import *

vdata = [[0],[1,2],[0,2,4],[0,2]]
data = np.concatenate(vdata)
lens = [len(d) for d in vdata]
Va = Varray(vdata)
Ve = Varray([])


def test_Varray_init():
    """Check proper initialization of Varray"""
    assert (Va.data == data).all()
    assert (Va.data[Va.ind[:-1]] == [ d[0] for d in vdata]).all()
    assert Va.width == max(lens)
    assert Ve.shape == (0,0)


def test_Varray_lengths():
    """Test lengths method of Varray"""
    assert (Va.lengths == [1,2,3,2]).all()


    # @property
    # def nrows(self):
    #     """Return the number of rows in the Varray"""
    #     return len(self.ind) - 1


    # @property
    # def size(self):
    #     """Return the total number of elements in the Varray"""
    #     return self.ind[-1]


    # @property
    # def shape(self):
    #     """Return a tuple with the number of rows and maximum row length"""
    #     return (self.nrows, self.width)


# End
