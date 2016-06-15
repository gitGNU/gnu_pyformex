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
"""OpenGL rendering objects for the new OpenGL2 engine.

"""
from __future__ import print_function


import pyformex as pf
from pyformex.opengl.sanitize import saneFloat, saneLineStipple, saneColorSet
from pyformex.opengl import colors
from OpenGL import GL
from OpenGL.arrays.vbo import VBO
#from pyformex.opengl.shader import Shader
from pyformex.opengl.texture import Texture
from pyformex.attributes import Attributes
from pyformex.formex import Formex
from pyformex.mesh import Mesh
from pyformex.elements import elementType, _default_eltype
from pyformex import geomtools as gt
from pyformex import arraytools as at
from pyformex import utils
import numpy as np
from numpy import int32,float32


### Drawable Objects ###############################################


def glObjType(nplex):
    if nplex <= 3:
        return [GL.GL_POINTS, GL.GL_LINES, GL.GL_TRIANGLES][nplex-1]
    else:
        # everything higher is a polygon
        #
        #  THIS IS BAD: CAN ONLY DRAW A SINGLE POLYGON, NOT MULTIPLE!!!
        #
        #return GL.GL_TRIANGLE_FAN

        raise ValueError("Can only draw plexitude <= 3!")


class Drawable(Attributes):
    """Base class for objects that can be rendered by the OpenGL engine.

    This is the basic drawable object in the pyFormex OpenGL rendering
    engine. It collects all the data that are needed to properly described
    any object to be rendered by the OpenGL shader programs.
    It has a multitude of optional attributes allowing it to describe
    many very different objects and rendering situations.

    This class is however not intended to be directly used to construct an
    object for rendering. The :class:`Actor` class and its multiple
    subclasses should be used for that purpose. The Actor classes provide
    an easier and more logical interface, and more powerful at the same time,
    since they can be compound: one Actor can hold multiple Drawables.

    The elementary objects that can be directly drawn by the shader programs
    are more simple, yet very diverse. The Drawable class collects all
    the data that are needed by the OpenGL engine to do a proper
    rendering of the object. It this represents a single, versatile
    interface of the Actor classes with the GPU shader programs.

    The versatility comes from the :class:`Attributes` base class, with
    an unlimited set of attributes. Any undefined attribute just returns
    None. Some of the most important attributes are described hereafter:

    - `rendertype`: int: the type of rendering process that will be applied
      by the rendering engine to the Drawable:

      0: A full 3D Actor. The Drawable will be rendered in full 3D with
         all active capabilities, such as camera rotation, projection,
         rendermode, lighting. The full object undergoes the camera
         transformations, and thus will appear as a 3D object in space.
         The object's vertices are defined in 3D world coordinates.
         Used in: :class:`Actor`.

      1: A 2D object (often a text or an image) inserted at a 3D position.
         The 2D object always keeps its orientation towards the camera.
         When the camera changes, the object can change its position on
         the viewport, but the oject itself looks the same.
         This can be used to add annotations to (parts of) a 3D object.
         The object is defined in viewport coordinates, the insertion
         points are in 3D world coordinates.
         Used in: :class:`textext.Text`.

      2: A 2D object inserted at a 2D position. Both object and position
         are defined in viewport coordinates. The object will take a fixed
         position on the viewport. This can be use to add decorations to
         the viewport (like color legends and background images).
         Used in: :class:`decors.ColorLegend`.

      3: Like 2, but with special purpose. These Drawables are not part of
         the user scene, but used for system purposes (like setting the
         background color, or adding an elastic rectangle during mouse picking).
         Used in: :meth:`Canvas.createBackground`.

      -1: Like 1, but with different insertion points for the multiple items
          in the object. Used to place a list of marks at a list of points.
          Used in: :class:`textext.Text`.

      -2: A 3D object inserted at a 2D position. The 3D object will rotate
          when the camera changes directions, but it will always be located
          on the same position of the viewport. This is normally used to
          display a helper object showing the global axis directions.
          Used in: :class:`decors.Triade`.


    The initialization of a Drawable takes a single parameter: `parent`,
    which is the Actor that created the Drawable. All other parameters
    should be keyword arguments, and are stored as attributes in the
    Drawable.

    Methods:

    - `prepare...`: creates sanitized and derived attributes/data. Its action
      pend on current canvas settings: mode, transparent, avgnormals

    - `render`: push values to shader and render the object:
      depends on canvas and renderer.

    - `pick`: fake render to be used during pick operations

    - `str`: format the full data set of the Drawable

    """

    # A list of acceptable attributes in the drawable
    # These are the parent attributes that can be overridden
    attributes = [
        'cullface', 'subelems', 'color', 'name', 'highlight', 'opak',
        'linewidth', 'pointsize', 'lighting', 'offset', 'vbo', 'nbo', 'ibo',
        'alpha', 'drawface', 'objectColor', 'useObjectColor',
        'texture', 'texcoords',
        ]

    def __init__(self,parent,**kargs):
        """Create a new drawable."""

        # Should we really restrict this????
        #kargs = utils.selectDict(kargs, Drawable.attributes)
        Attributes.__init__(self, kargs, default=parent)
        #print("ATTRIBUTES STORED IN DRAWABLE",self)
        #print("ATTRIBUTES STORED IN PARENT",parent)

        # Default lighting parameter:
        # rendertype 0 (3D) follows canvas lighting
        # other rendertypes set lighting=False by default
        if self.rendertype != 0 and self.lighting is None:
            self.lighting = False

        # The final plexitude of the drawn objects
        if self.subelems is not None:
            self.nplex = self.subelems.shape[-1]
        else:
            self.nplex = self._fcoords.shape[-2]
        self.glmode = glObjType(self.nplex)


        self.prepareColor()
        #self.prepareNormals()  # The normals are currently always vertex
        self.prepareSubelems()
        if self.texture is not None:
            self.prepareTexture()


    def prepareColor(self):
        """Prepare the colors for the shader."""
        #
        # This should probably be moved to Actor
        #
        if self.highlight:
            # we set single highlight color in shader
            # Currently do everything in Formex model
            # And we always need this one
            self.avbo = VBO(self.fcoords)
            self.useObjectColor = 1
            self.objectColor = np.array(colors.red)

        elif self.color is not None:
            #print("COLOR",self.color)
            if self.color.ndim == 1:
                # here we only accept a single color for front and back
                # different colors should have been handled before
                self.useObjectColor = 1
                self.objectColor = self.color
            elif self.color.ndim == 2:
                self.useObjectColor = 0
                self.vertexColor = at.multiplex(self.color, self.object.nplex())
                #pf.debug("Multiplexing colors: %s -> %s " % (self.color.shape, self.vertexColor.shape),pf.DEBUG.OPENGL2)
            elif self.color.ndim == 3:
                self.useObjectColor = 0
                self.vertexColor = self.color

            if self.vertexColor is not None:
                self.cbo = VBO(self.vertexColor.astype(float32))
                #print("VERTEX COLOR SHAPE = %s" % str(self.cbo.shape))

        #### TODO: should we make this configurable ??
        #
        #  !!!!!!!!!!!!   Fix a bug with AMD cards   !!!!!!!!!!!!!!!
        #
        #  it turns out that some? AMD? cards do not like an unbound cbo
        #  even if that attribute is not used in the shader.
        #  Creating a dummy color buffer seems to solve that problem
        #
        if self.cbo is None:
            self.cbo = VBO(np.array(colors.red))

        #if self.rendertype == 3:
        #    print("CBO DATA %s\n" % self.name,self.cbo.data)


    def changeVertexColor(self,color):
        """Change the vertex color buffer of the object.

        This is experimental!!!
        Just make sure that the passed data have the correct shape!
        """
        self.cbo = VBO(color.astype(float32))


    def prepareTexture(self):
        """Prepare texture and texture coords"""
        if self.useTexture == 1:
            if self.texcoords.ndim == 2:
                #curshape = self.texcoords.shape
                self.texcoords = at.multiplex(self.texcoords, self.object.nelems(),axis=-2)
                #print("Multiplexing texture coords: %s -> %s " % (curshape, self.texcoords.shape))
        self.tbo = VBO(self.texcoords.astype(float32))
        self.texture.activate()


    def prepareSubelems(self):
        """Create an index buffer to draw subelements

        This is always used for nplex > 3, but also to draw the edges
        for nplex=3.
        """
        if self.ibo is None and self.subelems is not None:
            self.ibo = VBO(self.subelems.astype(int32), target=GL.GL_ELEMENT_ARRAY_BUFFER)


    def render(self, renderer):
        """Render the geometry of this object"""

        def render_geom():
            if self.ibo:
                GL.glDrawElementsui(self.glmode, self.ibo)
            else:
                GL.glDrawArrays(self.glmode, 0, np.asarray(self.vbo.shape[:-1]).prod())

        if self.offset:
            pf.debug("POLYGON OFFSET", pf.DEBUG.DRAW)
            GL.glPolygonOffset(1.0, 1.0)

        if self.linewidth:
            GL.glLineWidth(self.linewidth)

        renderer.shader.loadUniforms(self)

        if self.offset3d is not None:
            offset = renderer.camera.toNDC(self.offset3d)
            offset[...,2] = 0.
            offset += (1.,1.,0.)

            #print(self.rendertype)
            #print("OFFSET=",offset)
            #print("COORDS=",self.vbo.data)
            if offset.shape == (3,):
                renderer.shader.uniformVec3('offset3',offset)
            elif offset.ndim > 1:
                self.obo = VBO(offset.astype(float32))
                #self.obo = VBO(self._default_dict_.fcoords+offset)
                #print(self._default_dict_.fcoords)
                #print(offset)
                #print(self.obo.data.shape,self.vbo.data.shape)

                self.obo.bind()
                GL.glEnableVertexAttribArray(renderer.shader.attribute['vertexOffset'])
                GL.glVertexAttribPointer(renderer.shader.attribute['vertexOffset'], 3, GL.GL_FLOAT, False, 0, self.obo)


        if self.rendertype == -2:
            # This is currently a special code for the Triade
            # It needs an object with coords in pixel values,
            # centered around the origin
            # and must have attributes x,y, set to the viewport
            # position of the (0,0,0) point after rotation.
            #
            rot = renderer.camera.modelview.rot
            x = np.dot(self._fcoords.reshape(-1,3),rot).reshape(self._fcoords.shape)
            x[:,:,0] += self.x
            x[:,:,1] += self.y
            x[:,:,2] = 0
            self.vbo = VBO(x)


        self.vbo.bind()
        GL.glEnableVertexAttribArray(renderer.shader.attribute['vertexCoords'])
        GL.glVertexAttribPointer(renderer.shader.attribute['vertexCoords'], 3, GL.GL_FLOAT, False, 0, self.vbo)

        if self.ibo:
            self.ibo.bind()

        if self.nbo:
            self.nbo.bind()
            GL.glEnableVertexAttribArray(renderer.shader.attribute['vertexNormal'])
            GL.glVertexAttribPointer(renderer.shader.attribute['vertexNormal'], 3, GL.GL_FLOAT, False, 0, self.nbo)

        if self.cbo:
            self.cbo.bind()
            GL.glEnableVertexAttribArray(renderer.shader.attribute['vertexColor'])
            GL.glVertexAttribPointer(renderer.shader.attribute['vertexColor'], 3, GL.GL_FLOAT, False, 0, self.cbo)

        if self.tbo:
            self.tbo.bind()
            GL.glEnableVertexAttribArray(renderer.shader.attribute['vertexTexturePos'])
            GL.glVertexAttribPointer(renderer.shader.attribute['vertexTexturePos'], 2, GL.GL_FLOAT, False, 0, self.tbo)

        if self.cullface == 'front':
            # Draw back faces
            GL.glEnable(GL.GL_CULL_FACE)
            GL.glCullFace(GL.GL_FRONT)
        elif self.cullface == 'back':
            # Draw front faces
            GL.glEnable(GL.GL_CULL_FACE)
            GL.glCullFace(GL.GL_BACK)
        else:
            GL.glDisable(GL.GL_CULL_FACE)

        # Specifiy the depth comparison function
        if self.ontop:
            GL.glDepthFunc(GL.GL_ALWAYS)

        # Bind the texture
        if self.texture:
            self.texture.bind()

        render_geom()

        if self.ibo:
            self.ibo.unbind()

        if self.obo:
            self.obo.unbind()
            GL.glDisableVertexAttribArray(renderer.shader.attribute['vertexOffset'])

        if self.cbo:
            self.cbo.unbind()
            GL.glDisableVertexAttribArray(renderer.shader.attribute['vertexColor'])
        if self.tbo:
            self.tbo.unbind()
            GL.glDisableVertexAttribArray(renderer.shader.attribute['vertexTexturePos'])
        if self.nbo:
            self.nbo.unbind()
            GL.glDisableVertexAttribArray(renderer.shader.attribute['vertexNormal'])
        self.vbo.unbind()
        GL.glDisableVertexAttribArray(renderer.shader.attribute['vertexCoords'])
        if self.offset:
            pf.debug("POLYGON OFFSET RESET", pf.DEBUG.DRAW)
            GL.glPolygonOffset(0.0, 0.0)



    def pick(self, renderer):
        """Pick the geometry of this object"""

        def render_geom():
            if self.ibo:
                GL.glDrawElementsui(self.glmode, self.ibo)
            else:
                GL.glDrawArrays(self.glmode, 0, np.asarray(self.vbo.shape[:-1]).prod())

        renderer.shader.loadUniforms(self)

        self.vbo.bind()
        GL.glEnableVertexAttribArray(renderer.shader.attribute['vertexCoords'])
        GL.glVertexAttribPointer(renderer.shader.attribute['vertexCoords'], 3, GL.GL_FLOAT, False, 0, self.vbo)

        if self.ibo:
            self.ibo.bind()

        if self.cullface == 'front':
            # Draw back faces
            GL.glEnable(GL.GL_CULL_FACE)
            GL.glCullFace(GL.GL_FRONT)
        elif self.cullface == 'back':
            # Draw front faces
            GL.glEnable(GL.GL_CULL_FACE)
            GL.glCullFace(GL.GL_BACK)
        else:
            GL.glDisable(GL.GL_CULL_FACE)

        # Specifiy the depth comparison function
        if self.ontop:
            GL.glDepthFunc(GL.GL_ALWAYS)

        render_geom()

        if self.ibo:
            self.ibo.unbind()
        self.vbo.unbind()
        GL.glDisableVertexAttribArray(renderer.shader.attribute['vertexCoords'])


    def __str__(self):
        keys = sorted(set(self.keys()) - set(('_default_dict_',)))
        print("Keys %s" % keys)
        out = utils.formatDict(utils.selectDict(self,keys))
        print(out)
        return out

