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
"""Interface with VTK.

This module provides an interface with some function of the Python
Visualiztion Toolkit (VTK).
Documentation for VTK can be found on http://www.vtk.org/

This module provides the basic interface to convert data structures between
vtk and pyFormex.
"""
from __future__ import print_function

from pyformex import utils
utils.requireModule('vtk')

from pyformex import zip
from pyformex.arraytools import DEG, RAD, normalize, length, trfMatrix, rotationAnglesFromMatrix
from pyformex.coordsys import CoordinateSystem
from pyformex.formex import Formex
from pyformex.mesh import Mesh
from pyformex.coords import Coords
from pyformex.varray import Varray
from pyformex.plugins.curve import PolyLine

import vtk
from vtk.util.numpy_support import numpy_to_vtk as n2v
from vtk.util.numpy_support import vtk_to_numpy as v2n
from vtk.util.numpy_support import create_vtk_array as cva
from vtk.util.numpy_support import get_numpy_array_type as gnat
from vtk.util.numpy_support import get_vtk_array_type as gvat
from vtk import vtkXMLPolyDataReader, vtkXMLPolyDataWriter, vtkIntArray, vtkDoubleArray, vtkDataSetReader, vtkDataSetWriter

from numpy import *
import os

# List of vtk data types
#~ VTK_POLY_DATA 0
#~ VTK_STRUCTURED_POINTS 1
#~ VTK_STRUCTURED_GRID 2
#~ VTK_RECTILINEAR_GRID 3
#~ VTK_UNSTRUCTURED_GRID 4
#~ VTK_PIECEWISE_FUNCTION 5
#~ VTK_IMAGE_DATA 6
#~ VTK_DATA_OBJECT 7
#~ VTK_DATA_SET 8
#~ VTK_POINT_SET 9
#~ VTK_UNIFORM_GRID 10
#~ VTK_COMPOSITE_DATA_SET 11
#~ VTK_MULTIGROUP_DATA_SET 12
#~ VTK_MULTIBLOCK_DATA_SET 13
#~ VTK_HIERARCHICAL_DATA_SET 14
#~ VTK_HIERARCHICAL_BOX_DATA_SET 15
#~ VTK_GENERIC_DATA_SET 16
#~ VTK_HYPER_OCTREE 17
#~ VTK_TEMPORAL_DATA_SET 18
#~ VTK_TABLE 19
#~ VTK_GRAPH 20
#~ VTK_TREE 21
#~ VTK_SELECTION 22
#~ VTK_DIRECTED_GRAPH 23
#~ VTK_UNDIRECTED_GRAPH 24
#~ VTK_MULTIPIECE_DATA_SET 25
#~ VTK_DIRECTED_ACYCLIC_GRAPH 26
#~ VTK_ARRAY_DATA 27
#~ VTK_REEB_GRAPH 28
#~ VTK_UNIFORM_GRID_AMR 29
#~ VTK_NON_OVERLAPPING_AMR 30
#~ VTK_OVERLAPPING_AMR 31
#~ VTK_HYPER_TREE_GRID 32
#~ VTK_MOLECULE 33
#~ VTK_PISTON_DATA_OBJECT 34
#~ VTK_PATH 35

def cleanVPD(vpd):
    """Clean the vtkPolydata

    Clean the vtkPolydata, adjusting connectivity, removing duplicate elements
    and coords, renumbering the connectivity. This is often needed after
    setting the vtkPolydata, to make the vtkPolydata fit for use with other
    operations. Be aware that this operation will change the order and
    numbering of the original data.

    Parameters:

    - `vpd`: a vtkPolydata

    Returns the cleaned vtkPolydata.
    """
    from vtk import vtkCleanPolyData
    cleaner = vtkCleanPolyData()
    cleaner.SetInput(vpd)
    cleaner.Update()
    return  cleaner.GetOutput()


def checkClean(mesh):
    """Check if the mesh is fused, compacted and renumbered.

    If mesh is not clean (fused, compacted and renumbered),
    vtkCleanPolyData() will clean it before writing a vtp file.
    This should be avoided because the pyformex points and arrays
    may no longer correspond to the vtk points.
    """
    m1 = mesh.fuse().compact().renumber()
    if any(m1.coords!=mesh.coords):
        return False
    if any(m1.elems!=mesh.elems):
        return False
    return True


def coords2VTK(coords):
    """Convert pyFormex class Coords into VTK class vtkPoints"""
    # creating  vtk coords
    from vtk import vtkPoints
    pts = vtkPoints()
    ntype = gnat(pts.GetDataType())
    coordsv = n2v(asarray(coords, order='C', dtype=ntype), deep=1) # .copy() # deepcopy array conversion for C like array of vtk, it is necessary to avoid memry data loss
    pts.SetNumberOfPoints(len(coords))
    pts.SetData(coordsv)
    return pts


def elems2VTK(elems):
    """Convert pyFormex class Connectivity into VTK class vtkCellArray"""
    from vtk import vtkIdTypeArray, vtkCellArray
    # create vtk connectivity
    Nelems = len(elems)
    elms = vtkIdTypeArray()
    ntype = gnat(vtkIdTypeArray().GetDataType())
    Ncxel = len(elems[0])
    elmsv = concatenate([Ncxel*ones(Nelems).reshape(-1, 1), elems], axis=1)
    elmsv = n2v(asarray(elmsv, order='C', dtype=ntype), deep=1) # .copy() # deepcopy array conversion for C like array of vtk, it is necessary to avoid memry data loss
    elms.DeepCopy(elmsv)
    # set vtk Cell data
    datav = vtkCellArray()
    datav.SetCells(Nelems, elms)
    return datav


