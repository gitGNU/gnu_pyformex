#!/usr/bin/env pyformex
# $Id$
##
##  This file is part of pyFormex 0.8 Release Sat Jun 13 09:32:38 2009
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Website: http://pyformex.berlios.de/
##  Copyright (C) Benedict Verhegghe (bverheg@users.berlios.de) 
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
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
"""Create tetraeder mesh in side .STL surface and export in Abaqus format.

Usage: pyformex --nogui stl_abq input.stl
Generates input-surface.inp and input-volume.inp with the
surface and volume modules in Abaqus(R) input format. 
"""

from utils import runCommand
from plugins import surface, fe_abq, tetgen
import os


def abq_export(fn,nodes,elems,eltype,header="Exported by stl_examples.py"):
    """Export a finite element model in Abaqus .inp format."""
    fil = file(fn,'w')
    fe_abq.writeHeading(fil,header)
    fe_abq.writeNodes(fil,nodes)
    fe_abq.writeElems(fil,elems,eltype,nofs=1)
    fil.close()
    print "Abaqus file %s written." % fn


def stl_tetgen(fn):
    """Generate a volume tetraeder mesh inside an stl surface."""
    sta,out = runCommand('tetgen %s' % fn)
    message(out)


def stl_to_abaqus(fn):
    print "Converting %s to Abaqus .INP format" % fn
    stl_tetgen(fn)
    fb = os.path.splitext(fn)[0]
    nodes = tetgen.readNodes(fb+'.1.node')
    elems = tetgen.readElems(fb+'.1.ele')
    faces = tetgen.readSurface(fb+'.1.smesh')
    print "Exporting surface model"
    abq_export(fb+'-surface.inp',nodes,faces,'S3',"Abaqus model generated by tetgen from surface in STL file %s" % fn)
    print "Exporting volume model"
    abq_export(fb+'-volume.inp',nodes,elems,'C3D%d' % elems.shape[1],"Abaqus model generated by tetgen from surface in STL file %s" % fn)
     

# Processing starts here

if __name__ == "script":
    import sys

    for f in sys.argv[2:]:
        if f.endswith('.stl') and os.path.exists(f):
            print "Processing %s" % f
            stl_to_abaqus(f)
        else:
            print "Ignore argument %s" % f

           

# End
