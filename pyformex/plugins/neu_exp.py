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
"""Gambit neutral file exporter.

This module contains some functions to export
pyFormex mesh models to Gambit neutral files.

"""
from __future__ import print_function


import sys
from pyformex.plugins import tetgen
from time import strftime, gmtime
from numpy import *

# Gambit starts counting at 1 for elements and nodes
# this defines the offset for nodes (nofs), elements (eofs) and faces (fofs
nofs, eofs, fofs=1, 1, 1

def writeHeading(fil, nodes, elems, nbsets=0, heading=''):
    """Write the heading of the Gambit neutral file.

    `nbsets`: number of boundary condition sets (border patches).
    """
    fil.write("        CONTROL INFO 2.4.6\n")
    fil.write("** GAMBIT NEUTRAL FILE\n")
    fil.write('%s\n' %heading)
    fil.write('PROGRAM:                Gambit     VERSION:  2.4.6\n')
    fil.write(strftime('%d %b %Y    %H:%M:%S\n', gmtime()))
    fil.write('     NUMNP     NELEM     NGRPS    NBSETS     NDFCD     NDFVL\n')
    fil.write('%10i%10i%10i%10i%10i%10i\n' % (shape(nodes)[0], shape(elems)[0], 1,  nbsets, 3, 3))
    fil.write('ENDOFSECTION\n')

def writeNodes(fil, nodes):
    """Write nodal coordinates.

    """
    fil.write('   NODAL COORDINATES 2.4.6\n')
    for i, n in enumerate(nodes):
        fil.write("%10d%20.11e%20.11e%20.11e\n" % ((i+nofs,)+tuple(n)))
    fil.write('ENDOFSECTION\n')

def writeElems(fil, elems):
    """Write element connectivity.

    """
    shape = elems.shape[1]
    # Library to define the gambit element type number
    gamb_el_library = {#'line2':1, #Edge
                        'quad4': 2,  #Quadrilateral
                        'tri3': 3,  #Triangle
                        'hex8': 4,  #Brick
                        'wedge6': 5,  # Wedge (Prism)
                        'tet4': 6,  #Tetrahedron
                        #'pyr5':7,  #Pyramid
                        }
    try:
        gamb_shape = gamb_el_library[elems.eltype.name()]
    except KeyError:
        raise TypeError("Mesh element type '%s' not convertable"%(elems.eltype.name()))

    #Gambit uses a different convention for the numbering of hex-8 elements
    if gamb_shape==4:  # hex-8
        elems = elems[:, (0, 1, 3, 2, 4, 5, 7, 6)]
        fmt = '%8d %2d %2d %8d%8d%8d%8d%8d%8d%8d\n               %8d\n'
    elif gamb_shape==6:  # tet-4
        elems = elems[:, (0,2,3,1)] 
        fmt = '%8d %2d %2d %8d%8d%8d%8d\n'
        
    for i,e in enumerate(elems+nofs):
        fil.write(fmt%((i+eofs,gamb_shape,shape)+tuple(e)))
    fil.write('ENDOFSECTION\n')


def writeGroup(fil, elems):
    """Write group of elements.

    """
    fil.write('       ELEMENT GROUP 2.4.6\n')
    fil.write('GROUP:%11d ELEMENTS:%11d MATERIAL:%11d NFLAGS:%11d\n' % (1, shape(elems)[0], 2, 1))
    fil.write('%32s\n' %'fluid')
    fil.write('%8d\n' %0)
    n =  shape(elems)[0]/10
    for i in range(n):
        fil.write('%8d%8d%8d%8d%8d%8d%8d%8d%8d%8d\n' %(10*i+1, 10*i+2, 10*i+3, 10*i+4, 10*i+5, 10*i+6, 10*i+7, 10*i+8, 10*i+9, 10*i+10))
    for j in range(shape(elems)[0]-10*n):
        fil.write('%8d' %(10*n+j+1))
    fil.write('\n')
    fil.write('ENDOFSECTION\n')


