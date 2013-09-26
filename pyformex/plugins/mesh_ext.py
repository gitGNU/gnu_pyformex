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

"""Extended functionality of the Mesh class.

This module defines extended Mesh functionality.

It adds some extra methods to the Mesh class. These may be experimental or
not well tested methods.

Furthermore it defines some functions that generate simple and often used
standard meshes, mostly in 2D.
"""
from __future__ import print_function

from mesh import *
from formex import Formex,interpolate
import simple
import utils


##############################################################################


def smartSeed(n):
    if isInt(n):
        return seed(n)
    elif isinstance(n,tuple):
        return seed(*n)
    elif isinstance(n,list):
        return n
    else:
        raise ValueError,"Expected an integer, tuple or list"


def rectangle(L,W,nl,nw):
    """Create a plane rectangular mesh of quad4 elements

    Parameters:

    - L,W: length,width of the rectangle
    - nl,nw: seeds for the elements along the length, width of the rectangle.
      They should one of the following:

      - an integer number, specifying the number of equally sized elements
        along that direction,
      - a tuple (n,) or (n,e0) or (n,e0,e1), to be used as parameters in the
        :func:`mesh.seed` function,
      - a list of float values in the range 0.0 to 1.0, specifying the relative
        position of the seeds. The values should be ordered and the first and
        last values should be 0.0 and 1.0.

    """
    sl = smartSeed(nl)
    sw = smartSeed(nw)
    return quadgrid(sl,sw).resized([L,W,1.0])


def rectangle_with_hole(L,W,r,nr,nt,e0=0.0,eltype='quad4'):
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


