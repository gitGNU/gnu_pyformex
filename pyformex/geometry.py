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
"""A generic interface to the Coords transformation methods

This module defines a generic Geometry superclass which adds all the
possibilities of coordinate transformations offered by the
Coords class to the derived classes.
"""
from __future__ import print_function

from pyformex import zip
from pyformex import utils
from pyformex.coords import Coords, Int
from pyformex.attributes import Attributes
from pyformex.odict import OrderedDict
from pyformex.olist import List
import pyformex.arraytools as at
import numpy as np


class Geometry(object):
    """A generic geometry object allowing transformation of coords sets.

    The Geometry class is a generic parent class for all geometric classes,
    intended to make the Coords transformations available without explicit
    declaration. This class is not intended to be used directly, only
    through derived classes. Examples of derived classes are :class:`Formex`,
    :class:`Mesh`, :class:`Curve`.

    The Geometry class defines a set of methods which
    operate on the attribute `coords`, which should be a Coords object.
    Most of the transformation methods of the Coords class are thus exported
    through the Geometry class to its derived classes, and when called, will
    get executed on the `coords` attribute.
    The derived class constructor should make sure that the `coords` attribute
    exists, has the proper type and contains the coordinates of all the points
    that should get transformed under a Coords transformation.
    The derived classes should also call the Geometry initializer to create the
    'attrib' attribute.

    Derived classes can (and in most cases should) declare a method
    `_set_coords(coords)` returning an object that is identical to the
    original, except for its coords being replaced by new ones with the
    same array shape.

    The Geometry class provides two possible default implementations:

    - `_set_coords_inplace` sets the coords attribute to the provided new
      coords, thus changing the object itself, and returns itself,
    - `_set_coords_copy` creates a deep copy of the object before setting
      the coords attribute. The original object is unchanged, the returned
      one is the changed copy.

    When using the first method, a statement like ``B = A.scale(0.5)``
    will result in both `A` and `B` pointing to the same scaled object,
    while with the second method, `A` would still be the untransformed
    object. Since the latter is in line with the design philosophy of
    pyFormex, it is set as the default `_set_coords` method.
    Most derived classes that are part of pyFormex however override this
    default and implement a more efficient copy method.

    The following :class:`Geometry` methods return the value of the same
    method applied on the `coords` attribute. Refer to the correponding
    :class:`coords.Coords` method for their precise arguments.

    :meth:`x`,
    :meth:`y`,
    :meth:`z`,
    :meth:`bbox`,
    :meth:`center`,
    :meth:`centroid`,
    :meth:`sizes`,
    :meth:`dsize`,
    :meth:`bsphere`,
    :meth:`inertia`,
    :meth:`distanceFromPlane`,
    :meth:`distanceFromLine`,
    :meth:`distanceFromPoint`,
    :meth:`directionalSize`,
    :meth:`directionalWidth`,
    :meth:`directionalExtremes`,
    :meth:`__str__`.


    The following :class:`Coords` transformation methods can be directly applied
    to a :class:`Geometry` object or a derived class object. The return value
    is a new object identical to the original, except for the coordinates,
    which will have been transformed by the specified method.
    Refer to the correponding :class:`coords.Coords` method in for the precise
    arguments of these methods:

    :meth:`scale`,
    :meth:`translate`,
    :meth:`centered`,
    :meth:`rotate`,
    :meth:`shear`,
    :meth:`reflect`,
    :meth:`affine`,
    :meth:`position`,
    :meth:`cylindrical`,
    :meth:`hyperCylindrical`,
    :meth:`toCylindrical`,
    :meth:`spherical`,
    :meth:`superSpherical`,
    :meth:`toSpherical`,
    :meth:`bump`,
    :meth:`bump1`,
    :meth:`bump2`,
    :meth:`flare`,
    :meth:`map`,
    :meth:`map1`,
    :meth:`mapd`,
    :meth:`replace`,
    :meth:`swapAxes`,
    :meth:`rollAxes`,
    :meth:`projectOnPlane`,
    :meth:`projectOnSphere`,
    :meth:`projectOnCylinder`,
    :meth:`isopar`,
    :meth:`transformCS`,
    :meth:`addNoise`,
    :meth:`rot`,
    :meth:`trl`.
    """

    def __init__(self):
        """Initialize a Geometry"""
        self.attrib = Attributes()


    ########### Information from the coords #################

    def _coords_method(func):
        """Call a method on the .coords attribute of the object.

        This is a decorator function.
        """
        coords_func = getattr(Coords, func.__name__)
        def newf(self,*args,**kargs):
            """Call the Coords %s method on the coords attribute"""
            return coords_func(self.coords,*args,**kargs)
        newf.__name__ = func.__name__
        newf.__doc__ ="""Call '%s' method on the coords attribute of the Geometry object.

        See :meth:`coords.Coords.%s` for details.
""" % (func.__name__, func.__name__)
        return newf

    ########### Change the coords #################

    def _coords_transform(func):
        """Perform a transformation on the .coords attribute of the object.

        This is a decorator function.
        """
        coords_func = getattr(Coords, func.__name__)
        def newf(self,*args,**kargs):
            """Performs the Coords %s transformation on the coords attribute"""
            return self._set_coords(coords_func(self.coords,*args,**kargs))
        newf.__name__ = func.__name__
        newf.__doc__ ="""Apply '%s' transformation to the Geometry object.

        See :meth:`coords.Coords.%s` for details.
""" % (func.__name__, func.__name__)
        return newf


    def _set_coords_inplace(self, coords):
        """Replace the current coords with new ones.

        """
        coords = Coords(coords)
        if coords.shape == self.coords.shape:
            self.coords = coords
            return self
        else:
            raise ValueError("Invalid reinitialization of Geometry coords")


    def _set_coords_copy(self, coords):
        """Return a copy of the object with new coordinates replacing the old.

        """
        return self.copy()._set_coords_inplace(coords)

    _set_coords = _set_coords_copy


    def nelems(self):
        """Return the number of elements in the Geometry.

        This method should be re-implemented by the derived classes.
        For the (empty) Geometry class it always returns 0.
        """
        return 0


