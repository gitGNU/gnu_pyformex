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
"""Attributes

This module defines a general class for adding extra attributes to
other objects without cluttering the name space.
"""
from __future__ import print_function


from pyformex.mydict import Dict, returnNone
from pyformex import utils


class Attributes(Dict):
    """A general class for holding attributes.

    This class is a versatile dict class for objects that need a customizable
    set of attributes, while avoiding a wildly expanding name space.

    The class has dict type and object/attribute type syntax.
    Furthermore, an instance can be called as a function to populate
    or update its contents.
    Giving an attribute the value None removes it from the dict.
    Any non-existing attribute returns None.

    Parameters:

    - `data`: a dict or any other object that can be used to initialize a
      :class:`Dict`. This provides the data stored in the Attributes.
    - `default`: either another Attributes instance, or None. If another
      Attributes is specified, keys not existing in `self` will be looked up
      in `default` and that value will be returned.

    Example:

    >>> A = Attributes()
    >>> print(A)
    {}
    >>> A(color='red',alpha=0.7,ontop=True)
    >>> print(A)
    {'alpha': 0.7, 'color': 'red', 'ontop': True}
    >>> A.ontop = None
    >>> A.alpha = 0.8
    >>> print(A)
    {'alpha': 0.8, 'color': 'red'}
    >>> B = Attributes({'color':'green'},default=A)
    >>> print(B)
    {'color': 'green'}
    >>> print(B.color,B.alpha)
    green 0.8
    >>> A.clear()
    >>> print(A)
    {}
    >>> print(B.color,B.alpha)
    green None
    >>> B(color=None,alpha=1.0)
    >>> print(B)
    {'alpha': 1.0}
    >>> B['alpha'] = None
    >>> print(B)
    {}
    """

    def __init__(self,data={},default=None):
        """Create a new Attributes dict"""
        if isinstance(default, Attributes):
            self._default_dict_ = default
            default = self._return_default_
        elif default is None:
            default = returnNone
        elif callable(default):
            pass
        else:
            raise ValueError("The 'default' argument should be an Attributes instance or None; got %s:" % type(default))
            default = returnNone

        Dict.__init__(self, data, default)


    def __call__(self,**kargs):
        for k in kargs:
            setattr(self,k,kargs[k])


#    update = __call__


    def __setitem__(self, key, value):
        if value is None:
            if key in self:
                del self[key]
        else:
            Dict.__setitem__(self, key, value)


    __setattr__ = __setitem__


    def _return_default_(self, key):
        return self._default_dict_[key]


    def __str__(self):
        """Create a string representation of the Attributes.

        This will print the Attributes in a format like a dict, but with
        the keys sorted, and the _default_dict_ item is not printed.
        """
        return utils.dictStr(self,['_default_dict_' ])


    def __repr__(self):
        return dict.__repr__(utils.removeDict(self, ['_default_dict_']))


# End