########################################################################


class Base(Attributes):
    """Base class for all drawable objects in pyFormex.

    This defines the interface for all drawable objects, but does not
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

    The Base class is just an Attributes dict storing all the rendering
    parameters, and providing defaults from the current canvas drawoptions
    for the essential parameters that are not specified.

    Additional parameters can be set at init time or later using the
    update method. The specified parameters are sanitized before being
    stored.

    Arguments processed by the base class:

    - `marksize`: force to float and also copied as `pointsize`

    """

    def __init__(self,**kargs):
        """Initialize the Base class."""
        #try:
        #    print(pf.canvas.drawoptions)
        #except:
        #    pass
        Attributes.__init__(self, pf.canvas.drawoptions if pf.canvas else {})
        if kargs:
            self.update(**kargs)
            self.setLineWidth(self.linewidth)
            self.setLineStipple(self.linestipple)
            self.setColor(self.color,self.colormap)
            self.setTexture(self.texture)

    def setLineWidth(self, linewidth):
        """Set the linewidth of the Drawable."""
        self.linewidth = saneFloat(linewidth)

    def setLineStipple(self, linestipple):
        """Set the linewidth of the Drawable."""
        self.linestipple = saneLineStipple(linestipple)

    def setColor(self,color=None,colormap=None,ncolors=1):
        """Set the color of the Drawable."""
        self.color, self.colormap = saneColorSet(color, colormap, shape=(ncolors,))

    def setTexture(self, texture):
        """Set the texture data of the Drawable."""
        if texture is not None:
            if not isinstance(texture, Texture):
                try:
                    texture = Texture(texture)
                except:
                    texture = None
        self.texture = texture


