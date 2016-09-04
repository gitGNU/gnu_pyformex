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
from __future__ import absolute_import, division, print_function

from future_builtins import zip

_PY2_round = __builtins__['round']


def round(number, ndigits=None):
    """Python3 rounding behavior in Python2.

    >>> round(2.3)
    2
    >>> round(2.7)
    3
    >>> round(2.7, 0)
    3.0
    >>> round(1.5, 0)
    2.0
    >>> round(2.5, 0)
    2.0
    >>> round(-1.5)
    -2
    >>> round(-2.5)
    -2
    """
    intIt = ndigits is None
    ndigits = ndigits if ndigits is not None else 0

    f = number
    if abs(_PY2_round(f) - f) == 0.5:
        retAmount = 2.0 * _PY2_round(f / 2.0, ndigits);
    else:
        retAmount = _PY2_round(f, ndigits)

    if intIt:
        return int(retAmount)
    else:
        return retAmount



import cPickle as pickle

def execFile(f,*args,**kargs):
    return execfile(f,*args,**kargs)


def userInput(*args,**kargs):
    return raw_input(*args,**kargs)


# Print a string only in Python3
def print3(s):
    pass


def isFile(o):
    """Test if an object is a file"""
    return isinstance(o,file)


def isString(o):
    """Test if an object is a string (ascii or unicode)"""
    return isinstance(o,(str,unicode))

# End
