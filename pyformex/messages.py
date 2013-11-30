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

"""Error and Warning Messages

"""
from __future__ import print_function

import pyformex as pf


_message_data = None

def getMessage(msg):
    """Return the real message corresponding with the specified mnemonic.

    If no matching message was defined, the original is returned.
    """
    msg = str(msg) # allows for msg being a Warning
    msg = globals().get(msg,msg)
    if _message_data is not None:
        msg = msg % _message_data
    return msg


print_function = """..

print is now a function
-----------------------
This version of pyFormex enforces scripts to use the print function rather than
the print statement. This means that you should not use::

  print something

but rather::

  print(something)

You can convert your scripts automatically with the command::

  2to3 -f print -wn SCRIPTFILE

"""




warn_viewport_linking = "Linking viewports is an experimental feature and is not fully functional yet."

_future_deprecation = "This functionality is deprecated and will probably be removed in future, unless you explain to the developers why they should retain it."

warn_drawImage_changed = "The `drawImage` function has changed: it now draws an image in 2D on the canvas. Use `drawImage3D` to get the old behavior of drawing a 3D grid colored like the image."
warn_dxf_export = "Objects of type '%s' can not be exported to DXF file"
warn_dxf_noparser = """..

No dxfparser
------------
I can not import .DXF format on your machine, because I can not find the required external program *dxfparser*.

*dxfparser* comes with pyFormex, so this probably means that it just was not (properly) installed. The pyFormex install manual describes how to do it.
"""
if pf.installtype in 'SG':
    warn_dxf_noparser += """
If you are running pyFormex from SVN sources and you can get root access, you can go to the directory `...pyformex/extra/dxfparser/` and follow the instructions there, or you can just try the **Install externals** menu option of the **Help** menu.
"""
    warn_exit_all = "exit(all=True) is no longer supported."
warn_flat_removed = "The 'flat=True' parameter of the draw function has been replaced with 'nolight=True'."
warn_formex_eltype = "Formex eltype currently needs to be a string!"
warn_fuse_arg_rename = "The 'nodesperbox' argument has been renamed to 'ppb'. Please stop using the old name."
warn_mesh_extrude = "Mesh.extrude has changed. The step parameter has been removed and there is now a (total) length parameter."
warn_mesh_connect = "Mesh.connect does no longer automatically compact the Meshes. You may have to use the Mesh.compact method to do so."
mesh_connectedTo = "Mesh.connectedTo has changed! It now returns a list of element numbers instead of a Mesh. Use the select method on the result to extract the corresponding Mesh: Mesh.select(Mesh.connectedTo(...)."
mesh_notConnectedTo = "Mesh.notConnectedTo has been removed! It can be replaced with Mesh.cselect(Mesh.connectedTo(...))."
warn_mesh_partitionbyangle = "The partitioning may be incorrect due to nonplanar 'quad4' elements"
warn_mesh_reflect = "The Mesh.reflect will now by default reverse the elements after the reflection, since that is what the user will want in most cases. The extra reversal can be skipped by specifying 'reverse=False' in the argument list of the `reflect` operation."
warn_mesh_removed_eltype = "The 'eltype' attribute of the Mesh class has been removed. The eltype is now stored solely in the elems attibute. To get the element type from the Mesh, use Mesh.elType() or Mesh.elName(). To set the element type of a Mesh, use Mesh.setType(eltype)."
warn_mesh_reverse = "The meaning of Mesh.reverse has changed. Before, it would just reorder the nodes of the elements in backwards order (just like the Formex.reverse still does. The new definition of Mesh.reverse however is to reverse the line direction for 1D eltypes, to reverse the normals for 2D eltypes and to turn 3D volumes inside out. This definition may have more practical use. It can e.g. be used to fix meshes after a mirroring operation."

