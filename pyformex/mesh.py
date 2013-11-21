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

"""Finite element meshes in pyFormex.

This module defines the Mesh class, which can be used to describe discrete
geometrical models like those used in Finite Element models.
It also contains some useful functions to create such models.
"""
from __future__ import print_function

from arraytools import groupPositions
from coords import *
from formex import Formex
from connectivity import Connectivity
from elements import elementType
from geometry import Geometry
from attributes import Attributes
from simple import regularGrid
import utils


##############################################################

class Mesh(Geometry):
    """A Mesh is a discrete geometrical model defined by nodes and elements.

    In the Mesh geometrical data model, the coordinates of all the points
    are gathered in a single twodimensional array with shape (ncoords,3).
    The individual geometrical elements are then described by indices into
    the coordinates array.

    This model has some advantages over the Formex data model (which stores
    all the points of all the elements by their coordinates):

    - a more compact storage, because coordinates of coinciding
      points are not repeated,
    - faster connectivity related algorithms.

    The downside is that geometry generating algorithms are far more complex
    and possibly slower.

    In pyFormex we therefore mostly use the Formex data model when creating
    geometry, but when we come to the point of exporting the geometry to
    file (and to other programs), a Mesh data model may be more adequate.

    The Mesh data model has at least the following attributes:

    - `coords`: (ncoords,3) shaped Coords object, holding the coordinates of
      all points in the Mesh;
    - `elems`: (nelems,nplex) shaped Connectivity object, defining the elements
      by indices into the Coords array. All values in elems should be in the
      range 0 <= value < ncoords.
    - `prop`: an array of element property numbers, default None.
    - `eltype`: an element type (a subclass of :class:`Element`) or the name
      of an Element type, or None (default).
      If eltype is None, the eltype of the elems Connectivity table is used,
      and if that is missing, a default eltype is derived from the plexitude,
      by a call to :func:`elements.elementType`.
      In most cases the eltype can be set automatically.
      The user can override the default value, but an error will occur if
      the element type does not exist or does not match the plexitude.

    A Mesh can be initialized by its attributes (coords,elems,prop,eltype)
    or by a single geometric object that provides a toMesh() method.

    If only an element type is provided, a unit sized single element Mesh
    of that type is created. Without parameters, an empty Mesh is created.

    """
    ###################################################################
    ## DEVELOPERS: ATTENTION
    ##
    ## Because the TriSurface is derived from Mesh, all methods which
    ## return a Mesh and will also work correctly on a TriSurface,
    ## should use self.__class__ to return the proper class, and they
    ## should specify the prop and eltype arguments using keywords
    ## (because only the first two arguments match).
    ## See the copy() method for an example.
    ###################################################################

    def _formex_transform(func):
        """Perform a Formex transformation on the .coords attribute of the object.

        This is a decorator function. It should be used only for Formex methods
        which are not Geometry methods as well.
        """
        formex_func = getattr(Formex,func.__name__)
        def newf(self,*args,**kargs):
            """Performs the Formex %s transformation on the coords attribute"""
            F = Formex(self.coords).formex_func(self.coords,*args,**kargs)
            return self._set_coords(coords_func(self.coords,*args,**kargs))
        newf.__name__ = func.__name__
        newf.__doc__ = coords_func.__doc__
        return newf


    def __init__(self,coords=None,elems=None,prop=None,eltype=None):
        """Initialize a new Mesh."""
        self.attrib = Attributes()
        self.coords = self.elems = self.prop = None
        self.ndim = -1
        self.nodes = self.edges = self.faces = self.cells = None
        self.elem_edges = self.eadj = None
        self.conn = self.econn = self.fconn = None

        if coords is None:
            if eltype is None:
                # Create an empty Mesh object
                return

            else:
                # Create unit Mesh of specified type
                el = elementType(eltype)
                coords = el.vertices
                elems = el.getElement()

        if elems is None:
            # A single object was specified instead of (coords,elems) pair
            try:
                # initialize from a single object
                if isinstance(coords,Mesh):
                    M = coords
                else:
                    M = coords.toMesh()
                coords,elems = M.coords,M.elems
            except:
                raise ValueError,"No `elems` specified and the first argument can not be converted to a Mesh."

        try:
            self.coords = Coords(coords)
            if self.coords.ndim != 2:
                raise ValueError,"\nExpected 2D coordinate array, got %s" % self.coords.ndim
            self.elems = Connectivity(elems)
            if self.elems.size > 0 and (
                self.elems.max() >= self.coords.shape[0] or
                self.elems.min() < 0):
                raise ValueError,"\nInvalid connectivity data: some node number(s) not in coords array (min=%s, max=%s, ncoords=%s)" % (self.elems.min(),self.elems.max(),self.coords.shape[0])
        except:
            raise

        self.setType(eltype)
        self.setProp(prop)



    def __getattribute__(self,name):
        """This is temporarily here to warn people about the eltype removal"""
        if name == 'eltype':
            utils.warn("warn_mesh_removed_eltype")

        # Default behaviour
        return object.__getattribute__(self, name)


    def _set_coords(self,coords):
        """Replace the current coords with new ones.

        Returns a Mesh or subclass exactly like the current except
        for the position of the coordinates.
        """
        if isinstance(coords,Coords) and coords.shape == self.coords.shape:
            return self.__class__(coords,self.elems,prop=self.prop,eltype=self.elType())
        else:
            raise ValueError,"Invalid reinitialization of %s coords" % self.__class__


    def setType(self,eltype=None):
        """Set the eltype from a character string.

        This function allows the user to change the element type of the Mesh.
        The input is a character string with the name of one of the element
        defined in elements.py. The function will only allow to set a type
        matching the plexitude of the Mesh.

        This method is seldom needed, because the applications should
        normally set the element type at creation time.
        """
        # For compatibility reasons, the eltype is set as an attribute
        # of both the Mesh and the Mesh.elems attribute
        if eltype is None and hasattr(self.elems,'eltype'):
            eltype = self.elems.eltype
        self.elems.eltype = elementType(eltype,self.nplex())
        if self.elems.eltype is None:
            raise ValueError,"No element type set for Mesh/Connectivity"
        return self


    def elType(self):
        """Return the element type of the Mesh.

        """
        return self.elems.eltype


    def elName(self):
        """Return the element name of the Mesh.

        """
        return self.elType().name()


    ## def setProp(self,prop=None):
    ##     """Create or destroy the property array for the Mesh.

    ##     A property array is a rank-1 integer array with dimension equal
    ##     to the number of elements in the Mesh.
    ##     You can specify a single value or a list/array of integer values.
    ##     If the number of passed values is less than the number of elements,
    ##     they wil be repeated. If you give more, they will be ignored.

    ##     If a value None is given, the properties are removed from the Mesh.
    ##     """
    ##     if prop is None:
    ##         self.prop = None
    ##     else:
    ##         prop = array(prop).astype(Int)
    ##         self.prop = resize(prop,(self.nelems(),))
    ##     return self


    def setNormals(self,normals=None):
        """Set/Remove the normals of the mesh.

        """
        import geomtools as gt
        if normals is None:
            pass
        elif normals == 'auto':
            normals = gt.polygonNormals(self.coords[self.elems])
        elif normals == 'avg':
            normals = gt.averageNormals(self.coords,self.elems)
        else:
            normals = checkArray(normals,(self.nelems(),self.nplex(),3),'f')
        self.normals = normals


    def __getitem__(self,i):
        """Return element i of the Mesh.

        This allows addressing element i of Mesh M as M[i].
        The return value is an array with the coordinates of all the points
        of the element. M[i][j] then will return the coordinates of node j
        of element i.
        This also allows to change the individual coordinates or nodes, by
        an assignment like  M[i][j] = [1.,0.,0.].
        """
        return self.coords[self.elems[i]]


    def __setitem__(self,i,val):
        """Change element i of the Mesh.

        This allows changing all the coordinates of an element by direct
        assignment such as M[i] = [[1.,0.,0.], ...]. The user should make sure
        that the data match the plexitude of the element.
        """
        self.coords[i] = val


    ## def __getstate__(self):
    ##     import copy
    ##     state = copy.copy(self.__dict__)
    ##     #print("GOT = %s" % sorted(state.keys()))
    ##     # Store the element type by name,
    ##     # This is needed because of the way ElementType is initialized
    ##     # Maybe we should change that.
    ##     # The setstate then needs to set the elementType
    ##     # And this needs also to be done in Connectivity, if it has an eltype
    ##     ## try:
    ##     ##     state['eltype'] = state['eltype'].name()
    ##     ## except:
    ##     ##state['eltype'] = None
    ##     if 'eltype' in state:
    ##         del state['eltype']
    ##     #print("STORE = %s" % sorted(state.keys()))
    ##     return state


    def __setstate__(self,state):
        """Set the object from serialized state.

        This allows to read back old pyFormex Project files where the Mesh
        class did not set element type yet.
        """
        elems = state['elems']
        if 'eltype' in state:
            if state['eltype'] is not None:
                # We acknowledge this eltype, even if it is also stored
                # in elems. This makes the restore also work for older projects
                # where eltype was not in elems.
                elems.eltype = elementType(state['eltype'])
            # Do not store the eltype in the Mesh anymore
            del state['eltype']
        else:
            # No eltype in Mesh
            if hasattr(elems,'eltype'):
                # eltype in elems: leave as it is
                pass
            else:
                # Try to set elems eltype from plexitude
                try:
                    elems.eltype = elementType(nplex=elems.nplex())
                except:
                    raise ValueError,"I can not restore a Mesh without eltype"
        self.__dict__.update(state)


    def getProp(self):
        """Return the properties as a numpy array (ndarray)"""
        return self.prop


    def maxProp(self):
        """Return the highest property value used, or None"""
        if self.prop is None:
            return None
        else:
            return self.prop.max()


    def propSet(self):
        """Return a list with unique property values."""
        if self.prop is None:
            return None
        else:
            return unique(self.prop)


    def shallowCopy(self,prop=None):
        """Return a shallow copy.

        A shallow copy of a Mesh is a Mesh object using the same data arrays
        as the original Mesh. The only thing that can be changed is the
        property array. This is a convenient method to use the same Mesh
        with different property attributes.
        """
        if prop is None:
            prop = self.prop
        return self.__class__(self.coords,self.elems,prop=prop,eltype=self.elType())


    def toFormex(self):
        """Convert a Mesh to a Formex.

        The Formex inherits the element property numbers and eltype from
        the Mesh. Node property numbers however can not be translated to
        the Formex data model.
        """
        return Formex(self.coords[self.elems],self.prop,self.elName())


    def toMesh(self):
        """Convert to a Mesh.

        This just returns the Mesh object itself. It is provided as a
        convenience for use in functions that want work on different Geometry
        types.
        """
        return self


    def toSurface(self):
        """Convert a Mesh to a TriSurface.

        Only Meshes of level 2 (surface) and 3 (volume) can be converted to a
        TriSurface. For a level 3 Mesh, the border Mesh is taken first.
        A level 2 Mesh is converted to element type 'tri3' and then to a
        TriSurface.
        The resulting TriSurface is only fully equivalent with the input
        Mesh if the latter has element type 'tri3'.

        On success, returns a TriSurface corresponding with the input Mesh.
        If the Mesh can not be converted to a TriSurface, an error is raised.
        """
        from plugins.trisurface import TriSurface
        if self.level() == 3:
            obj = self.getBorderMesh()
        elif self.level() == 2:
            obj = self
        else:
            raise ValueError,"Can not convert a Mesh of level %s to a Surface" % self.level()

        obj = obj.convert('tri3')
        return TriSurface(obj)


    def toCurve(self):
        """Convert a Mesh to a Curve.

        If the element type is one of 'line*' types, the Mesh is converted
        to a Curve. The type of the returned Curve is dependent on the
        element type of the Mesh:

        - 'line2': PolyLine,
        - 'line3': BezierSpline (degree 2),
        - 'line4': BezierSpline (degree 3)

        This is equivalent with ::

          self.toFormex().toCurve()

        Any other type will raise an exception.
        """
        if self.elName() in ['line2','line3','line4']:
            closed = self.elems[-1,-1] == self.elems[0,0]
            return self.toFormex().toCurve(closed=closed)
        else:
            raise ValueError,"Can not convert a Mesh of type '%s' to a curve" % self.elName()


    def ndim(self):
        return 3
    def level(self):
        return self.elType().ndim
    def nelems(self):
        return self.elems.shape[0]
    def nplex(self):
        return self.elems.shape[1]
    def ncoords(self):
        return self.coords.shape[0]
    nnodes = ncoords
    npoints = ncoords
    def shape(self):
        return self.elems.shape


    def nedges(self):
        """Return the number of edges.

        This returns the number of rows that would be in getEdges(),
        without actually constructing the edges.
        The edges are not fused!
        """
        try:
            return self.nelems() * self.elType().nedges()
        except:
            return 0


    def info(self):
        """Return short info about the Mesh.

        This includes only the shape of the coords and elems arrays.
        """
        return "coords" + str(self.coords.shape) + "; elems" + str(self.elems.shape)

    def report(self,full=True):
        """Create a report on the Mesh shape and size.

        The report always contains the number of nodes, number of elements,
        plexitude, dimensionality, element type, bbox and size.
        If full==True(default), it also contains the nodal coordinate
        list and element connectivity table. Because the latter can be rather
        bulky, they can be switched off. (Though numpy will limit the printed
        output).

        TODO: We should add an option here to let numpy print the full tables.
        """
        bb = self.bbox()
        s = """
Mesh: %s nodes, %s elems, plexitude %s, ndim %s, eltype: %s
  BBox: %s, %s
  Size: %s
""" % (self.ncoords(),self.nelems(),self.nplex(),self.level(),self.elName(),bb[0],bb[1],bb[1]-bb[0])

        if full:
            s += "Coords:\n" + self.coords.__str__() +  "\nElems:\n" + self.elems.__str__()
        return s


    def __str__(self):
        """Format a Mesh in a string.

        This creates a detailed string representation of a Mesh,
        containing the report() and the lists of nodes and elements.
        """
        return self.report(False)


    def centroids(self):
        """Return the centroids of all elements of the Mesh.

        The centroid of an element is the point whose coordinates
        are the mean values of all points of the element.
        The return value is a Coords object with nelems points.
        """
        return self.coords[self.elems].mean(axis=1)


    def bboxes(self):
        """Returns the bboxes of all elements in the Mesh.

        Returns a coords with shape (nelems,2,3). Along the axis 1
        are stored the minimal and maximal values of the Coords
        in each of the elements of the Mesh.
        """
        return self.coords[self.elems].bboxes()


    def getCoords(self):
        """Get the coords data.

        Returns the full array of coordinates stored in the Mesh object.
        Note that this may contain points that are not used in the mesh.
        :meth:`compact` will remove the unused points.
        """
        return self.coords


    def getElems(self):
        """Get the elems data.

        Returns the element connectivity data as stored in the object.
        """
        return self.elems