########################################################################

class Actor(Base):
    """Proposal for drawn objects

    __init__:  store all static values: attributes, geometry, vbo's
    prepare: creates sanitized and derived attributes/data
    render: push values to shader and render the object

    __init__ is only dependent on input attributes and geometry

    prepare may depend on current canvas settings:
      mode, transparent, avgnormals

    render depends on canvas and renderer

    If the actor does not have a name, it will be given a
    default one.

    The actor has the following attributes, initialized or computed on demand

    """

    # default names for the actors
    defaultname = utils.NameSequence('object_0')


    def __init__(self,obj,**kargs):

        Base.__init__(self)

        # Check it is something we can draw
        if not isinstance(obj, Mesh) and not isinstance(obj, Formex):
            raise ValueError("Object is of type %s.\nCan only render Mesh, Formex and objects that can be converted to Formex" % type(obj))
        self.object = obj

        if isinstance(obj, Mesh): # should we store coords, elems and eltype?
            coords = obj.coords.astype(float32)
            elems = obj.elems.astype(int32)
            eltype = obj.elName()

        elif isinstance(obj, Formex):
            coords = obj.coords.astype(float32)
            elems = None
            eltype = obj.eltype
            #
            # We always want an eltype for drawing
            #
            if eltype is None:
                if obj.nplex() <= 4:
                    # Set default eltype
                    eltype = _default_eltype[obj.nplex()]

                else:
                    raise ValueError("Drawing of Formex with undefined element type and plexitude > 4 is not supported yet")

        self.eltype = elementType(eltype)

        self.drawable = []
        self.children = []

        # By default, Actors are pickable
        self.pickable = True

        # Acknowledge all object attributes and passed parameters
        self.update(obj.attrib)
        self.update(kargs)
        # Implement the default color='prop' if no color is set and
        # the object has props
        if self.color is None and hasattr(obj,'prop'):
            self.color = 'prop'
        if self.rendertype is None:
            self.rendertype = 0

        # copy marksize as pointsize for gl2 shader
        if 'marksize' in self:
            self['pointsize'] = self['marksize']

        if self.name is None:
            self.name = Actor.defaultname.next()

        # Store minimal data
        coords = coords.astype(float32)
        if elems is None:
            self._fcoords = coords
        else:
            self._coords = coords.reshape(-1, 3)
            self._elems = elems.astype(int32)

        # Currently do everything in Formex model
        # And we always need this one
        self.vbo = VBO(self.fcoords)
        #print("GEOM SHAPE %s" % str(self.fcoords.shape))
        


    def getType(self):
        return self.object.__class__


    def _fcoords_fuse(self):
        self._coords, self._elems = self._fcoords.fuse()
        if self._elems.ndim != 2:
            self._elems = self._elems[:, np.newaxis]


    @property
    def coords(self):
        """Return the fused coordinates of the object"""
        if self._coords is None:
            if self._fcoords is None:
                raise ValueError("Object has neither _coords nor _fcoords")
            self._fcoords_fuse()
        return self._coords

