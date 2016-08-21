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
"""pyFormex compatibility module for Python2.x

The compatibility modules for different Python versions are intended
to wrap code changes between the versions into functions located at
a single place.

Note that we can not implement this as a single module and test for
the Python version inside that module. The differences between the
versions might cause compilation to fail.
"""
from __future__ import absolute_import, print_function

from future_builtins import zip

import cPickle as pickle

def execFile(f,*args,**kargs):
    return execfile(f,*args,**kargs)


def userInput(*args,**kargs):
    return raw_input(*args,**kargs)


# Print a string only in Python3
def print3(s):
    pass


# End