def convert2VPD(M,clean=False,verbose=True):
    """Convert pyFormex data to vtkPolyData.

    Convert a pyFormex Mesh or Coords or open PolyLine object into vtkPolyData.
    This is limited to vertices, lines, and polygons.

    Parameters:

    - `M`: a Coords or Mesh or open PolyLine. If M is a Coords type it will be saved as
      VERTS. Else...
    - `clean`: if True, the resulting vtkPolyData will be cleaned by calling
      cleanVPD.

    Returns a vtkPolyData.
    """
    from vtk import vtkPolyData, vtkPoints, vtkIdTypeArray, vtkCellArray

    if verbose:
        print(('STARTING CONVERSION FOR DATA OF TYPE %s '%type(M)))

    if isinstance(M, Coords):
        M = Mesh(M, arange(M.ncoords()))
        elems = M.elems
    elif isinstance(M, PolyLine):
        if M.closed == True:
            raise ValueError('only an OPEN polyline can be convert to a vtkPolyData. Convert a closed polyline into a line2 Mesh.')
        M = M.toMesh()
        elems = arange(M.ncoords()).reshape(1, -1) #a polyline in vtk has one single element
    elif isinstance(M, Mesh):
        elems = M.elems
    else:
        raise ValueError('conversion of %s type to vtkPolyData is not yet supported'%type(M))

    plex = elems.shape[1]
    vpd = vtkPolyData()# create a vtkPolyData variable
    pts = coords2VTK(M.coords)# creating  vtk coords
    vpd.SetPoints(pts)
    datav = elems2VTK(elems)# create vtk connectivity as vtkCellArray

    if M.nplex() == 1:#point mesh
        try:
            if verbose:
                print("setting VERTS for data with %s maximum number of point for cell "%plex)
            vpd.SetVerts(datav)
        except:
            raise ValueError("Error in saving  VERTS")
    elif M.nplex() == 2:#line2 mesh or polyline
        try:
            if verbose:
                print("setting LINES for data with %s maximum number of point for cell "%plex)
            vpd.SetLines(datav)
        except:
            raise  ValueError("Error in saving  LINES")
    else:#polygons
        try:
            if verbose:
                print("setting POLYS for data with %s maximum number of point for cell "%plex)
            vpd.SetPolys(datav)
        except:
            raise ValueError("Error in saving  POLYS")
    vpd.Update()
    if clean:
        vpd = cleanVPD(vpd)
    return vpd


def convert2VTU(M):
    """Convert pyFormex Mesh to vtk unstructured grid.

    Return a VTK unstructured grid (VTU) supports any element type and
    is therefore an equivalent of pyFormex class Mesh.
    """
    def eltype2VTU(elname):
        """convert the Mesh.elName() into vtk cell type

        vtk cell type is an integer. See
        http://davis.lbl.gov/Manuals/VTK-4.5/vtkCellType_8h-source.html
        """
        import vtk
        if elname == 'point':
            return vtk.VTK_VERTEX
        if elname == 'line2':
            return vtk.VTK_LINE
        elif elname == 'tri3':
            return vtk.VTK_TRIANGLE
        elif elname == 'quad4':
            return vtk.VTK_QUAD
        elif elname == 'tet4':
            return vtk.VTK_TETRA
        elif elname == 'wedge6':
            return vtk.VTK_WEDGE
        elif elname == 'hex8':
            return vtk.VTK_HEXAHEDRON
        else:
            raise ValueError ('conversion not yet implemented')
    # create vtk coords
    pts = coords2VTK(M.coords)
    # create vtk connectivity
    datav = elems2VTK(M.elems)
    # find vtu cell type
    vtuCellType = eltype2VTU(M.elName())
    # create the vtu
    from vtk import vtkUnstructuredGrid
    vtu = vtkUnstructuredGrid()
    vtu.SetPoints(pts)
    vtu.SetCells(vtuCellType, datav)
    vtu.Update()
    return vtu


def convertVPD2Triangles(vpd):
    """Convert a vtkPolyData to a vtk triangular surface.

    Convert a vtkPolyData to a vtk triangular surface. This is convenient
    when vtkPolyData are non-triangular polygons.

    Parameters:

    - `vpd`: a vtkPolyData

    Returns
    """
    from vtk import vtkTriangleFilter

    triangles = vtkTriangleFilter()
    triangles.SetInput(vpd)
    triangles.Update()
    return triangles.GetOutput()