warn_nurbs_curve = "Nurbs curves of degree > 7 can currently not be drawn! You can create some approximation by evaluating the curve at some points."
warn_nurb_surface = "Nurbs surfaces of degree > 7 can currently not be drawn! You can approximate the surface by a lower order surface."
warn_nurbs_gic = "Your point set appears to contain double points. Currently I cannot handle that. I will skip the doubles and try to go ahead."
warn_old_numpy = "BEWARE: OLD VERSION OF NUMPY!!!! We advise you to upgrade NumPy!"
warn_old_project = """..

Old project format
------------------
This is an old format project file. Unless you need to read this project file from an older pyFormex version, we strongly advise you to convert the project file to the latest format. Otherwise future versions of pyFormex might not be able to read it back.
"""
warn_pickPolygonEdges = "pickPolygonEdges IS NOT IMPLEMENTED YET!"
warn_project_compression = "The contents of the file does not appear to be compressed."
warn_project_create = "The create=True argument should be replaced with access='w'"
warn_project_legacy = "The legacy=True argument has become superfluous"
warn_properties_setname = "!! 'setname' is deprecated, please use 'name'"
warn_widgets_updatedialogitems = "gui.widgets.updateDialogItems now expects data in the new InputItem format. Use gui.widgets.updateOldDialogItems for use with old data format."
warn_radio_enabler = "A 'radio' type input item can currently not be used as an enabler for other input fields."
warn_vmtk_includeprop = "includeprop %s are in the property set %s. Remesh will not have any effect."
warn_writevtp_notclean = "Mesh is not clean: vtk will alter the nodes. To clean: mesh.fuse().compact().renumber()"
warn_writevtp_shape = "The number of array cells should be equal to the number of elements"
warn_writevtp_shape2 = "The number of array points should be equal to the number of points"


error_widgets_enableitem = "Error in a dialog item enabler. This should not happen! Please file a bug report."
error_no_gts_bin = "I am missing the gts binary programs on your system.\nTherefore, some surface operations will not be available or fail.\n\nOn Debian, you can install the missing programs with `apt-get install libgts-bin`.\n"
error_no_gts_extra = "I am missing the gts binary programs on your system.\nTherefore, some surface operations will not be available or fail.\n\nOn Debian, you can install the missing programs with `apt-get install pyformex-extra`.\n"

depr_adjacencyArrays = "adjacencyArrays is deprecated. Use Adjacency.frontWalk() instead."
depr_image2numpy_arg = "The use of the `expand` parameter in image2numpy is deprecated. Use the `indexed` parameter instead."
depr_mesh_getlowerentities_unique = "The use of the unique argument is deprecated. Use Mesh.insertLevel() instead."
depr_pathextension = "patchextension is deprecated. Use border().extrude() instead."
depr_trisurface_Sphere = "trisurface.Sphere is deprecated: use simple.sphere(ndiv=2**(level-1)) instead"
depr_vertices = "vertices is deprecated. Use points() instead."

# removed in 0.9.1
## depr_tabs = "widgets.Tabs is deprecated. Use InputDialog instead."
## depr_tabledialog = "widgets.TableDialog is deprecated. Use InputDialog with a 'table' inputitem instead."
depr_getResult = "InputDialog.getResult is deprecated. Use getResults instead."
depr_checkarraydim = "checkArrayDim is deprecated. Use checkArray with ndim argument."

PolyLine_distanceOfPoints = "PolyLine.distanceOfPoints is deprecated"
PolyLine_distanceOfPolyline = "PolyLine.distanceOfPolyline is deprecated"

depr_facetarea = "TriSurface.facetArea is deprecated: use TriSurface.areas instead"

depr_abqdata_outres = "The use of the `res` and `out` arguments in AbqData is deprecated. Set them inside your Steps instead."
depr_avgNodalScalarOnAdjacentNodes = "avgNodalScalarOnAdjacentNodes is deprecated. It may be removed in future, unless someone can prove its virtue, generalize, cleanup and document the code and provide an example. See the source code for more comments."
depr_connectionSteps1 = "connectionSteps is deprecated and has been removed. Use frontWalk instead. See the FrontWalk example: walk 3 gives an equivalent result, though you might prefer the simpler solution of walk 2."


# End
