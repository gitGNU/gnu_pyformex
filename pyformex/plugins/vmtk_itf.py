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
"""Operations on triangulated surfaces using VMTK functions.

This module provides access to VMTK functionality from inside pyFormex.
Documentation for VMTK can be found on http://www.vmtk.org/Main/Tutorials/
and http://www.vmtk.org/VmtkScripts/vmtkscripts/
"""
from __future__ import print_function
from pyformex import zip

import pyformex as pf
from pyformex.coords import *
from pyformex.mesh import Mesh
from pyformex.plugins.trisurface import TriSurface
from pyformex import utils
import os
from pyformex.multi import multitask, cpu_count, splitar

def readVmtkCenterlineDat(fn):
   """Read a .dat file containing the centerlines generated with vmtk.

   The first line may contain a header.
   All other lines ('nlines') contain  'nf' floats.
   All data are seperated by blanks.

   The return value is a tuple of

   - a float array (nlines,nf) with the data
   - a list with the identifiers from the first line
   """
   fil = open(fn, 'r')
   line = fil.readline()
   s = line.strip('\n').split()
   data = fromfile(fil, sep=' ', dtype=float32)
   data = data.reshape(-1, len(s))
   return data, s


def centerline(self,seedselector='pickpoint',sourcepoints=[],
               targetpoints=[],endpoints=False,groupcl=False,capping=False):
    """Compute the centerline of a surface.

    The centerline is computed using VMTK. This is very well suited for
    computing the centerlines in vascular models.

    Parameters:

    - `seedselector`: str: seed point selection method, one of
      [`pickpoint`,`openprofiles`,`carotidprofiles`,`pointlist`,`idlist`].
      Note the `pointlist` option will not use the points defined in `sourcepoints`
      and `targetpoints` as end points of the centerline, but it will look
      for the closest surface point of the open profiles. To avoid this problem with
      this option the vmtksurfacecapper is activated with option centerpoint to
      select the correct point.
    - `sourcepoints`: list: source point coordinates (flattened array-like or Coords-like array)
      for `pointlist` method or a list of point ids for `idlist` method.
    - `targetpoints`: list: flattened target point coordinates for `pointlist` method
      or a list of point ids for `idlist` method
    - `endpoints`: boolean: append source- and targetpoints to centerlines
    - `capping`: boolean: closes open profile
    - `groupcl`: boolean: if True the points of the centerlines are merged and
      grouped to avoid repeated points and separate different branches
  
      Note that when seedselector is `idlist`, the surface must be clenead converting
      it to a vtkPolyData using the function convert2VPD with flag clean=True and then
      converted back using convertFromVPD implemented in the vtk_itf plugin to avoid
      wrong point selection of the vmtk function.

    Returns a tuple containing a list of centerlines returned as PolyLines and a dictionary
    of additional centerlines attributes (such as maximum inscribed sphere
    used for the centerline computation, local coordinate system
    and various integers values to group the centerline points according to
    the branching). Every key contains a list of the attributes arrays grouped per centerline.
    """    
    from pyformex.plugins.curve import PolyLine
    from pyformex.plugins.vtk_itf import readVTKObject
    
    tmp1 = utils.tempFile(suffix='.stl').name
    tmp2 = utils.tempFile(suffix='.vtp').name
    
    print("Writing temp files %s"%tmp1)
    self.write(tmp1, 'stl')
    
    print("Computing centerline using VMTK")
    cmds = []
    
    if capping or seedselector == 'pointlist':
        cmds.append('vmtk vmtksurfacecapper -method centerpoint -interactive 0 -ifile %s -ofile %s'%(tmp1, tmp1))
        
    cmd = 'vmtk vmtkcenterlines -seedselector %s -ifile %s -ofile %s'%(seedselector, tmp1, tmp2)
    
    if seedselector in ['pointlist', 'idlist']:
        if not(len(sourcepoints)) or not(len(targetpoints)):
            raise ValueError('sourcepoints and targetpoints cannot be an empty list when using seedselector= \'%s\''%seedselector)
        if seedselector=='pointlist':
            fmt=' %f'
            sourcepoints=asarray(sourcepoints).ravel()
            targetpoints=asarray(targetpoints).ravel()
        if seedselector=='idlist':
            fmt=' %i'

        cmd += ' -source%ss'%seedselector[:-4]
        cmd += fmt*len(sourcepoints)%tuple(sourcepoints)
        cmd += ' -target%ss'%seedselector[:-4]
        cmd += fmt*len(targetpoints)%tuple(targetpoints)

    cmd += ' -endpoints %i'%endpoints

    cmds.append(cmd)
    
    cmds.append('vmtk vmtkcenterlineattributes -ifile %s -ofile %s\n'%(tmp2, tmp2))
    if groupcl:    
        cmds.append('vmtk vmtkbranchextractor -ifile %s -radiusarray@ MaximumInscribedSphereRadius -ofile %s\n'%(tmp2, tmp2))
        cmds.append('vmtk vmtkcenterlinemerge -ifile %s -ofile %s -radiusarray@ MaximumInscribedSphereRadius \
        -groupidsarray@ GroupIds -centerlineidsarray@ CenterlineIds -tractidsarray@ TractIds \
        -blankingarray@ Blanking -mergeblanked 1'%(tmp2, tmp2))
    cmds.append('vmtk vmtksurfacecelldatatopointdata -ifile %s -ofile %s'%(tmp2, tmp2))

    for c in cmds:
        P = utils.command(c)
        if P.sta:
            print("An error occurred during the centerline computing\n %s"%P.out)
            return None
            
    datatmp = readVTKObject(tmp2,samePlex=0)
    
    os.remove(tmp1)
    os.remove(tmp2)
    
    cls = []
    data = {}
    for icl,clids in enumerate(datatmp[0][3]):
        cls.append(PolyLine(datatmp[0][0][clids]))
        for k in datatmp[3]:
            if not(icl): #initialize the array per every attribute
                data[k] = []
            data[k].append(datatmp[3][k][clids])
                
    return cls,data