def convertFromVPD(vpd,verbose=False,samePlex=True):
    """Convert a vtkPolyData into pyFormex objects.

    Parameters:

    - `vpd`: a vtkPolyData
    - `samePlex`: True if you are sure that all lines and polys have the same element type

    Returns:

        - a list with points, cells, polygons, lines, vertices numpy arrays if samePlex is True
         or pyFormex varray if samePlex is False.
        - `fielddata` : a dict of {name:fielddata_numpy_array}
        - `celldata` : a dict of {name:celldata_numpy_array}
        - `pointdata` : a dict of {name:pointdata_numpy_array}


    Returns None for the missing arrays, empty dict for empty data.
    """
    coords = cells = polys = lines = verts = None
    fielddata = celldata = pointdata = dict()

    if vpd is None:
        if verbose:
            print('The vtkPolyData is None')
        return [coords, cells, polys, lines, verts], fielddata, celldata, pointdata

    # getting points coords
    if  vpd.GetPoints().GetData().GetNumberOfTuples():
        ntype = gnat(vpd.GetPoints().GetDataType())
        coords = Coords(asarray(v2n(vpd.GetPoints().GetData()), dtype=ntype))
        if verbose:
            print('Saved points coordinates array')

    vtkdtype = vpd.GetDataObjectType()
    # getting Cells
    if vtkdtype not in [0]: # this list need to be updated according to the data type
        if  vpd.GetCells().GetData().GetNumberOfTuples():
            if samePlex == True:
                ntype = gnat(vpd.GetCells().GetData().GetDataType())
                Nplex = vpd.GetCells().GetMaxCellSize()
                cells = asarray(v2n(vpd.GetCells().GetData()), dtype=ntype).reshape(-1, Nplex+1)[:, 1:]
                if verbose:
                    print('Saved polys connectivity array')
            else:
                cells =  Varray(asarray(v2n(vpd.GetCells().GetData())))#vtkCellArray to varray
                if verbose:
                    print('Saved cells connectivity varray')

    # getting Strips
    if vpd.GetStrips().GetData().GetNumberOfTuples():
        if verbose:
            utils.warn("VTK_strips")
        vpd = convertVPD2Triangles(vpd)

    # getting Polygons
    if vtkdtype not in [4]: # this list need to be updated according to the data type
        if  vpd.GetPolys().GetData().GetNumberOfTuples():
            if samePlex == True:
                ntype = gnat(vpd.GetPolys().GetData().GetDataType())
                Nplex = vpd.GetPolys().GetMaxCellSize()
                polys = asarray(v2n(vpd.GetPolys().GetData()), dtype=ntype).reshape(-1, Nplex+1)[:, 1:]
                if verbose:
                    print('Saved polys connectivity array')
            else:
                polys =  Varray(asarray(v2n(vpd.GetPolys().GetData())))#vtkCellArray to varray
                if verbose:
                    print('Saved polys connectivity varray')

    # getting Lines
    if vtkdtype not in [4]: # this list need to be updated according to the data type
        if  vpd.GetLines().GetData().GetNumberOfTuples():
            if samePlex == True:
                ntype = gnat(vpd.GetLines().GetData().GetDataType())
                Nplex = vpd.GetLines().GetMaxCellSize()
                lines = asarray(v2n(vpd.GetLines().GetData()), dtype=ntype).reshape(-1, Nplex+1)[:, 1:]
                if verbose:
                    print('Saved lines connectivity array')
            else:
                lines =  Varray(asarray(v2n(vpd.GetLines().GetData())))#this is the case of polylines
                if verbose:
                    print('Saved lines connectivity varray')

    # getting Vertices
    if vtkdtype not in [4]: # this list need to be updated acoorind to the data type
        if  vpd.GetVerts().GetData().GetNumberOfTuples():
            ntype = gnat(vpd.GetVerts().GetData().GetDataType())
            Nplex = vpd.GetVerts().GetMaxCellSize()
            verts = asarray(v2n(vpd.GetVerts().GetData()), dtype=ntype).reshape(-1, Nplex+1)[:, 1:]
            if verbose:
                print('Saved verts connectivity array')

    # getting Fields
    if vpd.GetFieldData().GetNumberOfArrays():
        fielddata = vpd.GetFieldData() # get field arrays
        arraynm = [fielddata.GetArrayName(i) for i in range(fielddata.GetNumberOfArrays())]
        ntypes = [gnat(fielddata.GetArray(an).GetDataType()) for an in arraynm]
        fielddata = [asarray(v2n(fielddata.GetArray(an)), dtype=ntype) for ntype, an in zip(ntypes, arraynm)]
        fielddata = dict(zip(arraynm, fielddata)) # dictionary of array names
        if verbose:
            print(('Field Data Arrays: '+''.join(['%s, '%nm for nm in arraynm])))


    # getting cells data
    if vpd.GetCellData().GetNumberOfArrays():
        celldata = vpd.GetCellData() # get cell arrays
        arraynm = [celldata.GetArrayName(i) for i in range(celldata.GetNumberOfArrays())]
        ntypes = [gnat(celldata.GetArray(an).GetDataType()) for an in arraynm]
        celldata = [asarray(v2n(celldata.GetArray(an)), dtype=ntype) for ntype, an in zip(ntypes, arraynm)]
        celldata = dict(zip(arraynm, celldata)) # dictionary of array names
        if verbose:
            print(('Cell Data Arrays: '+''.join(['%s, '%nm for nm in arraynm])))


    # getting points data
    if vpd.GetPointData().GetNumberOfArrays():
        pointdata = vpd.GetPointData() # get point arrays
        arraynm = [pointdata.GetArrayName(i) for i in range(pointdata.GetNumberOfArrays())]
        ntypes = [gnat(pointdata.GetArray(an).GetDataType()) for an in arraynm]
        pointdata = [asarray(v2n(pointdata.GetArray(an)), dtype=ntype) for ntype, an in zip(ntypes, arraynm)]
        pointdata = dict(zip(arraynm, pointdata)) # dictionary of array names
        if verbose:
            print(('Point Data Arrays: '+''.join(['%s, '%nm for nm in arraynm])))


    return [coords, cells, polys, lines, verts], fielddata, celldata, pointdata