#
#    def points(self):
#        """Return the coords of the geometry as a 2D array"""
#        return self.object.points()


    def bbox(self):
        try:
            return self.object.bbox()
        except:
            print("No bbox because no _coords for object of type %s" % type(self.object))
            return np.zeros(6).reshape(2, 3)


    @property
    def elems(self):
        """Return the original elems of the object"""
        if self._elems is None:
            if self._fcoords is None:
                raise ValueError("Object has neither _coords nor _fcoords")
            self._fcoords_fuse()
        return self._elems


    @property
    def fcoords(self):
        """Return the full coordinate set of the object"""
        if self._fcoords is None:
            if self._coords is None or self._elems is None:
                raise ValueError("Object has neither _coords nor _fcoords")
            self._fcoords = self._coords[self._elems]
        return self._fcoords


    @property
    def faces(self):
        """Return the elems of the object as they will be drawn

        This returns a 2D index in a single element. All elements
        should have compatible node numberings.
        """
        if self._faces is None:
            if self.eltype is not None:
                self._faces = self.eltype.getDrawFaces()[0]
            else:
                if self.object.nplex() > 3:
                    # It is a polygon. We should create polygon elementtype!!
                    self._faces = polygonFaceIndex(self.object.nplex())
        return self._faces


    @property
    def edges(self):
        """Return the edges of the object as they will be drawn

        This returns a 2D index in a single element. All elements
        should have compatible node numberings.
        """
        if self._edges is None:
            if self.eltype is not None:
                self._edges = self.eltype.getDrawEdges()[0]
            else:
                if self.object.nplex() > 3:
                    # It is a polygon. We should create polygon elementtype!!
                    self._edges = polygonEdgeIndex(self.object.nplex())
        return self._edges


    @property
    def b_normals(self):
        """Return individual normals at all vertices of all elements"""
        if self._normals is None:
            self._normals = gt.polygonNormals(self.fcoords.astype(float32))
            #print("COMPUTED NORMALS: %s" % str(self._normals.shape))
            #print(self._normals)
        return self._normals


    @property
    def b_avgnormals(self):
        """Return averaged normals at the vertices"""
        if self._avgnormals is None:
            tol = pf.cfg['render/avgnormaltreshold']
            self._avgnormals = gt.averageNormals(self.coords, self.elems, False, tol).astype(float32)
            #print("COMPUTE AVGNORMALS: %s" % str(self._avgnormals.shape))
            #print(self._avgnormals)
        return self._avgnormals


    def prepare(self, canvas):
        """Prepare the attributes for the renderer.

        This sanitizes and completes the attributes for the renderer.
        Since the attributes may be dependent on the rendering mode,
        this method is called on each mode change.
        """
        self.color = self.okColor(self.color, self.colormap)
        self.bkcolor = self.okColor(self.bkcolor, self.bkcolormap)
        if self.color is not None:
            if self.color.ndim == 1:
                self.useObjectColor = 1
                self.objectColor = self.color
                self.color = None
                if self.bkcolor is not None and self.bkcolor.ndim == 1:
                    self.useObjectColor = 2
                    self.objectBkColor = self.bkcolor
                    self.bkcolor = None

        self.setAlpha(self.alpha, self.bkalpha)
        self.setTexture(self.texture,self.texcoords,self.texmode)
        self.setLineWidth(self.linewidth)
        self.setLineStipple(self.linestipple)

        #### CHILDREN ####
        for child in self.children:
            child.prepare(canvas)


    def changeMode(self, canvas):
        """Modify the actor according to the specified mode"""
        pf.debug("GEOMACTOR.changeMode", pf.DEBUG.DRAW)
        self.drawable = []
        self._prepareNormals(canvas)
        # ndim >= 2
        if (self.eltype is not None and self.eltype.ndim >= 2) or (self.eltype is None and self.object.nplex() >= 3):
            if self.mode:
                rendermode = self.mode
            else:
                rendermode = canvas.rendermode
            #print("RENDERMODE",rendermode)
            if rendermode == 'wireframe':
                # Draw the colored edges
                self._addEdges()
            else:
                # Draw the colored faces
                self._addFaces()
                # Overlay the black edges (or not)
                if rendermode.endswith('wire'):
                    self._addWires()
        # ndim < 2
        else:
            # Draw the colored faces
            self._addFaces()

        #### CHILDREN ####
        for child in self.children:
            child.changeMode(canvas)

        pf.debug("GEOMACTOR.changeMode create %s drawables" % len(self.drawable), pf.DEBUG.DRAW)


    def _prepareNormals(self, canvas):
        """Prepare the normals buffer object for the actor.

        The normals buffer object depends on the renderer settings:
        lighting, avgnormals
        """
        #if renderer.canvas.settings.lighting:
        if True:
            if canvas.settings.avgnormals:
                normals = self.b_avgnormals
            else:
                normals = self.b_normals
            # Normals are always full fcoords size
            #print("SIZE OF NORMALS: %s; COORDS: %s" % (normals.size,self.fcoords.size))
            self.nbo = VBO(normals)



    def fullElems(self):
        """Return an elems index for the full coords set"""
        nelems, nplex = self.fcoords.shape[:2]
        return np.arange(nelems*nplex).reshape(nelems, nplex)


    def subElems(self,nsel=None,esel=None):
        """Create an index for the drawable subelems

        This index always refers to the full coords (fcoords).

        The esel selects the elements to be used (default all).

        The nsel selects (possibly multiple) parts from each element.
        The selector is 2D (nsubelems, nsubplex). It is applied on all
        selected elements

        If both esel and esel are None, returns None
        """
        if (nsel is None or nsel.size==0) and (esel is None or esel.size==0):
            return None
        else:
            # The elems index defining the original elements
            # based on the full fcoords
            elems = self.fullElems()
            if esel is not None:
                elems = elems[esel]
            if nsel is not None:
                elems = elems[:, nsel].reshape(-1, nsel.shape[-1])
            return elems


    def _addFaces(self):
        """Draw the elems"""
        elems = self.subElems(nsel=self.faces)

        if (self.eltype is not None and self.eltype.ndim >= 2) or (self.eltype is None and self.object.nplex() >= 3):
            # Drawing triangles

            # TODO: what is the intention of this?