#######################################################################
    ## Entity selection and mesh traversal ##


    @utils.deprecation("Mesh.getLowerEntitiesSelector is deprecated. Use Element.getEntities instead.")
    def getLowerEntitiesSelector(self,level=-1):
        """Get the entities of a lower dimensionality.

        """
        return self.elType().getEntities(level)


    def getLowerEntities(self,level=-1,unique=False):
        """Get the entities of a lower dimensionality.

        If the element type is defined in the :mod:`elements` module,
        this returns a Connectivity table with the entities of a lower
        dimensionality. The full list of entities with increasing
        dimensionality  0,1,2,3 is::

            ['points', 'edges', 'faces', 'cells' ]

        If level is negative, the dimensionality returned is relative
        to that of the caller. If it is positive, it is taken absolute.
        Thus, for a Mesh with a 3D element type, getLowerEntities(-1)
        returns the faces, while for a 2D element type, it returns the edges.
        For both meshes however,  getLowerEntities(+1) returns the edges.

        By default, all entities for all elements are returned and common
        entities will appear multiple times. Specifying unique=True will
        return only the unique ones.

        The return value may be an empty table, if the element type does
        not have the requested entities (e.g. the 'point' type).
        If the eltype is not defined, or the requested entity level is
        outside the range 0..3, the return value is None.
        """
        sel = self.elType().getEntities(level)
        ent = self.elems.selectNodes(sel)
        ent.eltype = sel.eltype
        if unique:
            utils.warn("depr_mesh_getlowerentities_unique")
            ent = ent.removeDuplicate()

        return ent


    def getNodes(self):
        """Return the set of unique node numbers in the Mesh.

        This returns only the node numbers that are effectively used in
        the connectivity table. For a compacted Mesh, it is equivalent to
        ``arange(self.nelems)``.
        This function also stores the result internally so that future
        requests can return it without the need for computing it again.
        """
        if self.nodes is None:
            self.nodes  = unique(self.elems)
        return self.nodes


    def getPoints(self):
        """Return the nodal coordinates of the Mesh.

        This returns only those points that are effectively used in
        the connectivity table. For a compacted Mesh, it is equal to
        the coords attribute.
        """
        return self.coords[self.getNodes()]


    def getEdges(self):
        """Return the unique edges of all the elements in the Mesh.

        This is a convenient function to create a table with the element
        edges. It is equivalent to ``self.getLowerEntities(1,unique=True)``,
        but this also stores the result internally so that future
        requests can return it without the need for computing it again.
        """
        if self.edges is None:
            self.edges = self.elems.insertLevel(1)[1]
        return self.edges


    def getFaces(self):
        """Return the unique faces of all the elements in the Mesh.

        This is a convenient function to create a table with the element
        faces. It is equivalent to ``self.getLowerEntities(2,unique=True)``,
        but this also stores the result internally so that future
        requests can return it without the need for computing it again.
        """
        if self.faces is None:
            self.faces = self.elems.insertLevel(2)[1]
        return self.faces


    def getCells(self):
        """Return the cells of the elements.

        This is a convenient function to create a table with the element
        cells. It is equivalent to ``self.getLowerEntities(3,unique=True)``,
        but this also stores the result internally so that future
        requests can return it without the need for computing it again.
        """
        if self.cells is None:
            self.cells = self.elems.insertLevel(3)[1]
        return self.cells


    def getElemEdges(self):
        """Defines the elements in function of its edges.

        This returns a Connectivity table with the elements defined in
        function of the edges. It returns the equivalent of
        ``self.elems.insertLevel(self.elType().getEntities(1))``
        but as a side effect it also stores the definition of the edges
        and the returned element to edge connectivity in the attributes
        `edges`, resp. `elem_edges`.
        """
        if self.elem_edges is None:
            self.elem_edges,self.edges = self.elems.insertLevel(1)
        return self.elem_edges


    def getFreeEntities(self,level=-1,return_indices=False):
        """Return the border of the Mesh.

        Returns a Connectivity table with the free entities of the
        specified level of the Mesh. Free entities are entities
        that are only connected with a single element.

        If return_indices==True, also returns an (nentities,2) index
        for inverse lookup of the higher entity (column 0) and its local
        lower entity number (column 1).
        """
        hi,lo = self.elems.insertLevel(level)
        if hi.size == 0:
            if return_indices:
                return Connectivity(),[]
            else:
                return Connectivity()

        hiinv = hi.inverse()
        ncon = (hiinv>=0).sum(axis=1)
        isbrd = (ncon<=1)   # < 1 should not occur
        brd = lo[isbrd]
        #
        if brd.eltype is None:
            raise ValueError,"THIS ERROR SHOULD NOT OCCUR! CONTACT MAINTAINERS!"
        if not return_indices:
            return brd

        # return indices where the border elements come from
        binv = hiinv[isbrd]
        enr = binv[binv >= 0]  # element number
        a = hi[enr]
        b = arange(lo.shape[0])[isbrd].reshape(-1,1)
        fnr = where(a==b)[1]   # local border part number
        return brd,column_stack([enr,fnr])


    def getFreeEntitiesMesh(self,level=-1,compact=True):
        """Return a Mesh with lower entities.

        Returns a Mesh representing the lower entities of the specified
        level. If the Mesh has property numbers, the lower entities inherit
        the property of the element to which they belong.

        By default, the resulting Mesh is compacted. Compaction can be
        switched off by setting `compact=False`.
        """
        if self.prop==None:
            M = Mesh(self.coords,self.getFreeEntities(level=level))

        else:
            brd,indices = self.getFreeEntities(return_indices=True,level=level)
            enr = indices[:,0]
            M = Mesh(self.coords,brd,prop=self.prop[enr])

        if compact:
            M = M.compact()
        return M


    def getBorder(self,return_indices=False):
        """Return the border of the Mesh.

        This returns a Connectivity table with the border of the Mesh.
        The border entities are of a lower hierarchical level than the
        mesh itself. These entities become part of the border if they
        are connected to only one element.

        If return_indices==True, it returns also an (nborder,2) index
        for inverse lookup of the higher entity (column 0) and its local
        border part number (column 1).

        This is a convenient shorthand for ::

          self.getFreeEntities(level=-1,return_indices=return_indices)
        """
        return self.getFreeEntities(level=-1,return_indices=return_indices)


    def getBorderMesh(self,compact=True):
        """Return a Mesh with the border elements.

        The returned Mesh is of the next lower hierarchical level and
        contains all the free entitites of that level.
        If the Mesh has property numbers, the border elements inherit
        the property of the element to which they belong.

        By default, the resulting Mesh is compacted. Compaction can be
        switched off by setting `compact=False`.

        This is a convenient shorthand for ::

          self.getFreeEntitiesMesh(level=-1,compact=compact)
        """
        return self.getFreeEntitiesMesh(level=-1,compact=compact)


    def getBorderElems(self):
        """Return the elements that are on the border of the Mesh.

        This returns a list with the numbers of the elements that are on the
        border of the Mesh. Elements are considered to be at the border if they
        contain at least one complete element of the border Mesh (i.e. an
        element of the first lower hierarchical level). Thus, in a volume Mesh,
        elements only touching the border by a vertex or an edge are not
        considered border elements.
        """
        brd,ind = self.getBorder(True)
        return unique(ind[:,0])


    def getBorderNodes(self):
        """Return the nodes that are on the border of the Mesh.

        This returns a list with the numbers of the nodes that are on the
        border of the Mesh.
        """
        brd = self.getBorder()
        return unique(brd)


    def peel(self, nodal=False):
        """Return a Mesh with the border elements removed.

        If nodal is True all elements connected to a border node are removed.
        If nodal is False, it is a convenient shorthand for ::

          self.cselect(self.getBorderElems())
        """
        if nodal:
            brd=self.elems.connectedTo(self.getBorderNodes())
        else:
            brd=self.getBorderElems()
        return self.cselect(brd)


    def getFreeEdgesMesh(self,compact=True):
        """Return a Mesh with the free edge elements.

        The returned Mesh is of the hierarchical level 1 (no mather what
        the level of the parent Mesh is) and contains all the free entitites
        of that level.
        If the Mesh has property numbers, the border elements inherit
        the property of the element to which they belong.

        By default, the resulting Mesh is compacted. Compaction can be
        switched off by setting `compact=False`.

        This is a convenient shorthand for ::

          self.getFreeEntitiesMesh(level=1,compact=compact)
        """
        return self.getFreeEntitiesMesh(level=1,compact=compact)