def writeVTP(fn,mesh,fielddata={},celldata={},pointdata={},checkMesh=True):
    """Write a Mesh in .vtp or .vtk file format.

    - `fn`: a filename with .vtp or .vtk extension.
    - `mesh`: a Mesh of level 0, 1 or 2 (and volume Mesh in case of .vtk)
    - `fielddata`: dictionary of arrays associated to the fields (?).
    - `celldata`: dictionary of arrays associated to the elements.
    - `pointdata`: dictionary of arrays associated to the points (renumbered).
    - `checkMesh`: bool: if True, raises a warning if mesh is not clean.

    If the Mesh has property numbers, they are stored in a vtk array named prop.
    Additional arrays can be added and will be written as type double.

    The user should take care that the mesh is already fused, compacted and
    renumbered. If not, these operations will be done by vtkCleanPolyData()
    and the points may no longer correspond to the point data arrays.

    The .vtp or .vtk file can be viewed in paraview.

    VTP format can contain

    - polygons: triangles, quads, etc.
    - lines
    - points

    VTU format has been tested with

    - Mesh of type: point,line2,tri3,quad4,tet4,hex8

    """
    if checkMesh:
        if not checkClean(mesh):
            utils.warn("warn_writevtp_notclean")

    ftype = os.path.splitext(fn)[1]
    ftype = ftype.strip('.').lower()
    if ftype=='vtp':
        lvtk = convert2VPD(mesh, clean=True) # also clean=False?
    elif ftype=='vtk':
        lvtk = convert2VTU(mesh)
    else:
        raise ValueError ('extension not recongnized')

    if mesh.prop is not None: # convert prop numbers into vtk array
        ntype = gnat(vtkIntArray().GetDataType())
        vtkprop = n2v(asarray(mesh.prop, order='C', dtype=ntype), deep=1)
        vtkprop.SetName('prop')
        lvtk.GetCellData().AddArray(vtkprop)
    for k in fielddata.keys(): # same numbering of mesh.elems??
        ntype = gnat(vtkDoubleArray().GetDataType())
        if fielddata[k].shape[0]!=mesh.nelems():
            print((fielddata[k].shape,))
        fielddata = n2v(asarray(fielddata[k], order='C', dtype=ntype), deep=1)
        fielddata.SetName(k)
        lvtk.GetFieldData().AddArray(fielddata)
    for k in celldata.keys(): # same numbering of mesh.elems
        ntype = gnat(vtkDoubleArray().GetDataType())
        if celldata[k].shape[0]!=mesh.nelems():
            print((celldata[k].shape, mesh.nelems()))
            utils.warn("warn_writevtp_shape")
        celldata = n2v(asarray(celldata[k], order='C', dtype=ntype), deep=1)
        celldata.SetName(k)
        lvtk.GetCellData().AddArray(celldata)
    for k in pointdata.keys(): # same numbering of mesh.coords
        ntype = gnat(vtkDoubleArray().GetDataType())
        if pointdata[k].shape[0]!=mesh.ncoords(): # mesh should be clean!!
            print((pointdata[k].shape, mesh.ncoords()))
            utils.warn("warn_writevtp_shape2")
        pointdata = n2v(asarray(pointdata[k], order='C', dtype=ntype), deep=1)
        pointdata.SetName(k)
        lvtk.GetPointData().AddArray(pointdata)
    print(('************lvtk', lvtk))
    if ftype=='vtp':
        writer = vtkXMLPolyDataWriter()
    if ftype=='vtk':
        writer = vtkDataSetWriter()
    writer.SetInput(lvtk)
    writer.SetFileName(fn)
    writer.Write()


def writeVTPmany(fn,items):
    """Writes many objects in vtp or vtk file format.

    item can be a list of items supported by convert2VPD (mesh of coords, line2, tri3 and quad4)
    or convert2VTU (mesh of coords, line2, tri3, quad4, tet4 and hex8).

    This is experimental!
    """
    from vtk import vtkAppendPolyData
    ftype = os.path.splitext(fn)[1]
    ftype = ftype.strip('.').lower()

    if ftype=='vtp':
        from vtk import vtkAppendPolyData
        writer = vtkXMLPolyDataWriter()
        apd=vtkAppendPolyData()
        vtkitems = [convert2VPD(M=m) for m in items]
    if ftype=='vtk':
        from vtk import vtkAppendFilter
        writer = vtkDataSetWriter()
        apd = vtkAppendFilter()
        vtkitems = [convert2VTU(M=m) for m in items]
    [apd.AddInput(lvtk) for lvtk in vtkitems]
    vtkobj = apd.GetOutput()
    writer.SetInput(vtkobj)
    writer.SetFileName(fn)
    writer.Write()


def readVTKObject(fn,verbose=True,samePlex=True):
    """Read a .vtp file

    Read a .vtp file and return coords, list of elems, and a dict of arrays.

    Parameters

    - `fn`: a filename with any vtk object extension (vtp or vtk for the moment).


    Returns the same output of convertFomVPD:

        - a list with coords, cells, polygons, lines, vertices numpy arrays
        - `fielddata` : a dict of {name:fielddata_numpy_array}
        - `celldata` : a dict of {name:celldata_numpy_array}
        - `pointdata` : a dict of {name:pointdata_numpy_array}


    Returns None for the missing data.
    The dictionary of arrays can include the elements ids (e.g. properties).
    """
    ftype = utils.fileTypeFromExt(fn)
    if ftype=='vtp':
        reader = vtkXMLPolyDataReader()
    if ftype=='vtk':
        reader = vtkDataSetReader()
    reader.SetFileName(fn)
    reader.Update()
    vpd = reader.GetOutput() # vtk polydata object
    return convertFromVPD(vpd, verbose=verbose, samePlex=samePlex)



def pointInsideObject(S,P,tol=0.):
    """vtk function to test which of the points P are inside surface S

    Test which of the points pts are inside the surface surf.

    Parameters:

    - `S`: a TriSurface specifying a closed surface
    - `P`: a Coords (npts,3) specifying npts points
    - `tol`: a tolerance applied on matching float values

    Returns a bool array with True/False for points inside/outside the surface.
    """

    from vtk import vtkSelectEnclosedPoints

    vpp = convert2VPD(P)
    vps = convert2VPD(S, clean=False)

    enclosed_pts = vtkSelectEnclosedPoints()
    enclosed_pts.SetInput(vpp)
    enclosed_pts.SetTolerance(tol)
    enclosed_pts.SetSurface(vps)
    enclosed_pts.SetCheckSurface(1)
    enclosed_pts.Update()
    inside_arr = enclosed_pts.GetOutput().GetPointData().GetArray('SelectedPoints')
    enclosed_pts.ReleaseDataFlagOn()
    enclosed_pts.Complete()
    del enclosed_pts
    return asarray(v2n(inside_arr), 'bool')