#            if self.drawface is None:
#                drawface = 0
#            else:
#                drawface = self.drawface
                
            name = self.name

            if self.rendertype > 1 or self.drawface == 0:

                # Draw front and back at once, without culling
                # Beware: this does not work with different front/back color
                # as our Drawable currently has only one color
                D = Drawable(self,subelems=elems,name=name,cullface='',drawface=0)
                self.drawable.append(D)

            else:

                # Draw both back and front sides, with culling
                # First the back sides (they are more remote from eye)

                D = Drawable(self,subelems=elems,name=self.name+"_back",cullface='front',drawface=-1)
                self.drawable.append(D)

                # Then the front sides, using same ibo
                D = Drawable(self,subelems=elems,name=self.name+"_front",cullface='back',drawface=1,ibo=D.ibo)
                self.drawable.append(D)

        else:
            # Drawing lines and points
            D = Drawable(self, subelems=elems, name=self.name+"_faces", lighting=False)
            self.drawable.append(D)


    def _addEdges(self):
        """Draw the edges"""
        if self.edges is not None:
            elems = self.subElems(nsel=self.edges)
            self.drawable.append(Drawable(self, subelems=elems, name=self.name+"_edges", lighting=False))


    def _addWires(self):
        """Add or remove the edges depending on rendering mode"""
        #print("ADDWIRES")
        wiremode = pf.canvas.settings.wiremode
        elems = None
        if wiremode > 0 and self.edges is not None:
            if wiremode == 1:
                # all edges:
                #print("ADDWIRES %s" % self.edges)
                elems = self.subElems(nsel=self.edges)
            elif wiremode == 2:
                # border edges
                #print("SELF.ELEMS",self.elems)
                inv = at.inverseIndex(self.elems.reshape(-1, 1))[:, -1]
                #print("INVERSE",inv)
                M = Mesh(self.coords, self.elems)
                elems = M.getFreeEntities(level=1)
                elems = inv[elems]
                #print("ELEMS",elems)
            elif wiremode == 3:
                # feature edges
                print("FEATURE EDGES NOT YET IMPLEMENTED")


        if elems is not None and elems.size > 0:
            #print("ADDWIRES SIZE %s" % (elems.shape,))
            wires = Drawable(self, subelems=elems, lighting=False, color=np.array(colors.black), opak=True, name=self.name+"_wires")
            # Put at the front to make visible
            # ontop will not help, because we only sort actors
            self.drawable.insert(0, wires)


    def removeHighlight(self):
        """Remove the highlight for the current actor.

        Remove the highlight (whether full or partial) from the actor.
        """
        self.highlight = 0 # Full highlight
        if self._highlight:   # Partial highlight
            if self._highlight in self.drawable:
                self.drawable.remove(self._highlight)
            self._highlight = None


    def addHighlight(self):
        """Add full highlighting of the actor.

        This makes the whole actor being drawn in the highlight color.
        """
        self.highlight = 1


    def addHighlightElements(self,sel=None):
        """Add a highlight for the selected elements. Default is all."""
        self.removeHighlight()
        #print("ESEL",sel)
        elems = self.subElems(nsel=self.faces,esel=sel)
        #print("ELEMS",elems)
        self._highlight = Drawable(self, 
                                   subelems=elems, 
                                   name=self.name+"_highlight", 
                                   linewidth=10, 
                                   lighting=False, 
                                   color=np.array(colors.yellow), 
opak=True)
        # Put at the front to make visible
        self.drawable.insert(0, self._highlight)


    def addHighlightPoints(self,sel=None):
        """Add a highlight for the selected points. Default is all."""
        self.removeHighlight()
        vbo = VBO(self.object.points())
        self._highlight = Drawable(self, vbo=vbo, subelems=sel.reshape(-1, 1), name=self.name+"_highlight", linewidth=10, lighting=False, color=np.array(colors.yellow), opak=True, pointsize=10, offset=1.0)
        # Put at the front to make visible
        self.drawable.insert(0, self._highlight)


    def okColor(self,color,colormap=None):
        """Compute a color usable by the shader.

        The shader (currently) only supports 3*float type of colors:

        - None
        - single color (separate for front and back faces)
        - vertex colors
        """
        if isinstance(color, str):
            if color == 'prop' and hasattr(self.object, 'prop'):
                color = self.object.prop
            elif color == 'random':
                # create random colors
                color = np.random.rand(self.object.nelems(), 3)
            elif color.startswith('fld:'):
                # get colors from a named field
                fld = self.object.getField(color[4:])
                if fld and fld.fldtype == 'node':
                    color = fld.data
                    colormap = None
                else:
                    pf.warning("Could not set color from field %s" % color)

        color, colormap = saneColorSet(color, colormap, self.fcoords.shape)

        if color is not None:
            if color.dtype.kind == 'i':
                # We have a color index
                if colormap is None:
                    colormap = np.array(colors.palette)
                color = colormap[color]

        return color


    def setAlpha(self,alpha,bkalpha=None):
        """Set the Actors alpha value."""
        try:
            self.alpha = self.bkalpha = float(alpha)
        except:
            del self.alpha
            del self.bkalpha
        try:
            self.bkalpha = float(bkalpha)
        except:
            pass
        if self.opak is None:
            self.opak = (self.alpha == 1.0) and (self.bkalpha == 1.0 )


    def setTexture(self,texture,texcoords=None,texmode=None):
        """Set the texture data of the Drawable."""
        self.useTexture = 0
        if texture is not None:
            if not isinstance(texture, Texture):
                try:
                    texture = Texture(texture)
                except:
                    print("Error while creating Texture from %s" % type(texture))
                    raise
                    texture = None
            if texture is not None:
                if texcoords is None:
                    if (self.eltype is not None and self.eltype.ndim == 2):
                        texcoords = np.array(self.eltype.vertices[...,:2])
                    else:
                        print("Texture not allowed for eltype %s" % self.eltype)
                        self.texture = self.texcoords = None
                        return
                if texcoords.shape[-2:] != (self.eltype.nplex(),2):
                    print(self.eltype.nplex())
                    print("Shape of texcoords does not match: %s" % str(texcoords.shape))
                    texcoords = texture = None
            if texmode is None:
                texmode = 1

        if texture is not None:
            # everything ok, store the texture params
            self.useTexture = 1
            self.texture = texture
            self.texcoords = texcoords
            self.texmode = texmode


    ## def setLineWidth(self, linewidth):
    ##     """Set the linewidth of the Drawable."""
    ##     self.linewidth = saneLineWidth(linewidth)


    ## def setLineStipple(self, linestipple):
    ##     """Set the linewidth of the Drawable."""
    ##     self.linestipple = saneLineStipple(linestipple)


    def render(self, renderer):
        """Render the geometry of this object"""

        ## if self.modified:
        ##     print("LOAD GEOMACTOR uniforms")
        ##     renderer.shader.loadUniforms(self)
        ##     self.modified = False

        if not self.invisible:
            pf.debug("Render %s drawables for %s" % (len(self.drawable), self.name), pf.DEBUG.DRAW)
            for obj in self.drawable:
                pf.debug("Render %s" % obj.name, pf.DEBUG.DRAW)
                renderer.setDefaults()
                renderer.shader.loadUniforms(self)
                obj.render(renderer)

        for obj in self.children:
            renderer.setDefaults()
            obj.render(renderer)


    def inside(self,camera,rect=None,mode='actor',sel='any',return_depth=False):
        """Test whether the actor is rendered inside rect of camera.

        Parameters:

        - `camera`: a Camera that has been set up properly. Usually it
          will be the current canvas camera, pf.canvas.camera.
        - `rect`: a tuple of 4 values (x,y,w,h) specifying
          a rectangular subregion of the camera's viewport. The default
          is the full camera viewport.
        - `mode`: the testing mode. Currently defined modes:

          - 'actor' (default): test if the actor is (partly) inside
          - 'element': test which elements of the actor are inside
          - 'point': test which vertices of the actor are inside

        - `sel`: either 'all' or 'any'. This is not used with 'point' mode.
          It specifies whether all or any of the points of the actor,
          element, ... should be inside the rectangle in order to be flagged
          as a positive.

        The return value depends on the mode:

        - 'actor': True or False
        - 'element': the indices of the elements inside
        - 'point': the indices of the vertices inside

        If `return_depth` is True, a second value is returned, with the z-depth
        value of all the objects inside.

        """
        ins = camera.inside(self.object.points(), rect, return_depth)
        if return_depth:
            ins,depth = ins
            #print("INS,DEPTHS",ins,depth)

        if mode == 'point':
            ok = np.where(ins)[0]
            if return_depth:
                depth = depth[ok]

        else:
            if mode in ['element','actor']:
                if isinstance(self.object,Mesh):
                    elems = self.elems
                elif isinstance(self.object,Formex):
                    elems = self.fullElems()
                else:
                    raise ValueError("Element picking on objects of type %s is not implemented" % type(self.object))

                #print("PICK: elems\n",elems)
            elif mode == 'edge':
                # TODO: add edges selector
                #elems =
                raise ValueError("Edge picking is not implemented yet")

            ins = ins[elems]
            if sel == 'all':
                ok = ins.all(axis=-1)
            elif sel == 'any':
                ok = ins.any(axis=-1)
            else:
                # Useful?
                ok = ins[:, sel].all(axis=-1)

            if mode == 'actor':
                ok = ok.any()
                if return_depth:
                    depth =  depth[np.unique(elems)].min()

            else:
                ok = np.where(ok)[0]
                elems = elems[ok]
                if return_depth:
                    depth = depth[elems].min(axis=-1)

        if return_depth:
            return ok, depth
        else:
            return ok


    def __str__(self):
        keys = sorted(set(self.keys()) - set(('drawable',)))
        s = utils.formatDict(utils.selectDict(self,keys))
        for i,d in enumerate(self.drawable):
            s += "** Drawable %s **\n" % i
            s += d.__str__()
        return s