def remesh(self,elementsizemode='edgelength',edgelength=None,
           area=None, areaarray=None, aspectratio=None, excludeprop=None, includeprop=None, preserveboundary=False, conformal='border'):
    """Remesh a TriSurface.

    Returns the remeshed TriSurface. If the TriSurface has property numbers
    the property numbers will be inherited by the remeshed surface.

    Parameters:

    - `elementsizemode`: str: metric that is used for remeshing.
      `edgelength`, `area` and `areaarray` allow to specify a global
      target edgelength, area and areaarray (area at each node), respectively.
    - `edgelength`: float: global target triangle edgelength
    - `area`: float: global target triangle area
    - `areaarray`: array of float: nodal target triangle area
    - `aspectratio`: float: upper threshold for aspect ratio (default=1.2)
    - `includeprop`: either a single integer, or a list/array of integers.
      Only the regions with these property number(s) will be remeshed.
      This option is not compatible with `exludeprop`.
    - `excludeprop`: either a single integer, or a list/array of integers.
      The regions with these property number(s) will not be remeshed.
      This option is not compatible with `includeprop`.
    - `preserveboundary`: if True vmtk tries to keep the shape of the border.
    - `conformal`: None, `border` or `regionsborder`.
      If there is a border (ie. the surface is open) conformal=`border`
      preserves the border line (both points and connectivity); conformal=`regionsborder`
      preserves both border line and lines between regions with different property numbers.
    """
    if includeprop is not None:
        if excludeprop is not None:
            raise ValueError('you cannot use both excludeprop and includeprop')
        else:
            ps = self.propSet()
            mask = in1d(ar1=ps, ar2=checkArray1D(includeprop))
            if sum(mask)==0:
                utils.warn("warn_vmtk_includeprop", data=(includeprop, ps))
                return self
            excludeprop = ps[~mask]
    if conformal == 'border' or conformal == 'regionsborder':
        if elementsizemode=='areaarray':
            raise ValueError('conformal (regions)border and areaarray cannot be used together (yet)!')#conformalBorder alters the node list. Afterwards, the nodes do not correspond with pointdata.
        if self.isClosedManifold()==False:
            if conformal == 'regionsborder':
                if self.propSet() is not None:
                    if len(self.propSet())>1:
                        return TriSurface.concatenate([remesh(s2, elementsizemode=elementsizemode, edgelength=edgelength,
                        area=area, areaarray=None, aspectratio=aspectratio,
                        excludeprop=excludeprop, preserveboundary=preserveboundary, conformal='border') for s2 in self.splitProp()])
            added =TriSurface(self.getBorderMesh().convert('line3').setType('tri3'))
            s1 = self+added.setProp(-1)+added.setProp(-2)#add triangles on the border
            s1 = s1.fuse().compact().renumber()#this would mix up the areaarray!!
            excludeprop1 = array([-1, -2])
            if excludeprop is not None:
                excludeprop1 = append(excludeprop1, asarray(excludeprop).reshape(-1))
            return remesh(s1, elementsizemode=elementsizemode, edgelength=edgelength,
               area=area, areaarray=None, aspectratio=aspectratio, excludeprop=excludeprop1,
               preserveboundary=preserveboundary, conformal=None).cselectProp([-1, -2]).compact()
    else:
        if conformal is not None:
            raise ValueError('conformal should be either None, border or regionsborder')

    from pyformex.plugins.vtk_itf import writeVTP, checkClean, readVTKObject
    tmp = utils.tempFile(suffix='.vtp').name
    tmp1 = utils.tempFile(suffix='.vtp').name
    fielddata, celldata, pointdata = {}, {}, {}
    cmd = 'vmtk vmtksurfaceremeshing -ifile %s -ofile %s'  % (tmp, tmp1)
    if elementsizemode == 'edgelength':
        if  edgelength is None:
           self.getElemEdges()
           E = Mesh(self.coords, self.edges, eltype='line2')
           edgelength =  E.lengths().mean()
        cmd += ' -elementsizemode edgelength -edgelength %f' % edgelength
    elif elementsizemode == 'area':
        if  area is None:
            area = self.areas().mean()
        cmd += ' -elementsizemode area -area %f' % area
    elif elementsizemode == 'areaarray':
        if not checkClean(self):
            raise ValueError("Mesh is not clean: vtk will alter the node numbering and the areaarray will not correspond to the node numbering. To clean: mesh.fuse().compact().renumber()")
        cmd += ' -elementsizemode areaarray -areaarray nodalareas '
        pointdata['nodalareas'] = areaarray
    if aspectratio is not None:
        cmd += ' -aspectratio %f' % aspectratio
    if excludeprop is not None:
        cmd += ' -exclude '+' '.join(['%d'%i for i in checkArray1D(excludeprop, kind='i', allow=None)])
    if preserveboundary:
        cmd += ' -preserveboundary 1'
    if self.prop is not None:
        cmd += ' -entityidsarray prop'
    print("Writing temp file %s" % tmp)
    writeVTP(mesh=self, fn=tmp, pointdata=pointdata)
    print("Remeshing with command\n %s" % cmd)
    P = utils.command(cmd)
    os.remove(tmp)
    if P.sta:
        print("An error occurred during the remeshing.")
        print(P.out)
        return None
    [coords, cells, polys, lines, verts], fielddata, celldata, pointdata = readVTKObject(tmp1)
    S = TriSurface(coords, polys)
    if self.prop is not None:
        S=S.setProp(celldata['prop'])
    os.remove(tmp1)
    return S


