## $Id$
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
"""Create 3D graphical representations.

The draw module provides the basic user interface to the OpenGL
rendering capabilities of pyFormex. The full contents of this module
is available to scripts running in the pyFormex GUI without the need
to import it.
"""
from __future__ import print_function


import pyformex as pf
from pyformex import utils
from pyformex import coords
from pyformex.attributes import Attributes
from pyformex.formex import Formex

from pyformex.gui import toolbar
from pyformex.gui import image
from pyformex.gui import colors

from pyformex.opengl import drawable
from pyformex.opengl import decors
from pyformex.opengl import textext

from pyformex.script import getcfg, named

import numpy

############################## drawing functions ########################

def flatten(objects,recurse=True):
    """Flatten a list of geometric objects.

    Each item in the list should be either:

    - a drawable object,
    - a string with the name of such an object,
    - a list of any of these three.

    This function will flatten the lists and replace the string items with
    the object they point to. The result is a single list of drawable
    objects. This function does not enforce the objects to be drawable.
    That should be done by the caller.
    """
    r = []
    for i in objects:
        if isinstance(i, str):
            i = named(i)
        if isinstance(i, list):
            if recurse:
                r.extend(flatten(i, True))
            else:
                r.extend(i)
        else:
            r.append(i)
    return r


def drawable(objects):
    """Filters the drawable objects from a list.

    The input is a list, usually of drawable objects. For each item in the
    list, the following is done:

    - if the item is drawable, it is kept as is,
    - if the item is not drawable but can be converted to a Formex, it is
      converted,
    - if it is neither drawable nor convertible to Formex, it is removed.

    The result is a list of drawable objects (since a Formex is drawable).
    """
    def fltr(i):
        if hasattr(i, 'actor'):
            return i
        elif hasattr(i, 'toFormex'):
            return i.toFormex()
        elif hasattr(i, 'toMesh'):
            return i.toMesh()
        else:
            return None
    r = [ fltr(i) for i in objects ]
    return [ i for i in r if i is not None ]


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
    FL = flatten(FL)
    ntot = len(FL)

    # Transform to list of drawable objects
    FL = drawable(FL)
    nres = len(FL)

    # Get default drawing options and overwrite with specified values
    opts = Attributes(pf.canvas.drawoptions)
    opts.update(utils.selectDict(kargs,draw_options,remove=True))

    if nres < ntot and not opts.silent:
        raise ValueError("Data contains undrawable objects (%s/%s)" % (ntot-nres, ntot))

    # Shrink the objects if requested
    if opts.shrink:
        FL = [ _shrink(F, opts.shrink_factor) for F in FL ]

    ## # Execute the drawlock wait before doing first canvas change
    pf.GUI.drawlock.wait()

    if opts.clear_:
        clear_canvas()

    if opts.view is not None and opts.view != 'last':
        pf.debug("SETTING VIEW to %s" % opts.view, pf.DEBUG.DRAW)
        setView(opts.view)

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
                bbox = pf.canvas.scene.bbox
            if bbox == 'last':
                bbox = None

            pf.canvas.setCamera(bbox, view)

        # Update the rendering
        pf.canvas.update()
        pf.app.processEvents()

        # Save the rendering if autosave on
        pf.debug("AUTOSAVE %s" % image.autoSaveOn())
        if image.autoSaveOn():
            image.saveNext()

        # Make sure next drawing operation is retarded
        if opts.wait:
            pf.GUI.drawlock.lock()

    finally:
        pf.GUI.setBusy(False)

    if isinstance(F, list) or len(actors) != 1:
        return actors
    else:
        return actors[0]


def _setFocus(object, bbox, view):
    """Set focus after a draw operation"""
    if view is not None or bbox not in [None, 'last']:
        if view == 'last':
            view = pf.canvas.drawoptions['view']
        if bbox == 'auto':
            bbox = coords.bbox(object)
        pf.canvas.setCamera(bbox, view)
    pf.canvas.update()


def focus(object):
    """Move the camera thus that object comes fully into view.

    object can be anything having a bbox() method or a list thereof.
    if no view is given, the default is used.

    The camera is moved with fixed axis directions to a place
    where the whole object can be viewed using a 45. degrees lens opening.
    This technique may change in future!
    """
    pf.canvas.setCamera(bbox=coords.bbox(object))
    pf.canvas.update()


def setDrawOptions(kargs0={},**kargs):
    """Set default values for the draw options.

    Draw options are a set of options that hold default values for the
    draw() function arguments and for some canvas settings.
    The draw options can be specified either as a dictionary, or as
    keyword arguments.
    """
    d = {}
    d.update(kargs0)
    d.update(kargs)
    pf.canvas.setOptions(d)


