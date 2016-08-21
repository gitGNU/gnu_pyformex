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

"""Deprecated functionality of the Mesh class.

The Mesh methods in this module are deprecated and will likely be removed in
a future version of pyFormex. Their use is highly discouraged.
"""
from __future__ import absolute_import, print_function


from pyformex.mesh import *
from pyformex import utils


##############################################################################
from pyformex.elements import _default_eltype
linearElements = [_default_eltype[k].name() for k in _default_eltype] # ['line2','tri3','quad4','tet4','wedge6','hex8']

def elNameLinear(elname):
    """Return the linear element name

    E.g. quad8 -> quad4
    """
    i = [elname[:3] == l[:3] for l in linearElements]
    i = where(i)[0][0]
    return linearElements[i]

def isLinear(self):
    """Return True if the element is a linear element"""
    return self.elName() in linearElements

def convertToLinear(self,fuse=False):
    """Return the linear conversion of the mesh

    E.g. if self.elName is quad8 the mesh is converted to quad4
    """
    return self.convert(totype=elNameLinear(self.elName()),fuse=fuse)

def subdivideLinear(self,ndiv,fuse=True):
    """Linear subdivision

    A supra-linear mesh is first converted to linear mesh, then subdivided and converted back.
    """
    if isLinear(self):
        return self.subdivide(*ndiv,fuse=fuse)
    elname = self.elName()
    M = convertToLinear(self,fuse=fuse)
    M = M.subdivide(*ndiv,fuse=fuse)
    return M.convert(elname,fuse=fuse)

## GDS: this should probably be the only sibdivide function exposed to the user!!!
def subdivideIsopar(self, ndiv,totype=None,fuse=True):
    """Isoparametric subdivision

    A supra-linear mesh is subdivided using the isoparametric transformation.
    The returned mesh is linear if totype is None.
    totype should be the same shape: e.g. a quad cannot be subdivided with tri

    The fuse is passed to all functions that have it.
    """
    if totype!=None:
        if elNameLinear(self.elName())!=elNameLinear(totype):
            raise ValueError('you can only change element order in subdivideIsopar')
    if isLinear(self):
        M = self.subdivide(*ndiv,fuse=fuse)
        if totype!=None :
            M = M.convert(totype,fuse=fuse)
        return M
    else:
        #entrance type define isopar
        isop= self.elName()
        #create the isopar
        if totype==None:
            totype = elNameLinear(self.elName())
        v = Mesh(eltype=isop).coords
        #create the patch
        f = subdivideLinear(Mesh(eltype=totype),ndiv,fuse=fuse)
        # map the patch
        M = Mesh.concatenate([f.isopar(isop,h,v) for h in self.coords[self.elems]],fuse=fuse)
        return M.setProp(self.prop,[prod(ndiv)])

#
# Should we create some general 'masked mesh' class?
#
def connectedElements(self,startat,mask,level=0):
    """Return the elements reachable from startat.

    Finds the elements which can be reached from startat by walking along
    a mask (a subset of elements). Walking is possible over nodes, edges or faces,
    as specified in level.

    - `startat`: int or array_like, int.
    - `level`: int. Specify how elements can be reached:
      via node (0), edge (1) or face (2).
    - `mask`: a boolean array or index flagging the elements
      which are to be considered walkable.
    """
    startat = asarray(startat).reshape(-1)
    if len(intersect1d(startat, arange(self.nelems()))) < len(startat):
        raise ValueError("wrong elem index found in startat, outside range 0 - %d" % self.nelems())

    mask = asarray(mask)
    if mask.dtype == bool:
        if len(mask)!=self.nelems():
            raise ValueError("if it is an array of boolean mask should have all elements %d, got %d" % (self.nelems(), len(mask)))
        mask = where(mask)[0]
    if len(intersect1d(mask, arange(self.nelems()))) < len(mask):
        raise ValueError("wrong elem index found in mask, outside range 0 - %d" % self.nelems())

    startat = intersect1d(startat, mask)
    if len(startat) == 0:
        return []

    startat = findIndex(mask, startat)
    return mask[self.select(mask).reachableFrom(startat,level=level)]



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


