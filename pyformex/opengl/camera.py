# $Id$

"""OpenGL camera handling

Python OpenGL framework for pyFormex

This OpenGL framework is intended to replace (in due time)
the current OpenGL framework in pyFormex.

(C) 2013 Benedict Verhegghe and the pyFormex project.

"""
from __future__ import print_function

from matrix import Matrix4
import numpy as np
import pyformex.arraytools as at

import OpenGL.GL as GL
import OpenGL.GLU as GLU

def GL_projection():
    """Get the OpenGL projection matrix"""
    return GL.glGetDoublev(GL.GL_PROJECTION_MATRIX)
def GL_modelview():
    """Get the OpenGL modelview matrix"""
    return GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX)



def perspective_matrix(left,right,bottom,top,near,far):
    """Create a perspective Projection matrix.

    """
    m = Matrix4()
    m[0,0] = 2 * near / (right-left)
    m[1,1] = 2 * near / (top-bottom)
    m[2,0] = (right+left) / (right-left)
    m[2,1] = (top+bottom) / (top-bottom)
    m[2,2] = - (far+near) / (far-near)
    m[2,3] = -1.
    m[3,2] = -2 * near * far / (far-near)
    m[3,3] = 0.
    return m


def orthogonal_matrix(left,right,bottom,top,near,far):
    """Create an orthogonal Projection matrix.

    """
    m = Matrix4()
    m[0,0] = 2 / (right-left)
    m[1,1] = 2 / (top-bottom)
    m[2,2] = -2 / (far-near)
    m[3,0] = - (right+left) / (right-left)
    m[3,1] = - (top+bottom) / (top-bottom)
    m[3,2] = - (far+near) / (far-near)
    return m


def pick_matrix(x,y,w,h,viewport):
    """Create a pick Projection matrix

    """
    m = Matrix4()
    m[0,0] = viewport[2] / w;
    m[1,1] = viewport[3] / h;
    m[3,0] = (viewport[2] + 2.0 * (viewport[0] - x)) / w;
    m[3,1] = (viewport[3] + 2.0 * (viewport[1] - y)) / h;
    return m




built_in_views = {
    'front': (0.,0.,0.),
    'back': (180.,0.,0.),
    'right': (90.,0.,0.),
    'left': (270.,0.,0.),
    'top': (0.,90.,0.),
    'bottom': (0.,-90.,0.),
    'iso0': (45.,45.,0.),
    'iso1': (45.,135.,0.),
    'iso2': (45.,225.,0.),
    'iso3': (45.,315.,0.),
    'iso4': (-45.,45.,0.),
    'iso5': (-45.,135.,0.),
    'iso6': (-45.,225.,0.),
    'iso7': (-45.,315.,0.),
    }






class ViewAngles(dict):
    """A dict to keep named camera angle settings.

    This class keeps a dictionary of named angle settings. Each value is
    a tuple of (longitude, latitude, twist) camera angles.
    This is a static class which should not need to be instantiated.

    There are seven predefined values: six for looking along global
    coordinate axes, one isometric view.
    """

    def __init__(self,data = built_in_views):
       dict.__init__(self,data)
       self['iso'] = self['iso0']


    def get(self,name):
        """Get the angles for a named view.

        Returns a tuple of angles (longitude, latitude, twist) if the
        named view was defined, or None otherwise
        """
        return dict.get(self,name,None)


view_angles = ViewAngles()


