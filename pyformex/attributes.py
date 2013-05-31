# $Id$
"""Attributes

This module defines a general class for adding extra attributes to
other objects without cluttering the name space.
"""
from __future__ import print_function

from mydict import Dict,returnNone
import utils


class Attributes(Dict):
    """A general class for holding attributes.

    This class is a versatile dict class for objects that need a customizable
    set of attributes, while avoiding a wildly expanding name space.

    The class has dict type and object/attribute type syntax.
    Furthermore, an instance can be called as a function to populate
    or update its contents.
    Giving an attribute the value None removes it from the dict.
    Any non-existing attribute returns None.



    Example:

    >>> A = Attributes()
    >>> print(A)
    {}
    >>> A(color='red',alpha=0.7,ontop=True)
    >>> print(A)
    {'color': 'red', 'alpha': 0.7, 'ontop': True}
    >>> A.ontop = None
    >>> A.alpha = 0.8
    >>> print(A)
    {'color': 'red', 'alpha': 0.8}
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
    """

    def __init__(self,data={},default=None):
        """Create a new Attributes dict"""
        if isinstance(default,Attributes):
            self._default_dict_ = default
            default = self._return_default_
        else:
            default = returnNone

        Dict.__init__(self,data,default)

    def __call__(self,**kargs):
        self.update(kargs)


    def __setattr__(self,key,value):
        if value is None:
            if key in self:
                del self[key]
        else:
            self.__setitem__(key,value)


    def _return_default_(self,key):
        return self._default_dict_[key]


    def __str__(self):
        from utils import removeDict
        return dict.__str__(removeDict(self,['_default_dict_']))

# End