#############################################################################
    # Adjacency #

    def adjacency(self,level=0,diflevel=-1):
        """Create an element adjacency table.

        Two elements are said to be adjacent if they share a lower
        entity of the specified level.
        The level is one of the lower entities of the mesh.

        Parameters:

        - `level`: hierarchy of the geometric items connecting two elements:
          0 = node, 1 = edge, 2 = face. Only values of a lower hierarchy than
          the elements of the Mesh itself make sense.
        - `diflevel`: if >= level, and smaller than the hierarchy of
          self.elems, elements that have a connection of this level are removed.
          Thus, in a Mesh with volume elements, self.adjacency(0,1) gives the
          adjacency of elements by a node but not by an edge.

        Returns an Adjacency with integers specifying for each element
        its neighbours connected by the specified geometrical subitems.
        """
        if diflevel > level:
            return self.adjacency(level).symdiff(self.adjacency(diflevel))

        if level == 0:
            elems = self.elems
        else:
            elems,lo = self.elems.insertLevel(level)
        return elems.adjacency()


    def frontWalk(self,level=0,startat=0,frontinc=1,partinc=1,maxval=-1):
        """Visit all elements using a frontal walk.

        In a frontal walk a forward step is executed simultanuously from all
        the elements in the current front. The elements thus reached become
        the new front. An element can be reached from the current element if
        both are connected by a lower entity of the specified level. Default
        level is 'point'.

        Parameters:

        - `level`: hierarchy of the geometric items connecting two elements:
          0 = node, 1 = edge, 2 = face. Only values of a lower hierarchy than
          the elements of the Mesh itself make sense. There are no
          connections on the upper level.

        The remainder of the parameters are like in
        :meth:`Adjacency.frontWalk`.

        Returns an array of integers specifying for each element in which step
        the element was reached by the walker.
        """
        return self.adjacency(level).frontWalk(startat=startat,frontinc=frontinc,partinc=partinc,maxval=maxval)


    def maskedEdgeFrontWalk(self,mask=None,startat=0,frontinc=1,partinc=1,maxval=-1):
        """Perform a front walk over masked edge connections.

        This is like frontWalk(level=1), but allows to specify a mask to
        select the edges that are used as connectors between elements.

        Parameters:

        - `mask`: Either None or a boolean array or index flagging the nodes
          which are to be considered connectors between elements. If None,
          all nodes are considered connections.

        The remainder of the parameters are like in
        :meth:`Adjacency.frontWalk`.
        """
        if self.level() != 1:
            hi,lo = self.elems.insertLevel(1)
        else:
            hi = self.elems
        adj = hi.adjacency(mask=mask)
        return adj.frontWalk(startat=startat,frontinc=frontinc,partinc=partinc,maxval=maxval)


    # BV: DO WE NEED THE nparts ?
    def partitionByConnection(self,level=0,startat=0,sort='number',nparts=-1):
        """Detect the connected parts of a Mesh.

        The Mesh is partitioned in parts in which all elements are
        connected. Two elements are connected if it is possible to draw a
        continuous (poly)line from a point in one element to a point in
        the other element without leaving the Mesh.
        The partitioning is returned as a integer array having a value
        for ech element corresponding to the part number it belongs to.

        By default the parts are sorted in decreasing order of the number
        of elements. If you specify nparts, you may wish to switch off the
        sorting by specifying sort=''.
        """
        p = self.frontWalk(level=level,startat=startat,frontinc=0,partinc=1,maxval=nparts)
        if sort=='number':
            p = sortSubsets(p)
        #
        # TODO: add weighted sorting methods
        #
        return p


    def splitByConnection(self,level=0,startat=0,sort='number'):
        """Split the Mesh into connected parts.

        Returns a list of Meshes that each form a connected part.
        By default the parts are sorted in decreasing order of the number
        of elements.
        """
        p = self.partitionByConnection(level=level,startat=startat,sort=sort)
        return self.splitProp(p)


    def largestByConnection(self,level=0):
        """Return the largest connected part of the Mesh.

        This is equivalent with, but more efficient than ::

          self.splitByConnection(level)[0]
        """
        p = self.partitionByConnection(level=level)
        return self.select(p==0)


    def growSelection(self,sel,mode='node',nsteps=1):
        """Grow a selection of a surface.

        `p` is a single element number or a list of numbers.
        The return value is a list of element numbers obtained by
        growing the front `nsteps` times.
        The `mode` argument specifies how a single frontal step is done:

        - 'node' : include all elements that have a node in common,
        - 'edge' : include all elements that have an edge in common.
        """
        level = {'node':0,'edge':1}[mode]
        p = self.frontWalk(level=level,startat=sel,maxval=nsteps)
        return where(p>=0)[0]


    def partitionByAngle(self,**arg):
        """Partition a surface Mesh by the angle between adjacent elements.

        The Mesh is partitioned in parts bounded by the sharp edges in the
        surface. The arguments and return value are the same as in
        :meth:`TriSurface.partitionByAngle`.

        Currently this only works for 'tri3' and 'quad4' type Meshes.
        Also, the 'quad4' partitioning method currently only works correctly
        if the quads are nearly planar.
        """
        from plugins.trisurface import TriSurface
        if self.elName() not in [ 'tri3', 'quad4' ]:
            raise ValueError, "partitionByAngle currently only works for 'tri3' and 'quad4' type Meshes."

        S = TriSurface(self.convert('tri3'))
        p = S.partitionByAngle(**arg)
        if self.elName() == 'tri3':
            return p
        if self.elName() == 'quad4':
            p = p.reshape(-1,2)
            if not (p[:,0] == p[:,1]).all():
                utils.warn("warn_mesh_partitionbyangle")
            return p[:,0]