def showDrawOptions():
    print("Current Drawing Options: %s" % pf.canvas.drawoptions)
    print("Current Viewport Settings: %s" % pf.canvas.settings)


def reset():
    """reset the canvas"""
    pf.canvas.resetDefaults()
    pf.canvas.resetOptions()
    pf.GUI.drawwait = pf.cfg['draw/wait']
    try:
        if len(pf.GUI.viewports.all) == 1:
            size = (-1, -1)
            canvasSize(*size)
    except:
        print("Warning: Resetting canvas before initialization?")
    clear()
    view('front')


def resetAll():
    reset()
    wireframe()


def shrink(onoff,factor=None):
    """Set shrinking on or off, and optionally set shrink factor"""
    data = {'shrink':bool(onoff)}
    try:
        data['shrink_factor'] = float(factor)
    except:
        pass
    setDrawOptions(data)


def _shrink(F, factor):
    """Return a shrinked object.

    A shrinked object is one where each element is shrinked with a factor
    around its own center.
    """
    if not isinstance(F, Formex):
        F = F.toFormex()
    return F.shrink(factor)


def drawVectors(P,v,size=None,nolight=True,**drawOptions):
    """Draw a set of vectors.

    If size==None, draws the vectors v at the points P.
    If size is specified, draws the vectors size*normalize(v)
    P, v and size are single points
    or sets of points. If sets, they should be of the same size.

    Other drawoptions can be specified and will be passed to the draw function.
    """
    if size is None:
        Q = P + v
    else:
        Q = P + size*normalize(v)
    return draw(connect([P, Q]),nolight=nolight,**drawOptions)


def drawPlane(P,N,size,**drawOptions):
    from pyformex.plugins.tools import Plane
    p = Plane(P, N, size)
    return draw(p,bbox='last',**drawOptions)


def drawMarks(X,M,color='black',leader='',ontop=True):
    """Draw a list of marks at points X.

    X is a Coords array.
    M is a list with the same length as X.
    The string representation of the marks are drawn at the corresponding
    3D coordinate.
    """
    _large_ = 20000
    if len(M) > _large_:
        if not ack("You are trying to draw marks at %s points. This may take a long time, and the results will most likely not be readible anyway. If you insist on drawing these marks, anwer YES." % len(M)):
            return None
    from pyformex.opengl.textext import MarkList
    A = textext.MarkList(X, M, color=color, leader=leader)
    drawActor(A)
    return A


def drawFreeEdges(M,color='black'):
    """Draw the feature edges of a Mesh"""
    B = M.getFreeEdgesMesh()
    return draw(B, color=color, nolight=True)


def drawNumbers(F,numbers=None,color='black',trl=None,offset=0,leader='',ontop=None):
    """Draw numbers on all elements of F.

    numbers is an array with F.nelems() integer numbers.
    If no numbers are given, the range from 0 to nelems()-1 is used.
    Normally, the numbers are drawn at the centroids of the elements.
    A translation may be given to put the numbers out of the centroids,
    e.g. to put them in front of the objects to make them visible,
    or to allow to view a mark at the centroids.
    If an offset is specified, it is added to the shown numbers.
    """
    if ontop is None:
        ontop = getcfg('draw/numbersontop')
    try:
        X = F.centroids()
    except:
        return None
    if trl is not None:
        X = X.trl(trl)
    X = X.reshape(-1, 3)
    if numbers is None:
        numbers = numpy.arange(X.shape[0])
    return drawMarks(X, numbers+offset, color=color, leader=leader, ontop=ontop)


def drawPropNumbers(F,**kargs):
    """Draw property numbers on all elements of F.

    This calls drawNumbers to draw the property numbers on the elements.
    All arguments of drawNumbers except `numbers` may be passed.
    If the object F thus not have property numbers, -1 values are drawn.
    """
    if F.prop is None:
        nrs = -ones(F.nelems(), dtype=Int)
    else:
        nrs = F.prop
    drawNumbers(F,nrs,**kargs)


def drawVertexNumbers(F,color='black',trl=None,ontop=False):
    """Draw (local) numbers on all vertices of F.

    Normally, the numbers are drawn at the location of the vertices.
    A translation may be given to put the numbers out of the location,
    e.g. to put them in front of the objects to make them visible,
    or to allow to view a mark at the vertices.
    """
    FC = F.coords.reshape((-1, 3))
    if trl is not None:
        FC = FC.trl(trl)
    return drawMarks(FC, numpy.resize(numpy.arange(F.coords.shape[-2]), (FC.shape[0])), color=color, ontop=ontop)


