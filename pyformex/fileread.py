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
"""Read geometry from file in a whole number of formats.

This module defines basic routines to read geometrical data
from a file and the specialized importers to read files in a number of
well known standardized formats.

The basic routines are very versatile as well as optimized (using the version
in the pyFormex C-library) and allow to easily create new exporters for
other formats.
"""
from __future__ import print_function
from pyformex import zip

import pyformex as pf
from pyformex.mesh import *
from pyformex import utils
from pyformex.lib import misc
import os


def getParams(line):
    """Strip the parameters from a comment line"""
    s = line.split()
    d = {'mode': s.pop(0),'filename': s.pop(0)}
    d.update(zip(s[::2], s[1::2]))
    return d


def readNodes(fil):
    """Read a set of nodes from an open mesh file"""
    a = fromfile(fil, sep=" ").reshape(-1, 3)
    x = Coords(a)
    return x


def readElems(fil, nplex):
    """Read a set of elems of plexitude nplex from an open mesh file"""
    print("Reading elements of plexitude %s" % nplex)
    e = fromfile(fil, sep=" ", dtype=Int).reshape(-1, nplex)
    e = Connectivity(e)
    return e


def readEsets(fil):
    """Read the eset data of type generate"""
    data = []
    for line in fil:
        s = line.strip('\n').split()
        if len(s) == 4:
            data.append(s[:1]+ [int(i) for i in s[1:]])
    return data


def readMeshFile(fn):
    """Read a nodes/elems model from file.

    Returns a dict:

    - `coords`: a Coords with all nodes
    - `elems`: a list of Connectivities
    - `esets`: a list of element sets
    """
    d = {}
    fil = open(fn, 'r')
    for line in fil:
        if line[0] == '#':
            line = line[1:]
        globals().update(getParams(line))
        dfil = open(filename, 'r')
        if mode == 'nodes':
            d['coords'] = readNodes(dfil)
        elif mode == 'elems':
            elems = d.setdefault('elems', [])
            e = readElems(dfil, int(nplex)) - int(offset)
            elems.append(e)
        elif mode == 'esets':
            d['esets'] = readEsets(dfil)
        else:
            print("Skipping unrecognized line: %s" % line)
        dfil.close()

    fil.close()
    return d


def extractMeshes(d):
    """Extract the Meshes read from a .mesh file.

    """
    x = d['coords']
    e = d['elems']
    M = [ Mesh(x, ei) for ei in e ]
    return M


def convertInp(fn):
    """Convert an Abaqus .inp to a .mesh set of files"""
    converter = os.path.join(pf.cfg['pyformexdir'], 'bin', 'read_abq_inp.awk')
    fn = os.path.abspath(fn)
    dirname = os.path.dirname(fn)
    basename = os.path.basename(fn)
    cmd = 'cd %s;%s %s' % (dirname, converter, basename)
    utils.command(cmd, shell=True)


def readInpFile(filename):
    """Read the geometry from an Abaqus/Calculix .inp file

    This is a replacement for the convertInp/readMeshFile combination.
    It uses the ccxinp plugin to provide a direct import of the Finite
    Element meshes from an Abaqus or Calculix input file.
    Currently still experimental and limited in functionality (aimed
    primarily at Calculix). But also many simple meshes from Abaqus can
    already be read.

    Returns an dict.
    """
    from pyformex.plugins import ccxinp, fe
    ccxinp.skip_unknown_eltype = True
    model = ccxinp.readInput(filename)
    print("Number of parts: %s" % len(model.parts))
    fem = {}
    for part in model.parts:
        try:
            coords = Coords(part['coords'])
            nodid = part['nodid']
            nodpos = inverseUniqueIndex(nodid)
            print("nnodes = %s" % coords.shape[0])
            print("nodid: %s" % nodid)
            print("nodpos: %s" % nodpos)
            for e in part['elems']:
                print("Orig els %s" % e[1])
                print("Trl els %s" % nodpos[e[1]])
            elems = [ Connectivity(nodpos[e], eltype=t) for (t, e) in part['elems'] ]
            print('ELEM TYPES: %s' % [e.eltype for e in elems])
            fem[part['name']] = fe.Model(coords, elems)
        except:
            print("Skipping part %s" % part['name'])
    return fem


