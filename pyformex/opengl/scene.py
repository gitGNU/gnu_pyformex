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
"""This implements an OpenGL drawing widget for painting 3D scenes.

"""
from __future__ import print_function

## from numpy import *


## from formex import Formex
## from drawable import saneColor,glColor
## import arraytools as at
## import utils
## from mydict import Dict
## from gui import colors
## from gui import views

## from camera import Camera
## from renderer import Renderer
## from collection import Collection

import pyformex as pf
import arraytools as at
import coords
import drawable
from gui import actors
from gui import decors
from gui import marks


class ActorList(list):
    """A list of drawn objects of the same kind.

    This is used to collect the Actors, Decorations and Annotations
    in a scene.
    Currently the implementation does not check that the objects are of
    the proper type.
    """

    def __init__(self,canvas):
        self.canvas = canvas
        list.__init__(self)

    def add(self,actor):
        """Add an actor or a list thereof to a ActorList."""
        if type(actor) is list:
            self.extend(actor)
        else:
            self.append(actor)

    def delete(self,actor):
        """Remove an actor or a list thereof from an ActorList."""
        if not type(actor) in (list,tuple):
            actor = [ actor ]
        for a in actor:
            if a in self:
                self.remove(a)

    def clear(self):
        """Clear the list"""
        del self[:]


    ## def redraw(self):
    ##     """Redraw all actors in the list.

    ##     This redraws the specified actors (recreating their display list).
    ##     This could e.g. be used after changing an actor's properties.
    ##     """
    ##     for actor in self:
    ##         actor.redraw()





##################################################################
#
#  The Scene
#

class Scene(object):
    """An OpenGL scene.

    The Scene is a class holding a collection of Actors, Decorations and
    Annotations. It can also have a background.
    """

    def __init__(self,canvas=None):
        """Initialize an empty scene with default settings."""
        self.canvas = canvas
        self.actors = ActorList(self)
        self.oldactors = ActorList(self)
        self.annotations = ActorList(self)
        self.decorations = ActorList(self)
        self.background = None
        self._bbox = None


    @property
    def bbox(self):
        """Return the bounding box of the scene.

        The bounding box is normally computed automatically as the
        box enclosing all Actors in the scene. Decorations and
        Annotations are not included. The user can however set the
        bbox himself, in which case that value will be used.
        It can also be set to the special value None to force
        recomputing the bbox from all Actors.
        """
        if self._bbox is None:
            #print(self.actors)
            #print([type(a) for a in self.actors])
            #print([a.bbox() for a in self.actors])
            self._bbox = sane_bbox(coords.bbox(self.actors))
        return self._bbox


    @bbox.setter
    def bbox(self,bb):
        """Set the bounding box of the scene.

        This can be used to set the scene bounding box to another value
        than the one autocomputed from all actors.

        bb is a (2,3) shaped array specifying a bounding box.
        A special value None may be given to force
        recomputing the bbox from all Actors.
        """
        if bb is not None:
            bb = sane_bbox(bb)
        self._bbox = bb


    def back_decors(self):
        return [ a for a in self.decorations if not a.ontop ]
    def front_decors(self):
        return [ a for a in self.decorations if a.ontop ]
    def back_annot(self):
        return [ a for a in self.annotations if not a.ontop ]
    def front_annot(self):
        return [ a for a in self.annotations if a.ontop ]
    def back_actors(self):
        return [ a for a in self.actors if not a.ontop ]
    def front_actors(self):
        return [ a for a in self.actors if a.ontop ]


    def add(self,obj,**kargs):
        actor = GeomActor(obj,**kargs)
        self.actors.add(actor)


    def addActor(self,actor):
        self.actors.add(actor)
        actor.prepare(self.canvas)
        actor.changeMode(self.canvas)
        self.bbox = None
        self.canvas.camera.focus = self.bbox.center()
        #print("NEW BBOX: %s" % self.bbox)


    ## def prepare(self,canvas):
    ##     """Prepare the actors for rendering onto the canvas"""
    ##     print("RENDERER.prepare %s to %s" % (canvas.rendermode))
    ##     for a in self.actors:
    ##         actor.prepare(canvas)
    ##         actor.changeMode(canvas)
    ##     self._bbox = None
    ##     self.canvas.camera.focus = self.bbox.center()
    ##     #print("NEW BBOX: %s" % self.bbox


    def changeMode(self,canvas,mode=None):
        """This function is called when the rendering mode is changed

        This method should be called to update the actors on a rendering
        mode change.
        """
        for a in self.actors:
            a.changeMode(canvas)


    def addAny(self,actor):
        """Add any actor type or a list thereof.

        This will add any actor/annotation/decoration item or a list
        of any such items  to the scene. This is the prefered method to add
        an item to the scene, because it makes sure that each item is added
        to the proper list.
        """
        if isinstance(actor,list):
            [ self.addActor(a) for a in actor ]
        elif isinstance(actor,drawable.GeomActor):
            self.addActor(actor)
        elif isinstance(actor,actors.Actor):
            self.oldactors.add(actor)
        elif isinstance(actor,marks.Mark):
            self.annotations.add(actor)
        elif isinstance(actor,decors.Decoration):
            self.decorations.add(actor)


    def removeAny(self,actor):
        """Remove a list of any actor/highlights/annotation/decoration items.

        This will remove the items from any of the canvas lists in which the
        item appears.
        itemlist can also be a single item instead of a list.
        If None is specified, all items from all lists will be removed.
        """
        if isinstance(actor,list):
            [ self.addActor(a) for a in actor ]
        elif isinstance(actor,drawable.GeomActor):
            self.actors.delete(actor)
        elif isinstance(actor,actors.Actor):
            self.oldactors.delete(actor)
        elif isinstance(actor,marks.Mark):
            self.annotations.delete(actor)
        elif isinstance(actor,decors.Decoration):
            self.decorations.delete(actor)


    def clear(self):
        """Clear the whole scene"""
        self.actors.clear()
        self.oldactors.clear()
        self.annotations.clear()
        self.decorations.clear()


    def printTotals(self):
        print("SCENE: %s actors, %s oldactors, %s annotations, %s decorations" % (len(self.actors),len(self.oldactors),len(self.annotations),len(self.decorations)))


##########################################
# Utility functions
#

def sane_bbox(bb):
    """Return a sane nonzero bbox.

    bb should be a (2,3) float array or compatible
    Returns a (2,3) float array where the values of the second
    row are guaranteed larger than the first.
    A value 1 is added in the directions where the input bbox
    has zero size. Also, any NaNs will be transformed to numbers.
    """
    bb = at.checkArray(bb,(2,3),'f')
    # make sure we have no NaNs in the bbox
    try:
        bb = at.nan_to_num(bb)
    except:
        pf.message("Invalid Bbox: %s" % bb)
    # make sure bbox size is nonzero in all directions
    sz = bb[1]-bb[0]
    ds = 0.01 * at.length(sz)
    if ds == 0.0:
        ds = 0.5    # when bbox is zero in all directions
    bb[0,sz==0.0] -= ds
    bb[1,sz==0.0] += ds
    return coords.Coords(bb)


### End