def vmtkDistanceOfSurface(self, S, tryfixsign=True):
    """Find the distances of TriSurface S to the TriSurface self.

    Retuns a tuple of vector and signed scalar distances for all nodes of S.
    It is advisable to use a surface S which is clean (fused, compacted and renumbered).
    If not vmtk cleans the mesh and the nodes of S are re-matched.
    The signed distance is positive if the distance vector and the surface
    normal have negative dot product, i.e. if node of S is outer with respect to self.
    NB: the sign of sdist computed by vmtk can be wrong! This is a known bug of vmtk: 
    If the endpoint of the distancevector is located on an edge of self, 
    the normal is wrongly computed and the sign of sdist is wrong. 
    The option tryfixsign has been added to solve this bug by letting pyFormex re-computing the dot product.
    However, some wrong sign may still be wrong.
    """
    tmp = utils.tempFile(suffix='.vtp').name
    tmp1 = utils.tempFile(suffix='.vtp').name
    tmp2 = utils.tempFile(suffix='.vtp').name
    S.write(tmp, 'vtp')
    self.write(tmp1, 'vtp')
    cmd = 'vmtk vmtksurfacedistance -ifile %s -rfile %s -distancevectorsarray vdist -signeddistancearray sdist -ofile %s' % (tmp, tmp1, tmp2)
    P = utils.command(cmd)
    os.remove(tmp)
    os.remove(tmp1)
    if P.sta:
        print("An error occurred during the distance calculation.")
        print(P.out)
        return None
    from pyformex.plugins.vtk_itf import readVTKObject
    [coords, cells, polys, lines, verts], fielddata, celldata, pointdata = readVTKObject(tmp2)
    vdist, sdist = pointdata['vdist'], pointdata['sdist']
    os.remove(tmp2)
    from pyformex.plugins.vtk_itf import checkClean
    if not checkClean(S):
        print('nodes need to be re-matched because surface was not clean')
        reorderindex = Coords(coords).match(S.coords)
        vdist = vdist[reorderindex]
        sdist = sdist[reorderindex]
    if tryfixsign:
        from pyformex.plugins.vtk_itf import findElemContainingPoint
        cellids = findElemContainingPoint(self, S.coords+vdist)
        notFound = cellids==-1
        if sum(notFound)>0:
            print ("%d (of %d) points have not been found inside any cell. Check tolerance of findElemContainingPoint"%(sum(notFound), S.ncoords()))
        nc = self.areaNormals()[1][cellids]#normals of cellids
        sdist1 = sign(dotpr(nc, vdist))*abs(sdist)
        sdist[~notFound] = sdist1[~notFound]
    return vdist, sdist