##############################################################################
#
#  These are the methods that change a Geometry !
#
##############################################################################

    def setProp(self,prop=None,blocks=None):
        """Create or destroy the property array for the Geometry.

        A property array is a rank-1 integer array with dimension equal
        to the number of elements in the Geometry. Each element thus has its
        own property number. These numbers can be used for any purpose.
        They play an import role when creating new geometry: new elements
        inherit the property number of their parent element.
        Properties are also preserved on most geometrical transformations.

        Because elements with different property numbers can be drawn in
        different colors, the property numbers are also often used to impose
        color.

        Parameters:

        - `prop`: a single integer value or a list/array of integer values.
          If the number of passed values is less than the number of elements,
          they wil be repeated. If you give more, they will be ignored.

          The special value 'range' will set the property numbers
          equal to the element number.

          A value None (default) removes the properties from the Geometry.

        - `blocks`: a single integer value or a list/array of integer values.
          If the number of passed values is less than the length of `prop`,
          they wil be repeated. If you give more, they will be ignored.
          Every prop will be repeated the corresponding number of times
          specified in blocks.

        Returns the Geometry with the new properties inserted or with the
          properties deleted (if argument is None).
          Notice that unlike most other Geometry methods, this method changes
          (and returns) the existing object.
        """
        if prop is None:
            self.prop = None
        else:
            if prop == 'range':
                prop = np.arange(self.nelems())
            else:
                prop = np.array(prop)

            if blocks is not None:
                if isinstance(blocks, int):
                    blocks = [blocks]
                blocks = np.resize(blocks, prop.ravel().shape)
                prop = np.concatenate([np.resize(p, b) for p, b in zip(prop, blocks)]).astype(Int)

            self.prop = self.toProp(prop)
        return self


