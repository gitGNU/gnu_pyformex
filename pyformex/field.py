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
#
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see http://www.gnu.org/licenses/.
##

"""Field data in pyFormex.

This module defines the Field class, which can be used to describe
scalar and vectorial field data over a geometrical domain.
"""
from __future__ import print_function

import pyformex as pf
from pyformex import utils
import pyformex.arraytools as at
from pyformex.formex import Formex
from pyformex.mesh import Mesh


##############################################################

class Field(object):

    """Scalar or vectorial field data defined over a geometric domain.

    A scalar data field is a quantity having exactly one value in each
    point of some geometric domain. A vectorial field is a quantity having
    exactly `nval` values at each point, where `nval >= 1`.
    A vectorial field can also be considered as a collection of `nval`
    scalar fields: as far as the Field class is concerned, there is no
    relation between the `nval` components of a vectorial field.

    The definition of a field is always tied to some geometric domain.
    Currently pyFormex allows fields to be defined on Formex and Mesh
    type geometries.

    Fields should only be defined on geometries whose topology does not
    change anymore. This means that for Formex type, the shape of the
    `coords` attribute should not be changed, and for Mesh type, the
    shape of `coords` and the full contents of `elems` should not be
    changed. It is therefore best ot only add filed data to geometry
    objects that will not be changed in place.
    Nearly all methods in pyFormex return a copy of the object, and the
    copy currently looses all the fields defined on the parent.
    In future however, selected transformations may inherit fields from
    the parent.

    While Field class instances are usually created automatically by the
    :func:`Geometry.addField` method of some Geometry,
    it is possible to create Field
    instances yourself and manage the objects like you want. The Fields
    stored inside Geometry objects have some special features though,
    like being exported to a PGF file together with the geometry.

    A Field is defined by the following parameters:

    - `geometry`: Geometry instance: describes the geometrical domain
      over which the field is defined. Currently this has to be a
      :class:`Formex` or a :class:`Mesh`.

    - `fldtype`: string: one of the following predefined field types:

      - 'node': the field data are specified at the nodes of the geometry;
      - 'elemc': the field data are constant per element;
      - 'elemn': the field data vary over the element and are specified at
        the nodes of the elements;
      - 'elemg': the field data are specified at a number of points of
        the elements, from which they can be inter- or extrapolated;

      The actually available field types depend on the type of the
      `geometry` object. :class:`Formex` type has only 'elemc' and 'elemn'.
      `Mesh` currently has 'node', 'elemc' and 'elemn'.

    - `data`: an array with the field values defined at the specified
      points. The required shape of the array depends on `fldtype`:

      - 'node':  ( nnodes, ) or ( nval, nnodes )
      - 'elemc': ( nelems, ) or ( nval, nelems )
      - 'elemn': ( nelems, nplex ) or  (nval, nelems, nplex )
      - 'elemg': ( nelems, ngp ) or  (nval, nelems, ngp )

    - `fldname`: string: the name used to identify the field. Fields
      stored in a Geometry object can be retrieved using this name. See
      :func:`Geometry.getField`. If no name is specified, one is generated.

    """

    _autoname = utils.NameSequence('Field-0')


    def __init__(self,geometry,fldtype,data,fldname=None):
        """Initialize a Field.

        """
        if not hasattr(geometry,'fieldtypes') or fldtype not in geometry.fieldtypes:
            raise ValueError("Can not add field of type '%s' to a %s" % (fldtype,geometry.__class__.__name__))

        if fldtype == 'node':
            datashape = (-1,geometry.nnodes(),)
        elif fldtype == 'elemc':
            datashape = (-1,geometry.nelems(),)
        elif fldtype == 'elemn':
            datashape = (-1,geometry.nelems(),geometry.nplex())
        elif fldtype == 'elemg':
            datashape = (-1,geometry.nelems(),-1)

        if len(data.shape) < len(datashape):
            data = data.reshape((-1,)+data.shape)
        data = at.checkArray(data,shape=datashape)

        if fldname is None:
            fldname = Field._autoname.next()

        # All data seem OK, store them
        self.geometry = geometry
        self.fldname = fldname
        self.fldtype = fldtype
        self.data = data


    def convert(self,totype,toname=None):
        """Convert a Field to another type.

        """
        data = None
        if totype in self.geometry.fieldtypes:
            if self.fldtype == 'node':
                if totype == 'elemn':
                    data = self.data[:,self.geometry.elems]
                elif totype == 'elemc':
                    data = self.convert('elemn').convert('elemc')
            elif self.fldtype == 'elemn':
                if totype == 'elemc':
                    data = self.data.mean(axis=-1)
                elif totype == 'node':
                    data = nodalSum(data,self.geometry.elems,avg=True,return_all=False)
                    if data.shape[-1] < self.geometry.nnodes():
                        data = growAxis(data,self.geometry.nnodes()-data.shape[-1])
            elif self.fldtype == 'elemc':
                if totype == 'elemn':
                    data = repeat(data,self.geometry.nplex(),axis=-1)
                elif totype == 'node':
                    data = self.convert('elemn').convert('node')

        if data is None:
            raise ValueError("Can not convert %s field data from '%s' to '%s'" % (self.geometry.__class__.__name__,fromtype,totype))

        return Field(self.geometry,totype,data,toname)


# End