# REMOVED in 1.0.3
# @utils.deprecated_by('mesh_ext Mesh.elementToNodal','Field.convert')
# def elementToNodal(self, val):
#     """_Compute nodal values from element values.

#     Given scalar values defined on elements, finds the average values at
#     the nodes.
#     Returns the average values at the (maxnodenr+1) nodes.
#     Nodes not occurring in elems will have all zero values.
#     NB. It now works with scalar. It could be extended to vectors.

#     This method is deprecated: you should use the
#     :class:`Fields` class::

#       Field(aMesh,fldtype='elemc',data=val).convert('node')

#     """
#     eval = val.reshape(-1, 1, 1)
#     #
#     # Do we really need to duplicate all th
#     eval = column_stack(repeat([eval], self.nplex(), 0))#assign this area to all nodes of the elem
#     nval = nodalSum(val=eval, elems=self.elems, avg=True, return_all=False)
#     return nval.reshape(-1)


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
    #### Why would float64 fail and float32 not???
    if mask is None:
        for j in range(iter):
            avgval = sum(avgval[nadj]*inadj, axis=1)/lnadj # multiplying by inadj set to zero the values where nadj==-1
    else:
        for j in range(iter):
            avgval[mask] = (sum(avgval[nadj]*inadj, axis=1)/lnadj)[mask]
    return avgval



####
###  TODO: remove this! this is way too complex,
###        not clear what it is supposed to do: all just to fix normals????
###

# GDS: below an implementation of fixNormals using connectivity and adjacency only. To be tested on tri3.
# GDS: it could be extended also to other faces (quad)

def edgeSpin(edges, elems, check=True):
    """Check if edges spin like the face normals.

    elems is the connectivity of a surface mesh.
    edges is the connectivity of edges of a surface mesh.

    True means that edge is spinning like the face normal,
    False means that edge is spinning opposite to the face normal.
    If check is True, it raises an error in case of
    extraneous edges (edges that are not part of the surface),
    instead of returning False.

    edgeSpin([[3,0],...],[[0,2,3]]) is [True,...]
    edgeSpin([[0,3],...],[[0,2,3],..]) is [False,...]
    """
    n = range(elems.shape[1])
    n0 = column_stack([n,roll(n, -1, 0)] )
    spinok = [(edges == elems[:, i]).sum(axis=1)==2 for i in n0]
    spinok = array(sum(spinok, axis=0), dtype=bool)
    if check: # check that edges are valid edges
        n1 = n0[:, ::-1]
        spinbad = [(edges == elems[:, i]).sum(axis=1)==2 for i in n1]
        spinbad = array(sum(spinbad, axis=0), dtype=bool)
        diff = sum(spinok==spinbad)
        if diff>0:
            raise ValueError("there are %d edges which are not in elems" % diff)
    return spinok

def doubleSpinEdges(self,return_mask=False):
    """Find the edges which are adjacent to two triangles with different spin.

    Return True if the 2 adjacent elems have different spin.
    If return_mask == True, a second return value is a boolean array
    with the edges that connect two faces.

    spin2, mask = doubleSpinEdges(S, True)
    draw(Mesh(S.coords, S.getEdges()[mask][spin2]), color='blue', linewidth=4)
    """
    conn = self.getElemEdges().inverse()
    conn2 = (conn >= 0).sum(axis=-1) == 2
    conn = conn[conn2]#remove border edges
    e2 = self.getEdges()[conn2]
    spin0 = edgeSpin(e2, self.elems[conn[:, 0]])
    spin1 = edgeSpin(e2, self.elems[conn[:, 1]])
    spin2 = spin0 == spin1
    if return_mask:
        return spin2, conn2
    else:
        return spin2

