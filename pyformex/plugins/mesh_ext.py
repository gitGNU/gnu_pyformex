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


from pyformex.mesh import *
from pyformex import utils


##############################################################################

def reachableFrom(self,startat,level=0,mask=None,optim_mem=False):
    """Return the elements reachable from startat.

    Finds the elements which can be reached from startat by walking along 
    a mask (a subset of elements). Walking is possible over nodes, edges or faces, 
    as specified in level.
    
    - `startat`: int or array_like, int.
    - `level`: int. Specify how elements can be reached: 
      via node (0), edge (1) or face (2).
    - `mask`: either None or a boolean array or index flagging the elements
      which are to be considered walkable. If None, all elements are considered walkable.
    """
    startat = asarray(startat)
    if length(intersect1d(startat, arange(self.nelems()))) < length(startat):
        raise ValueError, 'wrong elem index found in startat, outside range 0 - %d'%self.nelems()

    if mask is None:
        p = self.frontWalk(level=level,startat=startat,frontinc=0,partinc=1,maxval=1,optim_mem=optim_mem)
        return where(p==0)[0]

    if mask.dtype == bool:
        if length(mask)!=self.nelems():
            raise ValueError, 'if it is an array of boolean mask should have all elements: %d'%self.nelems()
        mask = where(mask)[0]
    if length(intersect1d(mask, arange(self.nelems()))) < length(mask):
        raise ValueError, 'wrong elem index found in mask, outside range 0 - %d'%self.nelems()
        
    startat = intersect1d(startat, mask)
    if length(startat) == 0:
        return []
        
    startat = matchIndex(mask, startat)
    return mask[self.select(mask).reachableFrom(startat=startat,level=level,mask=None,optim_mem=optim_mem)]


@utils.deprecated_by('mesh_ext Mesh.connectedElements','Mesh.reachableFrom')
def connectedElements(self,startat,mask=None):
    return self.reachableFrom(startat=startat,mask=mask)

# REMOVED IN 1.0.0

# The use of both nodesource and elemsource is rather unprobable.
# And when using both, there are two choices: the elements connected
# to the startnodes are added in step 0, or step 1.
# Thus it is better to let the user decide what he wants.
# See the FrontWalk example

## @utils.deprecated("depr_connectionSteps1")
## def connectionSteps(self, nodesource=[], elemsource=[], maxstep=-1):
##     pass
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
    """Compute a quality measure for volume meshes.

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
        return concatenate([self.select(arange(slices[i], slices[i+1])).scaledJacobian(scaled=scaled, blksize=-1) for i in range(len(slices)-1)])
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


@utils.deprecated_by('mesh_ext Mesh.elementToNodal','Field.convert')
def elementToNodal(self, val):
    """_Compute nodal values from element values.

    Given scalar values defined on elements, finds the average values at
    the nodes.
    Returns the average values at the (maxnodenr+1) nodes.
    Nodes not occurring in elems will have all zero values.
    NB. It now works with scalar. It could be extended to vectors.

    This method is deprecated: you should use the
    :class:`Fields` class::

      Field(aMesh,fldtype='elemc',data=val).convert('node')

    """
    eval = val.reshape(-1, 1, 1)
    #
    # Do we really need to duplicate all th
    eval = column_stack(repeat([eval], self.nplex(), 0))#assign this area to all nodes of the elem
    nval = nodalSum(val=eval, elems=self.elems, avg=True, return_all=False)
    return nval.reshape(-1)


# BV:
# - name is misleading with other nodal averaging methods (which average
#   the nodal values at the same point, but obtained from different elems)
# - docstring still does not compile: the example script should go to
#   the example directory, as a pyFormex example
# - should be generalized: not only adjacency over edges
# - should be merged with smooth method

#GDS:
# - this is an image-processing function: see http://www.markschulze.net/java/meanmed.html
# - it should probably be renamed Field.mean() or Field.meanFilter() and placed in fields.py
# - it should be working also for fields defined at elem centers
# - leter a similar function can be added: medianFilter()

# BV: this looks like a smoothing function. Is it?
#     If so, it should be merged with other smoothing filters
#

def nodalAveraging(self, val, iter=1, mask=None,includeself=False):
    """_Replace a nodal value with the mean value of the adjacent nodes.

    Parameters:

    `val` : 1D float array of self.ncoords()
    `includeself` : bool, if True, the node will take part to the averaging process.
    `iter` : int, how many times the averaging procedure should be iterated.
    `mask` : either None or a boolean array or index flagging the nodes of which
      the value has to be changed. If None, all nodal values are replaced.

    This function could be used to apply blurring on a image,
    or smooth sharp variations on a countour plot.

    Example:

      3(5.0)---6(4.0)---2(3.3)
      |        |        |
      |        |        |
      7(6.5)---8(3.2)---5(8.0)
      |        |        |
      |        |        |
      0(1.0)---4(1.2)---1(2.2)

    node 8 is adjacent via edge to nodes 4,5,6,7.
    One avg iteration with includeself=False will give val[8] = (1.2+8.0+4.0+6.5)/4. = 4.925
    One avg iteration with includeself=True will give val[8] = (1.2+8.0+4.0+6.5+3.2)/5. = 4.580

    import elements

    q=Mesh(elements.Quad4())
    q=q.convert('quad4-4')
    VAL = array([1., 2.2, 3.3, 5., 1.2, 8., 4., 6.5, 3.2,])
    txt=['%.3f'%n for n in VAL]
    drawMarks(q.coords.trl([0., 0.05, 0.]), txt)
    draw(q, color='white')
    drawNumbers(q.coords, color='blue')

    q2 = q.trl([1.5, 0., 0.])
    draw(q2, color='red')
    from plugins import mesh_ext
    val2=nodalAveraging(q2, VAL, iter=1, mask=None,includeself=False)
    txt2=['%.3f'%n for n in val2]
    drawMarks(q2.coords, txt2)
    draw(q2, color='red')

    q3 = q.trl([3.0, 0., 0.])
    draw(q3, color='green')
    from plugins import mesh_ext
    val3=nodalAveraging(q3, VAL, iter=1, mask=None,includeself=True)
    txt3=['%.3f'%n for n in val3]
    drawMarks(q3.coords, txt3)
    draw(q3, color='red')

    setTriade()
    zoomAll()
    """

    avgval = checkArray1D(val,kind='f',size=self.ncoords())
    if iter==0:
        return avgval
    nadj = self.getEdges().adjacency(kind='n')
    if includeself:
        nadj = concatenate([nadj,arange(alen(nadj)).reshape(-1,1)],axis=1)
    inadj = nadj>=0#False if == -1
    lnadj = inadj.sum(axis=1)#nr of adjacent nodes
    lnadj = lnadj.astype(Float)#NEEDED!!!, otherwise it becomes float64 and fails if mask is not None !
    if mask is None:
        for j in range(iter):
            avgval = sum(avgval[nadj]*inadj, axis=1)/lnadj # multiplying by inadj set to zero the values where nadj==-1
    else:
        for j in range(iter):
            avgval[mask] = (sum(avgval[nadj]*inadj, axis=1)/lnadj)[mask]
    return avgval


# BV: REMOVED in 1.0.0
## @utils.deprecated("depr_correctNegativeVolumes")
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
#Mesh.connectionSteps = connectionSteps
Mesh.scaledJacobian = scaledJacobian
Mesh.elementToNodal = elementToNodal
Mesh.nodalAveraging = nodalAveraging
Mesh.reachableFrom = reachableFrom
Mesh.connectedElements = connectedElements
# End