class Camera(object):
    """A camera for OpenGL rendering.

    The Camera class holds all the camera related settings related to
    the rendering of a scene in OpenGL. These include camera position,
    the viewing direction of the camera, and the lens parameters (opening
    angle, front and back clipping planes).
    This class also provides convenient methods to change the settings so as
    to get smooth camera manipulation.

    Camera position and orientation:

        The camera viewing line is defined by two points: the position of
        the camera and the center of the scene the camera is looking at.
        We use the center of the scene as the origin of a local coordinate
        system to define the camera position. For convenience, this could be
        stored in spherical coordinates, as a distance value and two angles:
        longitude and latitude. Furthermore, the camera can also rotate around
        its viewing line. We can define this by a third angle, the twist.
        From these four values, the needed translation vector and rotation
        matrix for the scene rendering may be calculated.

        Inversely however, we can not compute a unique set of angles from
        a given rotation matrix (this is known as 'gimball lock').
        As a result, continuous (smooth) camera rotation by e.g. mouse control
        requires that the camera orientation be stored as the full rotation
        matrix, rather than as three angles. Therefore we store the camera
        position and orientation as follows:

        - `ctr`: `[ x,y,z ]` : the reference point of the camera:
          this is always a point on the viewing axis. Usually, it is set to
          the center of the scene you are looking at.
        - `dist`: distance of the camera to the reference point.
        - `rot`: a 3x3 rotation matrix, rotating the global coordinate system
          thus that the z-direction is oriented from center to camera.

        These values have influence on the ModelView matrix.

    Camera lens settings:

        The lens parameters define the volume that is seen by the camera.
        It is described by the following parameters:

        - `fovy`: the vertical lens opening angle (Field Of View Y),
        - `aspect`: the aspect ratio (width/height) of the lens. The product
          `fovy * aspect` is the horizontal field of view.
        - `near, far`: the position of the front and back clipping planes.
          They are given as distances from the camera and should both be
          strictly positive. Anything that is closer to the camera than
          the `near` plane or further away than the `far` plane, will not be
          shown on the canvas.

        Camera methods that change these values will not directly change
        the ModelView matrix. The :meth:`loadModelView` method has to be called
        explicitely to make the settings active.

        These values have influence on the Projection matrix.

    Methods that change the camera position, orientation or lens parameters
    will not directly change the related ModelView or Projection matrix.
    They will just flag a change in the camera settings. The changes are
    only activated by a call to the :meth:`loadModelView` or
    :meth:`loadProjection` method, which will test the flags to see whether
    the corresponding matrix needs a rebuild.

    The default camera is at distance 1.0 of the center point [0.,0.,0.] and
    looking in the -z direction.
    Near and far clipping planes are by default set to 0.1, resp 10 times
    the camera distance.

    Properties:

    - `modelview`: Matrix4: the OpenGL ModelView transformation matrix

    """

    # DEVELOPERS:
    #    The camera class assumes that matrixmode is always ModelView on entry.
    #    For operations in other modes, an explicit switch before the operations
    #    and afterwards back to ModelView should be performed.


    def __init__(self,focus=[0.,0.,0.],angles=[0.,0.,0.],dist=1.):
        """Create a new camera.

        The default camera is positioned at (0.,0.,1.) looking along the -z
        axis in the direction of the point (0.,0.,0.) and with the upvector
        in the direction of the y-axis.
        """
        self.locked = False
        self._modelview = Matrix4()
        self._projection = Matrix4()
        self.viewChanged = True
        self.lensChanged = True
        self.focus = focus
        self.dist = dist
        self.setModelView(angles=angles)
        self.setLens(45.,4./3.)
        self.setClip(0.1,10.)
        self.area = None
        self.resetArea()
        self.keep_aspect = True
        self.setPerspective(True)
        self.tracking = False
        self.p = self.v = None


    @property
    def modelview(self):
        if self.viewChanged:
            self.setModelView()
        return self._modelview

    @modelview.setter
    def modelview(self,value):
        self._modelview = Matrix4(value)


    @property
    def projection(self):
        if self.lensChanged:
            self.setProjection()
        return self._projection

    @projection.setter
    def projection(self,value):
        self._projection = Matrix4(value)


    @property
    def focus(self):
        """Return the camera reference point (the focus point)."""
        return self._focus

    @focus.setter
    def focus(self,vector):
        """Set the camera reference point (the focus point).

        The focus is the point the camer is looking at. It is a point on
        the camera's optical axis.

        - `vector`: (3,) float array: the global coordinates of the focus.

        """
        if not self.locked:
            self._focus = at.checkArray(vector,(3,),'f')
            self.viewChanged = True


    @property
    def dist(self):
        """Return the camera distance.

        The camera distance is the distance between the camera eye and
        the camera focus point.
        """
        return self._dist


    @dist.setter
    def dist(self,dist):
        """Set the camera distance.

        - `dist`: a strictly positive float value. Invalid values are
        silently ignored.
        """
        if not self.locked:
            if dist > 0.0 and dist != np.inf:
                self._dist = dist
                self.viewChanged = True


    @property
    def rot(self):
        """Return the camera rotation matrix."""
        return self._modelview.rot


    @ property
    def upvector(self):
        """Return the camera up vector"""
        return self._modelview.rot[:3,1].reshape((3,))


    def setAngles(self,angles):
        """Set the rotation angles.

        angles is either:

        - a tuple of angles (long,lat,twist)
        - a named view corresponding to angles in view_angles
        - None
        """
        if not self.locked:
            if type(angles) is str:
                angles = view_angles.get(angles)
            if angles is None:
                return
            self.setModelView(angles=angles)


    @property
    def eye(self):
        """Return the position of the camera."""
        return self.toWorld([0.,0.,0.])

    @eye.setter
    def eye(self):
        """Set the position of the camera."""
        return self.toWorld([0.,0.,0.])


    def lock(self,onoff=True):
        """Lock/unlock a camera.

        When a camera is locked, its position and lens parameters can not be
        changed.
        This can e.g. be used in multiple viewports layouts to create fixed
        views from different angles.
        """
        self.locked = bool(onoff)


    def report(self):
        """Return a report of the current camera settings."""
        return """Camera Settings:
  Focus: %s
  Distance: %s
  Rotation Matrix:
  %s
  Field of View y: %s
  Aspect Ratio: %s
  Area: %s, %s
  Near/Far Clip: %s, %s
""" % (self.focus,self.dist,self.rot,self.fovy,self.aspect,self.area[0],self.area[1],self.near,self.far)


    def dolly(self,val):
        """Move the camera eye towards/away from the scene center.

        This has the effect of zooming. A value > 1 zooms out,
        a value < 1 zooms in. The resulting enlargement of the view
        will approximately be 1/val.
        A zero value will move the camera to the center of the scene.
        The front and back clipping planes may need adjustment after
        a dolly operation.
        """
        if not self.locked:
            self.dist *= val
            self.viewChanged = True


    def pan(self,val,axis=0):
        """Rotate the camera around axis through its eye.

        The camera is rotated around an axis through the eye point.
        For axes 0 and 1, this will move the focus, creating a panning
        effect. The default axis is parallel to the y-axis, resulting in
        horizontal panning. For vertical panning (axis=1) a convenience
        alias tilt is created.
        For axis = 2 the operation is equivalent to the rotate operation.
        """
        if not self.locked:
            if axis==0 or axis ==1:
                pos = self.eye
                self.eye[axis] = (self.eye[axis] + val) % 360
                self.focus = diff(pos,sphericalToCartesian(self.eye))
            elif axis==2:
                self.twist = (self.twist + val) % 360
            self.viewChanged = True


    def tilt(self,val):
        """Rotate the camera up/down around its own horizontal axis.

        The camera is rotated around and perpendicular to the plane of the
        y-axis and the viewing axis. This has the effect of a vertical pan.
        A positive value tilts the camera up, shifting the scene down.
        The value is specified in degrees.
        """
        if not self.locked:
            self.pan(val,1)
            self.viewChanged = True


    def move(self,dx,dy,dz):
        """Move the camera over translation (dx,dy,dz) in global coordinates.

        The focus of the camera is moved over the specified translation
        vector. This has the effect of moving the scene in opposite direction.
        """
        if not self.locked:
            x,y,z = self.ctr
            self.focus += [dx,dy,dz]

