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
"""pyFormex compatibility module for Python3.x

The compatibility modules for different Python versions are intended
to wrap code changes between the versions into functions located at
a single place.

Note that we can not implement this as a single module and test for
the Python version inside that module. The differences between the
versions might cause compilation to fail.
"""
from __future__ import absolute_import, division, print_function

py3_warning = """
#####################################################################
##  Warning! This is an experimental Python3 version of pyFormex.  ##
##  It is only meant for development and debugging purposes.       ##
##  It is not functional yet. For production purposes, use the     ##
##  Python2 version.                                               ##
#####################################################################
"""
print(py3_warning)

import sys
if (sys.hexversion & 0xFFFF0000) == 0x03010000:

    # Python 3.1 has no callable(), let's define it here
    import collections
    def callable(f):
        return isinstance(f, collections.Callable)
    __builtins__['callable'] = callable


zip = __builtins__['zip']
round = __builtins__['round']
__builtins__['unicode'] = str


import pickle


def execFile(f,*args,**kargs):
    return exec(compile(open(f,'r').read(), f, 'exec'),*args,**kargs)


def userInput(*args,**kargs):
    return input(*args,**kargs)


# Print a string only in Python3
print3 = print

def isFile(o):
    """Test if an object is a file"""
    import io
    return isinstance(o,io.IOBase)


def isString(o):
    """Test if an object is a string (ascii or unicode)"""
    return isinstance(o,(str,bytes))


# End