def frontWalkEdge(self, maskedge, **kargs):
    """Front walk over elems connected by edges not in maskedge"""
    adj = self.adjacency(level=1)
    cadj = self.getElemEdges().inverse()[maskedge]
    cadj = concatenate([cadj, cadj[:, ::-1]])
    cpos = adj[cadj[:, 0]] == cadj[:, 1].reshape(-1, 1)
    adj[cadj[:, 0], where(cpos)[1]]=-1
    return adj.frontWalk(**kargs)

def findSpinFaces(self):
    """Find a set of differently spinning faces of a surface.

    By looking at the edge adjacency it detects differently spinning triangles.
    The algorithm works like that:

    - find spinedges (edge adjacent to triangles with opposite spin)
    - select a triangle without spinedges as a start (i0)
    - from i0 does a front walk without crossing the spinedges
    - add one frontinc, and store it a set of elems with bad normals
    - reverse the triangles in the frontinc
    # A
    - find spinedges
    - from i0 does a front walk without crossing the spinedges
    - add one frontinc, and store it a set of elems with bad normals
    - reverse the triangles in the frontinc, modifying the surface
    # B
    - repeat from A to B until there no more spinedges

    If self is not a single edge-connected part, the function is called
    on each part.
    """
    s = self.copy()
    parts = s.partitionByConnection(level=1)
    maxpart = parts.max()
    if maxpart > 0: # to handle multiple edge-connected parts
        prev = [findSpinFaces(self.select(parts==pi)) for pi in range(maxpart+1)]
        pw = [where(parts==pi)[0] for pi in range(maxpart+1)]
        rev = [iw[irev] for iw, irev in zip(pw, prev) if len(irev)>0]
        return concatenate(rev)

    spin2, mask = doubleSpinEdges(s, True)
    if all(~spin2):
        return array([])
    espin = where(mask)[0][spin2]#spin edges
    p0 = s.connectedTo(espin, level=1)
    i0 = delete(range(s.nelems()), p0, 0)[0]#this face is chosen as the start for the correct normals
    p = frontWalkEdge(s, maskedge=espin, startat=i0, frontinc=0, partinc=0, maxval=1)
    oldfront = where(p==0)[0]
    p = s.adjacency(level=1).frontWalk(startat=oldfront, frontinc=1, partinc=0, maxval=1)
    tmpRev = where(p==1)[0]
    rev = [tmpRev]
    completed = False
    while(completed==False):
        s = s.reverse(tmpRev)
        spin2, mask = doubleSpinEdges(s, True)
        if any(spin2):
            espin = where(mask)[0][spin2]
            p = frontWalkEdge(s, maskedge=espin, startat=i0, frontinc=0, partinc=1, maxval=1)
            p = s.adjacency(level=1).frontWalk(startat=where(p==0)[0], frontinc=1, partinc=1, maxval=1)
            tmpRev = where(p==1)[0]
            rev.append(tmpRev)
        else:
            completed = True
    return concatenate(rev)

def fixNormals2(self,outwards=True):
    """Fix the orientation of the normals.

    Parameters:

    - `outwards`: boolean: if True (default), a test is done whether
      the surface is a closed manifold, and if so, the normals are
      oriented outwards. Setting this value to False will skip this
      test and the (possible) reversal of the normals.
    """
    S = self.reverse(findSpinFaces(self))
    if outwards:
        s = S.copy()
        parts = s.partitionByConnection(level=0)
        for p in range(parts.max()+1):
            s1 = s.select(parts==p).compact()
            if s1.isClosedManifold() and s1.volume() < 0.:
                S = S.reverse(where(parts==p)[0])
    return S




#####################################################
#
# Install
#
Mesh.scaledJacobian = scaledJacobian
Mesh.nodalAveraging = nodalAveraging
Mesh.connectedElements = connectedElements
Mesh.fixNormals2 = fixNormals2
Mesh.subdivideIsopar = subdivideIsopar
# End