# for compatibility
GeomActor = Actor

########################################################################


def polygonFaceIndex(n):
    i0 = (n-1) * np.ones(n-2, dtype=int)
    i1 = np.arange(n-2)
    i2 = i1+1
    return np.column_stack([i0, i1, i2])


def polygonEdgeIndex(n):
    i0 = np.arange(n)
    i1 = np.roll(i0, -1)
    return np.column_stack([i0, i1])


########################################################################

## from pyformex.legacy.actors import Actor as OldActor
## from pyformex import arraytools as at

## class Text3DActor(OldActor):
##     """A text as a 3D object.

##     This class provides an Actor representing a text as an object
##     in 3D space.
##     """
##     def __init__(self, text, font, facesize, color, trl):
##         OldActor.__init__(self)
##         self.text = text
##         self.font = font
##         self.setFaceSize(*facesize)
##         self.setColor(color)
##         self.trl = at.checkArray(trl, (3,), 'f')

##     def setFaceSize(self, a, b):
##         self.font.FaceSize(a, b)

##     def setColor(self, color):
##         from pyformex.opengl.sanitize import saneColor
##         self.color = saneColor(color)

##     def bbox(self):
##         bb = self.font.BBox(self.text)
##         return [bb[:3], bb[3:]]

##     def render(self, renderer):
##         """Render the geometry of this object"""
##         GL.glMatrixMode(GL.GL_MODELVIEW)
##         GL.glPushMatrix()
##         GL.glTranslate(*self.trl)
##         GL.glColor3fv(self.color)
##         self.font.Render(self.text)
##         GL.glMatrixMode(GL.GL_MODELVIEW)
##         GL.glPopMatrix()
##         # Because of the way font.Render works, we need an update here
##         #pf.canvas.update()


##     def draw(self,canvas):
##         self.render(None)

### End
