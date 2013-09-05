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



### Override some configuration settings

#pf.cfg['canvas/linewidth'] = 2


#### Definitions to be imported in gui.draw #####

def clear_canvas():
    pf.canvas.renderer.clear()
    pf.canvas.clear()


## def draw(o,**kargs):
##     """New draw function for OpenGL2"""
##     pf.canvas.renderer.add(o,**kargs)


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

    # Extract non-object attributes
    view = kargs.get('view',None)
    bbox = kargs.get('bbox',None)
    highlight = kargs.get('highlight',False)

    ## # Fill in the remaining defaults

    if bbox is None:
        bbox = pf.canvas.options.get('bbox','auto')

    ## if shrink is None:
    ##     shrink = pf.canvas.options.get('shrink',None)

    ## ## if marksize is None:
    ## ##     marksize = pf.canvas.options.get('marksize',pf.cfg.get('marksize',5.0))

    ## # Shrink the objects if requested
    ## if shrink:
    ##     FL = [ _shrink(F,pf.canvas.options.get('shrink_factor',0.8)) for F in FL ]

    ## # Execute the drawlock wait before doing first canvas change
    ## pf.GUI.drawlock.wait()

    ## if clear is None:
    ##     clear = pf.canvas.options.get('clear',False)
    ## if clear:
    ##     clear_canvas()

    if view is not None and view != 'last':
        pf.debug("SETTING VIEW to %s" % view,pf.DEBUG.DRAW)
        gui.draw.setView(view)

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

            #print "COLOR OUT",Fcolor
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
                if highlight:
                    pf.canvas.addHighlight(actor)
                else:
                    pf.canvas.addActor(actor)

        # Adjust the camera
        if view is not None or bbox not in [None,'last']:
            if view == 'last':
                view = pf.canvas.options['view']
            if bbox == 'auto':
                bbox = coords.bbox(FL)
            if bbox == 'last':
                bbox = None

            pf.canvas.setCamera(bbox,view)

        pf.canvas.update()
        pf.app.processEvents()
        #pf.debug("AUTOSAVE %s" % image.autoSaveOn())
        ## if image.autoSaveOn():
        ##     image.saveNext()
        ## if wait: # make sure next drawing operation is retarded
        ##     pf.GUI.drawlock.lock()
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


# End