def read_off(fn):
    """Read an OFF surface mesh.

    The mesh should consist of only triangles!
    Returns a nodes,elems tuple.
    """
    print("Reading .OFF %s" % fn)
    with utils.File(fn, 'r') as fil:
        head = fil.readline().strip()
        if head != "OFF":
            print("%s is not an OFF file!" % fn)
            return None, None
        nnodes, nelems, nedges = [int(i) for i in fil.readline().split()]
        nodes = fromfile(file=fil, dtype=Float, count=3*nnodes, sep=' ')
        # elems have number of vertices + 3 vertex numbers
        elems = fromfile(file=fil, dtype=int32, count=4*nelems, sep=' ')
    print("Read %d nodes and %d elems" % (nnodes, nelems))
    return nodes.reshape((-1, 3)), elems.reshape((-1, 4))[:, 1:]


def read_gts(fn):
    """Read a GTS surface mesh.

    Return a coords,edges,faces tuple.
    """
    print("Reading GTS file %s" % fn)
    with utils.File(fn, 'r') as fil:
        header = fil.readline().split()
        ncoords, nedges, nfaces = [int(i) for i in header[:3]]
        if len(header) >= 7 and header[6].endswith('Binary'):
            raise RuntimeError("We can not read binary GTS format yet. See https://savannah.nongnu.org/bugs/index.php?38608. Maybe you should recompile the extra/gts commands.")
            sep=''
        else:
            sep=' '
        coords = fromfile(fil, dtype=Float, count=3*ncoords, sep=sep).reshape(-1, 3)
        edges = fromfile(fil, dtype=int32, count=2*nedges, sep=' ').reshape(-1, 2) - 1
        faces = fromfile(fil, dtype=int32, count=3*nfaces, sep=' ').reshape(-1, 3) - 1
    print("Read %d coords, %d edges, %d faces" % (ncoords, nedges, nfaces))
    if coords.shape[0] != ncoords or \
       edges.shape[0] != nedges or \
       faces.shape[0] != nfaces:
        print("Error while reading GTS file: the file is probably incorrect!")
    return coords, edges, faces


def read_stl_bin(fn):
    """Read a binary stl.

    Returns a Coords with shape (ntri,4,3). The first item of each
    triangle is the normal, the other three are the vertices.
    """
    def addTriangle(i):
        x[i] = fromfile(file=fil, dtype=Float, count=12).reshape(4, 3)
        fil.read(2)

    print("Reading binary .STL %s" % fn)
    fil = open(fn, 'rb')
    head = fil.read(80)
    if head[:5] == 'solid':
        raise ValueError("%s looks like an ASCII STL file!" % fn)
    i = head.find('COLOR=')
    if i >= 0 and i <= 70:
        color = fromstring(head[i+6:i+10], dtype=uint8, count=4)
    else:
        color = None

    ntri = fromfile(file=fil, dtype=Int, count=1)[0]
    print("Number of triangles: %s" % ntri)
    x = zeros((ntri, 4, 3), dtype=Float)
    nbytes = 12*4 + 2
    [ addTriangle(i) for i in range(ntri) ]
    print("Finished reading binary stl")
    x = Coords(x)
    if color is not None:
        from pyformex.opengl.colors import GLcolor
        color = GLcolor(color[:3])
    return x, color


def read_gambit_neutral(fn):
    """Read a triangular surface mesh in Gambit neutral format.

    The .neu file nodes are numbered from 1!
    Returns a nodes,elems tuple.
    """
    scr = os.path.join(pf.cfg['bindir'], 'gambit-neu ')
    utils.command("%s '%s'" % (scr, fn))
    nodesf = utils.changeExt(fn, '.nodes')
    elemsf = utils.changeExt(fn, '.elems')
    nodes = fromfile(nodesf, sep=' ', dtype=Float).reshape((-1, 3))
    elems = fromfile(elemsf, sep=' ', dtype=int32).reshape((-1, 3))
    return nodes, elems-1


def read_gambit_neutral_hex(fn):
    """Read an hexahedral mesh in Gambit neutral format.

    The .neu file nodes are numbered from 1!
    Returns a nodes,elems tuple.
    """
    scr = os.path.join(pf.cfg['bindir'], 'gambit-neu-hex ')
    print("%s '%s'" % (scr, fn))
    utils.command("%s '%s'" % (scr, fn))
    nodesf = utils.changeExt(fn, '.nodes')
    elemsf = utils.changeExt(fn, '.elems')
    nodes = fromfile(nodesf, sep=' ', dtype=Float).reshape((-1, 3))
    elems = fromfile(fn_e, sep=' ', dtype=int32).reshape((-1, 8))
    elems = elems[:, (0, 1, 3, 2, 4, 5, 7, 6)]
    return nodes, elems-1

# End

