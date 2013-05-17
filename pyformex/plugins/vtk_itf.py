# $Id$
##
##  This file is part of pyFormex 0.9.0  (Mon Mar 25 13:52:29 CET 2013)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2012 (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
##  Distributed under the GNU General Public License version 3 or later.
##
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

from pyformex import utils

utils.requireModule('vtk')

from vtk.util.numpy_support import numpy_to_vtk as n2v
from vtk.util.numpy_support import vtk_to_numpy as v2n
from vtk.util.numpy_support import create_vtk_array as cva
from vtk.util.numpy_support import get_numpy_array_type as gnat
from vtk.util.numpy_support import get_vtk_array_type as gvat
from numpy import *

from mesh import Mesh
from coords import Coords
from plugins.trisurface import TriSurface

import os

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
    cleaner=vtkCleanPolyData()
    cleaner.SetInput(vpd)
    cleaner.Update()
    return  cleaner.GetOutput()


def convert2VPD(M,clean=False,lineopt='line',verbose=False):
    """Convert pyFormex data to vtkPolyData.

    Convert a pyFormex Mesh or Coords object into vtkPolyData.
    This is limited to vertices, lines, and polygons.
    Lines should already be ordered (with connectedLineElems for instance).

    Parameters:

    - `M`: a Mesh or Coords type. If M is a Coords type it will be saved as
      VERTS. Else...
    - `clean`: if True, the resulting vtkdata will be cleaned by calling
      cleanVPD.
    - `lineopt`: can have 2 options for handling a line conversion
        'line' will save the entire line
        'segments' will save the line as segments
    

    Returns a vtkPolyData.
    """
    from vtk import vtkPolyData,vtkPoints,vtkIdTypeArray,vtkCellArray

    if verbose:
        print('STARTING CONVERSION FOR DATA OF TYPE %s '%type(M))

    if  isinstance(M,Coords):
        M = Mesh(M,arange(M.ncoords()))

    Nelems = M.nelems() # Number of elements
    Ncxel = M.nplex() # # Number of nodes per element
    
    elems=M.elems
    if Ncxel==2: 
        if lineopt=='line':
            Nelems=1
            Ncxel=M.ncoords()
            elems=arange(M.ncoords()).reshape(1,-1)

    # create a vtkPolyData variable
    vpd=vtkPolyData()

    # creating  vtk coords
    pts = vtkPoints()
    ntype=gnat(pts.GetDataType())
    coordsv = n2v(asarray(M.coords,order='C',dtype=ntype),deep=1) #.copy() # deepcopy array conversion for C like array of vtk, it is necessary to avoid memry data loss
    pts.SetNumberOfPoints(M.ncoords())
    pts.SetData(coordsv)
    vpd.SetPoints(pts)


    # create vtk connectivity
    elms = vtkIdTypeArray()
    ntype=gnat(vtkIdTypeArray().GetDataType())
    elmsv = concatenate([Ncxel*ones(Nelems).reshape(-1,1),elems],axis=1)
    elmsv = n2v(asarray(elmsv,order='C',dtype=ntype),deep=1) #.copy() # deepcopy array conversion for C like array of vtk, it is necessary to avoid memry data loss
    elms.DeepCopy(elmsv)

    # set vtk Cell data
    datav = vtkCellArray()
    datav.SetCells(Nelems,elms)
    if M.nplex() == 1:
        try:
            if verbose:
                print("setting VERTS for data with %s maximum number of point for cell "%Ncxel)
            vpd.SetVerts(datav)
        except:
            raise ValueError,"Error in saving  VERTS"

    elif M.nplex() == 2:
        try:
            if verbose:
                print ("setting LINES for data with %s maximum number of point for cell "%Ncxel)
            vpd.SetLines(datav)
        except:
            raise  ValueError,"Error in saving  LINES"

    else:
        try:
            if verbose:
                print ("setting POLYS for data with %s maximum number of point for cell "%Ncxel)
            vpd.SetPolys(datav)
        except:
            raise ValueError,"Error in saving  POLYS"

    vpd.Update()
    if clean:
        vpd=cleanVPD(vpd)
    return vpd


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