##    def truck(self,dx,dy,dz):
##        """Move the camera translation vector in local coordinates.

##        This has the effect of moving the scene in opposite direction.
##        Positive coordinates mean:
##          first  coordinate : truck right,
##          second coordinate : pedestal up,
##          third  coordinate : dolly out.
##        """
##        #pos = self.position
##        ang = self.getAngles()
##        tr = [dx,dy,dz]
##        for i in [1,0,2]:
##            r = rotationMatrix(i,ang[i])
##            tr = multiply(tr, r)
##        self.move(*tr)
##        self.viewChanged = True


    def setLens(self,fovy=None,aspect=None):
        """Set the field of view of the camera.

        We set the field of view by the vertical opening angle fovy
        and the aspect ratio (width/height) of the viewing volume.
        A parameter that is not specified is left unchanged.
        """
        if fovy:
            self.fovy = min(abs(fovy),180)
        if aspect:
            self.aspect = abs(aspect)
        self.lensChanged = True


    def resetArea(self):
        """Set maximal camera area.

        Resets the camera window area to its maximum values corresponding
        to the fovy setting, symmetrical about the camera axes.
        """
        self.setArea(0.,0.,1.,1.,False)


    def setArea(self,hmin,vmin,hmax,vmax,relative=True,focus=False,clip=True):
        """Set the viewable area of the camera."""
        area = np.array([hmin,vmin,hmax,vmax])
        if clip:
            area = area.clip(0.,1.)
        if area[0] < area[2] and area[1] < area[3]:
            area = area.reshape(2,2)
            mean = (area[1]+area[0]) * 0.5
            diff = (area[1]-area[0]) * 0.5

            if relative:
                if focus:
                    mean = zeros(2)
                if self.keep_aspect:
                    aspect = diff[0] / diff[1]
                    if aspect > 1.0:
                        diff[1] = diff[0] #/ self.aspect
                        # no aspect factor: this is relative!!!
                    else:
                        diff[0] = diff[1] #* self.aspect
                    area[0] = mean-diff
                    area[1] = mean+diff
                #print("RELATIVE AREA %s" % (area))
                area = (1.-area) * self.area[0] + area * self.area[1]

            #print("OLD ZOOM AREA %s (aspect %s)" % (self.area,self.aspect))
            #print("NEW ZOOM AREA %s" % (area))

            self.area = area
            self.lensChanged = True



    def zoomArea(self,val=0.5,area=None):
        """Zoom in/out by shrinking/enlarging the camera view area.

        The zoom factor is relative to the current setting.
        Values smaller than 1.0 zoom in, larger values zoom out.
        """
        if val>0:
            #val = (1.-val) * 0.5
            #self.setArea(val,val,1.-val,1.-val,focus=focus)
            if area is None:
                area = self.area
            #print("ZOOM AREA %s (%s)" % (area.tolist(),val))
            mean = (area[1]+area[0]) * 0.5
            diff = (area[1]-area[0]) * 0.5 * val
            area[0] = mean-diff
            area[1] = mean+diff
            self.area = area
            #print("CAMERA AREA %s" % self.area.tolist())
            self.lensChanged = True


    def transArea(self,dx,dy):
        """Pan by moving the vamera area.

        dx and dy are relative movements in fractions of the
        current area size.
        """
        #print("TRANSAREA %s,%s" % (dx,dy))
        area = self.area
        diff = (area[1]-area[0]) * np.array([dx,dy])
        area += diff
        self.area = area
        self.lensChanged = True


    def setClip(self,near,far):
        """Set the near and far clipping planes"""
        if near > 0 and near < far:
            self.near,self.far = near,far
            self.lensChanged = True
        else:
            print("Error: Invalid Near/Far clipping values")


    ## def setClipRel(self,near,far):
    ##     """Set the near and far clipping planes"""
    ##     if near > 0 and near < far:
    ##         self.near,self.far = near,far
    ##         self.lensChanged = True
    ##     else:
    ##         print("Error: Invalid Near/Far clipping values")

    def setPerspective(self,on=True):
        """Set perspective on or off"""
        self.perspective = on
        self.lensChanged = True


    ## def zoom(self,val=0.5):
    ##     """Zoom in/out by shrinking/enlarging the camera view angle.

    ##     The zoom factor is relative to the current setting.
    ##     Use setFovy() to specify an absolute setting.
    ##     """
    ##     if val>0:
    ##         self.fovy *= val
    ##     self.lensChanged = True


    #### global manipulation ###################

    def set3DMatrices(self):
        self.loadProjection()
        self.loadModelView()
        self.p = GL.glGetDoublev(GL.GL_PROJECTION_MATRIX)
        self.v = GL.glGetIntegerv(GL.GL_VIEWPORT)


    def project(self,x,y,z):
        "Map the object coordinates (x,y,z) to window coordinates."""
        self.set3DMatrices()
        return GLU.gluProject(x,y,z,self._modelview,self.p,self.v)


    def unProject(self,x,y,z):
        "Map the window coordinates (x,y,z) to object coordinates."""
        self.set3DMatrices()
        return GLU.gluUnProject(x,y,z,self._modelview,self.p,self.v)


    def setTracking(self,onoff=True):
        """Enable/disable coordinate tracking using the camera"""
        if onoff:
            self.tracking = True
            self.set3DMatrices()
        else:
            self.tracking = False



    # TODO
    def translate(self,vx,vy,vz,local=True):
        if not self.locked:
            if local:
                vx,vy,vz = self.toWorld([vx,vy,vz,1])
            self.move(-vx,-vy,-vz)


