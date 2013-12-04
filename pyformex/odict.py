#!/usr/bin/python
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

"""Specialized dictionary types.



"""
from __future__ import print_function

try:
    from collections import OrderedDict
except:
    from pyformex.backports import OrderedDict


from collections import defaultdict

class CascadingDict(defaultdict):
    """A cascading dict: keys not in dict are searched in all dict values.

    This is equivalent to the Dict class, except that if a key is not found
    and the CDict has items with values that are themselves instances
    of Dict or CDict, the key will be looked up in those Dicts as well.

    As you expect, this will make the lookup cascade into all lower levels
    of CDict's. The cascade will stop if you use a Dict.
    There is no way to guarantee in which order the (Cascading)Dict's are
    visited, so if multiple Dicts on the same level hold the same key,
    you should know yourself what you are doing.
    """

    def __init__(self,default=None,*args,**kargs):
        """Initialize the CascadingDict"""

        defaultdict.__init__(self,default,*args,**kargs)


    def __missing__(self,key):
        if self.default_factory is None:
            raise KeyError
        else:
            return self.default_factory(key)


if __name__ == "__main__":

    c = CascadingDict(None, zip(range(4),range(4)))
    print(c)


    d = CascadingDict(c.get, zip(range(3),range(3)))
    print(d)

    print(c[3])
    #print(c[4])
    print(d[3])

# End