def convertFromVPD(vpd,verbose=False):
    """Convert a vtkPolyData into pyFormex objects.

    Parameters:

    - `vpd`: a vtkPolyData

    Returns a tuple with points, polygons, lines, vertices numpy arrays.
    Returns None for the missing data.
    """
    pts=polys=lines=verts=None

    if vpd is None:
        return [pts, polys, lines, verts]

    # getting points coords
    if  vpd.GetPoints().GetData().GetNumberOfTuples():
        ntype=gnat(vpd.GetPoints().GetDataType())
        pts = asarray(v2n(vpd.GetPoints().GetData()),dtype=ntype)
        if verbose:
            print('Saved points coordinates array')

    # getting Polygons
    if  vpd.GetPolys().GetData().GetNumberOfTuples():
        ntype=gnat(vpd.GetPolys().GetData().GetDataType())
        Nplex = vpd.GetPolys().GetMaxCellSize()
        polys = asarray(v2n(vpd.GetPolys().GetData()),dtype=ntype).reshape(-1,Nplex+1)[:,1:]
        if verbose:
            print('Saved polys connectivity array')

    # getting Lines
    if  vpd.GetLines().GetData().GetNumberOfTuples():
        ntype=gnat(vpd.GetLines().GetData().GetDataType())
        Nplex = vpd.GetLines().GetMaxCellSize()
        lines = asarray(v2n(vpd.GetLines().GetData()),dtype=ntype).reshape(-1,Nplex+1)[:,1:]
        if verbose:
            print('Saved lines connectivity array')

    # getting Vertices
    if  vpd.GetVerts().GetData().GetNumberOfTuples():
        ntype=gnat(vpd.GetVerts().GetData().GetDataType())
        Nplex = vpd.GetVerts().GetMaxCellSize()
        verts = asarray(v2n(vpd.GetVerts().GetData()),dtype=ntype).reshape(-1,Nplex+1)[:,1:]
        if verbose:
            print('Saved verts connectivity array')

    return [pts, polys, lines, verts]


def pointInsideObject(S,P,tol=0.):
    """vtk function to test which of the points P are inside surface S"""

    from vtk import vtkSelectEnclosedPoints

    vpp = convert2VPD(P)
    vps =convert2VPD(S,clean=False)

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
    return asarray(v2n(inside_arr),'bool')



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
    from vtk import vtkOBBTree,vtkPoints,vtkIdList

    vsurf = convert2VPD(surf,clean=False)
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
        loc.IntersectWithLine(lines.coords[lines.elems][i][1],lines.coords[lines.elems][i][0],ptstmp, cellidstmp)
        if cellidstmp.GetNumberOfIds():
            cellids[i] = [cellidstmp.GetId(j) for j in range(cellidstmp.GetNumberOfIds())]
            pts[i] = Coords(v2n(ptstmp.GetData()).squeeze())
    loc.FreeSearchStructure()
    del loc
    return pts,cellids

def convertTransform4x4FromVtk(transform):
    """Convert a VTK transform to numpy array

    Convert a vtk transformation instance vtkTrasmorm into a 4x4 transformation
    matrix array
    """
    trMat4x4 = [[ transform.GetMatrix().GetElement(r,c) for c in range(4)] for r in range(4)]
    return asarray(trMat4x4)


def convertTransform4x4ToVtk(trMat4x4):
    """Convert a numpy array to a VTK transform

    Convert a 4x4 transformation matrix array into a vtkTransform instance
    """
    from vtk import vtkTransform
    trMatVtk=vtkTransform()
    [[trMatVtk.GetMatrix().SetElement(r,c,trMat4x4[r,c]) for c in range(4)] for r in range(4)]
    return trMatVtk


def transform(source,trMat4x4):
    """Apply a 4x4 transformation

    Apply a 4x4 transformation matrix array to source of Coords or any
    surface type.

    Returns the transformed coordinates
    """

    from vtk import vtkTransformPolyDataFilter

    source=convert2VPD(source)
    trMat4x4=convertTransform4x4ToVtk(trMat4x4)
    transformFilter = vtkTransformPolyDataFilter()
    transformFilter.SetInput(source)
    transformFilter.SetTransform(trMat4x4)
    transformFilter.Update()
    return Coords(convertFromVPD(transformFilter.GetOutput())[0])


def octree(surf,tol=0.0,npts=1.):
    """Compute the octree structure of the surface.

    Returns the octree structure of surf according to the maximum
    tolerance tol and the maximum number of points npts in each octant.
    It returns a list of hexahedral meshes of each level of the octree
    with property equal to the number of point of the in each region.
    """
    from vtk import vtkOctreePointLocator, vtkPolyData
    from formex import Formex
    from connectivity import Connectivity

    vm = convert2VPD(surf,clean=False)
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
            region.append(bounds[:,(0,2,4)])
            region.append(bounds[:,(1,2,4)])
            region.append(bounds[:,(1,3,4)])
            region.append(bounds[:,(0,3,4)])

            region.append(bounds[:,(0,2,5)])
            region.append(bounds[:,(1,2,5)])
            region.append(bounds[:,(1,3,5)])
            region.append(bounds[:,(0,3,5)])

        ptsinregion.append(loc.GetPointsInRegion(lf).GetNumberOfTuples())
        regions.append(Coords(region))

    regions = Formex(regions).toMesh().setProp(asarray(ptsinregion,dtype=int32))

    pfrep = []
    for level in range(loc.GetLevel()+1):
        loc.GenerateRepresentation(level,rep)
        reptmp = convertFromVPD(rep)
        reptmp[1] = reptmp[1].reshape(-1,6*4)[:,(0,1,2,3,9,8,11,10)]
        reptmp[0] = reptmp[0][Connectivity(reptmp[1]).renumber()[1]]

        pfrep.append(Mesh(reptmp[0], reptmp[1]).setProp(0))
        centroids = pfrep[-1].matchCentroids(regions)
        pfrep[-1].prop[centroids[centroids>-1]] = regions.prop[centroids>-1]

    loc.FreeSearchStructure()
    del loc
    return pfrep


# End