###########################################################################

    #
    #  IDEA: Should we move these up to Connectivity ?
    #        That would also avoid some possible problems
    #        with storing conn and econn
    #

    def nodeConnections(self):
        """Find and store the elems connected to nodes."""
        if self.conn is None:
            self.conn = self.elems.inverse()
        return self.conn


    def nNodeConnected(self):
        """Find the number of elems connected to nodes."""
        return (self.nodeConnections() >=0).sum(axis=-1)


    def edgeConnections(self):
        """Find and store the elems connected to edges."""
        if self.econn is None:
            self.econn = self.getElemEdges().inverse()
        return self.econn


    def nEdgeConnected(self):
        """Find the number of elems connected to edges."""
        return (self.edgeConnections() >=0).sum(axis=-1)


    #
    # Are these really needed? better use adjacency(level)
    #
    #
    def nodeAdjacency(self):
        """Find the elems adjacent to each elem via one or more nodes."""
        return self.elems.adjacency()


    def nNodeAdjacent(self):
        """Find the number of elems which are adjacent by node to each elem."""
        return (self.nodeAdjacency() >=0).sum(axis=-1)


    def edgeAdjacency(self):
        """Find the elems adjacent to elems via an edge."""
        return self.getElemEdges().adjacency()


    def nEdgeAdjacent(self):
        """Find the number of adjacent elems."""
        return (self.edgeAdjacency() >=0).sum(axis=-1)


    def nonManifoldNodes(self):
        """Return the non-manifold nodes of a Mesh.

        Non-manifold nodes are nodes where subparts of a mesh of level >= 2
        are connected by a node but not by an edge.

        Returns an integer array with a sorted list of non-manifold node
        numbers. Possibly empty (always if the dimensionality of the Mesh
        is lower than 2).
        """
        if self.level() < 2:
            return []

        ML = self.splitByConnection(1,sort='')
        nm = [ intersect1d(Mi.elems,Mj.elems) for Mi,Mj in combinations(ML,2) ]
        return unique(concat(nm))


    def nonManifoldEdges(self):
        """Return the non-manifold edges of a Mesh.

        Non-manifold edges are edges where subparts of a mesh of level 3
        are connected by an edge but not by an face.

        Returns an integer array with a sorted list of non-manifold edge
        numbers. Possibly empty (always if the dimensionality of the Mesh
        is lower than 3).

        As a side effect, this constructs the list of edges in the object.
        The definition of the nonManifold edges in tgerms of the nodes can
        thus be got from ::

          self.edges[self.nonManifoldEdges()]
        """
        if self.level() < 3:
            return []

        elems = self.getElemEdges()
        p = self.partitionByConnection(2,sort='')
        eL = [ elems[p==i] for i in unique(p) ]
        nm = [ intersect1d(ei,ej) for ei,ej in combinations(eL,2) ]
        return unique(concat(nm))


    def nonManifoldEdgeNodes(self):
        """Return the non-manifold edge nodes of a Mesh.

        Non-manifold edges are edges where subparts of a mesh of level 3
        are connected by an edge but not by an face.

        Returns an integer array with a sorted list of numbers of nodes
        on the non-manifold edges.
        Possibly empty (always if the dimensionality of the Mesh
        is lower than 3).
        """
        if self.level() < 3:
            return []

        ML = self.splitByConnection(2,sort='')
        nm = [ intersect1d(Mi.elems,Mj.elems) for Mi,Mj in combinations(ML,2) ]
        return unique(concat(nm))


    def fuse(self,**kargs):
        """Fuse the nodes of a Meshes.

        All nodes that are within the tolerance limits of each other
        are merged into a single node.

        The merging operation can be tuned by specifying extra arguments
        that will be passed to :meth:`Coords:fuse`.
        """
        coords,index = self.coords.fuse(**kargs)
        return self.__class__(coords,index[self.elems],prop=self.prop,eltype=self.elType())


    def matchCoords(self,coords,**kargs):
        """Match nodes of coords with nodes of self.

        coords can be a Coords or a Mesh object
        This is a convenience function equivalent to::

           self.coords.match(mesh.coords,**kargs)
           or
           self.coords.match(coords,**kargs)

        See also :meth:`Coords.match`
        """
        if not(isinstance(coords,Coords)):
            coords=coords.coords
        return self.coords.match(coords,**kargs)


    def matchCentroids(self, mesh,**kargs):
        """Match elems of Mesh with elems of self.

        self and Mesh are same eltype meshes
        and are both without duplicates.

        Elems are matched by their centroids.
        """
        c = Mesh(self.centroids(), arange(self.nelems() ))
        mc = Mesh(mesh.centroids(), arange(mesh.nelems() ))
        return c.matchCoords(mc,**kargs)


    # BV: I'm not sure that we need this. Looks like it can or should
    # be replaced with a method applied on the BorderMesh
    #~ FI It has been tested on quad4-quad4, hex8-quad4, tet4-tri3
    def matchLowerEntitiesMesh(self,mesh,level=-1):
        """_Match lower entity of mesh with the lower entity of self.

        self and Mesh can be same eltype meshes or different eltype but of the
        same hierarchical type (i.e. hex8-quad4 or tet4 - tri3)
        and are both without duplicates.

        Returns the indices array of the elems of self that matches
        the lower entity of mesh, and the matched lower entity number
        """
        if level < 0:
            level = m1.elType().ndim + level

        sel = self.elType().getEntities(level)
        hi,lo = self.elems.insertLevel(sel)
        hiinv = hi.inverse()
        fm = Mesh(self.coords,self.getLowerEntities(level,unique=True))
        mesh = Mesh(mesh.coords,mesh.getLowerEntities(level,unique=True))
        c = fm.matchCentroids(mesh)
        hiinv = hiinv[c]
        hpos = matchIndex(c,hi).reshape(hi.shape)
        enr =  unique(hiinv[hiinv >= 0])  # element number
        fnr=column_stack(where(hpos!=-1)) # face number
        return enr,fnr

    def matchFaces(self,mesh):
        """_Match faces of mesh with faces of self.

        self and Mesh can be same eltype meshes or different eltype but of the
        same hierarchical type (i.e. hex8-quad4 or tet4 - tri3)
        and are both without duplicates.

        eturns the indices array of the elems of self that matches
        the faces of mesh, and the matched face number
        """
        enr,fnr = self.matchLowerEntitiesMesh(mesh,level=2)
        return enr,fnr


    def compact(self):
        """Remove unconnected nodes and renumber the mesh.

        Returns a mesh where all nodes that are not used in any
        element have been removed, and the nodes are renumbered to
        a compacter scheme.

        Example:

          >>> x = Coords([[i] for i in arange(5)])
          >>> M = Mesh(x,[[0,2],[1,4],[4,2]])
          >>> M = M.compact()
          >>> print(M.coords)
          [[ 0.  0.  0.]
           [ 1.  0.  0.]
           [ 2.  0.  0.]
           [ 4.  0.  0.]]
          >>> print(M.elems)
          [[0 2]
           [1 3]
           [3 2]]
          >>> M = Mesh(x,[[0,2],[1,3],[3,2]])
          >>> M = M.compact()
          >>> print(M.coords)
          [[ 0.  0.  0.]
           [ 1.  0.  0.]
           [ 2.  0.  0.]
           [ 3.  0.  0.]]
          >>> print(M.elems)
          [[0 2]
           [1 3]
           [3 2]]

        """
        if self.nelems() == 0:
            ret = self.__class__([],[],eltype=self.elType())
        else:
            elems,nodes = self.elems.renumber()
            if elems is self.elems:
                # node numbering is compact
                if self.coords.shape[0] > len(nodes):
                    # remove extraneous nodes
                    self.coords = self.coords[:len(nodes)]
                # numbering has not been changed, safe to use same object
                ret = self
            else:
                # numbering has been changed, return new object
                coords = self.coords[nodes]
                ret = self.__class__(coords,elems,prop=self.prop,eltype=self.elType())
        return ret


    def _select(self,selected,compact=True):
        """_Return a Mesh only holding the selected elements.

        This is the low level select method. The normal user interface
        is via the Geometry.select method.
        """
        selected = checkArray1D(selected)
        M = self.__class__(self.coords,self.elems[selected],eltype=self.elType())
        if self.prop is not None:
            M.setProp(self.prop[selected])
        if compact:
            M = M.compact()
        return M


    def avgNodes(self,nodsel,wts=None):
        """Create average nodes from the existing nodes of a mesh.

        `nodsel` is a local node selector as in :meth:`selectNodes`
        Returns the (weighted) average coordinates of the points in the
        selector as `(nelems*nnod,3)` array of coordinates, where
        nnod is the length of the node selector.
        `wts` is a 1-D array of weights to be attributed to the points.
        Its length should be equal to that of nodsel.
        """
        elems = self.elems.selectNodes(nodsel)
        return self.coords[elems].average(wts=wts,axis=1)


    # The following is equivalent to avgNodes(self,nodsel,wts=None)
    # But is probably more efficient
    def meanNodes(self,nodsel):
        """Create nodes from the existing nodes of a mesh.

        `nodsel` is a local node selector as in :meth:`selectNodes`
        Returns the mean coordinates of the points in the selector as
        `(nelems*nnod,3)` array of coordinates, where nnod is the length
        of the node selector.
        """
        elems = self.elems.selectNodes(nodsel)
        return self.coords[elems].mean(axis=1)


    def addNodes(self,newcoords,eltype=None):
        """Add new nodes to elements.

        `newcoords` is an `(nelems,nnod,3)` or`(nelems*nnod,3)` array of
        coordinates. Each element gets exactly `nnod` extra nodes from this
        array. The result is a Mesh with plexitude `self.nplex() + nnod`.
        """
        newcoords = newcoords.reshape(-1,3)
        newnodes = arange(newcoords.shape[0]).reshape(self.elems.shape[0],-1) + self.coords.shape[0]
        elems = Connectivity(concatenate([self.elems,newnodes],axis=-1))
        coords = Coords.concatenate([self.coords,newcoords])
        return Mesh(coords,elems,self.prop,eltype)


    def addMeanNodes(self,nodsel,eltype=None):
        """Add new nodes to elements by averaging existing ones.

        `nodsel` is a local node selector as in :meth:`selectNodes`
        Returns a Mesh where the mean coordinates of the points in the
        selector are added to each element, thus increasing the plexitude
        by the length of the items in the selector.
        The new element type should be set to correct value.
        """
        newcoords = self.meanNodes(nodsel)
        return self.addNodes(newcoords,eltype)


    def selectNodes(self,nodsel,eltype=None):
        """Return a mesh with subsets of the original nodes.

        `nodsel` is an object that can be converted to a 1-dim or 2-dim
        array. Examples are a tuple of local node numbers, or a list
        of such tuples all having the same length.
        Each row of `nodsel` holds a list of local node numbers that
        should be retained in the new connectivity table.
        """
        elems = self.elems.selectNodes(nodsel)
        prop = self.prop
        if prop is not None:
            prop = column_stack([prop]*len(nodsel)).reshape(-1)
        return Mesh(self.coords,elems,prop=prop,eltype=eltype)


    @utils.deprecation("Mesh.withProp is deprecated. Use selectProp instead.")
    def withProp(self,val):
        return self.selectProp(val)


    @utils.deprecation("Mesh.withoutProp is deprecated. Use Geometry.cselectProp instead.")
    def withoutProp(self,val):
        return self.cselectProp(val)


    def connectedTo(self,nodes):
        """Return a Mesh with the elements connected to the specified node(s).

        `nodes`: int or array_like, int.

        Return a Mesh with all the elements from the original that contain at
        least one of the specified nodes.
        """
        return self.select(self.elems.connectedTo(nodes))


    def notConnectedTo(self,nodes):
        """Return a Mesh with the elements not connected to the given node(s).

        `nodes`: int or array_like, int.

        Returns a Mesh with all the elements from the original that do not
        contain any of the specified nodes.
        """
        return self.cselect(self.elems.connectedTo(nodes))


    def hits(self, entities, level):
        """Count the lower entities from a list connected to the elements.

        `entities`: a single number or a list/array of entities
        `level`: 0 or 1 or 2 if entities are nodes or edges or faces, respectively.

        The numbering of the entities corresponds to self.insertLevel(level).
        Returns an (nelems,) shaped int array with the number of the
        entities from the list that are contained in each of the elements.
        This method can be used in selector expressions like::

          self.select(self.hits(entities,level) > 0)
        """
        hi = self.elems.insertLevel(level)[0]
        return hi.hits(nodes=entities)


    def splitRandom(self,n,compact=True):
        """Split a Mesh in n parts, distributing the elements randomly.

        Returns a list of n Mesh objects, constituting together the same
        Mesh as the original. The elements are randomly distributed over
        the subMeshes.

        By default, the Meshes are compacted. Compaction may be switched
        off for efficiency reasons.
        """
        sel = random.randint(0,n,(self.nelems()))
        return [ self.select(sel==i,compact=compact) for i in range(n) if i in sel ]


