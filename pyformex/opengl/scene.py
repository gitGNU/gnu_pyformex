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

import pyformex as pf
from pyformex import utils
from pyformex import arraytools as at
from pyformex import coords
from pyformex.opengl.drawable import Actor


class ItemList(list):
    """A list of drawn objects of the same kind.

    This is used to collect the Actors, Decorations and Annotations
    in a scene.
    Currently the implementation does not check that the objects are of
    the proper type.
    """

    def __init__(self, canvas):
        self.canvas = canvas
        list.__init__(self)

    def add(self, item):
        """Add an item or a list thereof to a ItemList."""
        if isinstance(item, (tuple,list)):
            self.extend(item)
        else:
            self.append(item)


    def delete(self, items, sticky=True):
        """Remove item(s) from an ItemList.

        Parameters:

        - `items`: a single item or a list or tuple of items
        - `sticky`: bool: if True, also sticky items are removed.
          The default is to not remove sticky items.
          Sticky items are items having an attribute sticky=True.

        """
        if not isinstance(items,(tuple,list)):
            items = [ items ]
        for a in items:
            #
            ## TODO: we should probably standardize on using ids
            ##
            #
            try:
                self.remove(a)
            except:
                print("Could not remove object of type %s from list" % type(a))
                ids = [id(i) for i in self]
                ida = id(a)
                try:
                    ind = ids.index(id(a))
                    print("However, the object is in the list: removing it by id")
                    del self[ind]
                except:
                    print("The object is not in the list: skipping")


    def clear(self, sticky=False):
        """Clear the list.

        Parameters:

        - `sticky`: bool: if True, also sticky items are removed.
          The default is to not remove sticky items.
          Sticky items are items having an attribute sticky=True.

        """
        if sticky:
            del self[:]
        else:
            self[:] = [ a for a in self if (hasattr(a,'sticky') and a.sticky) ]



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
        self.actors = ItemList(self)
        self.oldactors = ItemList(self)
        self.annotations = ItemList(self)
        self.decorations = ItemList(self)
        self.backgrounds = ItemList(self)
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
            self.set_bbox(self.actors)
        return self._bbox


    @bbox.setter
    def bbox(self, bb):
        """Set the bounding box of the scene.

        This can be used to set the scene bounding box to another value
        than the one autocomputed from all actors.

        bb is a (2,3) shaped array specifying a bounding box.
        A special value None may be given to force
        recomputing the bbox from all Actors.
        """
        if bb is None:
            bb = self.actors
        self.set_bbox(bb)


    def set_bbox(self, bb):
        """Set the bounding box of the scene.

        This can be used to set the scene bounding box to another value
        than the one autocomputed from all actors.

        bb is a (2,3) shaped array specifying a bounding box.
        A special value None may be given to force
        recomputing the bbox from all Actors.
        """
        self._bbox = sane_bbox(coords.bbox(bb))


    def changeMode(self,canvas,mode=None):
        """This function is called when the rendering mode is changed

        This method should be called to update the actors on a rendering
        mode change.
        """
        for a in self.actors:
            a.changeMode(canvas)


    def addAny(self, actor):
        """Add any actor type or a list thereof.

        This will add any actor/annotation/decoration item or a list
        of any such items  to the scene. This is the prefered method to add
        an item to the scene, because it makes sure that each item is added
        to the proper list.
        """
        from pyformex.legacy import actors as oldactors
        if isinstance(actor, (tuple,list)):
            [ self.addAny(a) for a in actor ]
        elif isinstance(actor, oldactors.Actor):
            self.oldactors.add(actor)
        elif isinstance(actor, Actor):
            if abs(actor.rendertype) == 1:
                self.annotations.add(actor)
            elif abs(actor.rendertype) == 2:
                self.decorations.add(actor)
            elif actor.rendertype == 3:
                self.backgrounds.add(actor)
            else:
                self.actors.add(actor)
            actor.prepare(self.canvas)
            actor.changeMode(self.canvas)
            self._bbox = None #coords.bbox([actor,self.bbox])


    def removeAny(self, actor):
        """Remove a list of any actor/highlights/annotation/decoration items.

        This will remove the items from any of the canvas lists in which the
        item appears.
        itemlist can also be a single item instead of a list.
        If None is specified, all items from all lists will be removed.
        """
        from pyformex.legacy import actors as oldactors
        if isinstance(actor, (tuple,list)):
            [ self.removeAny(a) for a in actor ]
        elif isinstance(actor, oldactors.Actor):
            self.oldactors.delete(actor)
        elif isinstance(actor, Actor):
            if abs(actor.rendertype) == 1:
                self.annotations.delete(actor)
            elif abs(actor.rendertype) == 2:
                #print(type(actor))
                self.decorations.delete(actor)
            elif actor.rendertype == 3:
                self.backgounds.delete(actor)
            else:
                self.actors.delete(actor)
            self._bbox = None


    def clear(self,sticky=False):
        """Clear the whole scene"""
        self.actors.clear(sticky)
        self.oldactors.clear(sticky)
        self.annotations.clear(sticky)
        self.decorations.clear(sticky)
        self.backgrounds.clear(sticky)


    ## def highlight(self, actors):
    ##     """Highlight the actors in the list."""
    ##     for  in actors:
    ##         obj.removeHighlight()
    ##         obj.highlight = 1


    def removeHighlight(self,actors=None):
        """Remove the highlight from the actors in the list.

        If no actors list is specified, all the highlights are removed.
        """
        if actors is None:
            actors = self.actors
        for actor in actors:
            actor.removeHighlight()


    def printTotals(self):
        print("SCENE: %s actors, %s oldactors, %s annotations, %s decorations" % (len(self.actors), len(self.oldactors), len(self.annotations), len(self.decorations)))


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
    bb = at.checkArray(bb, (2, 3), 'f')
    # make sure we have no NaNs in the bbox
    try:
        bb = at.nan_to_num(bb)
    except:
        print("Invalid Bbox: %s" % bb)
    # make sure bbox size is nonzero in all directions
    sz = bb[1]-bb[0]
    ds = 0.01 * at.length(sz)
    if ds == 0.0:
        ds = 0.5    # when bbox is zero in all directions
    bb[0, sz==0.0] -= ds
    bb[1, sz==0.0] += ds
    return coords.Coords(bb)

### End
