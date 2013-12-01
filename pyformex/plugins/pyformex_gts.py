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
"""Operations on triangulated surfaces using GTS functions.

This module provides access to GTS from insisde pyFormex.
"""
from __future__ import print_function

import pyformex as pf
from coords import *
import utils
import os
from plugins.trisurface import TriSurface
from multi import multitask

if not utils.hasExternal('gts-bin'):
    utils.warn("error_no_gts_bin")
if not utils.hasExternal('gts-extra'):
    utils.warn("error_no_gts_extra")


#
# gts commands used:
#   in Debian package: stl2gts gts2stl gtscheck
#   not in Debian package: gtssplit gtscoarsen gtsrefine gtssmooth gtsinside
#


def read_gts_intersectioncurve(fn):
    import re
    from formex import Formex
    RE = re.compile("^VECT 1 2 0 2 0 (?P<data>.*)$")
    r = []
    for line in open(fn, 'r'):
        m = RE.match(line)
        if m:
            r.append(m.group('data'))
    nelems = len(r)
    x = fromstring('\n'.join(r), sep=' ').reshape(-1, 2, 3)
    F = Formex(x)
    return F


def boolean(self,surf,op,check=False,verbose=False):
    """Perform a boolean operation with another surface.

    Boolean operations between surfaces are a basic operation in
    free surface modeling. Both surfaces should be closed orientable
    non-intersecting manifolds.
    Use the :meth:`check` method to find out.

    The boolean operations are set operations on the enclosed volumes:
    union('+'), difference('-') or intersection('*').

    Parameters:

    - `surf`: a closed manifold surface
    - `op`: boolean operation: one of '+', '-' or '*'.
    - `filt`: a filter command to be executed on the gtsset output
    - `ext`: extension of the result file
    - `check`: boolean: check that the surfaces are not self-intersecting;
      if one of them is, the set of self-intersecting faces is written
      (as a GtsSurface) on standard output
    - `verbose`: boolean: print statistics about the surface

    Returns: a closed manifold TriSurface

    .. note: This uses the external command 'gtsset'
    """
    return self.gtsset(surf, op, filt = '', ext='.gts', check=check, verbose=verbose)


def intersection(self,surf,check=False,verbose=False):
    """Return the intersection curve of two surfaces.

    Boolean operations between surfaces are a basic operation in
    free surface modeling. Both surfaces should be closed orientable
    non-intersecting manifolds.
    Use the :meth:`check` method to find out.

    Parameters:

    - `surf`: a closed manifold surface
    - `check`: boolean: check that the surfaces are not self-intersecting;
      if one of them is, the set of self-intersecting faces is written
      (as a GtsSurface) on standard output
    - `verbose`: boolean: print statistics about the surface

    Returns: a list of intersection curves.
    """
    return self.gtsset(surf, op='*', ext='.list', curve=True, check=check, verbose=verbose)


def gtsset(self,surf,op,filt='',ext='.tmp',curve=False,check=False,verbose=False):
    """_Perform the boolean/intersection methods.

    See the boolean/intersection methods for more info.
    Parameters not explained there:

    - curve: if True, an intersection curve is computed, else the surface.

    Returns the resulting TriSurface (curve=False), or a plex-2 Formex
    (curve=True), or None if the input surfaces do not intersect.
    """
    op = {'+':'union', '-':'diff', '*':'inter'}[op]
    options = ''
    if curve:
        options += '-i'
    if check:
        options += ' -s'
    if not verbose:
        options += ' -v'
    tmp = utils.tempFile(suffix='.gts').name
    tmp1 = utils.tempFile(suffix='.gts').name
    tmp2 = utils.tempFile(suffix=ext).name
    pf.message("Writing temp file %s" % tmp)
    self.write(tmp, 'gts')
    pf.message("Writing temp file %s" % tmp1)
    surf.write(tmp1, 'gts')
    pf.message("Performing boolean operation")
    cmd = "gtsset %s %s %s %s %s" % (options, op, tmp, tmp1, filt)
    P = utils.system(cmd, stdout=open(tmp2, 'w'))
    os.remove(tmp)
    os.remove(tmp1)
    if P.sta or verbose:
        pf.message(P.out)
    if P.sta:
        pf.message(P.err)
        return None
    pf.message("Reading result from %s" % tmp2)
    if curve:
        res = read_gts_intersectioncurve(tmp2)
    else:
        res = TriSurface.read(tmp2)
    os.remove(tmp2)
    return res