def vmtkDistanceOfPoints(self, X, tryfixsign=True, nproc=1):
    """Find the distances of points X to the TriSurface self.

    - `X` is a (nX,3) shaped array of points.
    - `nproc`: number of parallel processes to use. On multiprocessor machines
      this may be used to speed up the processing. If <= 0 , the number of
      processes will be set equal to the number of processors, to achieve
      a maximal speedup.

    Retuns a tuple of vector and signed scalar distances for all points.
    The signed distance is positive if the distance vector and the surface
    normal have negative dot product, i.e. if X is outer with respect to self.
    """
    if nproc < 1:
        nproc = cpu_count()
    if nproc==1:
        S = TriSurface(X, arange(X.shape[0]).reshape(-1, 1)*ones(3, dtype=int).reshape(1, -1))
        return vmtkDistanceOfSurface(self, S, tryfixsign)
    else:
        datablocks = splitar(X, nproc, close=False)
        print ('-----distance of %d points from %d triangles with %d proc'%(len(X), self.nelems(), nproc))
        tasks = [(vmtkDistanceOfPoints, (self, d, tryfixsign, 1)) for d in datablocks]
        ind = multitask(tasks, nproc)
        vdist, sdist = list(zip(*ind))
        return concatenate(vdist), concatenate(sdist)

def vmtkDistancePointsToSegments(X, L, atol=1.e-4):
    """Find the shortest distances from points X to segments L.

    X is a (nX,3) shaped array of points.
    L is a line2 Mesh.
    atol is the height of the triangles built from lines L (use lines as non-degenerated triangles to vmtk)

    Retuns a tuple of vector and scalar distances for all points.
    Points and lines are first converted into nearly degenerate triangles
    which are then used by vmtkDistanceOfSurface.
    """
    SX = TriSurface(X, arange(X.shape[0]).reshape(-1, 1)*ones(3, dtype=int).reshape(1, -1))
    from geomtools import anyPerpendicularVector
    Lf = L.coords[L.elems]
    L0, L1 = Lf[:, 0], Lf[:, 1]    
    perp = anyPerpendicularVector(L1-L0)    
    L2=0.5*(L0+L1) + normalize(perp)*atol
    SL=TriSurface(concatenate([L0,L1,L2], axis=1).reshape(-1, 3, 3))#NB they should not be fully degenerate otherwise VMTK will not consider them!
    vdist, dist = vmtkDistanceOfSurface(SL, SX, tryfixsign=False)
    return vdist, abs(dist)


def install_trisurface_methods():
    """Install extra TriSurface methods

    """
    #from plugins.trisurface import TriSurface
    TriSurface.centerline = centerline
    TriSurface.remesh = remesh
    TriSurface.vmtkDistanceOfPoints = vmtkDistanceOfPoints

install_trisurface_methods()

# End