def drawBbox(F,color='black',linewidth=None):
    """Draw the bounding box of the geometric object F.

    F is any object that has a `bbox` method.
    Returns the drawn Annotation.
    """
    A = decors.BboxActor(F.bbox(), color=color, linewidth=linewidth)
    drawActor(A)
    return A


def drawPrincipal(F,weight=None):
    """Draw the principal axes of the geometric object F.

    F is any object that has a `coords` attribute.
    If specified, weight is an array of weights attributed to the points
    of F. It should have the same length as `F.coords`.
    """
    A = actors.PrincipalActor(F, weight)
    drawActor(A)
    return A


def drawText3D(P,text,color=None,size=18,font=None,ontop=True):
    """Draw a text at a 3D point P."""
    A = textext.Text(text,P, color=color, size=size, font=font, ontop=ontop)
    drawActor(A)
    return A


def drawText(text,x,y,gravity='E',font=None,size=14,color=None):
    """Show a text at position x,y using font."""
    A = textext.Text(text, (x,y), gravity=gravity, fonttex=font, size=size, color=color)
    drawActor(A)
    return A


def drawViewportAxes3D(pos,color=None):
    """Draw two viewport axes at a 3D position."""
    A = texText.Mark((0,200,0),image,size=40,color=red)
    drawActor(A)
    return A


def drawAxes(CS=None,*args,**kargs):
    """Draw the axes of a CoordinateSystem.

    CS is a CoordinateSystem. If not specified, the global coordinate system
    is used. Other arguments can be added just like in the
    :class:`AxesActor` class.

    While you can draw a CoordinateSystem using the :func:`draw` function,
    this function gives a better result because it has specialized color
    and annotation settings and provides reasonable deafults.
    """
    if CS is None:
        from pyformex.coordsys import CoordinateSystem
        CS = CoordinateSystem()
    A = actors.AxesActor(CS,*args,**kargs)
    drawActor(A)
    return A


def drawImage3D(image,nx=0,ny=0,pixel='dot'):
    """Draw an image as a colored Formex

    Draws a raster image as a colored Formex. While there are other and
    better ways to display an image in pyFormex (such as using the imageView
    widget), this function allows for interactive handling the image using
    the OpenGL infrastructure.

    Parameters:

    - `image`: a QImage or any data that can be converted to a QImage,
      e.g. the name of a raster image file.
    - `nx`,`ny`: width and height (in cells) of the Formex grid.
      If the supplied image has a different size, it will be rescaled.
      Values <= 0 will be replaced with the corresponding actual size of
      the image.
    - `pixel`: the Formex representing a single pixel. It should be either
      a single element Formex, or one of the strings 'dot' or 'quad'. If 'dot'
      a single point will be used, if 'quad' a unit square. The difference
      will be important when zooming in. The default is 'dot'.

    Returns the drawn Actor.

    See also :func:`drawImage`.
    """
    pf.GUI.setBusy()
    from pyformex.plugins.imagearray import image2glcolor, resizeImage

    # Create the colors
    image = resizeImage(image, nx, ny)
    nx, ny = image.width(), image.height()
    color, colortable = image2glcolor(image)

    # Create a 2D grid of nx*ny elements
    # !! THIS CAN PROBABLY BE DONE FASTER
    if isinstance(pixel, Formex) and pixel.nelems()==1:
        F = pixel
    elif pixel == 'quad':
        F = Formex('4:0123')
    else:
        F = Formex('1:0')
    F = F.replic2(nx, ny).centered()

    # Draw the grid using the image colors
    FA = draw(F, color=color, colormap=colortable, nolight=True)
    pf.GUI.setBusy(False)
    return FA


def drawImage(image,w=0,h=0,x=-1,y=-1,color=colors.white,ontop=False):
    """Draws an image as a viewport decoration.

    Parameters:

    - `image`: a QImage or any data that can be converted to a QImage,
      e.g. the name of a raster image file. See also the :func:`loadImage`
      function.
    - `w`,`h`: width and height (in pixels) of the displayed image.
      If the supplied image has a different size, it will be rescaled.
      A value <= 0 will be replaced with the corresponding actual size of
      the image.
    - `x`,`y`: position of the lower left corner of the image. If negative,
      the image will be centered on the current viewport.
    - `color`: the color to mix in (AND) with the image. The default (white)
      will make all pixels appear as in the image.
    - `ontop`: determines whether the image will appear as a background
      (default) or at the front of the 3D scene (as on the camera glass).

    Returns the Decoration drawn.

    Note that the Decoration has a fixed size (and position) on the canvas
    and will not scale when the viewport size is changed.
    The :func:`bgcolor` function can be used to draw an image that completely
    fills the background.
    """
    utils.warn("warn_drawImage_changed")
    from pyformex.plugins.imagearray import image2numpy
    from pyformex.opengl.decors import Rectangle

    image = image2numpy(image, resize=(w, h), indexed=False)
    w, h = image.shape[:2]
    if x < 0:
        x = (pf.canvas.width() - w) // 2
    if y < 0:
        y = (pf.canvas.height() - h) // 2
    R = Rectangle(x, y, x+w, y+h, color=color, texture=image, ontop=ontop)
    decorate(R)
    return R