def writeBCsets(fil, bcsets, elgeotype):
    """Write boundary condition sets of faces.

    Parameters:

    - `bcsets`: a dict where the values are BorderFace arrays (see below).
    - `elgeotype`: element geometry type: 4 for hexahedrons, 6 for
      tetrahedrons.

    BorderFace array: A set of border faces defined as a (n,2) shaped int
    array: echo row contains an element number (enr) and face number (fnr).

    There are 2 ways to construct the BorderFace arrays:

    # find border both as mesh and enr/fnr and keep correspondence::

        brde, brdfaces = M.getFreeEntities(level=-1,return_indices=True)
        brd = Mesh(M.coords, brde)

      .. note: This needs further explanation. Gianluca?

    # matchFaces: Given a volume mesh M and a surface meshes S, being
      (part of) the border of M, BorderFace array for the surface S can
      be obtained from::

        bf = M.matchFaces(S)[1]
    
    To define other boundary types: 
    Value - Boundary Entity Type,
    
    0 UNSPECIFIED, 1 AXIS, 2 CONJUGATE, 3 CONVECTION, 4 CYCLIC,
    5 DEAD, 6 ELEMENT_SIDE, 7 ESPECIES, 8 EXHAUST_FAN, 9 FAN, 
    10 FREE_SURFACE, 11 GAP, 12 INFLOW, 13 INLET, 14 INLET_VENT,
    15 INTAKE_FAN, 16 INTERFACE, 17 INTERIOR, 18 INTERNAL, 19 LIVE,
    20 MASS_FLOW_INLET, 21 MELT, 22 MELT_INTERFACE, 
    23 MOVING_BOUNDARY, 24 NODE, 25 OUTFLOW, 26 OUTLET,
    27 OUTLET_VENT, 28 PERIODIC, 29 PLOT, 30 POROUS, 31 POROUS_JUMP,
    32 PRESSURE, 33 PRESSURE_FAR_FIELD, 34 PRESSURE_INFLOW, 
    35 PRESSURE_INLET, 36 PRESSURE_OUTFLOW, 37 PRESSURE_OUTLET,
    38 RADIATION, 39 RADIATOR , 40 RECIRCULATION_INLET, 41 RECIRCULATION_OUTLET,
    42 SLIP, 43 SREACTION, 44 SURFACE, 45 SYMMETRY, 46 TRACTION, 47 TRAJECTORY,
    48 VELOCITY, 49 VELOCITY_INLET, 50 VENT, 51 WALL, 52 SPRING 
    
    See also
    http://combust.hit.edu.cn:8080/fluent/Gambit13_help/modeling_guide/mg0b.htm#mg0b01
    for the description of the neu file syntax.
    """
    if  elgeotype==4:
        py2neuHF = asarray([3,1,0,2,4,5])#hex faces numbering conversion (pyformex to gambit neu)
    elif  elgeotype==6:
        py2neuHF = asarray([1,3,2,0])# tet faces numbering conversion (pyformex to gambit neu)
        
    if bcsets is not None:
        for k in bcsets.keys():
            print ('Writing BC set : %s\n'%k)
            fil.write('BOUNDARY CONDITIONS 2.4.6\n')
            val = bcsets[k]
            val[:, 1]=py2neuHF[val[:, 1]]
            val+=fofs#faces are counted starting from 1
            fil.write('%32s       1%8d       0%8d\n'%(k, len(val), 6))#patchname, 0/1 is node/face,nr of faces, 0, 
            #type of BC (6 = ELEMENT_SIDE : OK if you import the neu file in fluent)
            for v in val:
                txt='%10d%5d%5d\n'%(v[0], elgeotype, v[1])#elem nr, el type (4 is hex, 6 is tet), face nr
                fil.write(txt)
            fil.write('ENDOFSECTION\n')


def read_tetgen(filename):
    """Read a tetgen tetraedral model.

    filename is the base of the path of the input files.
    For a filename 'proj', nodes are expected in 'proj.1.node'  and
    elems are in file 'proj.1.ele'.
    """
    nodes = tetgen.readNodeFile(filename+'.1.node')[0]
    print("Read %d nodes" % nodes[0].shape[0])
    elems = tetgen.readEleFile(filename+'.1.ele')[0]
    print("Read %d tetraeders" % elems.shape[0])
    return nodes, elems


def write_neu(fil, mesh, bcsets=None, heading='generated with pyFormex'):
    """Export a mesh as .neu file (For use in Gambit/Fluent)

    - `fil`: file name
    - `mesh`: pyFormex Mesh
    - `heading`: heading text to be shown in the gambit header
    - `bcsets`: dictionary of 2D arrays: {'name1': brdfaces1, ...}, see writeBCsets
    """
    if not fil.endswith('.neu'):
        fil += '.neu'
    f = open(fil, 'w')
    if bcsets == None:
        nbsets =0
    else:
        nbsets=len(bcsets.keys())
    print ('Writing %d BC sets'%nbsets)
    writeHeading(f, mesh.coords, mesh.elems, nbsets=nbsets, heading=heading)
    print('Writing %s nodes to .neu file'% len(mesh.coords))
    writeNodes(f, mesh.coords)
    print("Writing %s elements of type '%s' to .neu file"%(len(mesh.elems), mesh.elems.eltype.name()))
    writeElems(f, mesh.elems)
    writeGroup(f, mesh.elems)
    if mesh.elName()=='hex8':
        elgeotype=4
    if mesh.elName()=='tet4':
        elgeotype=6
    writeBCsets(f, bcsets, elgeotype)
    f.close()
    print("Mesh exported to  '%s'"%fil)


def testConverts():
    """_This debug function generates a .neu file for each element type"""

    chdir('~')
    testdir = 'f2fluTests'
    if not os.path.exists(testdir):
        os.makedirs(testdir)
    chdir(testdir)

    from pyformex.simple import cuboid
    mesh = Formex([0., 0., 0.]).extrude(3, dir=0).toMesh().extrude(3, dir=1)
    write_neu('test-quad4.neu', mesh)
    write_neu('test-tri3.neu', mesh.convert('tri3'))
    mesh = cuboid().toMesh().convert('hex8-8')
    write_neu('test-hex8.neu', mesh)
    mesh = Mesh([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.], [1., 0., 1.], [0., 1., 1.]], [[0, 1, 2, 3, 4, 5]])
    write_neu('test-wed6.neu', mesh)
    mesh = Mesh([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]], [[0, 1, 2, 3]], eltype='tet4')
    write_neu('test-tet4.neu', mesh)

# This is special for pyFormex scripts !
if __name__ == 'draw':
    testConverts()


# End
