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
"""Tools for handling collections of elements belonging to multiple parts.

This module defines the Collection class.
"""
from __future__ import absolute_import, division, print_function


import pyformex as pf
import numpy as np

################# Collection of Actors or Actor Elements ###############

class Collection(object):
    """A collection  is a set of (int,int) tuples.

    The first part of the tuple has a limited number of values and are used
    as the keys in a dict.
    The second part can have a lot of different values and is implemented
    as an integer array with unique values.
    This is e.g. used to identify a set of individual parts of one or more
    OpenGL actors.

    Examples:

    >>> a = Collection()
    >>> a.add(range(7),3)
    >>> a.add(range(4))
    >>> a.remove([2,4],3)
    >>> print(a)
    -1 [0 1 2 3]; 3 [0 1 3 5 6];
    >>> a.add([[2,0],[2,3],[-1,7],[3,88]])
    >>> print(a)
    -1 [0 1 2 3 7]; 2 [0 3]; 3 [ 0  1  3  5  6 88];
    >>> a[2] = [1,2,3]
    >>> print(a)
    -1 [0 1 2 3 7]; 2 [1 2 3]; 3 [ 0  1  3  5  6 88];
    >>> a[2] = []
    >>> print(a)
    -1 [0 1 2 3 7]; 3 [ 0  1  3  5  6 88];
    >>> a.set([[2,0],[2,3],[-1,7],[3,88]])
    >>> print(a)
    -1 [7]; 2 [0 3]; 3 [88];
    >>> print(a.keys())
    [-1  2  3]
    >>> 2 in a
    True

    """
    def __init__(self,object_type=None):
        self.d = {}
        self.obj_type = object_type


    def __len__(self):
        return len(self.d)


    def setType(self, obj_type):
        self.obj_type = obj_type


    def clear(self,keys=[]):
        if keys:
            for k in keys:
                k = int(k)
                if k in self.d.keys():
                    del self.d[k]
        else:
            self.d = {}


    def add(self,data,key=-1):
        """Add new data to the collection.

        data can be a 2d array with (key,val) tuples or a 1-d array
        of values. In the latter case, the key has to be specified
        separately, or a default value will be used.

        data can also be another Collection, if it has the same object
        type.
        """
        if isinstance(data, Collection):
            if data.obj_type == self.obj_type:
                for k in data.d:
                    self.add(data.d[k], k)
                return
                return
            else:
                raise ValueError("Cannot add Collections with different object type")

        if len(data) == 0:
            return
        data = np.asarray(data)
        if data.ndim == 2:
            for key in np.unique(data[:, 0]):
                self.add(data[data[:, 0]==key, 1], key)

        else:
            key = int(key)
            data = np.unique(data)
            if key in self.d:
                self.d[key] = np.union1d(self.d[key], data)
            elif data.size > 0:
                self.d[key] = data


    def set(self,data,key=-1):
        """Set the collection to the specified data.

        This is equivalent to clearing the corresponding keys
        before adding.
        """
        self.clear()
        self.add(data, key)


    def remove(self,data,key=-1):
        """Remove data from the collection."""
        if isinstance(data, Collection):
            if data.obj_type == self.obj_type:
                for k in data.d:
                    self.remove(data.d[k], k)
                return
            else:
                raise ValueError("Cannot remove Collections with different object type")

        data = np.asarray(data)
        if data.ndim == 2:
            for key in np.unique(data[:, 0]):
                self.remove(data[data[:, 0]==key, 1], key)

        else:
            key = int(key)
            if key in self.d:
                data = np.setdiff1d(self.d[key], np.unique(data))
                if data.size > 0:
                    self.d[key] = data
                else:
                    del self.d[key]
            else:
                pf.debug("Not removing from non-existing selection for actor %s" % key, pf.DEBUG.DRAW)


    def __contains__(self, key):
         """Check whether the collection has an entry for the key.

         This inplements the 'in' operator for a Collection.
         """
         return key in self.d


    def __setitem__(self, key, data):
        """Set new values for the given key."""
        key = int(key)
        data = np.unique(data)
        if data.size > 0:
            self.d[key] = data
        else:
            del self.d[key]


    def __getitem__(self, key):
        """Return item with given key."""
        return self.d[key]


    def get(self, key, default=[]):
        """Return item with given key or default."""
        key = int(key)
        return self.d.get(key, default)


    def keys(self):
        """Return a sorted array with the keys"""
        keys = sorted(self.d.keys())
        return np.asarray(keys)


    def items(self):
        """Return a zipped list of keys and values."""
        return self.d.items()


    def __str__(self):
        s = ''
        for k in self.keys():
            s += "%s %s; " % (k, self.d[k])
        return s.rstrip()


# End
