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

"""Extended functionality of the Mesh class.

The Mesh methods in this module are either deprecated or need some further
work before they get added to the regular mesh.py module.
"""
from __future__ import print_function

from mesh import *
import utils


##############################################################################


# Deprecated: to be removed soon

# The use of both nodesource and elemsource is rather unprobable.
# And when using both, there are two choices: the elements connected
# to the startnodes are added in step 0, or step 1.
# Thus it is better to let the user decide what he wants.
# See the FrontWalk example

@utils.deprecation("depr_connectionSteps1")
def connectionSteps(self, nodesource=[], elemsource=[], maxstep=-1):
    pass
    ## """_Return the elems connected to some sources via multiple nodal steps.

    ## - 'nsources' : are node sources,
    ## - 'esource' : are elem sources,
    ## - 'maxstep' : is the max number of walked elements. If negative (default),
    ##  all rings are returned.

    ## Returns a list of elem indices at each nodal connection step:
    ## elemATstep1 are elem connected to esource or nsource via a node;
    ## elemATstep2 are elem connected to elemATstep1
    ## elemATstep3 are elem connected to elemATstep2
    ## ...
    ## The last member of the list is either the connection after walking `maxstep` edges
    ## or the last possible connection (meaning that one more step would
    ## not find any connected elem).
    ## If the user would like elemsource as first list's item:
    ## [checkArray1D(elemsource)]+self.connectionSteps(nodesource, elemsource, maxstep)

    ## Todo:
    ## -add a connection 'level' to extend to edge and face connections
    ## -add a edgesource and facesource.


    ## """
    ## L = []
    ## ns = unique(concatenate([self.elems[elemsource].ravel(), nodesource]))
    ## if maxstep<0:
    ##     maxstep = self.nelems()
    ## for i in range(maxstep):
    ##     xsource = self.elems.connectedTo(ns)
    ##     mult, bins = multiplicity(concatenate([xsource, elemsource]))
    ##     newring = bins[mult==1]
    ##     if len(newring)==0:
    ##         return L
    ##     L.append(newring)
    ##     elemsource = xsource
    ##     ns = unique(self.elems[elemsource])
    ## return L


#
# TODO: what with other element types ?
#       can this be generalized to 2D meshes?
#       can the listed numerica data not be found from elements.py?
#

def scaledJacobian(self,scaled=True,blksize=100000):
    """
    Compute a quality measure for volume meshes.

    Parameters:

    - `scaled`: if False returns the Jacobian at the corners of each
      element. If True, returns a quality metrics, being the
      minimum value of the scaled Jacobian in each element (at one corner,
      the Jacobian divided by the volume of a perfect brick).

    - `blksize`: int: to reduce the memory required for large meshes, the
      Mesh is split in blocks with this number of elements.
      If not positive, all elements are handled at once.

    If `scaled` is True each tet or hex element gets a value between
    -1 and 1.
    Acceptable elements have a positive scaled Jacobian. However, good
    quality requires a minimum of 0.2.
    Quadratic meshes are first converted to linear.
    If the mesh contain mainly negative Jacobians, it probably has negative
    volumes and can be fixed with the correctNegativeVolumes.
    """
    ne = self.nelems()
    if blksize>0 and ne>blksize:
        slices = splitrange(n=self.nelems(), nblk=self.nelems()/blksize)
        return concatenate([self.select(range(slices[i], slices[i+1])).scaledJacobian(scaled=scaled, blksize=-1) for i in range(len(slices)-1)])
    if self.elName()=='hex20':
        self = self.convert('hex8')
    elif self.elName()=='tet10':
        self = self.convert('tet4')
    if self.elName()=='tet4':
        iacre=array([
        [[0, 1], [1, 2], [2, 0], [3, 2]],
        [[0, 2], [1, 0], [2, 1], [3, 1]],
        [[0, 3], [1, 3], [2, 3], [3, 0]],
        ], dtype=int)
        nc = 4
    elif self.elName()=='hex8':
        iacre=array([
        [[0, 4], [1, 5], [2, 6], [3, 7], [4, 7], [5, 4], [6, 5], [7, 6]],
        [[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4]],
        [[0, 3], [1, 0], [2, 1], [3, 2], [4, 0], [5, 1], [6, 2], [7, 3]],
        ], dtype=int)
        nc = 8
    acre = self.coords[self.elems][:, iacre]
    vacre = acre[:,:,:, 1]-acre[:,:,:, 0]
    cvacre = concatenate(vacre, axis=1)
    J = vectorTripleProduct(*cvacre).reshape(ne, nc)
    if not scaled:
        return J
    else:
        # volume of 3 normal edges
        normvol = prod(length(cvacre), axis=0).reshape(ne, nc)
        Jscaled = J/normvol
        return Jscaled.min(axis=1)