##############################################################################
#
#  All other methods leave the object untouched, and return a copy instead.
#
##############################################################################

    def toProp(self, prop):
        """Converts the argument into a legal set of properties for the object.

        The conversion involves resizing the argument to a 1D array of
        length self.nelems(), and converting the data type to integer.
        """
        return np.resize(prop, (self.nelems(),)).astype(Int)


    def whereProp(self, val):
        """Return the numbers of the elements with property val.

        val is either a single integer, or a list/array of integers.
        The return value is an array holding all the numbers of all the
        elements that have the property val, resp. one of the values in val.

        If the object has no properties, a empty array is returned.
        """
        if self.prop is not None and np.array(val).size > 0:
            return np.concatenate([np.where(self.prop==v)[0] for v in np.unique(np.array(val))])
        return np.array([], dtype=Int)


    ########### Return information about the coords #################

    def getCoords(self):
        """Get the coords data.

        Returns the full array of coordinates stored in the Geometry object.
        Note that subclasses may store more points in this array than are used
        to define the geometry.
        """
        return self.coords


    def points(self):
        return self.coords.points()
    @property
    def x(self):
        return self.coords.x
    @property
    def y(self):
        return self.coords.y
    @property
    def z(self):
        return self.coords.z
    @property
    def xy(self):
        return self.coords.xy
    @property
    def yz(self):
        return self.coords.yz
    @property
    def xz(self):
        return self.coords.xz
    @property
    def xyz(self):
        return self.coords.xyz
    @x.setter
    def x(self, value):
        self.coords.x = value
    @y.setter
    def y(self, value):
        self.coords.y = value
    @z.setter
    def z(self, value):
        self.coords.z = value
    @xy.setter
    def xy(self, value):
        self.coords.xy = value
    @yz.setter
    def yz(self, value):
        self.coords.yz = value
    @xz.setter
    def xz(self, value):
        self.coords.xz = value
    @xyz.setter
    def xyz(self, value):
        self.coords.xyz = value
    def bbox(self):
        return self.coords.bbox()
    def center(self):
        return self.coords.center()
    def bboxPoint(self,*args,**kargs):
        return self.coords.bboxPoint(*args,**kargs)
    def centroid(self):
        return self.coords.centroid()
    def sizes(self):
        return self.coords.sizes()
    def dsize(self):
        return self.coords.dsize()
    def bsphere(self):
        return self.coords.bsphere()
    def bboxes(self):
        return self.coords.bboxes()
    def inertia(self,*args,**kargs):
        return self.coords.inertia(*args,**kargs)
    def prinCS(self,*args,**kargs):
        return self.coords.prinCS(*args,**kargs)
    def principalSizes(self):
        return self.coords.principalSizes()
    def principalBbox(self):
        return self.coords.principalBbox()
    def convexHull(self,dir=None,return_mesh=True):
        """Return the convex hull of a Coords.

        This works like :meth:`Coords.convexHull`, but has return_mesh=True
        as default. It is equivalent with::

          self.coords.convexHull(dir,return_mesh)

        """
        return self.coords.convexHull(dir,return_mesh)


    def info(self):
        return "Geometry: coords shape = %s; level = %s" % (self.coords.shape, self.level())
    def level(self):
        """Return the dimensionality of the Geometry, or -1 if unknown"""
        return -1

    def distanceFromPlane(self,*args,**kargs):
        return self.coords.distanceFromPlane(*args,**kargs)
    def distanceFromLine(self,*args,**kargs):
        return self.coords.distanceFromLine(*args,**kargs)
    def distanceFromPoint(self,*args,**kargs):
        return self.coords.distanceFromPoint(*args,**kargs)
    def directionalSize(self,*args,**kargs):
        return self.coords.directionalSize(*args,**kargs)
    def directionalWidth(self,*args,**kargs):
        return self.coords.directionalWidth(*args,**kargs)
    def directionalExtremes(self,*args,**kargs):
        return self.coords.directionalExtremes(*args,**kargs)

    def __str__(self):
        return self.coords.__str__()

    ########### Return a copy or selection #################

    def copy(self):
        """Return a deep copy of the Geometry  object.

        The returned object is an exact copy of the input, but has
        all of its data independent of the former.
        """
        from copy import deepcopy
        return deepcopy(self)


    @utils.warning("warn_select_changed")
    def select(self,sel,compact=False):
        """Return a Geometry only containing the selected elements.

        Parameters:

        - `sel`: an object that can be used as an index in an array:

          - a single element number
          - a list, or array, of element numbers
          - a bool list, or array, of length self.nelems(), where True values
            flag the elements to be selected

        - `compact`: boolean. Only useful for Mesh type Geometries.
          If True (default), the returned Mesh will be compacted, i.e.
          the unused nodes are removed and the nodes are renumbered from
          zero. If False, returns the node set and numbers unchanged.

        Returns a Geometry (or subclass) with only the selected elements.

        See :meth:`cselect` for the complementary operation.
        """
        return self._select(sel, compact=compact)


    @utils.warning("warn_select_changed")
    def cselect(self,sel,compact=False):
        """Return a Geometry with the selected elements removed.

        Parameters:

        - `sel`: an object that can be used as an index in an array:

          - a single element number
          - a list, or array, of element numbers
          - a bool list, or array, of length self.nelems(), where True values
            flag the elements to be selected

        - `compact`: boolean. Only useful for Mesh type Geometries.
          If True (default), the returned Mesh will be compacted, i.e.
          the unused nodes are removed and the nodes are renumbered from
          zero. If False, returns the node set and numbers unchanged.
        - `sel`: an object that can be used as an index in the
          `elems` array, such as

          - a single element number
          - a list, or array, of element numbers
          - a bool list, or array, of length self.nelems(), where True values
            flag the elements to be selected

        - `compact`: boolean. Only useful for Mesh type Geometries.
          If True (default), the returned Mesh will be compacted, i.e.
          the unused nodes are removed and the nodes are renumbered from
          zero. If False, returns the node set and numbers unchanged.

        Returns a Geometry (or subclass) with all but the selected elements.

        This is the complimentary operation of :meth:`select`.
        """
        return self._select(at.complement(sel, self.nelems()), compact=compact)


    @utils.warning("warn_clip_changed")
    def clip(self, sel):
        """Return a Geometry only containing the selected elements.

        For a Formex, this is equivalent with select(sel).
        For a Mesh, this is equivalent with select(sel,compact=True).

        See :meth:`select` for more information.
        """
        return self.select(sel, compact=True)


    @utils.warning("warn_clip_changed")
    def cclip(self, sel):
        """Return a Geometry with the selected elements removed.

        For a Formex, this is equivalent with cselect(sel).
        For a Mesh, this is equivalent with cselect(sel,compact=True).

        See :meth:`cselect` for more information.

        This is the complimentary operation of :meth:`clip`.
        """
        return self.cselect(sel, compact=True)


    def selectProp(self, val, compact=False):
        """Return an object which holds only the elements with property val.

        val is either a single integer, or a list/array of integers.
        The return value is a object holding all the elements that
        have the property val, resp. one of the values in val.
        The returned object inherits the matching properties.

        If the object has no properties, a copy with all elements is returned.
        """
        if self.prop is None:
            return self.copy()
        else:
            return self._select(self.whereProp(val), compact=compact)


    def cselectProp(self, val, compact=False):
        """Return an object without the elements with property `val`.

        This is the complementary method of selectProp.
        val is either a single integer, or a list/array of integers.
        The return value is a object holding all the elements that do not
        have the property val, resp. one of the values in val.
        The returned object inherits the matching properties.

        If the object has no properties, a copy with all elements is returned.
        """
        if self.prop is None:
            return self.copy()
        else:
            return self.cselect(self.whereProp(val), compact=compact)


    def splitProp(self,prop=None,compact=True):
        """Partition a Geometry (Formex/Mesh) according to the values in prop.

        Parameters:

        - `prop`: an int array with length self.nelems(), or None. If None,
          the `prop` attribute of the Geometry is used.

        Returns a list of Geometry objects of the same type as the input.
        Each object contains all the elements having the same value of `prop`.
        The number of objects in the list is equal to the number of unique
        values in `prop`. The list is sorted in ascending order of their
        `prop` value.

        If `prop` is None and the the object has no `prop` attribute, an empty
        list is returned.
        """
        if prop is None:
            prop = self.prop
        else:
            prop = self.toProp(prop)
        if prop is None:
            split = []
        else:
            split = [ self.select(prop==p,compact=compact) for p in np.unique(prop) ]
        return List(split)


    ########### Coords transformations #################

    @_coords_transform
    def scale(self,*args,**kargs):
        pass


    def resized(self,size=1.,tol=1.e-5):
        """Return a copy of the Geometry scaled to the given size.

        size can be a single value or a list of three values for the
        three coordinate directions. If it is a single value, all directions
        are scaled to the same size.
        Directions for which the geometry has a size smaller than tol times
        the maximum size are not rescaled.
        """
        from numpy import resize
        s = self.sizes()
        size = Coords(resize(size, (3,)))
        ignore = s<tol*s.max()
        s[ignore] = size[ignore]
        return self.scale(size/s)


    @_coords_transform
    def adjust(self,*args,**kargs):
        pass
    @_coords_transform
    def translate(self,*args,**kargs):
        pass
    @_coords_transform
    def centered(self,*args,**kargs):
        pass
    @_coords_transform
    def align(self,*args,**kargs):
        pass
    @_coords_transform
    def rotate(self,*args,**kargs):
        pass
    @_coords_transform
    def shear(self,*args,**kargs):
        pass
    @_coords_transform
    def reflect(self,*args,**kargs):
        pass
    @_coords_transform
    def affine(self,*args,**kargs):
        pass
    @_coords_transform
    def toCS(self,*args,**kargs):
        pass
    @_coords_transform
    def fromCS(self,*args,**kargs):
        pass
    @_coords_transform
    def position(self,*args,**kargs):
        pass


    @_coords_transform
    def cylindrical(self,*args,**kargs):
        pass
    @_coords_transform
    def hyperCylindrical(self,*args,**kargs):
        pass
    @_coords_transform
    def toCylindrical(self,*args,**kargs):
        pass
    @_coords_transform
    def spherical(self,*args,**kargs):
        pass
    @_coords_transform
    def superSpherical(self,*args,**kargs):
        pass
    @_coords_transform
    def egg(self,*args,**kargs):
        pass
    @_coords_transform
    def toSpherical(self,*args,**kargs):
        pass
    @_coords_transform

    def bump(self,*args,**kargs):
        pass
    @_coords_transform
    def bump1(self,*args,**kargs):
        pass
    @_coords_transform
    def bump2(self,*args,**kargs):
        pass
    @_coords_transform
    def flare(self,*args,**kargs):
        pass
    @_coords_transform
    def map(self,*args,**kargs):
        pass
    @_coords_transform
    def map1(self,*args,**kargs):
        pass
    @_coords_transform
    def mapd(self,*args,**kargs):
        pass

    @_coords_transform
    def replace(self,*args,**kargs):
        pass
    @_coords_transform
    def swapAxes(self,*args,**kargs):
        pass
    @_coords_transform
    def rollAxes(self,*args,**kargs):
        pass

    @_coords_transform
    def projectOnPlane(self,*args,**kargs):
        pass
    @_coords_transform
    def projectOnSphere(self,*args,**kargs):
        pass
    @_coords_transform
    def projectOnCylinder(self,*args,**kargs):
        pass
    @_coords_transform
    def isopar(self,*args,**kargs):
        pass
    @_coords_transform
    def transformCS(self,*args,**kargs):
        pass
    @_coords_transform
    def addNoise(self,*args,**kargs):
        pass

    rot = rotate
    trl = translate


    @property
    def fields(self):
        """Return the Fields dict of this Geometry.

        If the Geometry has no Fields, an empty dict is returned.
        """
        if hasattr(self,'_fields'):
            return self._fields
        else:
            return {}


    def addField(self,fldtype,data,fldname):
        """Add a data field to the geometry.

        Add a scalar or vectorial field defined over the domain of the
        Geometry. This creates a :class:`Field` instance with the specified
        parameters and adds it to the Geometry object.
        Fields stored inside a Geometry object are exported to PGF file
        whenever the object is exported.

        Parameters:

        - `fldtype`, `data`, `fldname`: are passed together with the
          Geometry object to the Field initialization. See :class:`Field`
          for details.

        """
        from pyformex.field import Field

        if not hasattr(self,'fieldtypes') or fldtype not in self.fieldtypes:
            raise ValueError("Can not add field of type '%s' to a %s" % (fldtype,self.__class__.__name__))

        fld = Field(self,fldtype,data,fldname)
        self.add_field(fld)


    def add_field(self,field):
        """Low level function to add a Field"""
        if not hasattr(self,'_fields'):
            self._fields = OrderedDict()
        self._fields[field.fldname] = field


    def convertField(self,fldname,totype,toname):
        """Convert the data field with the specified name.

        If the data field does not exist, returns None
        """
        if fldname in self.fields:
            fld = self.fields[fldname].convert(totype,toname)
            self.add_field(fld)


    def getField(self,fldname):
        """Get the data field with the specified name.

        If the data field does not exist, returns None
        """
        if fldname in self.fields:
            return self.fields[fldname]


    def delField(self,fldname):
        """Delete the Field with the given name.

        A nonexisting name is silently ignored.
        """
        if fldname in self.fields:
            del self.fields[fldname]


    @property
    def fields(self):
        if hasattr(self,'_fields'):
            return self._fields
        else:
            return {}


    def fieldReport(self):
        """Print a short report of the stored fields"""
        return '\n'.join([
            "Field '%s', fldtype '%s', dtype %s, shape %s" % \
            (f.fldname,f.fldtype,f.data.dtype,f.data.shape) \
            for f in self.fields.values() ])


    def write(self,filename,sep=' ',mode='w'):
        """Write a Geometry to a .pgf file.

        This writes the Geometry to a pyFormex Geometry File (PGF) with
        the specified name.

        It is a convenient shorthand for::

          script.writeGeomFile(filename, self, sep=sep, mode=mode)

        """
        from pyformex.script import writeGeomFile
        writeGeomFile(filename, self, sep=sep, mode=mode)


    @classmethod
    def read(clas,filename):
        """Read a Geometry from a PGF file.

        This reads a single object (the object) from a PGF file
        and returns it.

        It is a convenient shorthand for::

          script.readGeomFile(filename, 1).values()[0]
        """
        from pyformex.script import readGeomFile
        res = readGeomFile(filename,1)
        return res.values()[0]


if __name__ == '__draw__':

    from pyformex.gui.draw import draw

    def draw(self,*args,**kargs):
        draw(self.coords,*args,**kargs)


    clear()
    F = Formex('4:0123')

    G = Geometry()
    G.coords = F.coords
    G.draw(color='red')

    G1 = G.scale(2).trl([0.2, 0.7, 0.])
    G1.draw(color='green')

    G2 = G.translate([0.5, 0.5, 0.5])
    G2.draw(color='blue')

    print(Geometry.scale.__doc__)
    print(Coords.scale.__doc__)

# End