def drawActor(A):
    """Draw an actor and update the screen."""
    pf.canvas.addActor(A)
    pf.canvas.update()

def drawAny(A):
    """Draw an Actor/Annotation/Decoration and update the screen."""
    pf.canvas.addAny(A)
    pf.canvas.update()

def undraw(itemlist):
    """Remove an item or a number of items from the canvas.

    Use the return value from one of the draw... functions to remove
    the item that was drawn from the canvas.
    A single item or a list of items may be specified.
    """
    if itemlist:
        pf.canvas.removeAny(itemlist)
    pf.canvas.update()
    pf.app.processEvents()


def view(v,wait=True):
    """Show a named view, either a builtin or a user defined.

    This shows the current scene from another viewing angle.
    Switching views of a scene is much faster than redrawing a scene.
    Therefore this function is prefered over :func:`draw` when the actors
    in the scene remain unchanged and only the camera viewpoint changes.

    Just like :func:`draw`, this function obeys the drawing lock mechanism,
    and by default it will restart the lock to retard the next draing operation.
    """
    pf.GUI.drawlock.wait()
    if v != 'last':
        angles = pf.canvas.view_angles.get(v)
        if not angles:
            warning("A view named '%s' has not been created yet" % v)
            return
        pf.canvas.setCamera(None, angles)
    setView(v)
    pf.canvas.update()
    if wait:
        pf.GUI.drawlock.lock()


def setTriade(on=None,pos='lb',siz=100):
    """Toggle the display of the global axes on or off.

    If on is True, the axes triade is displayed, if False it is
    removed. The default (None) toggles between on and off.
    """
    pf.canvas.setTriade(on, pos, siz)
    pf.canvas.update()
    pf.app.processEvents()


def annotate(annot):
    """Draw an annotation."""
    pf.canvas.addAnnotation(annot)
    pf.canvas.update()

def unannotate(annot):
    pf.canvas.removeAnnotation(annot)
    pf.canvas.update()

def decorate(decor):
    """Draw a decoration."""
    pf.canvas.addDecoration(decor)
    pf.canvas.update()

def undecorate(decor):
    pf.canvas.removeDecoration(decor)
    pf.canvas.update()


def createView(name,angles,addtogui=False):
    """Create a new named view (or redefine an old).

    The angles are (longitude, latitude, twist).
    By default, the view is local to the script's viewport.
    If addtogui is True, a view button to set this view is added to the GUI.
    """
    pf.canvas.view_angles[name] = angles
    if addtogui:
        pf.GUI.createView(name, angles)


def setView(name,angles=None):
    """Set the default view for future drawing operations.

    If no angles are specified, the name should be an existing view, or
    the predefined value 'last'.
    If angles are specified, this is equivalent to createView(name,angles)
    followed by setView(name).
    """
    if name != 'last' and angles:
        createView(name, angles)
    setDrawOptions({'view':name})


def saveView(name,addtogui=False):
    pf.GUI.saveView(name)


def frontView():
    view("front")
def backView():
    view("back")
def leftView():
    view("left")
def rightView():
    view("right")
def topView():
    view("top");
def bottomView():
    view("bottom")
def isoView():
    view("iso")


def bgcolor(color=None,image=None):
    """Change the background color and image.

    Parameters:

    - `color`: a single color or a list of 4 colors. A single color sets a
      solid background color. A list of four colors specifies a gradient.
      These 4 colors are those of the Bottom Left, Bottom Right, Top Right
      and Top Left corners respectively.
    - `image`: the name of an image file. If specified, the image will be
      overlayed on the background colors. Specify a solid white background
      color to sea the image unaltered.
    """
    pf.canvas.setBackground(color=color, image=image)
    pf.canvas.display()
    pf.canvas.update()


def fgcolor(color):
    """Set the default foreground color."""
    pf.canvas.setFgColor(color)

def hicolor(color):
    """Set the highlight color."""
    pf.canvas.setSlColor(color)


def colormap(color=None):
    """Gets/Sets the current canvas color map"""
    return pf.canvas.settings.colormap