###########################################################################
    ## simple mesh transformations ##

    def reverse(self,sel=None):
        """Return a Mesh where the elements have been reversed.

        Reversing an element has the following meaning:

        - for 1D elements: reverse the traversal direction,
        - for 2D elements: reverse the direction of the positive normal,
        - for 3D elements: reverse inside and outside directions of the
          element's border surface. This also changes the sign of the
          elementt's volume.

        The :meth:`reflect` method by default calls this method to undo
        the element reversal caused by the reflection operation.

        Parameters:

        -`sel`: a selector (index or True/False array)
        """
        utils.warn('warn_mesh_reverse')
        # TODO: These can be merged
        if sel is None:
            if hasattr(self.elType(),'reversed'):
                elems = self.elems[:,self.elType().reversed]
            else:
                elems = self.elems[:,::-1]
        else:
            elems = self.elems.copy()
            elsel = elems[sel]
            if hasattr(self.elType(),'reversed'):
                elsel = elsel[:,self.elType().reversed]
            else:
                elsel = elsel[:,::-1]
            elems[sel] = elsel
        return self.__class__(self.coords,elems,prop=self.prop,eltype=self.elType())


    def reflect(self,dir=0,pos=0.0,reverse=True,**kargs):
        """Reflect the coordinates in one of the coordinate directions.

        Parameters:

        - `dir`: int: direction of the reflection (default 0)
        - `pos`: float: offset of the mirror plane from origin (default 0.0)
        - `reverse`: boolean: if True, the :meth:`Mesh.reverse` method is
          called after the reflection to undo the element reversal caused
          by the reflection of its coordinates. This will in most cases have
          the desired effect. If not however, the user can set this to False
          to skip the element reversal.
        """
        if reverse is None:
            reverse = True
            utils.warn("warn_mesh_reflect")

        M = Geometry.reflect(self,dir=dir,pos=pos)
        if reverse:
            M = M.reverse()
        return M


    def convert(self,totype,fuse=False):
        """Convert a Mesh to another element type.

        Converting a Mesh from one element type to another can only be
        done if both element types are of the same dimensionality.
        Thus, 3D elements can only be converted to 3D elements.

        The conversion is done by splitting the elements in smaller parts
        and/or by adding new nodes to the elements.

        Not all conversions between elements of the same dimensionality
        are possible. The possible conversion strategies are implemented
        in a table. New strategies may be added however.

        The return value is a Mesh of the requested element type, representing
        the same geometry (possibly approximatively) as the original mesh.

        If the requested conversion is not implemented, an error is raised.

        .. warning:: Conversion strategies that add new nodes may produce
          double nodes at the common border of elements. The :meth:`fuse`
          method can be used to merge such coincident nodes. Specifying
          fuse=True will also enforce the fusing. This option become the
          default in future.
        """
        #
        # totype is a string !
        #

        if elementType(totype) == self.elType():
            return self

        strategy = self.elType().conversions.get(totype,None)

        while not type(strategy) is list:
            # This allows for aliases in the conversion database
            strategy = self.elType().conversions.get(strategy,None)

            if strategy is None:
                raise ValueError,"Don't know how to convert %s -> %s" % (self.elName(),totype)

        # 'r' and 'v' steps can only be the first and only step
        steptype,stepdata = strategy[0]
        if steptype == 'r':
            # Randomly convert elements to one of the types in list
            return self.convertRandom(stepdata)
        elif steptype == 'v':
            return self.convert(stepdata).convert(totype)

        # Execute a strategy
        mesh = self
        totype = totype.split('-')[0]
        for step in strategy:
            steptype,stepdata = step

            if steptype == 'a':
                mesh = mesh.addMeanNodes(stepdata,totype)

            elif steptype == 's':
                mesh = mesh.selectNodes(stepdata,totype)

            else:
                raise ValueError,"Unknown conversion step type '%s'" % steptype

        if fuse:
            mesh = mesh.fuse()
        return mesh


    def convertRandom(self,choices):
        """Convert choosing randomly between choices

        Returns a Mesh obtained by converting the current Mesh by a
        randomly selected method from the available conversion type
        for the current element type.
        """
        ml = self.splitRandom(len(choices),compact=False)
        ml = [ m.convert(c) for m,c in zip(ml,choices) ]
        prop = self.prop
        if prop is not None:
            prop = concatenate([m.prop for m in ml])
        elems = concatenate([m.elems for m in ml],axis=0)
        eltype = set([m.elName() for m in ml])
        if len(eltype) > 1:
            raise RuntimeError,"Invalid choices for random conversions"
        eltype = eltype.pop()
        return Mesh(self.coords,elems,prop,eltype)


    ## TODO:
    ## - mesh_wts and mesh_els functions should be moved to elements.py
    def subdivide(self,*ndiv,**kargs):
        """Subdivide the elements of a Mesh.

        Parameters:

        - `ndiv`: specifies the number (and place) of divisions (seeds)
          along the edges of the elements. Accepted type and value depend
          on the element type of the Mesh. Currently implemented:

          - 'tri3': ndiv is a single int value specifying the number of
            divisions (of equal size) for each edge.

          - 'quad4': ndiv is a sequence of two int values nx,ny, specifying
            the number of divisions along the first, resp. second
            parametric direction of the element

          - 'hex8': ndiv is a sequence of three int values nx,ny,nz specifying
            the number of divisions along the first, resp. second and the third
            parametric direction of the element

        - `fuse`: bool, if True (default), the resulting Mesh is completely
          fused. If False, the Mesh is only fused over each individual
          element of the original Mesh.

        Returns a Mesh where each element is replaced by a number of
        smaller elements of the same type.

        .. note:: This is currently only implemented for Meshes of type 'tri3'
          and 'quad4' and 'hex8' and for the derived class 'TriSurface'.
        """
        elname = self.elName()
        try:
            mesh_wts = globals()[elname+'_wts']
            mesh_els = globals()[elname+'_els']
        except:
            raise ValueError,"Can not subdivide element of type '%s'" % elname

        wts = mesh_wts(*ndiv)
        lndiv = [nd if isinstance(nd,int) else len(nd)-1 for nd in ndiv]
        els = mesh_els(*lndiv)
        X = self.coords[self.elems]
        U = dot(wts,X).transpose([1,0,2]).reshape(-1,3)
        e = concatenate([els+i*wts.shape[0] for i in range(self.nelems())])
        M = self.__class__(U,e,eltype=self.elType()).setProp(self.prop,blocks=[prod(lndiv)])
        if kargs.get('fuse',True):
            M = M.fuse()
        return M


    def reduceDegenerate(self,eltype=None):
        """Reduce degenerate elements to lower plexitude elements.

        This will try to reduce the degenerate elements of the mesh to elements
        of a lower plexitude. If a target element type is given, only the
        matching reduce scheme is tried.
        Else, all the target element types for which
        a reduce scheme from the Mesh eltype is available, will be tried.

        The result is a list of Meshes of which the last one contains the
        elements that could not be reduced and may be empty.
        Property numbers propagate to the children.
        """
        #
        # This duplicates a lot of the functionality of
        # Connectivity.reduceDegenerate
        # But this is really needed to keep the properties
        #

        if self.nelems() == 0:
            return [self]

        try:
            strategies = self.elType().degenerate
        except:
            return [self]

        if eltype is not None:
            s = strategies.get(eltype,[])
            if s:
                strategies = {eltype:s}
            else:
                strategies = {}
        if not strategies:
            return [self]

        m = self
        ML = []

        for eltype in strategies:

            elems = []
            prop = []
            for conditions,selector in strategies[eltype]:
                e = m.elems
                cond = array(conditions)
                w = (e[:,cond[:,0]] == e[:,cond[:,1]]).all(axis=1)
                sel = where(w)[0]
                if len(sel) > 0:
                    elems.append(e[sel][:,selector])
                    if m.prop is not None:
                        prop.append(m.prop[sel])
                    # remove the reduced elems from m
                    m = m.select(~w,compact=False)

                    if m.nelems() == 0:
                        break

            if elems:
                elems = concatenate(elems)
                if prop:
                    prop = concatenate(prop)
                else:
                    prop = None
                ML.append(Mesh(m.coords,elems,prop,eltype))

            if m.nelems() == 0:
                break

        ML.append(m)

        return ML


    def splitDegenerate(self,autofix=True):
        """Split a Mesh in degenerate and non-degenerate elements.

        If autofix is True, the degenerate elements will be tested against
        known degeneration patterns, and the matching elements will be
        transformed to non-degenerate elements of a lower plexitude.

        The return value is a list of Meshes. The first holds the
        non-degenerate elements of the original Mesh. The last holds
        the remaining degenerate elements.
        The intermediate Meshes, if any, hold elements
        of a lower plexitude than the original. These may still contain
        degenerate elements.
        """
        deg = self.elems.testDegenerate()
        M0 = self.select(~deg,compact=False)
        M1 = self.select(deg,compact=False)
        if autofix:
            ML = [M0] + M1.reduceDegenerate()
        else:
            ML = [M0,M1]

        return ML


    def removeDegenerate(self,eltype=None):
        """Remove the degenerate elements from a Mesh.

        Returns a Mesh with all degenerate elements removed.
        """
        deg = self.elems.testDegenerate()
        return self.select(~deg,compact=False)


    def removeDuplicate(self,permutations=True):
        """Remove the duplicate elements from a Mesh.

        Duplicate elements are elements that consist of the same nodes,
        by default in no particular order. Setting permutations=False will
        only consider elements with the same nodes in the same order as
        duplicates.

        Returns a Mesh with all duplicate elements removed.
        """
        ind,ok = self.elems.testDuplicate(permutations)
        return self.select(ind[ok])


    def renumber(self,order='elems'):
        """Renumber the nodes of a Mesh in the specified order.

        order is an index with length equal to the number of nodes. The
        index specifies the node number that should come at this position.
        Thus, the order values are the old node numbers on the new node
        number positions.

        order can also be a predefined value that will generate the node
        index automatically:

        - 'elems': the nodes are number in order of their appearance in the
          Mesh connectivity.
        - 'random': the nodes are numbered randomly.
        - 'front': the nodes are numbered in order of their frontwalk.
        """
        if order == 'elems':
            order = renumberIndex(self.elems)
        elif order == 'random':
            order = arange(self.nnodes())
            random.shuffle(order)
        elif order == 'front':
            adj = self.elems.adjacency('n')
            p = adj.frontWalk()
            order = p.argsort()
        newnrs = inverseUniqueIndex(order)
        return self.__class__(self.coords[order],newnrs[self.elems],prop=self.prop,eltype=self.elType())


    def reorder(self,order='nodes'):
        """Reorder the elements of a Mesh.

        Parameters:

        - `order`: either a 1-D integer array with a permutation of
          ``arange(self.nelems())``, specifying the requested order, or one of
          the following predefined strings:

          - 'nodes': order the elements in increasing node number order.
          - 'random': number the elements in a random order.
          - 'reverse': number the elements in reverse order.

        Returns a Mesh equivalent with self but with the elements ordered as
        specified.

        See also: :meth:`Connectivity.reorder`
        """
        order = self.elems.reorder(order)
        if self.prop is None:
            prop = None
        else:
            prop = self.prop[order]
        return self.__class__(self.coords,self.elems[order],prop=prop,eltype=self.elType())


    # for compatibility:
    renumberElems = reorder