def _add_extra_Mesh_methods():
    """_Add some extra Mesh methods

    Calling this function will install some of the mesh functions
    defined in this modules as Mesh methods.
    This function is called when the module is loaded, so the functions
    installed here will always be available as Mesh methods just by
    importing the mesh_ext module.
    """

    #
    # What is a ring
    # What is returned?
    def rings(self, sources=0, nrings=-1):
        """_
        It finds rings of elements connected to sources by a node.

        Sources can be a single element index (integer) or a list of element indices.
        A list of rings is returned, from zero (ie. the sources) to nrings.
        If nrings is negative (default), all rings are returned.
        """
    #
    # TODO: this should be made an example
    #
        ## Example:

        ## S=Sphere(2)
        ## smooth()
        ## draw(S, mode='wireframe')
        ## drawNumbers(S, ontop=True, color='white')
        ## r=S.rings(sources=[2, 6], nrings=2)
        ## print(r)
        ## for i, ri in enumerate(r):
        ##     draw(S.select(ri).setProp(i), mode='smooth')

        if nrings == 0:
            return [array(sources)]
        r=self.frontWalk(startat=sources,maxval=nrings-1, frontinc=1)
        ar, rr= arange(len(r)), range(r.max()+1)
        return [ar[r==i] for i in rr ]



    def scaledJacobian(self, scaled=True, blksize=100000):
        """
        Returns a quality measure for volume meshes.


        - `blksize`: split in groups to reduce memory requirements for large meshes.
           If negative, the full mesh will be processed at once.

        - `scaled`: if False returns the Jacobian at the corners of each element.
        If scaled True, it returns a quality metrics, being the minumum value of the
        scaled Jacobian in each element (at one corner, the Jacobian divided by the volume of a perfect brick).

        If scaled is True each tet or hex element gets a value between -1 and 1.
        Acceptable elements have a positive scaled Jacobian. However, good
        quality requires a minimum of 0.2. Quadratic meshes are first converted to linear.
        If the mesh contain mainly negative Jacobians, it probably has negative
        volumes and can be fixed with the  correctNegativeVolumes.

        To reduce the memory required for large meshes, the blksize parameter can be used
        specify how many elements will be processed per time. Default 100000.
        """
        ne = self.nelems()
        if blksize>0 and ne>blksize:
            slices=splitrange(n=self.nelems(),nblk=self.nelems()/blksize)
            return concatenate([self.select(range(slices[i], slices[i+1])).scaledJacobian(scaled=scaled, blksize=-1) for i in range(len(slices)-1)])
        if self.elName()=='hex20':
            self = self.convert('hex8')
        if self.elName()=='tet10':
            self = self.convert('tet4')
        if self.elName()=='tet4':
            iacre=array([
            [[0, 1], [1, 2],[2, 0],[3, 2]],
            [[0, 2], [1, 0],[2, 1],[3, 1]],
            [[0, 3], [1, 3],[2, 3],[3, 0]],
            ], dtype=int)
            nc = 4
        if self.elName()=='hex8':
            iacre=array([
            [[0, 4], [1, 5],[2, 6],[3, 7], [4, 7], [5, 4],[6, 5],[7, 6]],
            [[0, 1], [1, 2],[2, 3],[3, 0], [4, 5], [5, 6],[6, 7],[7, 4]],
            [[0, 3], [1, 0],[2, 1],[3, 2], [4, 0], [5, 1],[6, 2],[7, 3]],
            ], dtype=int)
            nc = 8
        acre = self.coords[self.elems][:, iacre]
        vacre = acre[:, :,:,1]-acre[:, :,:,0]
        cvacre = concatenate(vacre, axis=1)

        J = vectorTripleProduct(*cvacre).reshape(ne, nc)
        if not scaled:
            return J
        else:
            normvol = prod(length(cvacre), axis=0).reshape(ne, nc)#volume of 3 nprmal edges
            Jscaled = J/normvol
            return Jscaled.min(axis=1)


    def elementToNodal(self, val):
        """Compute nodal values from element values.

        Given scalar values defined on elements, finds the average values at the nodes.
        Returns the average values at the (maxnodenr+1) nodes. Nodes not occurring in elems
        will have all zero values.
        NB. It now works with scalar. It could be extended to vectors.
        """
        eval = val.reshape(-1,1,1)
        eval = column_stack(repeat([eval], self.nplex(), 0))#assign this area to all nodes of the elem
        nval = nodalSum(val=eval,elems=self.elems,avg=True,return_all=False)
        return nval.reshape(-1)


    def nodalToElement(self, val):
        """Compute element values from nodal values.

        Given scalar values defined on nodes, finds the average values at elements.
        NB. It now works with scalar. It could be extended to vectors.
        """
        return val[self.elems].mean(axis=1)


    # BV: name is way too complex
    # should not be a mesh method, but of some MeshValue class? Field?
    # should be generalized: not only adjacency over edges
    # should be merged with smooth method
    # needs an example
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
            nadj = concatenate([nadj,arange(alen(nadj)).reshape(-1,1)],axis=1)

        inadj = nadj>=0
        lnadj = inadj.sum(axis=1)
        avgval = val

        for j in range(iter):
            avgval = sum(avgval[nadj]*inadj, axis=1)/lnadj # multiplying by inadj set to zero the values where nadj==-1
            if ival!=None:
                avgval[where(ival!=True)] = val[where(ival!=True)]
        return avgval


    @utils.deprecation("depr_correctNegativeVolumes")
    def correctNegativeVolumes(self):
        """_Modify the connectivity of negative-volume elements to make
        positive-volume elements.

        Negative-volume elements (hex or tet with inconsistent face orientation)
        may appear by error during geometrical trnasformations
        (e.g. reflect, sweep, extrude, revolve).
        This function fixes those elements.
        Currently it only works with linear tet and hex.
        """
        vol=self.volumes()<0.
        if self.elName()=='tet4':
            self.elems[vol]=self.elems[vol][:,  [0, 2, 1, 3]]
        if self.elName()=='hex8':
            self.elems[vol]=self.elems[vol][:,  [4, 5, 6, 7, 0, 1, 2, 3]]
        return self


    #####################################################
    #
    # Install
    #
    Mesh.rings = rings
    #Mesh.correctNegativeVolumes = correctNegativeVolumes
    Mesh.scaledJacobian = scaledJacobian
    Mesh.elementToNodal = elementToNodal
    Mesh.nodalToElement = nodalToElement
    Mesh.avgNodalScalarOnAdjacentNodes = avgNodalScalarOnAdjacentNodes


_add_extra_Mesh_methods()


# End