def colorindex(color):
    """Return the index of a color in the current colormap"""
    cmap = pf.canvas.settings.colormap
    color=array(color)
    i = where((cmap==color).all(axis=1))[0]
    if len(i) > 0:
        return i[0]
    else:
        i = len(cmap)
        print("Add color %s = %s to viewport colormap" % (i, color))
        color = color.reshape(1, 3)
        pf.canvas.settings.colormap = concatenate([cmap, color], axis=0)
    return i


def renderModes():
    """Return a list of predefined render profiles."""
    return canvas.CanvasSettings.RenderProfiles.keys()


def renderMode(mode,light=None):
    """Change the rendering profile to a predefined mode.

    Currently the following modes are defined:

    - wireframe
    - smooth
    - smoothwire
    - flat
    - flatwire
    - smooth_avg
    """
    # ERROR The following redraws twice !!!
    pf.canvas.setRenderMode(mode, light)
    pf.canvas.update()
    toolbar.updateViewportButtons(pf.canvas)
    #toolbar.updateNormalsButton()
    #toolbar.updateTransparencyButton()
    #toolbar.updateLightButton()
    pf.GUI.processEvents()


def wireMode(mode):
    """Change the wire rendering mode.

    Currently the following modes are defined: 'none', 'border',
    'feature','all'
    """
    modes = [ 'all', 'border', 'feature' ]
    if mode in modes:
        state = True
        mode = 1 + modes.index(mode)
    elif mode == 'none':
        state = False
        mode = None
    else:
        return
    pf.canvas.setWireMode(state, mode)
    pf.canvas.update()
    pf.GUI.processEvents()


def wireframe():
    renderMode("wireframe")

def smooth():
    renderMode("smooth")

def smoothwire():
    renderMode("smoothwire")

def flat():
    renderMode("flat")

def flatwire():
    renderMode("flatwire")

def smooth_avg():
    renderMode("smooth_avg")

## def opacity(alpha):
##     """Set the viewports transparency."""
##     pf.canvas.alpha = float(alpha)

def lights(state=True):
    """Set the lights on or off"""
    pf.canvas.setLighting(state)
    pf.canvas.update()
    toolbar.updateLightButton()
    pf.GUI.processEvents()


def transparent(state=True):
    """Set the transparency mode on or off."""
    pf.canvas.setToggle('alphablend', state)
    pf.canvas.update()
    toolbar.updateTransparencyButton()
    pf.GUI.processEvents()


def perspective(state=True):
    pf.canvas.camera.setPerspective(state)
    pf.canvas.update()
    toolbar.updatePerspectiveButton()
    pf.GUI.processEvents()


def set_material_value(typ, val):
    """Set the value of one of the material lighting parameters

    typ is one of 'ambient','specular','emission','shininess'
    val is a value between 0.0 and 1.0
    """
    setattr(pf.canvas, typ, val)
    pf.canvas.setLighting(True)
    pf.canvas.update()
    pf.app.processEvents()

def set_light(light,**args):
    light = int(light)
    pf.canvas.lights.set(light,**args)
    pf.canvas.setLighting(True)
    pf.canvas.update()
    pf.app.processEvents()

def set_light_value(light, key, val):
    light = int(light)
    pf.canvas.lights.set_value(light, key, val)
    pf.canvas.setLighting(True)
    pf.canvas.update()
    pf.app.processEvents()


def linewidth(wid):
    """Set the linewidth to be used in line drawings."""
    pf.canvas.setLineWidth(wid)

def linestipple(factor, pattern):
    """Set the linewidth to be used in line drawings."""
    pf.canvas.setLineStipple(factor, pattern)

def pointsize(siz):
    """Set the size to be used in point drawings."""
    pf.canvas.setPointSize(siz)


def canvasSize(width, height):
    """Resize the canvas to (width x height).

    If a negative value is given for either width or height,
    the corresponding size is set equal to the maximum visible size
    (the size of the central widget of the main window).

    Note that changing the canvas size when multiple viewports are
    active is not approved.
    """
    pf.canvas.changeSize(width, height)


# This is not intended for the user
def clear_canvas(sticky=False):
    pf.canvas.removeAll(sticky)
    pf.canvas.clearCanvas()


def clear(sticky=False):
    """Clear the canvas.

    Removes everything from the current scene and displays an empty
    background.

    This function waits for the drawing lock to be released, but will
    not reset it.
    """
    pf.GUI.drawlock.wait()
    clear_canvas()
    pf.canvas.update()


def redraw():
    pf.canvas.redrawAll()
    pf.canvas.update()


#### End