def gtsinside(self,pts,dir=0):
    """_Test whether points are inside the surface.

    pts is a plex-1 Formex.
    dir is the shooting direction.

    Returns a list of point numbers that are inside.
    This is not intended to be used directly. Use inside instead
    """
    import os
    S = self.rollAxes(dir)
    P = pts.rollAxes(dir)
    tmp = utils.tempFile(suffix='.gts').name
    tmp1 = utils.tempFile(suffix='.dta').name
    tmp2 = utils.tempFile(suffix='.out').name
    #print("Writing temp file %s" % tmp)
    S.write(tmp, 'gts')
    #print("Writing temp file %s" % tmp1)
    with open(tmp1, 'w') as f:
        P.coords.tofile(f, sep=' ')
        f.write('\n')

    #print("Performing inside testing")
    cmd = "gtsinside %s %s" % (tmp, tmp1)
    P = utils.command(cmd, stdout=open(tmp2, 'w'))
    os.remove(tmp)
    os.remove(tmp1)
    if P.sta:
        #pf.message("An error occurred during the testing.\nSee file %s for more details." % tmp2)
        pf.message(P.out)
        return None
    #print("Reading results from %s" % tmp2)
    ind = fromfile(tmp2, sep=' ', dtype=Int)
    os.remove(tmp2)
    return ind


def inside(self,pts,atol='auto',multi=False):
    """Test which of the points pts are inside the surface.

    Parameters:

    - `pts`: a (usually 1-plex) Formex or a data structure that can be used
      to initialize a Formex.

    Returns an integer array with the indices of the points that are
    inside the surface. The indices refer to the onedimensional list
    of points as obtained from pts.points().
    """
    from formex import Formex
    if not isinstance(pts, Formex):
        pts = Formex(pts)
    pts = Formex(pts)#.asPoints()

    if atol == 'auto':
        atol = pts.dsize()*0.001

    # determine bbox of common space of surface and points
    bb = bboxIntersection(self, pts)
    if (bb[0] > bb[1]).any():
        # No bbox intersection: no points inside
        return array([], dtype=Int)

    # Limit the points to the common part
    # Add point numbers as property, to allow return of original numbers
    pts.setProp(arange(pts.nelems()))
    pts = pts.clip(testBbox(pts, bb, atol=atol))

    ins = zeros((3, pts.nelems()), dtype=bool)
    if pf.scriptMode == 'script' or not multi:
        for i in range(3):
            dirs = roll(arange(3), -i)[1:]
            # clip the surface perpendicular to the shooting direction
            # !! gtsinside seems to fail sometimes when using clipping
            S = self#.clip(testBbox(self,bb,dirs=dirs,atol=atol),compact=False)
            # find inside points shooting in direction i
            ok = gtsinside(S, pts, dir=i)
            ins[i, ok] = True
    else:
        tasks = [(gtsinside, (self, pts, i)) for i in range(3)]
        ind = multitask(tasks, 3)
        for i in range(3):
            ins[i, ind[i]] = True

    ok = where(ins.sum(axis=0) > 1)[0]
    return pts.prop[ok]



def install_more_trisurface_methods():

    ###################################################
    ## install these functions as TriSurface methods ##

    from trisurface import TriSurface
    TriSurface.boolean = boolean
    TriSurface.intersection = intersection
    TriSurface.gtsset = gtsset


# End