##############################################################
    #
    # Connection, Extrusion, Sweep, Revolution
    #

    def connect(self,coordslist,div=1,degree=1,loop=False,eltype=None):
        """Connect a sequence of toplogically congruent Meshes into a hypermesh.

        Parameters:

        - `coordslist`: either a list of Coords objects, or a list of
          Mesh objects or a single Mesh object.

          If Mesh objects are given, they should (all) have the same element
          type as `self`. Their connectivity tables will not be used though.
          They will only serve to construct a list of Coords objects by
          taking the `coords` attribute of each of the Meshes. If only a single
          Mesh was specified, `self.coords` will be added as the first Coords
          object in the list.

          All Coords objects in the coordslist (either specified or
          constructed from the Mesh objects), should have the exact same
          shape as `self.coords`. The number of Coords items in the list should
          be a multiple of `degree`, plus 1.

          Each of the Coords in the final coordslist is combined with the
          connectivity table, element type and property numbers of `self` to
          produce a list of toplogically congruent meshes.
          The return value is the hypermesh obtained by connecting
          each consecutive slice of (degree+1) of these meshes. The hypermesh
          has a dimensionality that is one higher than the original Mesh (i.e.
          points become lines, lines become surfaces, surfaces become volumes).
          The resulting elements will be of the given `degree` in the
          direction of the connection.

          Notice that unless a single Mesh was specified as coordslist, the
          coords of `self` are not used. In many cases however `self` or
          `self.coords` will be one of the items in the specified `coordslist`.

        - `degree`: degree of the connection. Currently only degree 1 and 2
          are supported.

          - If degree is 1, every Coords from the `coordslist`
            is connected with hyperelements of a linear degree in the
            connection direction.

          - If degree is 2, quadratic hyperelements are
            created from one Coords item and the next two in the list.
            Note that all Coords items should contain the same number of nodes,
            even for higher order elements where the intermediate planes
            contain less nodes.

            Currently, degree=2 is not allowed when `coordslist` is specified
            as a single Mesh.

        - `loop`: if True, the connections with loop around the list and
          connect back to the first. This is accomplished by adding the first
          Coords item back at the end of the list.

        - `div`: This should only be used for degree==1.

          With this parameter the generated connections can be further
          subdivided along the connection direction. `div` is either a
          single input for the :func:`smartSeed` function, or a list thereof.
          In the latter case, the length of the list should be one less
          than the length of the `coordslist`. Each pair of consecutive
          items from the coordinate list will be connected using the
          seeds generated by the corresponding value from `div`, passed to
          :func:`smartSeed` with `start=1` parameter. Notice that if seed
          values are specified directly as a list of floats, the list
          should not contain the first value (0.0), while the final value
          should be 1.0.

        - `eltype`: the element type of the constructed hypermesh. Normally,
          this is set automatically from the base element type and the
          connection degree. If a different element type is specified,
          a final conversion to the requested element type is attempted.
        """
        if type(coordslist) is list:
            if type(coordslist[0]) == Mesh:
                if sum([c.elType() != self.elType() for c in coordslist]):
                    raise ValueError,"All Meshes in the list should have same element type"
                clist = [ c.coords for c in coordslist ]
            else:
                clist = coordslist
        elif isinstance(coordslist,Mesh):
            clist = [ self.coords, coordslist.coords ]
            if degree == 2:
                raise ValueError,"This only works for linear connection"
            ## BV: Any reason why this would not work??
            ##     xm = 0.5 * (clist[0]+clist[1])
            ##     clist.insert(1, xm)
        else:
            raise ValueError,"Invalid coordslist argument"

        if sum([c.shape != self.coords.shape for c in clist]):
            raise ValueError,"Incompatible shape  in coordslist"

        # implement loop parameter
        if loop:
            clist.append(clist[0])

        if (len(clist)-1) % degree != 0:
            raise ValueError,"Invalid length of coordslist (%s) for degree %s." % (len(clist),degree)

        # set divisions
        if degree > 1:
            div = 1
        if not isinstance(div,list) or isFloat(div[0]):
            div=[div]

        # now we should have list of: ints, tuples or floatlists
        div = [ smartSeed(divi,start=1) for divi in div ]
        # check length
        nsteps = (len(clist)-1)/degree
        if len(div) == 1:
            div = div * nsteps
        elif len(div)!=nsteps:
            raise ValueError,"A list of div seeds must have a length equal to (len(clist)-1)/degree) = %s" % nsteps

        # For higher order non-lagrangian elements the procedure could be
        # optimized by first compacting the coords and elems.
        # Instead we opted for the simpler method of adding the maximum
        # number of nodes, and then selecting the used ones.
        # A final compact() throws out the unused points.

        # Concatenate the coordinates
        if degree == 1:
            # We do not have a 2nd degree interpolation yet
            x = [ Coords.interpolate(xi,xj,d).reshape(-1,3) for xi,xj,d in zip(clist[:-1],clist[1:],div) ]
            clist = clist[:1] + x
        x = Coords.concatenate(clist)

        # Create the connectivity table
        nnod = self.ncoords()
        nrep = (x.shape[0]//nnod - 1) // degree
        ## print("NREP %s" % nrep)
        e = extrudeConnectivity(self.elems,nnod,degree)
        e = replicConnectivity(e,nrep,nnod*degree)

        # Create the Mesh
        M = Mesh(x,e).setProp(self.prop)
        # convert to proper eltype
        if eltype:
            M = M.convert(eltype)
        return M


    def extrude(self,div,dir=0,length=1.0,degree=1,eltype=None):
        """Extrude a Mesh in one of the axes directions.

        Parameters:

        - `div`: a value accepted as input by the :func:`smartSeed` function.
          It specified how the extruded direction will be subdivided in
          elements.
        - `dir`: the direction of the extrusion: either a global axis
          number or a direction vector.
        - `length`: the length of the extrusion, measured along the direction
          `dir`.

        Returns a new Mesh obtained by extruding the given Mesh over the
        given `length` in direction `dir`, subdividing this length according
        to the seeds specified by `dir`.
        """
        utils.warn("warn_mesh_extrude")
        print("Extrusion in direction %s over length %s" % (dir,length))
        t = smartSeed(div)
        #print("SEED %s" % t)
        if degree > 1:
            t2 = 0.5 * (t[:-1] + t[1:])
            t = concatenate([t[:1], column_stack([t2,t[1:]]).ravel()])
            #print("Quadratic SEED %s" % t)
        x0 = self.coords
        x1 = x0.trl(dir,length)
        dx = x1-x0
        x = [x0 + ti*dx for ti in t ]
        return self.connect(x,degree=degree,eltype=eltype)


    def revolve(self,n,axis=0,angle=360.,around=None,loop=False,eltype=None):
        """Revolve a Mesh around an axis.

        Returns a new Mesh obtained by revolving the given Mesh
        over an angle around an axis in n steps, while extruding
        the mesh from one step to the next.
        This extrudes points into lines, lines into surfaces and surfaces
        into volumes.
        """
        angles = arange(n+1) * angle / n
        seq = [ self.coords.rotate(angle=a,axis=axis,around=around) for a in angles ]
        return self.connect(seq,loop=loop,eltype=eltype)


    def sweep(self,path,eltype=None,**kargs):
        """Sweep a mesh along a path, creating an extrusion

        Returns a new Mesh obtained by sweeping the given Mesh
        over a path.
        The returned Mesh has double plexitude of the original.

        This method accepts all the parameters of :func:`coords.sweepCoords`,
        with the same meaning. Usually, you will need to at least set the
        `normal` parameter.
        The `eltype` parameter can be used to set the element type on the
        returned Meshes.

        This operation is similar to the extrude() method, but the path
        can be any 3D curve.
        """
        seq = sweepCoords(self.coords,path,**kargs)
        return self.connect(seq,eltype=eltype)


    def smooth(self, iterations=1, lamb=0.5, k=0.1, edg=True, exclnod=[], exclelem=[],weight=None):
        """Return a smoothed mesh.

        Smoothing algorithm based on lowpass filters.

        If edg is True, the algorithm tries to smooth the
        outer border of the mesh seperately to reduce mesh shrinkage.

        Higher values of k can reduce shrinkage even more
        (up to a point where the mesh expands),
        but will result in less smoothing per iteration.

        - `exclnod`: It contains a list of node indices to exclude from the smoothing.
          If exclnod is 'border', all nodes on the border of the mesh will
          be unchanged, and the smoothing will only act inside.
          If exclnod is 'inner', only the nodes on the border of the mesh will
          take part to the smoothing.

        - `exclelem`: It contains a list of elements to exclude from the smoothing.
          The nodes of these elements will not take part to the smoothing.
          If exclnod and exclelem are used at the same time the union of them
          will be exluded from smoothing.

        -`weight` : it is a string  that can assume 2 values `inversedistance` and
          `distance`. It allows to specify the weight of the adjancent points according
          to their distance to the point
        """
        if iterations < 1:
            return self

        if lamb*k == 1:
            raise ValueError,"Cannot assign values of lamb and k which result in lamb*k==1"

        mu = -lamb/(1-k*lamb)
        adj = self.getEdges().adjacency(kind='n')
        incl = resize(True, self.ncoords())

        if exclnod == 'border':
            exclnod = unique(self.getBorder())
            k = 0. #k can be zero because it cannot shrink
            edg = False #there is no border edge
        if exclnod == 'inner':
            exclnod = delete(arange(self.ncoords()), unique(self.getBorder()))
        exclelemnod = unique(self.elems[exclelem])
        exclude=array(unique(concatenate([exclnod, exclelemnod])), dtype = int)

        incl[exclude] = False

        if edg:
            externals = resize(False,self.ncoords())
            expoints = unique(self.getFreeEntities())
            if len(expoints) != self.ncoords():
                externals[expoints] = True
                a = adj[externals].ravel()
                inpoints = delete(range(self.ncoords()), expoints)
                for i in range(len(a)):
                    if a[i] in inpoints:
                        a[i]=-2
                adj[externals] = a.reshape(adj[externals].shape)
            else:
                message('Failed to recognize external points.\nShrinkage may be considerable.')
        w = ones(adj.shape,dtype=float)

        if weight == 'inversedistance':
            dist = length(self.coords[adj]-self.coords.reshape(-1,1,3))
            w[dist!=0] /= dist[dist!=0]

        if weight == 'distance':
            w = length(self.coords[adj]-self.coords.reshape(-1,1,3))

        w[adj<0] = 0.
        w /= w.sum(-1).reshape(-1,1)
        w = w.reshape(adj.shape[0],adj.shape[1],1)
        c = self.coords.copy()
        for i in range(iterations):
            c[incl] = (1.-lamb)*c[incl] + lamb*(w[incl]*c[adj][incl]).sum(1)
            c[incl] = (1.-mu)*c[incl] + mu*(w[incl]*c[adj][incl]).sum(1)
        return self.__class__(c, self.elems, prop=self.prop, eltype=self.elType())


    def __add__(self,other):
        """Return the sum of two Meshes.

        The sum of the Meshes is simply the concatenation thereof.
        It allows us to write simple expressions as M1+M2 to concatenate
        the Meshes M1 and M2. Both meshes should be of the same plexitude
        and have the same eltype.
        The result will be of the same class as self (either a Mesh or a
        subclass thereof).
        """
        return self.concatenate([self,other])


    @classmethod
    def concatenate(clas,meshes,**kargs):
        """Concatenate a list of meshes of the same plexitude and eltype

        All Meshes in the list should have the same plexitude.
        Meshes with plexitude are ignored though, to allow empty
        Meshes to be added in.

        Merging of the nodes can be tuned by specifying extra arguments
        that will be passed to :meth:`Coords:fuse`.

        If any of the meshes has property numbers, the resulting mesh will
        inherit the properties. In that case, any meshes without properties
        will be assigned property 0.
        If all meshes are without properties, so will be the result.

        This is a class method, and should be invoked as follows::

          Mesh.concatenate([mesh0,mesh1,mesh2])
        """
        def _force_prop(m):
            if m.prop is None:
                return zeros(m.nelems(),dtype=Int)
            else:
                return m.prop

        meshes = [ m for m in meshes if m.nplex() > 0 ]
        nplex = set([ m.nplex() for m in meshes ])
        if len(nplex) > 1:
            raise ValueError,"Cannot concatenate meshes with different plexitude: %s" % str(nplex)
        eltype = set([ m.elType() for m in meshes ])
        if len(eltype) > 1:
            raise ValueError,"Cannot concatenate meshes with different eltype: %s" % [ m.elName() for m in meshes ]

        # Keep the available props
        prop = [m.prop for m in meshes if m.prop is not None]
        if len(prop) == 0:
            prop = None
        elif len(prop) < len(meshes):
            prop = concatenate([_force_prop(m) for m in meshes])
        else:
            prop = concatenate(prop)

        coords,elems = mergeMeshes(meshes,**kargs)
        elems = concatenate(elems,axis=0)
        return clas(coords,elems,prop=prop,eltype=eltype.pop())


    # Test and clipping functions


    def test(self,nodes='all',dir=0,min=None,max=None,atol=0.):
        """Flag elements having nodal coordinates between min and max.

        This function is very convenient in clipping a Mesh in a specified
        direction. It returns a 1D integer array flagging (with a value 1 or
        True) the elements having nodal coordinates in the required range.
        Use where(result) to get a list of element numbers passing the test.
        Or directly use clip() or cclip() to create the clipped Mesh

        The test plane can be defined in two ways, depending on the value of dir.
        If dir == 0, 1 or 2, it specifies a global axis and min and max are
        the minimum and maximum values for the coordinates along that axis.
        Default is the 0 (or x) direction.

        Else, dir should be compaitble with a (3,) shaped array and specifies
        the direction of the normal on the planes. In this case, min and max
        are points and should also evaluate to (3,) shaped arrays.

        nodes specifies which nodes are taken into account in the comparisons.
        It should be one of the following:

        - a single (integer) point number (< the number of points in the Formex)
        - a list of point numbers
        - one of the special strings: 'all', 'any', 'none'

        The default ('all') will flag all the elements that have all their
        nodes between the planes x=min and x=max, i.e. the elements that
        fall completely between these planes. One of the two clipping planes
        may be left unspecified.
        """
        if min is None and max is None:
            raise ValueError,"At least one of min or max have to be specified."

        f = self.coords[self.elems]
        if type(nodes)==str:
            nod = range(f.shape[1])
        else:
            nod = nodes

        if array(dir).size == 1:
            if not min is None:
                T1 = f[:,nod,dir] > min
            if not max is None:
                T2 = f[:,nod,dir] < max
        else:
            if min is not None:
                T1 = f.distanceFromPlane(min,dir) > -atol
            if max is not None:
                T2 = f.distanceFromPlane(max,dir) < atol

        if min is None:
            T = T2
        elif max is None:
            T = T1
        else:
            T = T1 * T2

        if len(T.shape) > 1:
            # We have results for more than 1 node per element
            if nodes == 'any':
                T = T.any(axis=1)
            elif nodes == 'none':
                T = ~T.any(axis=1)
            else:
                T = T.all(axis=1)

        return asarray(T)


    def clip(self,t,compact=True):
        """Return a Mesh with all the elements where t>0.

        t should be a 1-D integer array with length equal to the number
        of elements of the Mesh.
        The resulting Mesh will contain all elements where t > 0.
        """
        return self.select(t>0,compact=compact)


    def cclip(self,t,compact=True):
        """This is the complement of clip, returning a Mesh where t<=0.

        """
        return self.select(t<=0,compact=compact)


    def clipAtPlane(self,p,n,nodes='any',side='+'):
        """Return the Mesh clipped at plane (p,n).

        This is a convenience function returning the part of the Mesh
        at one side of the plane (p,n)
        """
        if side == '-':
            n = -n
        return self.clip(self.test(nodes=nodes,dir=n,min=p))


    def levelVolumes(self):
        """Return the level volumes of all elements in a Mesh.

        The level volume of an element is defined as:

        - the length of the element if the Mesh is of level 1,
        - the area of the element if the Mesh is of level 2,
        - the (signed) volume of the element if the Mesh is of level 3.

        The level volumes can be computed directly for Meshes of eltypes
        'line2', 'tri3' and 'tet4' and will produce accurate results.
        All other Mesh types are converted to one of these before computing
        the level volumes. Conversion may result in approximation of the
        results. If conversion can not be performed, None is returned.

        If succesful, returns an (nelems,) float array with the level
        volumes of the elements.
        Returns None if the Mesh level is 0, or the conversion to the
        level's base element was unsuccesful.

        Note that for level-3 Meshes, negative volumes will be returned
        for elements having a reversed node ordering.
        """
        from geomtools import levelVolumes

        base_elem = {
            1:'line2',
            2:'tri3',
            3:'tet4'
            }

        try:
            base = base_elem[self.level()]
        except:
            return None

        if self.elName() == base:
             M = self
        else:
            try:
                print("CONVERT TO %s" % base)
                M = self.shallowCopy(prop=arange(self.nelems())).convert(base)
            except:
                return None

        V = levelVolumes(M.coords[M.elems])
        if V is not None and M != self:
            index = groupPositions(M.prop,arange(self.nelems()))
            V = array([ V[ind].sum() for ind in index ])
        return V


    def lengths(self):
        """Return the length of all elements in a level-1 Mesh.

        For a Mesh with eltype 'line2', the lengths are exact. For other
        eltypes, a conversion to 'line2' is done before computing the lengths.
        This may produce an exact result, an approximated result or no result
        (if the conversion fails).

        If succesful, returns an (nelems,) float array with the lengths.
        Returns None if the Mesh level is not 1, or the conversion to 'line2'
        does not succeed.
        """
        if self.level() == 1:
            return self.levelVolumes()
        else:
            return None


    def areas(self):
        """Return the area of all elements in a level-2 Mesh.

        For a Mesh with eltype 'tri3', the areas are exact. For other
        eltypes, a conversion to 'tri3' is done before computing the areas.
        This may produce an exact result, an approximate result or no result
        (if the conversion fails).

        If succesful, returns an (nelems,) float array with the areas.
        Returns None if the Mesh level is not 2, or the conversion to 'tri3'
        does not succeed.
        """
        if self.level() == 2:
            return self.levelVolumes()
        else:
            return None


    def volumes(self):
        """Return the signed volume of all the mesh elements

        For a 'tet4' tetraeder Mesh, the volume of the elements is calculated
        as 1/3 * surface of base * height.

        For other Mesh types the volumes are calculated by first splitting
        the elements into tetraeder elements.

        The return value is an array of float values with length equal to the
        number of elements.
        If the Mesh conversion to tetraeder does not succeed, the return
        value is None.
        """
        if self.level() == 3:
            return self.levelVolumes()
        else:
            return None


    def length(self):
        """Return the total length of a Mesh.

        Returns the sum of self.lengths(), or 0.0 if the self.lengths()
        returned None.
        """
        try:
            return self.lengths().sum()
        except:
            return 0.0


    def area(self):
        """Return the total area of a Mesh.

        Returns the sum of self.areas(), or 0.0 if the self.areas()
        returned None.
        """
        try:
            return self.areas().sum()
        except:
            return 0.0


    def volume(self):
        """Return the total volume of a Mesh.

        For a Mesh of level < 3, a value 0.0 is returned.
        For a Mesh of level 3, the volume is computed by converting its
        border to a surface and taking the volume inside that surface.
        It is equivalent with ::

            self.toSurface().volume()

        This is far more efficient than `self.volumes().sum()`.
        """
        if self.level() == 3:
            return self.toSurface().volume()
        else:
            return 0.0


    def fixVolumes(self):
        """Reverse the elements with negative volume.

        Elements with negative volume may result from incorrect
        local node numbering. This method will reverse all elements
        in a Mesh of dimensionality 3, provide the volumes of these
        elements can be computed.
        """
        return self.reverse(self.volumes() < 0.)


##########################################
    ## Field values ##

    def nodalToElement(self,val):
        """Compute element values from nodal values.

        Given scalar values defined on nodes,
        finds the average values at elements.
        NB. It now works with scalar. It could be extended to vectors.
        """
        return val[self.elems].mean(axis=1)



    def actor(self,**kargs):

        if self.nelems() == 0:
            return None

        from gui.actors import GeomActor
        return GeomActor(self,**kargs)


######################## Functions #####################

# BV: THESE SHOULD GO TO connectivity MODULE

def extrudeConnectivity(e,nnod,degree):
    """_Extrude a Connectivity to a higher level Connectivity.

    e: Connectivity
    nnod: a number > highest node number
    degree: degree of extrusion (currently 1 or 2)

    The extrusion adds `degree` planes of nodes, each with an node increment
    `nnod`, to the original Connectivity `e` and then selects the target nodes
    from it as defined by the e.eltype.extruded[degree] value.

    Currently returns an integer array, not a Connectivity!
    """
    try:
        eltype,reorder = e.eltype.extruded[degree]
    except:
        try:
            eltype = e.eltype.name()
        except:
            eltype = None
        raise ValueError,"I don't know how to extrude a Connectivity of eltype '%s' in degree %s" % (eltype,degree)
    # create hypermesh Connectivity
    e = concatenate([e+i*nnod for i in range(degree+1)],axis=-1)
    # Reorder nodes if necessary
    if len(reorder) > 0:
        e = e[:,reorder]
    return Connectivity(e,eltype=eltype)


def replicConnectivity(e,n,inc):
    """_Repeat a Connectivity with increasing node numbers.

    e: a Connectivity
    n: integer: number of copies to make
    inc: integer: increment in node numbers for each copy

    Returns the concatenation of n connectivity tables, which are each copies
    of the original e, but having the node numbers increased by inc.
    """
    return Connectivity(concatenate([e+i*inc for i in range(n)]),eltype=e.eltype)


def mergeNodes(nodes,fuse=True,**kargs):
    """Merge all the nodes of a list of node sets.

    Merging the nodes creates a single Coords object containing all nodes,
    and the indices to find the points of the original node sets in the
    merged set.

    Parameters:

    - `nodes`: a list of Coords objects, all having the same shape, except
      possibly for their first dimension
    - `fuse`: if True (default), coincident (or very close) points will
      be fused to a single point
    - `**kargs`: keyword arguments that are passed to the fuse operation

    Returns:

    - a Coords with the coordinates of all (unique) nodes,
    - a list of indices translating the old node numbers to the new. These
      numbers refer to the serialized Coords.

    The merging operation can be tuned by specifying extra arguments
    that will be passed to :meth:`Coords.fuse`.
    """
    coords = Coords(concatenate([x for x in nodes],axis=0))
    if fuse:
        coords,index = coords.fuse(**kargs)
    else:
        index = arange(coords.shape[0])
    n = array([0] + [ x.npoints() for x in nodes ]).cumsum()
    ind = [ index[f:t] for f,t in zip(n[:-1],n[1:]) ]
    return coords,ind


def mergeMeshes(meshes,fuse=True,**kargs):
    """Merge all the nodes of a list of Meshes.

    Each item in meshes is a Mesh instance.
    The return value is a tuple with:

    - the coordinates of all unique nodes,
    - a list of elems corresponding to the input list,
      but with numbers referring to the new coordinates.

    The merging operation can be tuned by specifying extra arguments
    that will be passed to :meth:`Coords:fuse`.
    Setting fuse=False will merely concatenate all the mesh.coords, but
    not fuse them.
    """
    coords = [ m.coords for m in meshes ]
    elems = [ m.elems for m in meshes ]
    coords,index = mergeNodes(coords,fuse,**kargs)
    return coords,[Connectivity(i[e],eltype=e.eltype) for i,e in zip(index,elems)]


def unitAttractor(x,e0=0.,e1=0.):
    """Moves values in the range 0..1 closer to or away from the limits.

    - `x`: a list or array with values in the range 0.0 to 1.0.
    - `e0`, `e1`: attractor parameters for the start, resp. the end of the
      range. A value larger than zero will attract the points closer to the
      corresponding endpoint, while a negative value will repulse them.
      If two positive values are given, the middle part of the interval
      will become sparsely populated.

    .. note: This function is usually called from the :func:`seed` function,
       passing an initially uniformly distributed set of points.

    Example:


    >>> set_printoptions(precision=4)
    >>> print(unitAttractor([0.,0.25,0.5,0.75,1.0],2.))
    [ 0.      0.0039  0.0625  0.3164  1.    ]
    """
    x = asarray(x)
    e0 = 2**e0
    e1 = 2**e1
    at0 = lambda x,e: x**e
    at1 = lambda x,e: 1.-(1.-x)**e
    return 0.5 * (at1(at0(x,e0),e1) + at0(at1(x,e1),e0))


def seed(n,e0=0.,e1=0.):
    """Create a list of seed values.

    A seed list is a list of float values in the range 0.0 to 1.0.
    It can be used to subdivide a line segment or to seed nodes
    along lines for meshing purposes.

    This function divides the unit interval in `n` parts, resulting
    in `n+1` seed values. While the intervals are by default of equal
    length, the `e0` and `e1` can be used to create unevenly spaced
    seed values.

    Parameters:

    - `n`: positive integer: the number of elements (yielding `n+1`
      parameter values).
    - `e0`, `e1`: attractor parameters for the start, resp. the end of the
      range. A value larger than zero will attract the points closer to the
      corresponding endpoint, while a negative value will repulse them.
      If two positive values are given, the middle part of the interval
      will become sparsely populated.

    Returns a list of `n+1` float values in the range 0.0 to 1.0.
    The values are in ascending order, starting with 0.0 and ending with 1.0.

    See also :func: `smartSeed` for an analogue function accepting a variety
    of input.

    Example:

    >>> set_printoptions(precision=4)
    >>> print(seed(5,2.,2.))
    [ 0.      0.0639  0.3362  0.6638  0.9361  1.    ]
    """
    x = arange(n+1) * 1. / n
    return unitAttractor(x,e0,e1)


def smartSeed(n,start=0):
    """Create a list of seed values.

    Like the :func:`seed` function, this function creates a list of float
    values in the range 0.0 to 1.0. It accepts however a variety of inputs,
    making it the prefered choice when it is not known in advance how the
    user wants to control the seeds: automatically created or self specified.

    Parameters:

    - `n`: can be one of the following:

      - a positive integer: returns `seed(n)`,
      - a tuple (n,), (n,e0) or (n,e0,e1): returns `seed(*n)`,
      - a list or array of floats: returns the input parameter as is.

    - `start`: 0 or 1: The default (0) makes the full list created by
      `seed()` to be returned. If 1, the first value (0.0) is omitted:
      this can be useful when creating seeds over multiple adjacent
      intervals.

    """
    if isInt(n):
        return seed(n)[start:]
    elif isinstance(n,tuple):
        return seed(*n)[start:]
    elif isinstance(n,(list,ndarray)):
        return n
    else:
        raise ValueError,"Expected an integer, tuple or list; got %s = %s" % (type(n),n)

#
# Local utilities: move these to elements.py ??
#

def tri3_wts(ndiv):
    n = ndiv+1
    seeds = arange(n)
    pts = concatenate([
        column_stack([seeds[:n-i],[i]*(n-i)])
        for i in range(n)])
    pts = column_stack([ndiv-pts.sum(axis=-1),pts])
    return pts / float(ndiv)

def tri3_els(ndiv):
    n = ndiv+1
    els1 = [ row_stack([ array([0,1,n-j]) + i for i in range(ndiv-j) ]) + j * n - j*(j-1)/2 for j in range(ndiv) ]
    els2 = [ row_stack([ array([1,1+n-j,n-j]) + i for i in range(ndiv-j-1) ]) + j * n - j*(j-1)/2 for j in range(ndiv-1) ]
    elems = row_stack(els1+els2)

    return elems


def gridpoints(seed0,seed1=None,seed2=None):
    """Create weigths for 1D, 2D or 3D element coordinates.

    Parameters:

    - 'seed0' : int or list of floats . It specifies divisions along
      the first parametric direction of the element

    - 'seed1' : int or list of floats . It specifies divisions along
      the second parametric direction of the element

    - 'seed2' : int or list of floats . It specifies divisions along
      the t parametric direction of the element

    If these parametes are integer values the divisions will be equally
    spaced between 0 and 1.
    """
    if seed0 is not None:
        if isinstance(seed0,int):
            seed0 = seed(seed0)
        sh = 1
        pts = seed0
    if seed1 is not None:
        if isinstance(seed1,int):
            seed1 = seed(seed1)
        sh = 4
        x1 = seed0
        y1 = seed1
        x0 = 1.-x1
        y0 = 1.-y1
        pts = dstack([outer(y0,x0),outer(y0,x1),outer(y1,x1),outer(y1,x0)])
    if seed2 is not None:
        if isinstance(seed2,int):
            seed2 = seed(seed2)
        sh = 8
        z1 = seed2
        z0 = 1.-z1
        pts = dstack([dstack([outer(pts[:,:,ipts],zz) for ipts in range(pts.shape[2])]) for zz in [z0,z1] ])
    return pts.reshape(-1,sh).squeeze()


# TODO: can be removed, this is equivalent to gridpoints(seed(nx),seed(ny))
def quad4_wts(seed0,seed1):
    """ Create weights for quad4 subdivision.

        Parameters:

        - 'seed0' : int or list of floats . It specifies divisions along the
          first parametric direction of the element

        - 'seed1' : int or list of floats . It specifies divisions along
          the second parametric direction of the element

        If these parametes are integer values the divisions will be equally spaced between  0 and 1

    """
    return gridpoints(seed0,seed1)


def quad4_els(nx,ny):
    n = nx+1
    els = [ row_stack([ array([0,1,n+1,n]) + i for i in range(nx) ]) + j * n for j in range(ny) ]
    return row_stack(els)


def quadgrid(seed0,seed1):
    """Create a quadrilateral mesh of unit size with the specified seeds.

    The seeds are a monotonously increasing series of parametric values
    in the range 0..1. They define the positions of the nodes in the
    parametric directions 0, resp. 1.
    Normally, the first and last values of the seeds are 0., resp. 1.,
    leading to a unit square grid.

    The seeds are usually generated with the seed() function.
    """
    from elements import Quad4
    wts = gridpoints(seed0,seed1)
    n0 = len(seed0)-1
    n1 = len(seed1)-1
    E = Quad4.toMesh()
    X = E.coords.reshape(-1,4,3)
    U = dot(wts,X).transpose([1,0,2]).reshape(-1,3)
    els = quad4_els(n0,n1)
    e = concatenate([els+i*wts.shape[0] for i in range(E.nelems())])
    M = Mesh(U,e,eltype=E.elType())
    return M.fuse()


def hex8_wts(seed0,seed1,seed2):
    """ Create weights for hex8 subdivision.

    Parameters:

    - 'seed0' : int or list of floats . It specifies divisions along the
      first parametric direction of the element

    - 'seed1' : int or list of floats . It specifies divisions along
      the second parametric direction of the element

    - 'seed2' : int or list of floats . It specifies divisions along
      the t parametric direction of the element


    If these parametes are integer values the divisions will be equally
    spaced between  0 and 1
    """
    return gridpoints(seed0,seed1,seed2)



def hex8_els(nx,ny,nz):
    """ Create connectivity table for hex8 subdivision.

    """
    n = nz+1
    els = [row_stack([row_stack([asarray([array([0,1,n+1,n]) + k for k in range(nz) ])+i * n for i  in range(nx) ])]) +j * (n*(nx+1)) for j in range(ny+1)]
    els = concatenate([row_stack(els[:-1]),row_stack(els[1:])],axis=1)
    return els


def rectangle(L,W,nl,nw):
    """Create a plane rectangular mesh of quad4 elements.

    Parameters:

    - nl,nw: seeds for the elements along the length, width of the rectangle.
      They should one of the following:

      - an integer number, specifying the number of equally sized elements
        along that direction,
      - a tuple (n,) or (n,e0) or (n,e0,e1), to be used as parameters in the
        :func:`mesh.seed` function,
      - a list of float values in the range 0.0 to 1.0, specifying the relative
        position of the seeds. The values should be ordered and the first and
        last values should be 0.0 and 1.0.
    - L,W: length,width of the rectangle.

    """
    sl = smartSeed(nl)
    sw = smartSeed(nw)
    return quadgrid(sl,sw).resized([L,W,1.0])


def rectangleWithHole(L,W,r,nr,nt,e0=0.0,eltype='quad4'):
    """Create a quarter of rectangle with a central circular hole.

    Parameters:

    - L,W: length,width of the (quarter) rectangle
    - r: radius of the hole
    - nr,nt: number of elements over radial,tangential direction
    - e0: concentration factor for elements in the radial direction

    Returns a Mesh
    """
    L = W
    import elements
    from formex import interpolate
    base = elements.Quad9.vertices.scale([L,W,1.])
    F0 = Formex([[[r,0.,0.]]]).rosette(5,90./4)
    F2 = Formex([[[L,0.]],[[L,W/2]],[[L,W]],[[L/2,W]],[[0,W]]])
    F1 = interpolate(F0,F2,div=[0.5])
    FL = [F0,F1,F2]
    X0,X1,X2 = [ F.coords.reshape(-1,3) for F in FL ]
    trf0 = Coords([X0[0],X2[0],X2[2],X0[2],X1[0],X2[1],X1[2],X0[1],X1[1]])
    trf1 = Coords([X0[2],X2[2],X2[4],X0[4],X1[2],X2[3],X1[4],X0[3],X1[3]])

    seed0 = seed(nr,e0)
    seed1 = seed(nt)
    grid = quadgrid(seed0,seed1).resized([L,W,1.0])

    grid0 = grid.isopar('quad9',trf0,base)
    grid1 = grid.isopar('quad9',trf1,base)
    return (grid0+grid1).fuse()


def quadrilateral(x,n1,n2):
    """Create a quadrilateral mesh

    Parameters:

    - `x`: Coords(4,3): Four corners of the mesh, in anti-clockwise order.
    - `n1`: number of elements along sides x0-x1 and x2-x3
    - `n2`: number of elements along sides x1-x2 and x3-x4

    Returns a Mesh of quads filling the quadrilateral defined  by the four
    points `x`.
    """
    from elements import Quad4
    from plugins import isopar
    x = checkArray(x,(4,3),'f')
    M = rectangle(1.,1.,nl,nw).isopar('quad4',x,Quad4.vertices)
    return M


def quarterCircle(n1,n2):
    """Create a mesh of quadrilaterals filling a quarter circle.

    Parameters:

    - `n1`: number of elements along sides x0-x1 and x2-x3
    - `n2`: number of elements along sides x1-x2 and x3-x4

    Returns a Mesh representing a quarter circle with radius 1 and
    center at the origin.

    The quarter circle mesh has a kernel of n1*n1 cells, and two
    border meshes of n1*n2 cells. The resulting mesh has n1+n2 cells
    in radial direction and 2*n1 cells in tangential direction (in the
    border mesh).

    """
    from plugins.curve import Arc,PolyLine
    r = float(n1)/(n1+n2)  # radius of the kernel
    P0,P1 = Coords([[0.,0.,0.],[r ,0.,0.]])
    P2 = P1.rot(45.)
    P3 = P1.rot(90.)
    # Kernel is a quadrilateral
    C0 = PolyLine([P0,P1]).approx(n1).toMesh()
    C1 = PolyLine([P3,P2]).approx(n1).toMesh()
    M0 = C0.connect(C1,div=n1)
    # Border meshes
    C0 = Arc(center=P0,radius=1.,angles=(0.,45.)).approx(n1).toMesh()
    C1 = PolyLine([P1,P2]).approx(n1).toMesh()
    M1 = C0.connect(C1,div=n2)
    C0 = Arc(center=P0,radius=1.,angles=(45.,90.)).approx(n1).toMesh()
    C1 = PolyLine([P2,P3]).approx(n1).toMesh()
    M2 = C0.connect(C1,div=n2)
    return M0+M1+M2


########### Deprecated #####################


# BV:
# While this function seems to make sense, it should be avoided
# The creator of the mesh normally KNOWS the correct connectivity,
# and should immediately fix it, instead of calculating it from
# coordinate data
# It could be used in a general Mesh checking/fixing utility

def correctHexMeshOrientation(hm):
    """_hexahedral elements have an orientation.

    Some geometrical transformation (e.g. reflect) may produce
    inconsistent orientation, which results in negative (signed)
    volume of the hexahedral (triple product).
    This function fixes the hexahedrals without orientation.
    """
    from formex import vectorTripleProduct
    hf=hm.coords[hm.elems]
    tp=vectorTripleProduct(hf[:, 1]-hf[:, 0], hf[:, 2]-hf[:, 1], hf[:, 4]-hf[:, 0])# from formex.py
    hm.elems[tp<0.]=hm.elems[tp<0.][:,  [4, 5, 6, 7, 0, 1, 2, 3]]
    return hm



# End
