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
"""Operations on triangulated surfaces using VMTK functions.

This module provides access to VMTK functionality from inside pyFormex.
Documentation for VMTK can be found on http://www.vmtk.org/Main/Tutorials/
and http://www.vmtk.org/VmtkScripts/vmtkscripts/
"""
from __future__ import print_function

import pyformex as pf
from coords import *
from mesh import Mesh
from plugins.trisurface import TriSurface
import utils
import os


def readVmtkCenterlineDat(fn):
   """Read a .dat file containing the centerlines generated with vmtk.

   The first line may contain a header.
   All other lines ('nlines') contain  'nf' floats.
   All data are seperated by blanks.
   
   The return value is a tuple of
   
   - a float array (nlines,nf) with the data
   - a list with the identifiers from the first line
   """
   fil = file(fn,'r')
   line = fil.readline()
   s = line.strip('\n').split()
   data = fromfile(fil,sep=' ',dtype=float32)
   data = data.reshape(-1,len(s))
   return data, s


def centerline(self):
    """Compute the centerline of a surface.

    The centerline is computed using VMTK. This is very well suited for
    computing the centerlines in vascular models.

    Return a Coords with the points defining the centerline.
    """
    tmp = utils.tempFile(suffix='.stl').name
    tmp1 = utils.tempFile(suffix='.dat').name
    pf.message("Writing temp file %s" % tmp)
    self.write(tmp,'stl')
    pf.message("Computing centerline using VMTK")
    cmd = 'vmtk vmtkcenterlines -ifile %s -ofile %s'%(tmp,tmp1)
    sta,out = utils.runCommand(cmd)
    os.remove(tmp)
    if sta:
        pf.message("An error occurred during the remeshing.")
        pf.message(out)
        return None
    data, header = readVmtkCenterlineDat(tmp1)
    print(header)
    cl = Coords(data[:,:3])
    os.remove(tmp1)
    return cl


def centerline(self,seedselector='pickpoint',sourcepoints=[],
               targetpoints=[],endpoints=False):
    """Compute the centerline of a surface.

    The centerline is computed using VMTK. This is very well suited for
    computing the centerlines in vascular models.

    Parameters:
    
    - `seedselector`: str: seed point selection method, one of
      [`pickpoint`,`openprofiles`,`carotidprofiles`,`pointlist`]
    - `sourcepoints`: list: source point coordinates for `pointlist` method
    - `targetpoints`: list: target point coordinates for `pointlist` method
    - `endpoints`: boolean: append source- and targetpoints to centerlines.

    Returns a Coords with the points defining the centerline.
    """
    tmp = utils.tempFile(suffix='.stl').name
    tmp1 = utils.tempFile(suffix='.dat').name
    pf.message("Writing temp file %s" % tmp)
    self.write(tmp,'stl')
    pf.message("Computing centerline using VMTK")
    cmd = 'vmtk vmtkcenterlines -seedselector %s -ifile %s -ofile %s'%(seedselector,tmp,tmp1)
    if len(sourcepoints) != 0:
        cmd += ' -sourcepoints'
        for val in sourcepoints:
            cmd += ' %s' % val
    if len(targetpoints) != 0:   
        cmd += ' -targetpoints'
        for val in targetpoints:
            cmd += ' %s' % val
    if endpoints == True:
        cmd += ' -endpoints 1'
    sta,out = utils.runCommand(cmd)
    os.remove(tmp)
    if sta:
        pf.message("An error occurred during the remeshing.")
        pf.message(out)
        return None
    data, header = readVmtkCenterlineDat(tmp1)
    print(header)
    cl = Coords(data[:,:3])
    os.remove(tmp1)
    return cl


def remesh(self,elementsizemode='edgelength',edgelength=None,
           area=None,aspectratio=None):
    """Remesh a TriSurface.

    Parameters:

    - `elementsizemode`: str: metric that is used for remeshing,
      `edgelength` and `area` allow to specify a global target triangle
      edgelength and area respectively.
    - `edgelength`: float: global target triangle edgelength
    - `area`: float: global target triangle area
    - `aspectratio`: float: upper threshold for aspect ratio (default=1.2).
    
    Returns the remeshed TriSurface.
    """
    tmp = utils.tempFile(suffix='.stl').name
    tmp1 = utils.tempFile(suffix='.stl').name
    pf.message("Writing temp file %s" % tmp)
    self.write(tmp,'stl')
    cmd = 'vmtk vmtksurfaceremeshing -ifile %s -ofile %s'  % (tmp,tmp1)
    if elementsizemode == 'edgelength':
        if  edgelength is None:
           self.getElemEdges()
           E = Mesh(self.coords,self.edges,eltype='line2')
           edgelength =  E.lengths().mean()
        cmd += ' -elementsizemode edgelength -edgelength %s' % edgelength
    elif elementsizemode == 'area':
        if  area is None:
            self.areaNormals()
            area = self.areas.mean()
        cmd += ' -elementsizemode area -area %s' % area
    if aspectratio is not None:
        cmd += ' -aspectratio %s' % aspectratio
    pf.message("Remeshing with command\n %s" % cmd)
    sta,out = utils.runCommand(cmd)
    os.remove(tmp)
    if sta:
        pf.message("An error occurred during the remeshing.")
        pf.message(out)
        return None
    S = TriSurface.read(tmp1)
    os.remove(tmp1)
    return S


def install_trisurface_methods():
    """Install extra TriSurface methods

    """
    #from plugins.trisurface import TriSurface
    TriSurface.centerline = centerline
    TriSurface.remesh = remesh

install_trisurface_methods()

# End













