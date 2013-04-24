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
"""OpenGL rendering objects for the new OpenGL2 engine.

"""
from __future__ import print_function

from gui.drawable import *


### Drawable Objects ###############################################

class Drawable(object):
    """A Drawable is anything that can be drawn on the OpenGL Canvas.

    This defines the interface for all drawbale objects, but does not
    implement any drawable objects.
    Drawable objects should be instantiated from the derived classes.
    Currently, we have the following derived classes:
      Actor: a 3-D object positioned and oriented in the 3D scene. Defined
             in actors.py.
      Mark: an object positioned in 3D scene but not undergoing the camera
             axis rotations and translations. It will always appear the same
             to the viewer, but will move over the screen according to its
             3D position. Defined in marks.py.
      Decor: an object drawn in 2D viewport coordinates. It will unchangeably
             stick on the viewport until removed. Defined in decors.py.

    A Drawable subclass should minimally reimplement the following methods:
      bbox(): return the actors bounding box.
      nelems(): return the number of elements of the actor.
      drawGL(mode): to draw the object. Takes a mode argument so the
        drawing function can act differently depending on the rendering mode.
        There are currently 5 modes:
           wireframe, flat, smooth, flatwire, smoothwire.
        drawGL should only contain OpenGL calls that are allowed inside a
        display list. This may include calling the display list of another
        actor but *not* creating a new display list.
    """

    def __init__(self,nolight=False,ontop=False,**kargs):
        self.list = None
        self.listmode = None # stores mode of self.list: wireframe/smooth/flat
        self.mode = None # subclasses can set a persistent drawing mode
        self.opak = True
        self.nolight = nolight
        self.ontop = ontop
        self.extra = [] # list of dependent Drawables

    def drawGL(self,**kargs):
        """Perform the OpenGL drawing functions to display the actor."""
        pass

    def pickGL(self,**kargs):
        """Mimick the OpenGL drawing functions to pick (from) the actor."""
        pass

    def redraw(self,**kargs):
        self.draw(**kargs)

    def draw(self,**kargs):
        self.prepare_list(**kargs)
        self.use_list()

    def prepare_list(self,**kargs):
        mode = self.mode
        if mode is None:
            if 'mode' in kargs:
                mode = kargs['mode']
            else:
                canvas = kargs.get('canvas',pf.canvas)
                mode = canvas.rendermode

        if mode.endswith('wire'):
            mode = mode[:-4]

        if self.list is None or mode != self.listmode:
            kargs['mode'] = mode
            self.delete_list()
            self.list = self.create_list(**kargs)

    def use_list(self):
        if self.list:
            GL.glCallList(self.list)
        for i in self.extra:
            i.use_list()

    def create_list(self,**kargs):
        displist = GL.glGenLists(1)
        GL.glNewList(displist,GL.GL_COMPILE)
        ok = False
        try:
            if self.nolight:
                GL.glDisable(GL.GL_LIGHTING)
            if self.ontop:
                GL.glDepthFunc(GL.GL_ALWAYS)
            self.drawGL(**kargs)
            ok = True
        finally:
            if not ok:
                pf.debug("Error while creating a display list",pf.DEBUG.DRAW)
                displist = None
            GL.glEndList()
        self.listmode = kargs['mode']
        return displist

    def delete_list(self):
        if self.list:
            GL.glDeleteLists(self.list,1)
        self.list = None


    def setLineWidth(self,linewidth):
        """Set the linewidth of the Drawable."""
        self.linewidth = saneLineWidth(linewidth)

    def setLineStipple(self,linestipple):
        """Set the linewidth of the Drawable."""
        self.linestipple = saneLineStipple(linestipple)

    def setColor(self,color=None,colormap=None,ncolors=1):
        """Set the color of the Drawable."""
        self.color,self.colormap = saneColorSet(color,colormap,shape=(ncolors,))

    def setTexture(self,texture):
        """Set the texture data of the Drawable."""
        if texture is not None:
            if not isinstance(texture,Texture):
                try:
                    texture = Texture(texture)
                except:
                    texture = None
        self.texture = texture

### Actors ###############################################

