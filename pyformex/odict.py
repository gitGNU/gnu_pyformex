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



class DDict(dict):
    """A dict with multiple ways to set the default values.

    This is equivalent to the dict class, except that if a key is not found
    it's value may be found from calling a function or from looking it up
    in another dict.

    This differs in two ways from the :class:`collections.defaultdict` class:

    - the default function takes the missing key as a parameter,
    - the value looked up through the default function is not stored in
      the DDict itself, but will be looked up againe with the default
      function on each subsequent access of the same key.
      See :class:`EDict` for an analog class that stores the looked up values
      in itself.

    Parameters:

    - `default`: either None, a function. If it is a function, it should take
      the key as parameter and return the value for that key. It can
      appropriately be set to the get method of another dict, to have
      missing keys being looked up in another dict. The default None will
      cause a KeyError on missing keys.

    - all other parameters are passed to the dict initialisation.

    Examples:

    >>> d = DDict(lambda x:-x)
    >>> print(d)
    {}
    >>> print(d[1],d[2],d[3])
    -1 -2 -3
    >>> d[2] = 2
    >>> e = DDict(d.get,{1:1})
    >>> print(e)
    {1: 1}
    >>> print(e[1],e[2],e[3])
    1 2 None

    """

    def __init__(self, default=None, *args, **kargs):
        """Initialize the CascadingDict"""
        self.default_factory = default
        dict.__init__(self, *args, **kargs)


    def __missing__(self,key):
        if self.default_factory is None:
            raise KeyError
        else:
            return self.default_factory(key)


class EDict(dict):
    """An extensible DDict

    This class is like DDict, but it installs missing keys in itself,
    with the value of the first default lookup.

    Examples (compare with DDict):

    >>> d = EDict(lambda x:-x)
    >>> print(d)
    {}
    >>> print(d[1],d[2],d[3])
    -1 -2 -3
    >>> d[2] = 2
    >>> e = EDict(d.get,{1:1})
    >>> print(e)
    {1: 1}
    >>> print(e[1],e[2],e[3])
    1 2 -3

    """

    def __init__(self, factory=None, *args, **kargs):
        """Initialize the CascadingDict"""
        self.default_factory = factory
        dict.__init__(self, *args, **kargs)


    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError
        else:
            self[key] = self.default_factory(key)
            return self[key]


# End