#################################################################
##  Operations on modelview matrix  ##


    def setProjection(self,pick=None):
        """Load the projection/perspective matrix.

        The caller will have to setup the correct GL environment beforehand.
        No need to set matrix mode though. This function will switch to
        GL_PROJECTION mode before loading the matrix

        If keepmode=True, does not switch back to GL_MODELVIEW mode.

        A pick region can be defined to use the camera in picking mode.
        pick defines the picking region center and size (x,y,w,h).

        This function does it best at autodetecting changes in the lens
        settings, and will only reload the matrix if such changes are
        detected. You can optionally force loading the matrix.
        """
        if self.locked:
            return

        fv = at.tand(self.fovy*0.5)
        if self.perspective:
            fv *= self.near
        else:
            fv *= self.dist
        fh = fv * self.aspect
        x0,x1 = 2*self.area - 1.0
        frustum = (fh*x0[0],fh*x1[0],fv*x0[1],fv*x1[1],self.near,self.far)
        if self.perspective:
            func = perspective_matrix
        else:
            func = orthogonal_matrix
        self.projection = func(*frustum)
        try:
            self.projection_callback(self)
        except:
            pass


    def loadProjection (self,pick=None):
        """Load the Projection matrix.

        If lens parameters of the camera have been changed, the current
        Projection matrix is rebuild.
        Then, the current Projection matrix of the camera is loaded into the
        OpenGL engine.

        A pick region can be specified to use the camera in picking mode.

        - `pick`: a tuple (x,y,w,h,viewport) where x,y,w,h are floats
          defining the picking region center (x,y) and size (w,h), and
          viewport is a tuple of 4 int values (xmin,ymin,xmax,ymax) defining
          the viewport.
        """
        m = self.projection
        if pick is not None:
            m *= pick_matrix(*pick)

        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadMatrixf(m.gl())
        GL.glMatrixMode(GL.GL_MODELVIEW)