class Actor(Drawable):
    """An Actor is anything that can be drawn in an OpenGL 3D Scene.

    The visualisation of the Scene Actors is dependent on camera position and
    angles, clipping planes, rendering mode and lighting.

    An Actor subclass should minimally reimplement the following methods:

    - `bbox()`: return the actors bounding box.
    - `drawGL(mode)`: to draw the actor. Takes a mode argument so the
      drawing function can act differently depending on the mode. There are
      currently 5 modes: wireframe, flat, smooth, flatwire, smoothwire.
      drawGL should only contain OpenGL calls that are allowed inside a
      display list. This may include calling the display list of another
      actor but *not* creating a new display list.

    The interactive picking functionality requires the following methods,
    for which we provide do-nothing defaults here:

    - `npoints()`:
    - `nelems()`:
    - `pickGL()`:
    """

    def __init__(self,**kargs):
        Drawable.__init__(self,**kargs)

    def bbox(self):
        """Default implementation for bbox()."""
        try:
            return self.coords.bbox()
        except:
            raise ValueError,"No bbox() defined and no coords attribute"

    def npoints(self):
        return 0
    def nelems(self):
        return 0
    def pickGL(self,mode):
        pass

###########################################################################


class GeomActor(Actor):
    """An OpenGL actor representing a geometrical model.

    The model can either be in Formex or Mesh format.
    """
    mark = False

    def __init__(self,data,elems=None,eltype=None,mode=None,color=None,colormap=None,bkcolor=None,bkcolormap=None,alpha=1.0,bkalpha=None,linewidth=None,linestipple=None,marksize=None,texture=None,avgnormals=None,**kargs):
        """Create a geometry actor.

        The geometry is either in Formex model: a coordinate block with
        shape (nelems,nplex,3), or in Mesh format: a coordinate block
        with shape (npoints,3) and an elems block with shape (nelems,nplex).

        In both cases, an eltype may be specified if the default is not
        suitable. Default eltypes are Point for plexitude 1, Line for
        plexitude 2 and Triangle for plexitude 3 and Polygon for all higher
        plexitudes. Actually, Triangle is just a special case of Polygon.

        Here is a list of possible eltype values (which should match the
        corresponding plexitude):

        =========   ===========   ============================================
        plexitude   `eltype`      element type
        =========   ===========   ============================================
        4           ``tet4``      a tetrahedron
        6           ``wedge6``    a wedge (triangular prism)
        8           ``hex8``      a hexahedron
        =========   ===========   ============================================

        The colors argument specifies a list of OpenGL colors for each
        of the property values in the Formex. If the list has less
        values than the PropSet, it is wrapped around. It can also be
        a single OpenGL color, which will be used for all elements.
        For surface type elements, a bkcolor color can be given for
        the backside of the surface. Default will be the same
        as the front color.
        The user can specify a linewidth to be used when drawing
        in wireframe mode.
        """
        Actor.__init__(self,**kargs)

        # Store a reference to the drawn object
        self.object = data
        self.normals = None

        if isinstance(data,GeomActor):
            self.coords = data.coords
            self.elems = data.elems
            self.eltype = data.eltype

        elif isinstance(data,Mesh):
            self.coords = data.coords
            self.elems = data.elems
            self.eltype = data.elName()
            if hasattr(data,'normals'):
                self.normals = data.normals

        elif isinstance(data,Formex):
            self.coords = data.coords
            self.elems = None
            self.eltype = data.eltype

        else:
            self.coords = data
            self.elems = elems
            self.eltype = eltype

        self.mode = mode
        self.setColor(color,colormap)
        self.setBkColor(bkcolor,bkcolormap)
        self.setAlpha(alpha,bkalpha)
        self.setLineWidth(linewidth)
        self.setLineStipple(linestipple)
        self.marksize = marksize
        self.setTexture(texture)
        self.avgnormals = avgnormals


    def level(self):
        try:
            return self.object.level()
        except:
            return 0

    def getType(self):
        return self.object.__class__

    def nplex(self):
        """Return the plexitude of the elements in the actor."""
        return self.shape()[1]

    def nelems(self):
        """Return the number of elements in the actor."""
        return self.shape()[0]

    def shape(self):
        """Return the number and plexitude of the elements in the actor."""
        if self.elems is None:
            return self.coords.shape[:-1]
        else:
            return self.elems.shape

    def npoints(self):
        return self.points().shape[0]

    def nedges(self):
        # This is needed to be able to pick edges!!
        try:
            return self.object.nedges()
        except:
            try:
                return self.object.getEdges().shape[0]
            except:
                return 0

    def points(self):
        """Return the vertices as a 2-dim array."""
        return self.coords.points()


    def setColor(self,color,colormap=None):
        """Set the color of the Actor."""
        self.color,self.colormap = saneColorSet(color,colormap,self.shape())


    def setBkColor(self,color,colormap=None):
        """Set the backside color of the Actor."""
        self.bkcolor,self.bkcolormap = saneColorSet(color,colormap,self.shape())


    def setAlpha(self,alpha,bkalpha):
        """Set the Actors alpha value."""
        try:
            self.alpha = float(alpha)
        except:
            self.alpha = None
        if bkalpha is None:
            bkalpha = alpha
        try:
            self.bkalpha = float(bkalpha)
        except:
            self.bkalpha = None
        self.opak = (self.alpha == 1.0) or (self.bkalpha == 1.0 )

    def bbox(self):
        return self.coords.bbox()


    def draw(self,**kargs):
        #print(self.__dict__.keys())
        mode = self.mode
        if mode is None:
            if 'mode' in kargs:
                mode = kargs['mode']
            else:
                canvas = kargs.get('canvas',pf.canvas)
                mode = canvas.rendermode

        #print("DRAW MODE %s" % mode)
        if mode.endswith('wire'):
            #print("WIRE MODE")
            try:
                if self.level() > 1:

                    if not hasattr(self,'wire'):
                        import copy
                        wire = copy.copy(self)
                        wire.mode = 'wireframe' # Lock the mode
                        wire.nolight = True
                        wire.ontop = False # True will make objects transparent for edges
                        wire.list = None
                        Drawable.prepare_list(wire,color=asarray(black))
                        self.wire = wire

                    # Add the existing wire to the extra list, and then draw w/o wire
                    if self.wire not in self.extra:
                        self.extra.append(self.wire)
                        # AVOID RECURSION
                        self.wire.extra = []

            except:
                # AVOID error (which should not occur)
                #print("GEOMACTOR.draw: %s" % type(self.object))
                #print self.object.level()
                raise
                pass

            mode = mode[:-4]

        else:
            if hasattr(self,'wire') and self.wire in self.extra:
                self.extra.remove(self.wire)

        if self.list is None or mode != self.listmode:
            kargs['mode'] = mode
            self.delete_list()
            self.list = self.create_list(**kargs)
            self.listmode = mode

        self.use_list()


    def drawGL(self,canvas=None,mode=None,color=None,**kargs):
        """Draw the geometry on the specified canvas.

        The drawing parameters not provided by the Actor itself, are
        derived from the canvas defaults.

        mode and color can be overridden for the sole purpose of allowing
        the recursive use for modes ending on 'wire' ('smoothwire' or
        'flatwire'). In these cases, two drawing operations are done:
        one with mode='wireframe' and color=black, and one with mode=mode[:-4].
        """
        if canvas is None:
            canvas = pf.canvas

        if mode is None:
           mode = self.mode
        if mode is None:
            mode = canvas.rendermode

        if mode != canvas.rendermode:
            canvas.overrideMode(mode)

        ############# set drawing attributes #########
        avgnormals = self.avgnormals
        if avgnormals is None:
            avgnormals = canvas.settings.avgnormals

        lighting = canvas.settings.lighting

        alpha = self.alpha
        if alpha is None:
            alpha = canvas.settings.transparency
        bkalpha = self.bkalpha
        if bkalpha is None:
            bkalpha = canvas.settings.transparency

        if color is None:
            color,colormap = self.color,self.colormap
            bkcolor, bkcolormap = self.bkcolor,self.bkcolormap
        else:
            # THIS OPTION IS ONLY MEANT FOR OVERRIDING THE COLOR
            # WITH THE EDGECOLOR IN ..wire DRAWING MODES
            # SO NO NEED TO SET bkcolor
            #
            # NOT SURE IF WE STILL NEED THIS !   YES!!!
            #
            #raise ValueError,"THIS ERROR SHOULD NOT OCCUR: Contact mainitainers"
            color,colormap = saneColor(color),None
            bkcolor, bkcolormap = None,None

        # convert color index to full colors
        if color is not None and color.dtype.kind == 'i':
            color = colormap[color]

        if bkcolor is not None and bkcolor.dtype.kind == 'i':
            bkcolor = bkcolormap[bkcolor]

        linewidth = self.linewidth
        if linewidth is None:
            linewidth = canvas.settings.linewidth

        if self.linewidth is not None:
            GL.glLineWidth(self.linewidth)

        if self.linestipple is not None:
            glLineStipple(*self.linestipple)

        if mode.startswith('smooth'):
            if hasattr(self,'specular'):
                fill_mode = GL.GL_FRONT
                import colors
                if color is not None:
                    spec = color * self.specular# *  pf.canvas.specular
                    spec = append(spec,1.)
                else:
                    spec = colors.GREY(self.specular)# *  pf.canvas.specular
                GL.glMaterialfv(fill_mode,GL.GL_SPECULAR,spec)
                GL.glMaterialfv(fill_mode,GL.GL_EMISSION,spec)
                GL.glMaterialfv(fill_mode,GL.GL_SHININESS,self.specular)

        ################## draw the geometry #################
        nplex = self.nplex()

        if nplex == 1:
            marksize = self.marksize
            if marksize is None:
                marksize = canvas.settings.pointsize
            # THIS SHOULD GO INTO drawPoints
            if self.elems is None:
                coords = self.coords
            else:
                coords = self.coords[self.elems]
            drawPoints(coords,color,alpha,marksize)

        elif nplex == 2:
            drawLines(self.coords,self.elems,color)

        # beware: some Formex eltypes are strings and may not
        # represent a valid Mesh elementType
        # This is only here for Formex type.
        # We can probably remove it if we avoid eltype 'curve'
        elif nplex == 3 and self.eltype == 'curve':
            drawQuadraticCurves(self.coords,self.elems,color)

        elif self.eltype is None:
            # polygons
            if mode=='wireframe' :
                drawPolyLines(self.coords,self.elems,color)
            else:
                if bkcolor is not None:
                    GL.glEnable(GL.GL_CULL_FACE)
                    GL.glCullFace(GL.GL_BACK)

                drawPolygons(self.coords,self.elems,color,alpha,self.texture,None,None,lighting,avgnormals)
                if bkcolor is not None:
                    GL.glCullFace(GL.GL_FRONT)
                    drawPolygons(self.coords,self.elems,bkcolor,bkalpha,None,None,None,lighting,avgnormals)
                    GL.glDisable(GL.GL_CULL_FACE)

        else:
            el = elementType(self.eltype)

            if mode=='wireframe' or el.ndim < 2:
                for edges in el.getDrawEdges(el.name() in pf.cfg['draw/quadline']):
                    drawEdges(self.coords,self.elems,edges,edges.eltype,color)
            else:
                for faces in el.getDrawFaces(el.name() in pf.cfg['draw/quadsurf']):
                    if bkcolor is not None:
                        # Enable drawing front and back with different colors
                        GL.glEnable(GL.GL_CULL_FACE)
                        GL.glCullFace(GL.GL_BACK)

                    drawFaces(self.coords,self.elems,faces,faces.eltype,color,alpha,self.texture,None,self.normals,lighting,avgnormals)

                    if bkcolor is not None:
                        # Draw the back sides
                        GL.glCullFace(GL.GL_FRONT)
                        drawFaces(self.coords,self.elems,faces,faces.eltype,bkcolor,bkalpha,None,None,self.normals,lighting,avgnormals)
                        GL.glDisable(GL.GL_CULL_FACE)



    def pickGL(self,mode):
        """ Allow picking of parts of the actor.

        mode can be 'element', 'face', 'edge' or 'point'
        """
        if mode == 'element':
            pickPolygons(self.coords,self.elems)

        elif mode == 'face':
            faces = self.object.getFaces()
            if faces is not None:
                pickPolygons(self.coords,faces)

        elif mode == 'edge':
            edges = self.object.getEdges()
            if edges is not None:
                pickPolygons(self.coords,edges)

        elif mode == 'point':
            pickPoints(self.coords)


    def select(self,sel):
        """Return a GeomActor with a selection of this actor's elements

        Currently, the resulting Actor will not inherit the properties
        of its parent, but the eltype will be retained.
        """
        # This selection should be reworked to allow edge and point selections
        if self.elems is None:
            x = self.coords[sel]
            e = self.elems
        else:
            x = self.coords
            e = self.elems[sel]
        return GeomActor(x,e,eltype=self.eltype)

### End