def inside(surf,pts,tol='auto'):
    """Test which of the points pts are inside the surface surf.

    Parameters:

    - `surf`: a TriSurface specifying a closed surface
    - `pts`: a Coords (npts,3) specifying npts points
    - `tol`: a tolerance applied on matching float values

    Returns an integer array with the indices of the points that are
    inside the surface.

    See also :meth:`pyformex_gts.inside` for an equivalent and faster
    alternative.
    """
    if tol == 'auto':
        tol = 0.
    return where(pointInsideObject(surf, pts, tol))[0]


def intersectWithSegment(surf,lines,tol=0.0):
    """Compute the intersection of surf with lines.

    Parameters:

    - `surf`: Formex, Mesh or TriSurface
    - `lines`: a mesh of segments

    Returns a list of the intersection points lists and of the element number
    of surf where the point lies.
    The position in the list is equal to the line number. If there is no
    intersection with the correspondent lists are empty
    """
    from vtk import vtkOBBTree, vtkPoints, vtkIdList

    vsurf = convert2VPD(surf, clean=False)
    loc = vtkOBBTree()
    loc.SetDataSet(vsurf)
    loc.SetTolerance(tol)
    loc.BuildLocator()
    loc.Update()
    cellids = [[],]*lines.nelems()
    pts = [[],]*lines.nelems()
    for i in range(lines.nelems()):
        ptstmp = vtkPoints()
        cellidstmp = vtkIdList()
        loc.IntersectWithLine(lines.coords[lines.elems][i][1], lines.coords[lines.elems][i][0], ptstmp, cellidstmp)
        if cellidstmp.GetNumberOfIds():
            cellids[i] = [cellidstmp.GetId(j) for j in range(cellidstmp.GetNumberOfIds())]
            pts[i] = Coords(v2n(ptstmp.GetData()).squeeze())
    loc.FreeSearchStructure()
    del loc
    return pts, cellids


def convertTransform4x4FromVtk(transform):
    """Convert a VTK transform to numpy array

    Convert a vtk transformation instance vtkTrasmorm into a 4x4 transformation
    matrix array
    """
    trMat4x4 = [[ transform.GetMatrix().GetElement(r, c) for c in range(4)] for r in range(4)]
    return asarray(trMat4x4)


def convertTransform4x4ToVtk(trMat4x4):
    """Convert a numpy array to a VTK transform

    Convert a 4x4 transformation matrix array into a vtkTransform instance
    """
    from vtk import vtkTransform
    trMatVtk = vtkTransform()
    [[trMatVtk.GetMatrix().SetElement(r, c, trMat4x4[r, c]) for c in range(4)] for r in range(4)]
    return trMatVtk


def transform(source, trMat4x4):
    """Apply a 4x4 transformation

    Apply a 4x4 transformation matrix array to source of Coords or any
    surface type.

    Returns the transformed coordinates
    """

    from vtk import vtkTransformPolyDataFilter

    source = convert2VPD(source)
    trMat4x4 = convertTransform4x4ToVtk(trMat4x4)
    transformFilter = vtkTransformPolyDataFilter()
    transformFilter.SetInput(source)
    transformFilter.SetTransform(trMat4x4)
    transformFilter.Update()
    return Coords(convertFromVPD(transformFilter.GetOutput())[0])


def _vtkCutter(self,vtkif):
    """Cut a Mesh with a vtk implicit function.

    Parameters:

    - `mesh`: a Mesh.
    - `vtkif`: a vtk implicit function.

    In vtk `cut` means intersection: mesh dimension is reduced by one.
    Returns a mesh of points if self is a line2 mesh,
    a mesh of lines if self is a surface tri3 or quad4 mesh,
    a triangular mesh if self is tet4 or hex8 mesh.
    If there is no intersection returns None.
    This functions should not be used by the user.
    VTK implicit functions are listed here:
    http://www.vtk.org/doc/nightly/html/classvtkImplicitFunction.html
    """
    from vtk import vtkCutter
    vtkobj = convert2VTU(self)
    cutter = vtkCutter()
    cutter.SetCutFunction(vtkif)
    cutter.SetInput(vtkobj)
    cutter.Update()
    cutter = cutter.GetOutput()
    [coords, cells, polys, lines, verts], fielddata, celldata, pointdata=convertFromVPD(cutter,verbose=True,samePlex=True)
    if verts is not None: #self was a line mesh
        return Mesh(coords, verts)
    elif lines is not None: #self was a surface mesh
        return Mesh(coords, lines)
    elif polys is not None: #self was a volume mesh
        return Mesh(coords, polys)
    else:
        return None #no intersection found


