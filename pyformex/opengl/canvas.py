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

from gui.canvas import *
from camera import Camera
from renderer import Renderer


class Canvas(object):
    """A canvas for OpenGL rendering.

    The Canvas is a class holding all global data of an OpenGL scene rendering.
    This includes colors, line types, rendering mode.
    It also keeps lists of the actors and decorations in the scene.
    The canvas has a Camera object holding important viewing parameters.
    Finally, it stores the lighting information.

    It does not however contain the viewport size and position.
    """

    def __init__(self,settings={}):
        """Initialize an empty canvas with default settings."""
        self.highlights = ActorList(self)
        self.annotations = ActorList(self)
        self.decorations = ActorList(self)
        self.camera = None
        self.triade = None
        self.background = None
        self._bbox = None
        self.setBbox([[0.,0.,0.],[1.,1.,1.]])
        self.settings = CanvasSettings(**settings)
        self.mode2D = False
        self.rendermode = pf.cfg['draw/rendermode']
        self.setRenderMode(pf.cfg['draw/rendermode'])
        self.resetLighting()
        #print("INIT: %s, %s" %(self.rendermode,self.settings.fill))
        self.view_angles = views.ViewAngles()
        self.cursor = None
        self.focus = False
        pf.debug("Canvas Setting:\n%s"% self.settings,pf.DEBUG.DRAW)


    @property
    def actors(self):
        return self.renderer._objects


    def enable_lighting(self,state):
        """Toggle lights on/off."""
        if state:
            self.lightprof.activate()
            self.material.activate()
            #print("ENABLE LIGHT")
            GL.glEnable(GL.GL_LIGHTING)
        else:
            #print("DISABLE LIGHT")
            GL.glDisable(GL.GL_LIGHTING)


    def has_lighting(self):
        """Return the status of the lighting."""
        return GL.glIsEnabled(GL.GL_LIGHTING)


    def resetDefaults(self,dict={}):
        """Return all the settings to their default values."""
        self.settings.reset(dict)
        self.resetLighting()
        ## self.resetLights()

    def setAmbient(self,ambient):
        """Set the global ambient lighting for the canvas"""
        self.lightprof.ambient = float(ambient)

    def setMaterial(self,matname):
        """Set the default material light properties for the canvas"""
        self.material = pf.GUI.materials[matname]


    def resetLighting(self):
        """Change the light parameters"""
        self.lightmodel = pf.cfg['render/lightmodel']
        self.setMaterial(pf.cfg['render/material'])
        self.lightset = pf.cfg['render/lights']
        lights = [ Light(int(light[-1:]),**pf.cfg['light/%s' % light]) for light in self.lightset ]
        self.lightprof = LightProfile(self.lightmodel,pf.cfg['render/ambient'],lights)


    def setRenderMode(self,mode,lighting=None):
        """Set the rendering mode.

        This sets or changes the rendermode and lighting attributes.
        If lighting is not specified, it is set depending on the rendermode.

        If the canvas has not been initialized, this merely sets the
        attributes self.rendermode and self.settings.lighting.
        If the canvas was already initialized (it has a camera), and one of
        the specified settings is different from the existing, the new mode
        is set, the canvas is re-initialized according to the newly set mode,
        and everything is redrawn with the new mode.
        """
        #print("Setting rendermode to %s" % mode)
        if mode not in CanvasSettings.RenderProfiles:
            raise ValueError,"Invalid render mode %s" % mode

        self.settings.update(CanvasSettings.RenderProfiles[mode])
        #print(self.settings)
        if lighting is None:
            lighting = self.settings.lighting

        if self.camera:
            if mode != self.rendermode or lighting != self.settings.lighting:
                print("SWITCHING MODE")
                self.renderer.changeMode(mode)

            self.rendermode = mode
            self.settings.lighting = lighting
            self.reset()


    def setWireMode(self,state,mode=None):
        """Set the wire mode.

        This toggles the drawing of edges on top of 2D and 3D geometry.
        State is either True or False, mode is 1, 2 or 3 to switch:

        1: all edges
        2: feature edges
        3: border edges

        If no mode is specified, the current wiremode is used. A negative
        value inverses the state.
        """
        print("CANVAS.setWireMode %s %s" % (state,mode))
        oldstate = self.settings.wiremode
        if mode is None:
            mode = abs(oldstate)
        if state is False:
            state = -mode
        else:
            state = mode
        self.settings.wiremode = state
        self.do_wiremode(state,oldstate)


    def setToggle(self,attr,state):
        """Set or toggle a boolean settings attribute

        Furthermore, if a Canvas method do_ATTR is defined, it will be called
        with the old and new toggle state as a parameter.
        """
        #print("CANVAS.setTogggle %s = %s"%(attr,state))
        oldstate = self.settings[attr]
        if state not in [True,False]:
            state = not oldstate
        self.settings[attr] = state
        try:
            func = getattr(self,'do_'+attr)
            func(state,oldstate)
        except:
            pass


    def setLighting(self,onoff):
        self.setToggle('lighting',onoff)


    def do_wiremode(self,state,oldstate):
        """Change the wiremode"""
        print("CANVAS.do_wiremode: %s -> %s"%(oldstate,state))
        if state != oldstate and (state>0 or oldstate>0):
            # switching between two <= modes does not change anything
            print("Changemode %s" % self.renderer.canvas.settings.wiremode)
            self.renderer.changeMode()
            self.display()


    def do_alphablend(self,state,oldstate):
        """Toggle alphablend on/off."""
        #print("CANVAS.do_alphablend: %s -> %s"%(state,oldstate))
        if state != oldstate:
            self.renderer.changeMode()
            self.display()


    def do_lighting(self,state,oldstate):
        """Toggle lights on/off."""
        #print("CANVAS.do_lighting: %s -> %s"%(state,oldstate))
        if state != oldstate:
            self.enable_lighting(state)
            self.renderer.changeMode()
            self.display()


    def do_avgnormals(self,state,oldstate):
        print("CANVAS.do_avgnormals: %s -> %s" % (state,oldstate))
        if state!=oldstate and self.settings.lighting:
            self.renderer.changeMode()
            self.display()


    def setLineWidth(self,lw):
        """Set the linewidth for line rendering."""
        self.settings.linewidth = float(lw)


    def setLineStipple(self,repeat,pattern):
        """Set the linestipple for line rendering."""
        self.settings.update({'linestipple':(repeat,pattern)})


    def setPointSize(self,sz):
        """Set the size for point drawing."""
        self.settings.pointsize = float(sz)


    def setBackground(self,color=None,image=None):
        """Set the color(s) and image.

        Change the background settings according to the specified parameters
        and set the canvas background accordingly. Only (and all) the specified
        parameters get a new value.

        Parameters:

        - `color`: either a single color, a list of two colors or a list of
          four colors.
        - `image`: an image to be set.
        """
        self.settings.update(dict(bgcolor=color,bgimage=image))
        color = self.settings.bgcolor
        if color.ndim == 1 and not self.settings.bgimage:
            pf.debug("Clearing fancy background",pf.DEBUG.DRAW)
            self.background = None
        else:
            self.createBackground()
            #glSmooth()
            #glFill()
        self.clear()
        self.redrawAll()
        #self.update()


    def createBackground(self):
        """Create the background object."""
        x1,y1 = 0,0
        x2,y2 = self.getSize()
        from gui.drawable import saneColorArray
        color = saneColorArray(self.settings.bgcolor,(4,))
        #print color.shape,color
        image = None
        if self.settings.bgimage:
            from plugins.imagearray import image2numpy
            try:
                image = image2numpy(self.settings.bgimage,indexed=False)
            except:
                pass
        #print("BACKGROUN %s,%s"%(x2,y2))
        self.background = decors.Rectangle(x1,y1,x2,y2,color=color,texture=image)


    def setFgColor(self,color):
        """Set the default foreground color."""
        self.settings.fgcolor = colors.GLcolor(color)


    def setSlColor(self,color):
        """Set the highlight color."""
        self.settings.slcolor = colors.GLcolor(color)


    def setTriade(self,on=None,pos='lb',siz=100):
        """Toggle the display of the global axes on or off.

        If on is True, a triade of global axes is displayed, if False it is
        removed. The default (None) toggles between on and off.
        """
        if on is None:
            on = self.triade is None
        pf.debug("SETTING TRIADE %s" % on,pf.DEBUG.DRAW)
        if self.triade:
            self.removeAnnotation(self.triade)
            self.triade = None
        if on:
            self.triade = decors.Triade(pos,siz)
            self.addAnnotation(self.triade)


    def initCamera(self):
        self.makeCurrent()  # we need correct OpenGL context for camera
        self.camera = Camera()
        ## if pf.options.testcamera:
        ##     self.camera.modelview_callback = print_camera
        ##     self.camera.projection_callback = print_camera
        self.renderer = Renderer(self)


    def clear(self):
        """Clear the canvas to the background color."""
        self.settings.setMode()
        self.setDefaults()


    def setSize (self,w,h):
        if h == 0:	# prevent divide by zero
            h = 1
        GL.glViewport(0, 0, w, h)
        self.aspect = float(w)/h
        self.camera.setLens(aspect=self.aspect)
        if self.background:
            # recreate the background to match the current size
            self.createBackground()
        self.display()


    def drawit(self,a):
        """_Perform the drawing of a single item"""
        self.setDefaults()
        a.draw(self)


    def setDefaults(self):
        """Activate the canvas settings in the GL machine."""
        self.settings.activate()
        self.enable_lighting(self.settings.lighting)
        GL.glDepthFunc(GL.GL_LESS)


    def overrideMode(self,mode):
        """Override some settings"""
        settings = CanvasSettings.RenderProfiles[mode]
        CanvasSettings.glOverride(settings,self.settings)


    def reset(self):
        """Reset the rendering engine.

        The rendering machine is initialized according to self.settings:
        - self.rendermode: one of
        - self.lighting
        """
        self.setDefaults()
        self.setBackground(self.settings.bgcolor,self.settings.bgimage)
        self.clear()
        GL.glClearDepth(1.0)	       # Enables Clearing Of The Depth Buffer
        GL.glEnable(GL.GL_DEPTH_TEST)	       # Enables Depth Testing
        #GL.glEnable(GL.GL_CULL_FACE)
        if self.rendermode == 'wireframe':
            glPolygonOffset(0.0)
        else:
            glPolygonOffset(1.0)


    def glinit(self):
        """Initialize the rendering engine.

        """
        print("INITIALIZE RENDERING ENGINE")
        self.reset()


    def glupdate(self):
        """Flush all OpenGL commands, making sure the display is updated."""
        GL.glFlush()


    def display(self):
        """(Re)display all the actors in the scene.

        This should e.g. be used when actors are added to the scene,
        or after changing  camera position/orientation or lens.
        """
        #pf.debugt("UPDATING CURRENT OPENGL CANVAS",pf.DEBUG.DRAW)
        self.makeCurrent()

        self.clear()

        # draw background decorations in 2D mode
        self.begin_2D_drawing()

        if self.background:
            #pf.debug("Displaying background",pf.DEBUG.DRAW)
            # If we have a shaded background, we need smooth/fill anyhow
            glSmooth()
            glFill()
            self.background.draw(mode='smooth')

        # background decorations
        back_decors = [ d for d in self.decorations if not d.ontop ]
        for actor in back_decors:
            self.setDefaults()
            ## if hasattr(actor,'zoom'):
            ##     self.zoom_2D(actor.zoom)
            actor.draw(canvas=self)
            ## if hasattr(actor,'zoom'):
            ##     self.zoom_2D()

        # draw the focus rectangle if more than one viewport
        if len(pf.GUI.viewports.all) > 1 and pf.cfg['gui/showfocus']:
            if self.hasFocus(): # QT focus
                self.draw_focus_rectangle(0,color=colors.blue)
            if self.focus:      # pyFormex DRAW focus
                self.draw_focus_rectangle(2,color=colors.red)

        self.end_2D_drawing()

        # start 3D drawing
        self.camera.set3DMatrices()

        # Draw the opengl2 actors
        self.renderer.render()

        # draw the highlighted actors
        if self.highlights:
            for actor in self.highlights:
                self.setDefaults()
                actor.draw(canvas=self)

        ## # draw the scene actors and annotations
        ## sorted_actors = [ a for a in self.annotations if not a.ontop ] + \
        ##                 [ a for a in self.actors if not a.ontop ] + \
        ##                 [ a for a in self.actors if a.ontop ] + \
        ##                 [ a for a in self.annotations if a.ontop ]
        ## if self.settings.alphablend:
        ##     opaque = [ a for a in sorted_actors if a.opak ]
        ##     transp = [ a for a in sorted_actors if not a.opak ]
        ##     for actor in opaque:
        ##         self.setDefaults()
        ##         actor.draw(canvas=self)
        ##     GL.glEnable (GL.GL_BLEND)
        ##     GL.glDepthMask (GL.GL_FALSE)
        ##     if pf.cfg['draw/disable_depth_test']:
        ##         GL.glDisable(GL.GL_DEPTH_TEST)
        ##     GL.glBlendFunc (GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        ##     for actor in transp:
        ##         self.setDefaults()
        ##         actor.draw(canvas=self)
        ##     GL.glEnable(GL.GL_DEPTH_TEST)
        ##     GL.glDepthMask (GL.GL_TRUE)
        ##     GL.glDisable (GL.GL_BLEND)
        ## else:
        ##     for actor in sorted_actors:
        ##         self.setDefaults()
        ##         actor.draw(canvas=self)

        ## # annotations are decorations drawn in 3D space
        ## for actor in self.annotations:
        ##     self.setDefaults()
        ##     actor.draw(canvas=self)


        # draw foreground decorations in 2D mode
        self.begin_2D_drawing()
        decors = [ d for d in self.decorations if d.ontop ]
        for actor in decors:
            self.setDefaults()
            ## if hasattr(actor,'zoom'):
            ##     self.zoom_2D(actor.zoom)
            actor.draw(canvas=self)
            ## if hasattr(actor,'zoom'):
            ##     self.zoom_2D()
        self.end_2D_drawing()

        # make sure canvas is updated
        GL.glFlush()


    def zoom_2D(self,zoom=None):
        if zoom is None:
            zoom = (0,self.width(),0,self.height())
        GLU.gluOrtho2D(*zoom)


    def begin_2D_drawing(self):
        """Set up the canvas for 2D drawing on top of 3D canvas.

        The 2D drawing operation should be ended by calling end_2D_drawing.
        It is assumed that you will not try to change/refresh the normal
        3D drawing cycle during this operation.
        """
        #pf.debug("Start 2D drawing",pf.DEBUG.DRAW)
        if self.mode2D:
            #pf.debug("WARNING: ALREADY IN 2D MODE",pf.DEBUG.DRAW)
            return
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        self.zoom_2D()
        GL.glDisable(GL.GL_DEPTH_TEST)
        self.enable_lighting(False)
        self.mode2D = True


    def end_2D_drawing(self):
        """Cancel the 2D drawing mode initiated by begin_2D_drawing."""
        #pf.debug("End 2D drawing",pf.DEBUG.DRAW)
        if self.mode2D:
            GL.glEnable(GL.GL_DEPTH_TEST)
            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glPopMatrix()
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glPopMatrix()
            self.enable_lighting(self.settings.lighting)
            self.mode2D = False


    def sceneBbox(self):
        """Return the bbox of all actors in the scene"""
        return self.renderer.bbox


    def setBbox(self,bb=None):
        """Set the bounding box of the scene you want to be visible.

        bb is a (2,3) shaped array specifying a bounding box.
        If no bbox is given, the bounding box of all the actors in the
        scene is used, or if the scene is empty, a default unit bounding box.
        """
        if bb is None:
            bb = self.renderer.bbox
        else:
            bb = coords.Coords(bb)
        # make sure we have no nan's in the bbox
        try:
            bb = nan_to_num(bb)
        except:
            pf.message("Invalid Bbox: %s" % bb)
        # make sure bbox size is nonzero in all directions
        sz = bb[1]-bb[0]
        bb[1,sz==0.0] += 1.
        # Set bbox
        self._bbox = bb


    def addActor(self,itemlist):
        """Add a 3D actor or a list thereof to the 3D scene."""
        #self.actors.add(itemlist)
        # itemlist should be a new style GeomActor
        self.renderer.addActor(itemlist)


    def addHighlight(self,itemlist):
        """Add a highlight or a list thereof to the 3D scene."""
        self.highlights.add(itemlist)

    def addAnnotation(self,itemlist):
        """Add an annotation or a list thereof to the 3D scene."""
        self.annotations.add(itemlist)

    def addDecoration(self,itemlist):
        """Add a 2D decoration or a list thereof to the canvas."""
        self.decorations.add(itemlist)

    def addAny(self,itemlist=None):
        """Add any  item or list.

        This will add any actor/annotation/decoration item or a list
        of any such items  to the canvas. This is the prefered method to add
        an item to the canvas, because it makes sure that each item is added
        to the proper list. It can however not be used to add highlights.

        If you have a long list of a single type, it is more efficient to
        use one of the type specific add methods.
        """
        if type(itemlist) not in (tuple,list):
            itemlist = [ itemlist ]
        self.addActor([ i for i in itemlist if isinstance(i,actors.Actor)])
        self.addAnnotation([ i for i in itemlist if isinstance(i,marks.Mark)])
        self.addDecoration([ i for i in itemlist if isinstance(i,decors.Decoration)])


    def removeActor(self,itemlist=None):
        """Remove a 3D actor or a list thereof from the 3D scene.

        Without argument, removes all actors from the scene.
        This also resets the bounding box for the canvas autozoom.
        """
        if itemlist == None:
            itemlist = self.actors[:]
        self.actors.delete(itemlist)
        self.setBbox()

    def removeHighlight(self,itemlist=None):
        """Remove a highlight or a list thereof from the 3D scene.

        Without argument, removes all highlights from the scene.
        """
        if itemlist == None:
            itemlist = self.highlights[:]
        self.highlights.delete(itemlist)

    def removeAnnotation(self,itemlist=None):
        """Remove an annotation or a list thereof from the 3D scene.

        Without argument, removes all annotations from the scene.
        """
        if itemlist == None:
            itemlist = self.annotations[:]
        #
        # TODO: check whether the removal of the following code
        # does not have implications
        #
        ## if self.triade in itemlist:
        ##     pf.debug("REMOVING TRIADE",pf.DEBUG.DRAW)
        ##     self.triade = None
        self.annotations.delete(itemlist)

    def removeDecoration(self,itemlist=None):
        """Remove a 2D decoration or a list thereof from the canvas.

        Without argument, removes all decorations from the scene.
        """
        if itemlist == None:
            itemlist = self.decorations[:]
        self.decorations.delete(itemlist)


    def removeAny(self,itemlist=None):
        """Remove a list of any actor/highlights/annotation/decoration items.

        This will remove the items from any of the canvas lists in which the
        item appears.
        itemlist can also be a single item instead of a list.
        If None is specified, all items from all lists will be removed.
        """
        self.removeActor(itemlist)
        self.removeHighlight(itemlist)
        self.removeAnnotation(itemlist)
        self.removeDecoration(itemlist)


    def redrawAll(self):
        """Redraw all actors in the scene."""
        print("REDRAW CANVAS DOES NOT DO ANYTHING")
        pass
        ## self.actors.redraw()
        ## self.highlights.redraw()
        ## self.annotations.redraw()
        ## self.decorations.redraw()
        ## self.display()


    def setCamera(self,bbox=None,angles=None):
        """Sets the camera looking under angles at bbox.

        This function sets the camera parameters to view the specified
        bbox volume from the specified viewing direction.

        Parameters:

        - `bbox`: the bbox of the volume looked at
        - `angles`: the camera angles specifying the viewing direction.
          It can also be a string, the key of one of the predefined
          camera directions

        If no angles are specified, the viewing direction remains constant.
        The scene center (camera focus point), camera distance, fovy and
        clipping planes are adjusted to make the whole bbox viewed from the
        specified direction fit into the screen.

        If no bbox is specified, the following remain constant:
        the center of the scene, the camera distance, the lens opening
        and aspect ratio, the clipping planes. In other words the camera
        is moving on a spherical surface and keeps focusing on the same
        point.

        If both are specified, then first the scene center is set,
        then the camera angles, and finally the camera distance.

        In the current implementation, the lens fovy and aspect are not
        changed by this function. Zoom adjusting is performed solely by
        changing the camera distance.
        """
        #
        # TODO: we should add the rectangle (digital) zooming to
        #       the docstring

        self.makeCurrent()

        # set scene center
        if bbox is not None:
            pf.debug("SETTING BBOX: %s" % bbox,pf.DEBUG.DRAW)
            self.setBbox(bbox)

            X0,X1 = self._bbox
            self.camera.focus = 0.5*(X0+X1)

        # set camera angles
        if type(angles) is str:
            angles = self.view_angles.get(angles)
        if angles is not None:
            try:
                self.camera.setAngles(angles)
            except:
                raise ValueError,'Invalid view angles specified'

        # set camera distance and clipping planes
        if bbox is not None:
            # Currently, we keep the default fovy/aspect
            # and change the camera distance to focus
            fovy = self.camera.fovy
            #pf.debug("FOVY: %s" % fovy,pf.DEBUG.DRAW)
            self.camera.setLens(fovy,self.aspect)
            # Default correction is sqrt(3)
            correction = float(pf.cfg.get('gui/autozoomfactor',1.732))
            tf = coords.tand(fovy/2.)

            import simple
            bbix = simple.regularGrid(X0,X1,[1,1,1])
            bbix = dot(bbix,self.camera.rot[:3,:3])
            bbox = coords.Coords(bbix).bbox()
            dx,dy,dz = bbox[1] - bbox[0]
            vsize = max(dx/self.aspect,dy)
            dsize = bbox.dsize()
            offset = dz
            dist = (vsize/tf + offset) / correction

            if dist == nan or dist == inf:
                pf.debug("DIST: %s" % dist,pf.DEBUG.DRAW)
                return
            if dist <= 0.0:
                dist = 1.0
            self.camera.dist = dist

            ## print "vsize,dist = %s, %s" % (vsize,dist)
            ## near,far = 0.01*dist,100.*dist
            ## print "near,far = %s, %s" % (near,far)
            #near,far = dist-1.2*offset/correction,dist+1.2*offset/correction
            near,far = dist-1.0*dsize,dist+1.0*dsize
            # print "near,far = %s, %s" % (near,far)
            #print (0.0001*vsize,0.01*dist,near)
            # make sure near is positive
            near = max(near,0.0001*vsize,0.01*dist,finfo(coords.Float).tiny)
            # make sure far > near
            if far <= near:
                far += finfo(coords.Float).eps
            #print "near,far = %s, %s" % (near,far)
            self.camera.setClip(near,far)
            self.camera.resetArea()


    def project(self,x,y,z,locked=False):
        "Map the object coordinates (x,y,z) to window coordinates."""
        locked=False
        if locked:
            model,proj,view = self.projection_matrices
        else:
            self.makeCurrent()
            self.camera.loadProjection()
            model = GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX)
            proj = GL.glGetDoublev(GL.GL_PROJECTION_MATRIX)
            view = GL.glGetIntegerv(GL.GL_VIEWPORT)
        winx,winy,winz = GLU.gluProject(x,y,z,model,proj,view)
        return winx,winy,winz
        return self.camera.project(x,y,z)


    def unProject(self,x,y,z,locked=False):
        "Map the window coordinates (x,y,z) to object coordinates."""
        locked=False
        if locked:
            model,proj,view = self.projection_matrices
        else:
            self.makeCurrent()
            self.camera.loadProjection()
            model = GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX)
            proj = GL.glGetDoublev(GL.GL_PROJECTION_MATRIX)
            view = GL.glGetIntegerv(GL.GL_VIEWPORT)
        objx, objy, objz = GLU.gluUnProject(x,y,z,model,proj,view)
        return (objx,objy,objz)
        return self.camera.unProject(x,y,z)


    def zoom(self,f,dolly=True):
        """Dolly zooming.

        Zooms in with a factor `f` by moving the camera closer
        to the scene. This does noet change the camera's FOV setting.
        It will change the perspective view though.
        """
        if dolly:
            self.camera.dolly(f)


    def zoomRectangle(self,x0,y0,x1,y1):
        """Rectangle zooming.

        Zooms in/out by changing the area and position of the visible
        part of the lens.
        Unlike zoom(), this does not change the perspective view.

        `x0,y0,x1,y1` are pixel coordinates of the lower left and upper right
        corners of the area of the lens that will be mapped on the
        canvas viewport.
        Specifying values that lead to smaller width/height will zoom in.
        """
        w,h = float(self.width()),float(self.height())
        self.camera.setArea(x0/w,y0/h,x1/w,y1/h)


    def zoomCentered(self,w,h,x=None,y=None):
        """Rectangle zooming with specified center.

        This is like zoomRectangle, but the zoom rectangle is specified
        by its center and size, which may be more appropriate when using
        off-center zooming.
        """
        self.zoomRectangle(x-w/2,y-h/2,x+w/2,y+w/2)


    def zoomAll(self):
        """Rectangle zoom to make full scene visible.

        """
        self.camera.resetArea()


    def saveBuffer(self):
        """Save the current OpenGL buffer"""
        self.save_buffer = GL.glGetIntegerv(GL.GL_DRAW_BUFFER)

    def showBuffer(self):
        """Show the saved buffer"""
        pass

    def draw_focus_rectangle(self,ofs=0,color=colors.pyformex_pink):
        """Draw the focus rectangle.

        The specified width is HALF of the line width
        """
        w,h = self.width(),self.height()
        self._focus = decors.Grid(1+ofs,ofs,w-ofs,h-1-ofs,color=color,linewidth=1)
        self._focus.draw()

    def draw_cursor(self,x,y):
        """draw the cursor"""
        if self.cursor:
            self.removeDecoration(self.cursor)
        w,h = pf.cfg.get('draw/picksize',(20,20))
        col = pf.cfg.get('pick/color','yellow')
        self.cursor = decors.Grid(x-w/2,y-h/2,x+w/2,y+h/2,color=col,linewidth=1)
        self.addDecoration(self.cursor)

    def draw_rectangle(self,x,y):
        if self.cursor:
            self.removeDecoration(self.cursor)
        col = pf.cfg.get('pick/color','yellow')
        self.cursor = decors.Grid(self.statex,self.statey,x,y,color=col,linewidth=1)
        self.addDecoration(self.cursor)



    def pick_actors(self):
        """Set the list of actors inside the pick_window."""
        self.camera.loadProjection(pick=self.pick_window)
        self.camera.loadModelView()
        stackdepth = 1
        npickable = len(self.actors)
        print("PICKABLE OBJECTS: %s" % npickable)
        selbuf = GL.glSelectBuffer(npickable*(3+stackdepth))
        GL.glRenderMode(GL.GL_SELECT)
        GL.glInitNames()
        self.renderer.render(picking=True)
        ## for i,a in enumerate(self.actors):
        ##     print("PUSH %s" % i)
        ##     GL.glPushName(i)
        ##     a.render(self.renderer)
        ##     GL.glPopName()
        libGL.glRenderMode(GL.GL_RENDER)
        # Read the selection buffer
        store_closest = self.selection_filter == 'single' or \
                        self.selection_filter == 'closest'
        self.picked = []
        print("GOT selbuf %s " % selbuf)
        if selbuf[0] > 0:
            buf = asarray(selbuf).reshape(-1,3+selbuf[0])
            buf = buf[buf[:,0] > 0]
            self.picked = buf[:,3]
            print(self.picked)
            if store_closest:
                w = buf[:,1].argmin()
                self.closest_pick = (self.picked[w], buf[w,1])


    def pick_parts(self,obj_type,max_objects,store_closest=False):
        """Set the list of actor parts inside the pick_window.

        obj_type can be 'element', 'face', 'edge' or 'point'.
        'face' and 'edge' are only available for Mesh type geometry.
        max_objects specifies the maximum number of objects

        The picked object numbers are stored in self.picked.
        If store_closest==True, the closest picked object is stored in as a
        tuple ( [actor,object] ,distance) in self.picked_closest

        A list of actors from which can be picked may be given.
        If so, the resulting keys are indices in this list.
        By default, the full actor list is used.
        """
        self.picked = []
        pf.debug('PICK_PARTS %s %s %s' % (obj_type,max_objects,store_closest),pf.DEBUG.DRAW)
        if max_objects <= 0:
            pf.message("No such objects to be picked!")
            return
        self.camera.loadProjection(pick=self.pick_window)
        self.camera.loadModelView()
        stackdepth = 2
        selbuf = GL.glSelectBuffer(max_objects*(3+stackdepth))
        GL.glRenderMode(GL.GL_SELECT)
        GL.glInitNames()
        if self.pickable is None:
            pickable = self.actors
        else:
            pickable = self.pickable
        for i,a in enumerate(pickable):
            GL.glPushName(i)
            a.pickGL(obj_type)  # this will push the number of the part
            GL.glPopName()
        self.picked = []
        libGL.glRenderMode(GL.GL_RENDER)
        if selbuf[0] > 0:
            buf = asarray(selbuf).reshape(-1,3+selbuf[0])
            buf = buf[buf[:,0] > 0]
            self.picked = buf[:,3:]
            #pf.debug("PICKBUFFER: %s" % self.picked)
            if store_closest and len(buf) > 0:
                w = buf[:,1].argmin()
                self.closest_pick = (self.picked[w], buf[w,1])


    def pick_elements(self):
        """Set the list of actor elements inside the pick_window."""
        npickable = 0
        for a in self.actors:
            npickable += a.nelems()
        self.pick_parts('element',npickable,store_closest=\
                        self.selection_filter == 'single' or\
                        self.selection_filter == 'closest' or\
                        self.selection_filter == 'connected'
                        )


    def pick_points(self):
        """Set the list of actor points inside the pick_window."""
        npickable = 0
        for a in self.actors:
            pf.debug("ADDING %s pickable points"%a.npoints(),pf.DEBUG.DRAW)
            npickable += a.npoints()
        self.pick_parts('point',npickable,store_closest=\
                        self.selection_filter == 'single' or\
                        self.selection_filter == 'closest',
                        )


    def pick_edges(self):
        """Set the list of actor edges inside the pick_window."""
        npickable = 0
        for a in self.actors:
            if hasattr(a,'nedges'):
                npickable += a.nedges()
        self.pick_parts('edge',npickable,store_closest=\
                        self.selection_filter == 'single' or\
                        self.selection_filter == 'closest',
                        )


    def pick_faces(self):
        """Set the list of actor faces inside the pick_window."""
        npickable = 0
        for a in self.actors:
            if hasattr(a,'nfaces'):
                npickable += a.nfaces()
        self.pick_parts('face',npickable,store_closest=\
                        self.selection_filter == 'single' or\
                        self.selection_filter == 'closest',
                        )


    def pick_numbers(self):
        """Return the numbers inside the pick_window."""
        self.camera.loadProjection(pick=self.pick_window)
        self.camera.loadModelView()
        self.picked = [0,1,2,3]
        if self.numbers:
            self.picked = self.numbers.drawpick()


    def highlightActors(self,K):
        """Highlight a selection of actors on the canvas.

        K is Collection of actors as returned by the pick() method.
        colormap is a list of two colors, for the actors not in, resp. in
        the Collection K.
        """
        print("HIGHLIGHT_ACTORS",K)
        self.renderer.removeHighlight()
        for i in K.get(-1,[]):
            self.renderer._objects[i].highlight = True
        #self.update()

    def highlightElements(self,K):
        print("HIGHLIGHT_ELEMENTS",K)
        pass
    def highlightPoints(self,K):
        pass
    def highlightEdges(self,K):
        pass

    def removeHighlight(self):
        """Remove a highlight or a list thereof from the 3D scene.

        Without argument, removes all highlights from the scene.
        """
        self.renderer.removeHighlight()


    highlight_funcs = { 'actor': highlightActors,
                        'element': highlightElements,
                        'point': highlightPoints,
                        'edge': highlightEdges,
                        }

### End
