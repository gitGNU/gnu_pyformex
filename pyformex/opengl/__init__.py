# $Id$
##
##  This file is part of the pyFormex project.
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
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
"""Initialization of the pyFormex opengl module.

The opengl module contains everything related to the new OpenGL2 engine
of pyFormex. The initialization can make changes to the other
pyFormex modules in order to keep them working with the new engine.
"""
from __future__ import print_function


import pyformex as pf
from pyformex import utils
from pyformex import gui
from pyformex import coords
from pyformex.attributes import Attributes



### Override some configuration settings

#pf.cfg['canvas/linewidth'] = 2


#### Definitions to be imported in gui.draw #####


def clear_canvas():
    """Clear the canvas.

    This is a low level function not intended for the user.
    """
    pf.canvas.scene.clear()
    pf.canvas.clear()

#
# TODO: Note that the option 'clear' in the draw statement
#       should be 'clear_' int the gl2 version!
#       Maybe rename to erase?

def draw(F,
         ## color='prop',colormap=None,alpha=None,
         ## bkcolor=None,bkcolormap=None,bkalpha=None,
         ## mode=None,linewidth=None,linestipple=None,
         ## marksize=None,nolight=False,ontop=False,
         ## view=None,bbox=None,shrink=None,clear=None,
         ## wait=True,allviews=False,highlight=False,silent=True,
         # A trick to allow 'clear' argument, but not inside kargs
         clear=None,
         **kargs):
    """New draw function for OpenGL2"""

    if clear is not None:
        kargs['clear_'] = clear

    draw_options = [ 'silent','shrink','clear_','view','highlight','bbox',
                     'allviews' ]

    # For simplicity of the code, put objects to draw always in a list
    if isinstance(F, list):
        FL = F
    else:
        FL = [ F ]

    # Flatten the list, replacing named objects with their value
    FL = gui.draw.flatten(FL)
    ntot = len(FL)

    # Transform to list of drawable objects
    FL = gui.draw.drawable(FL)
    nres = len(FL)

    # Get default drawing options and overwrite with specified values
    opts = Attributes(pf.canvas.drawoptions)
    opts.update(utils.selectDict(kargs,draw_options,remove=True))

    if nres < ntot and not opts.silent:
        raise ValueError("Data contains undrawable objects (%s/%s)" % (ntot-nres, ntot))

    # Shrink the objects if requested
    if opts.shrink:
        FL = [ gui.draw._shrink(F, opts.shrink_factor) for F in FL ]

    ## # Execute the drawlock wait before doing first canvas change
    pf.GUI.drawlock.wait()

    if opts.clear_:
        clear_canvas()

    if opts.view is not None and opts.view != 'last':
        pf.debug("SETTING VIEW to %s" % opts.view, pf.DEBUG.DRAW)
        gui.draw.setView(opts.view)

    pf.GUI.setBusy()
    pf.app.processEvents()

    try:

        actors = []

        # loop over the objects
        for F in FL:

            # Create the actor
            actor = F.actor(**kargs)
            actors.append(actor)

            if actor is not None:
                # Show the actor
                if opts.highlight:
                    pf.canvas.addHighlight(actor)
                else:
                    pf.canvas.addActor(actor)

        view = opts.view
        bbox = opts.bbox
        pf.debug(pf.canvas.drawoptions, pf.DEBUG.OPENGL)
        pf.debug(opts, pf.DEBUG.OPENGL)
        pf.debug(view, pf.DEBUG.OPENGL)
        pf.debug(bbox, pf.DEBUG.OPENGL)

        # Adjust the camera
        if view is not None or bbox not in [None, 'last']:
            if view == 'last':
                view = pf.canvas.drawoptions['view']
            if bbox == 'auto':
                bbox = coords.bbox(FL)
            if bbox == 'last':
                bbox = None

            pf.canvas.setCamera(bbox, view)

        # Update the rendering
        pf.canvas.update()
        pf.app.processEvents()

        # Save the rendering if autosave on
        pf.debug("AUTOSAVE %s" % gui.image.autoSaveOn())
        if gui.image.autoSaveOn():
            gui.image.saveNext()

        # Make sure next drawing operation is retarded
        if opts.wait:
            pf.GUI.drawlock.lock()

    finally:
        pf.GUI.setBusy(False)

    if isinstance(F, list) or len(actors) != 1:
        return actors
    else:
        return actors[0]


#### Other definitions should start with _ ####


#### Override viewport function ####


#### Set the Formex and Mesh actor method ####

def _set_actors():
    def actor(self,**kargs):

        if self.nelems() == 0:
            return None

        from pyformex.opengl.drawable import GeomActor

        return GeomActor(self,**kargs)

    from pyformex import formex
    formex.Formex.actor = actor
    from pyformex import mesh
    mesh.Mesh.actor = actor

_set_actors()

#### Set the WebGL format_actor method

# End