#################################################################
##  Operations on modelview matrix  ##


    def lookAt(self,focus=None,eye=None,up=None):
        """Set the ModelView matrix to look at specified point.

        The ModelView matrix is set with the camera positioned at eye
        and looking at the focus points, while the camera up vector is
        in the plane of the camera axis (focus-eye) and the specified
        up vector.

        If any of the arguments is left unspecified, the current value
        will be used.
        """
        if not self.locked:
            if focus is None:
                focus = self.focus
            else:
                focus = at.checkArray(focus,(3,),'f')
            if eye is None:
                eye = self.eye
            else:
                eye = at.checkArray(eye,(3,),'f')
            if up is None:
                up = self.up
            else:
                up = at.normalize(at.checkArray(up,(3,),'f'))
            vector = eye-focus
            self.focus = focus
            self.dist = at.length(vector)
            axis2 = at.normalize(vector)
            axis0 = at.normalize(np.cross(up,axis2))
            axis1 = at.normalize(np.cross(axis2,axis0))
            m = Matrix4()
            m.rotate(np.column_stack([axis0,axis1,axis2]))
            m.translate(-eye)
            self.setModelView(m)


    def rotate(self,val,vx,vy,vz):
        """Rotate the camera around current camera axes."""
        if not self.locked:
            rot = self._modelview.rot
            m = Matrix4()
            m.translate([0,0,-self.dist])
            m.rotate(val % 360, [vx,vy,vz])
            m.rotate(rot)
            m.translate(-self.focus)
            self.setModelView(m)


    def setModelView (self,m=None,angles=None):
        """Set the ModelView matrix.

        The ModelView matrix can be set from one of the following sources:

        - if `mat` is specified, it is a 4x4 matrix with a valuable
          ModelView transformation. It will be set as the current camera
          ModelView matrix.

        - else, if `angles` is specified, it is a sequence of the three
          camera angles (latitude, longitude and twist). The camera
          ModelView matrix is set from the current camera focus,
          the current camera distance, and the specified angles.
          This option is typically used to change the viewing direction
          of the camera, while keeping the focus point and camera distance.

        - else, if the viewChanged flags is set, the camera ModelView
          matrix is set from the current camera focus, the current camera
          distance, and the current camera rotation matrix.
          This option is typically used after changing the camera focus
          point and/or distance, while keeping the current viewing angles.

        - else, the current ModelView matrix remains unchanged.

        In all cases, if a modelview callback was set, it is called,
        and the viewChanged flag is cleared.
        """
        if self.locked:
            return

        if m is None and (self.viewChanged or angles is not None):
            m = Matrix4()
            m.translate([0,0,-self.dist])
            if angles is None:
                m.rotate(self._modelview.rot)
            else:
                long,lat,twist = angles
                m.rotate(-twist % 360, [0.0, 0.0, 1.0])
                m.rotate(lat % 360, [1.0, 0.0, 0.0])
                m.rotate(-long % 360, [0.0, 1.0, 0.0])
            m.translate(-self.focus)

        if m is not None:
            self._modelview = Matrix4(m)

        try:
            self.modelview_callback(self)
        except:
            pass
        self.viewChanged = False


    def loadModelView (self):
        """Load the ModelView matrix.

        If camera positioning parameters have been changed, the current
        ModelView matrix is rebuild.
        Then, the current ModelView matrix of the camera is loaded into the
        OpenGL engine.
        """
        if self.viewChanged:
            self.setModelView()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glLoadMatrixf(self._modelview.gl())


    def transform(self,x):
        """Transform a vertex using the current Modelview matrix.

        Transforms the point from world to camera coordinates.
        """
        x = at.checkArray(x,(3,),'f')
        return x*self.modelview[:3,:3] + self.modelview[3,:3]


    def toWorld(self,x):
        """Transform a vertex from camera to world coordinates.

        This multiplies
        The specified vector can have 3 or 4 (homogoneous) components.
        This uses the currently saved rotation matrix.
        """
        x = at.checkArray(x,(3,),'f') + [0.,0.,self.dist]
        return x*self.rot.T + self.focus



#################################
    # Compatibility: should be removed after complete conversion

    def saveModelView(self):
        pass

# End