# BV: What is a value defined on an element? a constant for the element,
# a value at the center (what is the center?)
# Usually, values are defined at one or more integration points,
# and nodal values could be derived from using the correct
# interpolation formulas.

def elementToNodal(self, val):
    """Compute nodal values from element values.

    Given scalar values defined on elements, finds the average values at
    the nodes.
    Returns the average values at the (maxnodenr+1) nodes.
    Nodes not occurring in elems will have all zero values.
    NB. It now works with scalar. It could be extended to vectors.
    """
    eval = val.reshape(-1, 1, 1)
    #
    # Do we really need to duplicate all th
    eval = column_stack(repeat([eval], self.nplex(), 0))#assign this area to all nodes of the elem
    nval = nodalSum(val=eval, elems=self.elems, avg=True, return_all=False)
    return nval.reshape(-1)


# BV: name is way too complex
# docstring is not clean
# should not be a mesh method, but of some MeshValue class? Field?
# should be generalized: not only adjacency over edges
# should be merged with smooth method
# needs an example

@utils.deprecation("depr_avgNodalScalarOnAdjacentNodes")
def avgNodalScalarOnAdjacentNodes(self, val, iter=1, ival=None,includeself=False):
    """_Smooth nodal scalar values by averaging over adjacent nodes iter times.

    Nodal scalar values (val is a 1D array of self.ncoords() scalar values )
    are averaged over adjacent nodes an number of time (iter)
    in order to provide a smoothed mapping.

    Parameters:

        -'ival' : boolean of shape (self.coords(), 1 ) to select the nodes on which to average.
        The default value ivar=None selects all the nodes

        -'includeself' : include also the scalar value on the node to be average

    """

    if iter==0: return val
    nadj = self.getEdges().adjacency(kind='n')
    if includeself:
        nadj = concatenate([nadj, arange(alen(nadj)).reshape(-1, 1)], axis=1)

    inadj = nadj>=0
    lnadj = inadj.sum(axis=1)
    avgval = val

    for j in range(iter):
        avgval = sum(avgval[nadj]*inadj, axis=1)/lnadj # multiplying by inadj set to zero the values where nadj==-1
        if ival!=None:
            avgval[where(ival!=True)] = val[where(ival!=True)]
    return avgval


# BV: REMOVED in 1.0.0
## @utils.deprecation("depr_correctNegativeVolumes")
## def correctNegativeVolumes(self):
##     """_Modify the connectivity of negative-volume elements to make
##     positive-volume elements.

##     Negative-volume elements (hex or tet with inconsistent face orientation)
##     may appear by error during geometrical trnasformations
##     (e.g. reflect, sweep, extrude, revolve).
##     This function fixes those elements.
##     Currently it only works with linear tet and hex.
##     """
##     vol=self.volumes()<0.
##     if self.elName()=='tet4':
##         self.elems[vol]=self.elems[vol][:,  [0, 2, 1, 3]]
##     if self.elName()=='hex8':
##         self.elems[vol]=self.elems[vol][:,  [4, 5, 6, 7, 0, 1, 2, 3]]
##     return self


#####################################################
#
# Install
#
Mesh.connectionSteps = connectionSteps
Mesh.scaledJacobian = scaledJacobian
Mesh.elementToNodal = elementToNodal
Mesh.avgNodalScalarOnAdjacentNodes = avgNodalScalarOnAdjacentNodes



# End