def _vtkClipper(self,vtkif, insideout):
    """Clip a Mesh with a vtk implicit function.

    Parameters:

    - `mesh`: a Mesh.
    - `vtkif`: a vtk implicit function.

    In vtk `clip` means intersection and get a part of a mesh.
    Returns 3 meshes (line2, tri3, quad4):
    a line2 mesh if self is a line2 mesh,
    a tri3 mesh if self is a tri3 mesh,
    both tri3 and quad4 mesh is self is a quad4 mesh.
    None is returned if a mesh does not exist (e.g. not intersecting).
    It has not been tested with volume meshes.
    This functions should not be used by the user.   
    """
    from vtk import vtkClipPolyData
    from pyformex.plugins.vtk_itf import convert2VPD,  convertFromVPD
    if self.elName() not in ['line2','tri3','quad4']:
        warning('vtkClipper has not been tested with this element type %s'%self.elName())
    vtkobj = convert2VPD(self)   
    clipper = vtkClipPolyData()
    clipper.SetInput(vtkobj)
    clipper.SetClipFunction(vtkif)
    if insideout == True:
        clipper.InsideOutOn()
    clipper.Update()
    clipper = clipper.GetOutput()  
    [coords, cells, polys, lines, verts], fielddata, celldata, pointdata = convertFromVPD(vpd=clipper,verbose=True,samePlex=False)
    l2, t3, q4 = None, None, None
    if cells != None or verts != None:
        raise ValueError, 'unexpected output: please report it to developers!'
    if lines != None:
        l2 = Mesh(coords, lines.toArray())
    if polys != None:
        va = polys
        va = [va.select(va.lengths==l).toArray() for l in unique(va.lengths)]
        for ar in va:
            if ar.shape[1] == 3:
                t3 = Mesh(coords, ar)
            elif ar.shape[1] == 4:#could it also be a tet4?
                q4 = Mesh(coords, ar)
            else:
               raise ValueError, 'unexpected output: please report it to developers!'
    return l2, t3, q4


def _vtkPlane(p, n):
    from vtk import vtkPlane
    plane = vtkPlane()
    plane.SetOrigin(p)
    plane.SetNormal(n)
    return plane


def _vtkSphere(c, r):
    from vtk import vtkSphere
    sphere = vtkSphere()
    sphere.SetCenter(c)
    sphere.SetRadius(r)
    return sphere

##trf2CS is needed by setVTKbox
def trf2CS(CS, angle_spec=DEG):
    """Return the transformations to change coordinate system.

    Return a series of ordered transformations required to position
    an object into a new cartesian coordinate system (CS):
    scaling, rotation about x, rotation about y, rotation about z, translation.
    The scaling is needed for CS with non-unitary axes'vectors.
    Scaling, rotations and translations should be applied in order.
    An error is raised if CS is not orthogonal because
    shearing is not supported.
    """
    def isOrthogonal(CS, tol=1.e-4):
        """Check if a coordinate system is orthogonal
        """
        from pyformex.geomtools import rotationAngle
        r, ax = rotationAngle(CS[0]-CS[3], CS[1]-CS[3])
        if abs(r-90.)<tol:
            if sum(abs(normalize(CS[2]-CS[3]) - ax))<tol:
                return True
        return False
    if isOrthogonal(CS) == False:
        raise ValueError, 'the coordinate system is not orthogonal'
    sz = length(CS[:3]-CS[3])#axes`s length
    j = [3, 0, 2]#z,x,o
    mat, t = trfMatrix(CoordinateSystem()[j], CS[j])
    rx, ry, rz = rotationAnglesFromMatrix(mat,angle_spec)
    return sz, rx, ry, rz, t


##When 4x4 matrices will be added to pyFormex, the box
##could be also sheared by first rotating and then scaling.
def _vtkBox(p=None, trMat4x4=None):
    """Return scaled an positioned vtkBox.

    Parameters:

    - `p`: a coordinate system, 4 coords, a formex or a mesh.
    - `trMat4x4`: a 4x4 matrix.

    A vtkBox is an implicit vtk function defining a scaled cuboid in space.
    In order to place the cuboid in space you cannot assing coordinates to
    this vtk class, but you can transform an original box
    using affine transformations. In general a 4x4 matrix
    would be appropriate but it is not yet implemented in pyFormex.
    Alternatively, 4 points corresponding to the x,y,z,o of an orthogonal
    coordinate system can be used. In this case p can be either a list of 4 coords,
    a coordinate system, a cuboid defined as hex8-element Formex
    or Mesh (in this case only 4 points are taken).
    """
    from vtk import vtkBox
    box = vtkBox()
    if trMat4x4 is not None:
        if p is not None:
            raise ValueError, 'a box cannot be defined both by coordinates and matrix'
        else:
            vtkMat4x4 = convertTransform4x4ToVtk(trMat4x4)
            box.SetTransform(vtkMat4x4)
            return box
    elif p is not None:
        if type(p)==Mesh:
            p = p.toFormex()
        if type(p)==Formex:
            p = p.points()[[1, 3, 4, 0]]
        L, r0, r1, r2, trv = trf2CS(p)
        box = vtkBox()# vtk equivalent of simple.cuboid(xmin=xmin,xmax=xmax)
        box.SetXMin([0., 0., 0.])
        box.SetXMax(L)
        trans = vtk.vtkTransform()
        trans.RotateWXYZ(-r0, 1., 0., 0.)
        trans.RotateWXYZ(-r1, 0., 1., 0.)
        trans.RotateWXYZ(-r2, 0., 0., 1.)
        trans.Translate(-trv)
        box.SetTransform(trans)
        return box


