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
import gui
import coords
from attributes import Attributes



### Override some configuration settings

#pf.cfg['canvas/linewidth'] = 2


#### Definitions to be imported in gui.draw #####


def clear_canvas():
    """Clear the canvas.

    This is a low level function not intended for the user.
    """
    pf.canvas.scene.clear()
    pf.canvas.clear()


def draw(F,
         ## color='prop',colormap=None,alpha=None,
         ## bkcolor=None,bkcolormap=None,bkalpha=None,
         ## mode=None,linewidth=None,linestipple=None,
         ## marksize=None,nolight=False,ontop=False,
         ## view=None,bbox=None,shrink=None,clear=None,
         ## wait=True,allviews=False,highlight=False,silent=True,
         **kargs):
    """New draw function for OpenGL2"""

    # For simplicity of the code, put objects to draw always in a list
    if isinstance(F,list):
        FL = F
    else:
        FL = [ F ]

    # Flatten the list, replacing named objects with their value
    FL = gui.draw.flatten(FL)
    ntot = len(FL)

    # Transform to list of drawable objects
    FL = gui.draw.drawable(FL)
    nres = len(FL)

    if nres < ntot and not silent:
        raise ValueError,"Data contains undrawable objects (%s/%s)" % (ntot-nres,ntot)

    # Get default drawing options and overwrite with specified values
    attr = Attributes(pf.canvas.drawoptions)
    attr.update(kargs)
    print(pf.canvas.drawoptions)
    print(attr)

    # Shrink the objects if requested
    if attr.shrink:
        FL = [ _shrink(F,attr.shrink_factor) for F in FL ]

    ## # Execute the drawlock wait before doing first canvas change
    pf.GUI.drawlock.wait()

    if attr.clear_:
        clear_canvas()

    if attr.view is not None and attr.view != 'last':
        pf.debug("SETTING VIEW to %s" % attr.view,pf.DEBUG.DRAW)
        gui.draw.setView(attr.view)

    pf.GUI.setBusy()
    pf.app.processEvents()

    try:

        actors = []

        # loop over the objects
        for F in FL:

            ## if type(color) is str:
            ##     if color == 'prop':
            ##         try:
            ##             Fcolor = F.prop
            ##         except:
            ##             Fcolor = colors.black
            ##     elif color == 'random':
            ##         # create random colors
            ##         Fcolor = numpy.random.rand(F.nelems(),3)
            ##     else:
            ##         Fcolor = color
            ## else:
            ##     Fcolor = asarray(color)

            # Create the actor
            actor = F.actor(
#                color=Fcolor,colormap=colormap,alpha=alpha,
#                bkcolor=bkcolor,bkcolormap=bkcolormap,bkalpha=bkalpha,
#                mode=mode,linewidth=linewidth,linestipple=linestipple,
#                marksize=marksize,nolight=nolight,ontop=ontop,
                **kargs)

            actors.append(actor)

            if actor is not None:
                # Show the actor
                if attr.highlight:
                    pf.canvas.addHighlight(actor)
                else:
                    pf.canvas.addActor(actor)

        view = attr.view
        bbox = attr.bbox
        print(pf.canvas.drawoptions)
        print(attr)
        print(view)
        print(bbox)

        # Adjust the camera
        if view is not None or bbox not in [None,'last']:
            if view == 'last':
                view = pf.canvas.drawoptions['view']
            if bbox == 'auto':
                bbox = coords.bbox(FL)
            if bbox == 'last':
                bbox = None

            pf.canvas.setCamera(bbox,view)

        # Update the rendering
        pf.canvas.update()
        pf.app.processEvents()

        # Save the rendering if autosave on
        pf.debug("AUTOSAVE %s" % gui.image.autoSaveOn())
        if gui.image.autoSaveOn():
            gui.image.saveNext()

        # Make sure next drawing operation is retarded
        if attr.wait:
            pf.GUI.drawlock.lock()

    finally:
        pf.GUI.setBusy(False)

    if type(F) is list or len(actors) != 1:
        return actors
    else:
        return actors[0]


def drawActor(o):
    pf.canvas.renderer.addActor(o)

#### Other definitions should start with _ ####



#### Override viewport function ####


#### Set the Formex and Mesh actor method ####

def _set_actors():
    def actor(self,**kargs):

        if self.nelems() == 0:
            return None

        from opengl.drawable import GeomActor

        return GeomActor(self,**kargs)

    import formex
    formex.Formex.actor = actor
    import mesh
    mesh.Mesh.actor = actor

_set_actors()

#### Set the WebGL format_actor method

def _set_webgl():

    def format_actor (self,actor):
        """Export an actor in XTK Javascript format."""
        s = ""
        for attr in actor:
            name = attr.name
            s += "var %s = new X.mesh();\n" % name
            if len(attr.children) > 0:
                s += "%s.children = new Array();\n" % name
                for child in attr.children:
                    s += "%s.children.push(%s);\n" % (name,child)
            if attr.file is not None:
                s += "%s.file = '%s';\n" % (name,attr.file)
            if attr.caption is not None:
                s += "%s.caption = '%s';\n" % (name,attr.caption)
            if attr.useObjectColor and attr.color is not None:
               s += "%s.color = %s;\n" % (name,list(attr.color))
            if attr.alpha is not None:
                s += "%s.opacity = %s;\n" % (name,attr.alpha)
            if attr.lighting is not None:
                s += "%s.lighting = %s;\n" % (name,str(bool(attr.lighting)).lower())
            if attr.cullface is not None:
                s += "%s.cullface = '%s';\n" % (name,attr.cullface)
            if attr.magicmode is not None:
                s += "%s.magicmode = '%s';\n" % (name,str(bool(attr.magicmode)).lower())
            if len(attr.children) == 0:
                s += "r.add(%s);\n" % name
            s += "\n"
        return s

    from plugins import webgl
    webgl.WebGL.format_actor = format_actor


_set_webgl()

# End