def vtkCut(self, p=None, n=None, c=None, r=None, box=None):
    """Cut (get intersection of) a Mesh with a plane, a sphere or a box.

    Parameters:

    - `mesh`: a Mesh.
    - `p`, `n`: a point and normal vector defining the cutting plane.
    - `c`, `r`: center and radius defining a sphere.
    - `box`, either a 4x4 matrix to apply affine transformation (not yet implemented)
     or a box (cuboid) defined by 4 points, a formex or a mesh. See _vtkBox.

    Either (p,n) or (c,r) or box should be given.
    Cutting reduces the mesh dimension by one.
    Returns a mesh of points if self is a line2 mesh,
    a mesh of lines if self is a surface tri3 or quad4 mesh,
    a triangular mesh if self is tet4 or hex8 mesh.
    If there is no intersection returns None.
    """
    if c == r == box == None:
        if p!=None and n!=None:
            print("cutting mesh of type %s with plane"%self.elName())
            return _vtkCutter(self,_vtkPlane(p,n))
    elif p == n == box == None:
        if c!=None and r!=None:
            print("cutting mesh of type %s with sphere"%self.elName())
            return _vtkCutter(self,_vtkSphere(c, r))
    elif p == n == c == r == None:
        if box!=None:
            print("cutting mesh of type %s with box"%self.elName())
            return _vtkCutter(self,_vtkBox(box))
    else:
        raise ValueError, 'implicit object for cutting not well specified'
    

def vtkClip(self, p=None, n=None, c=None, r=None, box=None,insideout=False):
    """Clip (split) a Mesh with a plane, a sphere or a box.

    Parameters:

    - `mesh`: a Mesh (line2,tri3,quad4).
    - `p`, `n`: a point and normal vector defining the cutting plane.
    - `c`, `r`: center and radius defining a sphere.
    - `box`, either a 4x4 matrix to apply affine transformation (not yet implemented)
     or a box (cuboid) defined by 4 points, a formex or a mesh. See _vtkBox.
    - `insideout`:boolean to choose which side of the mesh should be returned.

    Either (p,n) or (c,r) or box should be given.
    Clipping does not reduce the mesh dimension.
    Returns always 3 meshes (line2, tri3, quad4):
    a line2 mesh if self is a line2 mesh,
    a tri3 mesh if self is a tri3 mesh,
    both tri3 and quad4 mesh is self is a quad4 mesh.
    None is returned if a mesh does not exist (e.g. clipping with
    a box which is outside the mesh).
    It has not been tested with volume meshes.
    """
    if c == r == box == None:
        if p!=None and n!=None:
            print("clipping mesh of type %s with plane"%self.elName())
            return _vtkClipper(self,_vtkPlane(p,n),insideout)
    elif p == n == box == None:
        if c!=None and r!=None:
            print("clipping mesh of type %s with sphere"%self.elName())
            return _vtkClipper(self,_vtkSphere(c, r),insideout)
    elif p == n == c == r == None:
        if box!=None:
            print("clipping mesh of type %s with box"%self.elName())
            return _vtkClipper(self,_vtkBox(box),insideout)
    else:
        raise ValueError, 'implicit object for cutting not well specified'


def octree(surf,tol=0.0,npts=1.):
    """Compute the octree structure of the surface.

    Returns the octree structure of surf according to the maximum
    tolerance tol and the maximum number of points npts in each octant.
    It returns a list of hexahedral meshes of each level of the octree
    with property equal to the number of point of the in each region.
    """
    from vtk import vtkOctreePointLocator, vtkPolyData
    from pyformex.formex import Formex
    from pyformex.connectivity import Connectivity

    vm = convert2VPD(surf, clean=False)
    loc = vtkOctreePointLocator()
    loc.SetDataSet(vm)
    loc.SetTolerance(tol)
    loc.SetMaximumPointsPerRegion(npts)

    loc.BuildLocator()
    rep = vtkPolyData()
    loc.Update()

    regions = []
    ptsinregion = []
    for lf in range(loc.GetNumberOfLeafNodes()):
        region = []
        bounds = zeros(6)
        loc.GetRegionBounds (lf, bounds)
        if (bounds!=zeros(6)).all():
            region.append(bounds[:, (0, 2, 4)])
            region.append(bounds[:, (1, 2, 4)])
            region.append(bounds[:, (1, 3, 4)])
            region.append(bounds[:, (0, 3, 4)])

            region.append(bounds[:, (0, 2, 5)])
            region.append(bounds[:, (1, 2, 5)])
            region.append(bounds[:, (1, 3, 5)])
            region.append(bounds[:, (0, 3, 5)])

        ptsinregion.append(loc.GetPointsInRegion(lf).GetNumberOfTuples())
        regions.append(Coords(region))

    regions = Formex(regions).toMesh().setProp(asarray(ptsinregion, dtype=int32))

    pfrep = []
    for level in range(loc.GetLevel()+1):
        loc.GenerateRepresentation(level, rep)
        reptmp = convertFromVPD(rep)
        reptmp[1] = reptmp[1].reshape(-1, 6*4)[:, (0, 1, 2, 3, 9, 8, 11, 10)]
        reptmp[0] = reptmp[0][Connectivity(reptmp[1]).renumber()[1]]

        pfrep.append(Mesh(reptmp[0], reptmp[1]).setProp(0))
        centroids = pfrep[-1].matchCentroids(regions)
        pfrep[-1].prop[centroids[centroids>-1]] = regions.prop[centroids>-1]

    loc.FreeSearchStructure()
    del loc
    return pfrep

def convexHull(object):
    """Compute a tetralihzed convex hull of any pyFormex class.

    Returns a Mesh object of tet4.

    """
    from vtk import vtkDelaunay3D
    chull=vtkDelaunay3D()
    chull.SetInput(convert2VPD(object))
    chull.Update()
    chull=convertFromVPD(chull.GetOutput())
    return Mesh(chull[0][0], chull[0][1], eltype='tet4')

def decimate(self, targetReduction=0.5, boundaryVertexDeletion=True, verbose=False):
    """decimate a surface (both tri3 or quad4) and returns a trisurface

    - `self` : is a tri3 or quad4 surface
    - `targetReduction` : float (from 0.0 to 1.0) : desired number of triangles relative to input number of triangles
    - `boundaryVertexDeletion` : bool : if True it allows boundary point deletion

    This function has been adapted from VMTK: vmtkScripts/vmtksurfacedecimation.py
    """
    from vtk import vtkDecimatePro
    from pyformex.plugins.trisurface import TriSurface

    vpd = convert2VPD(self, clean=True)#convert pyFormex surface to vpd
    vpd = convertVPD2Triangles(vpd)
    vpd = cleanVPD(vpd)
    decimationFilter = vtkDecimatePro()#decimate the surface
    decimationFilter.SetInput(vpd)
    decimationFilter.SetTargetReduction(targetReduction)
    decimationFilter.SetBoundaryVertexDeletion(boundaryVertexDeletion)
    decimationFilter.PreserveTopologyOn()
    decimationFilter.Update()
    vpd = decimationFilter.GetOutput()
    vpd=cleanVPD(vpd)
    [coords, cells, polys, lines, verts], fielddata, celldata, pointdata=convertFromVPD(vpd)#convert vpd to pyFormex surface
    if verbose:
        print(('%d faces decimated into %d triangles'%(self.nelems(), len(polys))))
    return TriSurface(coords, polys)


def findElemContainingPoint(self, pts, verbose=False):
    """Find indices of elements containing points.

    Parameters:

    - `self`: a Mesh (point, line, surface or volume meshes)
    - `pts`: a Coords (npts,3) specifying npts points

    This is experimental!
    Returns an integer array with the indices of the elems containing the points, returns -1 if no cell is found.
    Only one elem index per points is returned, which is probably the one with lower index number.
    VTK FindCell seems not having tolerance in python. However, the user could enlarge (unshrink) all elems.
    Docs on http://www.vtk.org/doc/nightly/html/classvtkAbstractCellLocator.html#a0c980b5fcf6adcfbf06932185e89defb
    """
    from vtk import vtkCellLocator
    vpd = convert2VTU(Mesh(self))
    cellLocator=vtkCellLocator()
    cellLocator.SetDataSet(vpd)
    cellLocator.BuildLocator()
    cellids = array([cellLocator.FindCell(pts[i]) for i in range(len(pts))])
    if verbose:
        print ('%d (of %d) points have not been found inside any cell'%(sum(cellids==-1), len(pts)))
    return cellids


def read_vtk_surface(fn):
    from pyformex.plugins.trisurface import TriSurface
    [coords, cells, polys, lines, verts], fielddata, celldata, pointdata = readVTKObject(fn)
    if cells is None:
        data = (coords, polys)
    elif polys is None:
        data = (coords, cells)
    else:
        raise "Both polys and cells are in file %s"%fn
    if 'prop' in celldata.keys():
        kargs = {'prop':celldata['prop']}
    return TriSurface(*data)






#FI Probably other features can be read from the obj (normals, vertices, colors etc)
# I did not check for the moment imports only the mesh
def importOBJ(fn):
    """Import a surface from a .obj file.

    Parameters:

    - `fn`: filename (.obj)
    """
    from vtk import vtkOBJReader
    reader = vtkOBJReader()
    reader.SetFileName(fn)
    reader.Update()
    obj=reader.GetOutput()
    [coords, cells, polys, lines, verts], fielddata, celldata, pointdata = convertFromVPD(vpd=obj,samePlex=True)
    return Mesh(coords,polys)


def import3ds(fn, vtkcolor='color', verbose=True):
    """Import an object from a .3ds file and returns a list of colored meshes.

    It reads and converts a .3ds file into a list of colored meshes,
    by using vtk as intermediate step.

    Parameters:

    - `fn`: filename (.3ds or .3DS)
    - `vtkcolor`: select which color to read from the vtk class: `color` or `specular`.
     The class vtkOpenGLProperty has multiple fields with colors.

    Free 3D galleries are
    archive3d.net
    archibase.net
    """
    from vtk import vtk3DSImporter
    importer = vtk3DSImporter()
    #~ importer.ComputeNormalsOn()
    importer.SetFileName(fn)
    importer.Read()
    ren = importer.GetRenderer()
    actors=ren.GetActors()
    ML = []
    for i in range(0, actors.GetNumberOfItems()):
        act=actors.GetItemAsObject(i)
        act.GetNextPart()
        propOfActor = act.GetProperty()#print (dir(propOfActor))#print list the methods to extract the 3ds such as camera settings and colors.
        if vtkcolor == 'color':
            col = propOfActor.GetColor()#also camera and other things can be extracted!!
        elif vtkcolor == 'specular':
            col = propOfActor.GetSpecularColor()
        else:
            raise ValueError, 'the color you selected in not yet implemented'
        obj = act.GetMapper()
        obj = obj.GetInputAsDataSet()
        obj.Update()
        [coords, cells, polys, lines, verts], fielddata, celldata, pointdata = convertFromVPD(vpd=obj,verbose=verbose,samePlex=True)
        m = Mesh(coords, polys)
        m.attrib(color=col)
        ML.append(m)
    if verbose == True:
        print ('model contains %d objects with a total of %d triangles'%(len(ML), Mesh.concatenate(ML).nelems()))
    return ML


def install_trisurface_methods():
    """Install extra TriSurface methods

    """
    from pyformex.plugins import trisurface
    trisurface.read_vtk_surface = read_vtk_surface
    trisurface.TriSurface.decimate = decimate
    trisurface.TriSurface.findElemContainingPoint = findElemContainingPoint

def install_mesh_methods():
    """Install extra Mesh methods

    """
    from pyformex import mesh
    mesh.Mesh.vtkCut = vtkCut
    mesh.Mesh.vtkClip = vtkClip

install_trisurface_methods()
install_mesh_methods()

# End
