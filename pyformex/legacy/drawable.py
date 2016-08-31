# $Id$
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
"""OpenGL drawing functions and base class for all drawable objects.

"""
from __future__ import absolute_import, division, print_function


import pyformex as pf
from pyformex import utils, olist, simple, geomtools
from pyformex.lib import drawgl_e as drawgl
from pyformex.formex import *
from pyformex.opengl.colors import *

from OpenGL import GL, GLU


def glObjType(nplex):
    if nplex == 1:
        objtype = GL.GL_POINTS
    elif nplex == 2:
        objtype = GL.GL_LINES
    elif nplex == 3:
        objtype = GL.GL_TRIANGLES
    elif nplex == 4:
        objtype = GL.GL_QUADS
    else:
        objtype = GL.GL_POLYGON
    return objtype

# A list of elements that can be drawn quadratically using NURBS
_nurbs_elements = [ 'line3', 'quad4', 'quad8', 'quad9', 'hex20' ]

### Some drawing functions ###############################################


def glTexture(texture,mode='*'):
    """Render-time texture environment setup"""
    texmode = {'*': GL.GL_MODULATE, '1': GL.GL_DECAL}[mode]
    # Configure the texture rendering parameters
    GL.glEnable(GL.GL_TEXTURE_2D)
    GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
    GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
    GL.glTexEnvf(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, texmode)
    # Re-select the texture
    GL.glBindTexture(GL.GL_TEXTURE_2D, texture.tex)



def drawPolygons(x,e,color=None,alpha=1.0,texture=None,t=None,normals=None,lighting=False,avgnormals=False,objtype=-1):
    """Draw a collection of polygons.

    The polygons can either be specified as a Formex model or as a Mesh model.

    Parameters:

    - `x`: coordinates of the points. Shape is (nelems,nplex,3) for Formex
      model, of (nnodes,3) for Mesh model.
    - `e`: None for a Formex model, definition of the elements (nelems,nplex)
      for a Mesh model.
    - `color`: either None or an RGB color array with shape (3,), (nelems,3)
      or (nelems,nplex,3).
    - `objtype`: OpenGL drawing mode. The default (-1) will select the
      appropriate value depending on the plexitude of the elements:
      1: point, 2: line, 3: triangle, 4: quad, >4: polygon.
      This value can be set to GL.GL_LINE_LOOP to draw the element's
      circumference independent from the drawing mode.
    """
    pf.debug("drawPolygons", pf.DEBUG.DRAW)
    if e is None:
        nelems = x.shape[0]
    else:
        nelems = e.shape[0]
    n = None
    #print("LIGHTING %s, AVGNORMALS %s" % (lighting,avgnormals))
    if lighting and objtype==-1:
        if normals is None:
            pf.debug("Computing normals", pf.DEBUG.DRAW)
            if avgnormals and e is not None:
                n = geomtools.averageNormals(x, e, treshold=pf.cfg['render/avgnormaltreshold'])
            else:
                if e is None:
                    n = geomtools.polygonNormals(x)
                else:
                    n = geomtools.polygonNormals(x[e])
                #pf.debug("NORMALS:%s" % str(n.shape),pf.DEBUG.DRAW)
        else:
            #print("NORMALS=%s"% normals)
            n = checkArray(normals, (nelems, -1, 3), 'f')

    # Texture
    if texture is not None:
        glTexture(texture)
        if t is None:
            t = array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]])
    else:
        t = None


    # Sanitize data before calling library function
    x = x.astype(float32)
    if e is not None:
        e = e.astype(int32)
    if n is not None:
        n = n.astype(float32)
    if color is not None:
        color = color.astype(float32)
        pf.debug("COLORS:%s" % str(color.shape), pf.DEBUG.DRAW)
        if color.shape[-1] != 3 or (
            color.ndim > 1 and color.shape[0] != nelems) :
            pf.debug("INCOMPATIBLE COLOR SHAPE: %s, while nelems=%s" % (str(color.shape), nelems), pf.DEBUG.DRAW)
            color = None
    if t is not None:
        t = t.astype(float32)

    # Call library function
    if e is None:
        drawgl.draw_polygons(x, n, color, t, alpha, objtype)
        #multi_draw_polygons(x,n,color,t,alpha,objtype)
    else:
        drawgl.draw_polygon_elems(x, e, n, color, t, alpha, objtype)




def drawBezier(x,color=None,objtype=GL.GL_LINE_STRIP,granularity=100):
    """Draw a collection of Bezier curves.

    x: (4,3,3) : control points
    color: (4,) or (4,4): colors
    """
    GL.glMap1f(GL.GL_MAP1_VERTEX_3, 0.0, 1.0, x)
    GL.glEnable(GL.GL_MAP1_VERTEX_3)
    if color is not None and color.shape == (4, 4):
        GL.glMap1f(GL.GL_MAP1_COLOR_4, 0.0, 1.0, color)
        GL.glEnable(GL.GL_MAP1_COLOR_4)

    u = arange(granularity+1) / float(granularity)
    if color is not None and color.shape == (4,):
        GL.glColor4fv(color)
        color = None

    GL.glBegin(objtype)
    for ui in u:
        #  For multicolors, this will generate both a color and a vertex
        GL.glEvalCoord1f(ui)
    GL.glEnd()

    GL.glDisable(GL.GL_MAP1_VERTEX_3)
    if color is not None:
        GL.glDisable(GL.GL_MAP1_COLOR_4)


def drawBezierPoints(x,color=None,granularity=100):
    drawBezier(x, color=None, objtype=GL.GL_POINTS, granularity=granularity)


def drawNurbsCurves(x,knots,color=None,alpha=1.0,samplingTolerance=5.0):
    """Draw a collection of Nurbs curves.

    x: (nctrl,ndim) or (ncurve,nctrl,ndim) float array: control points,
       specifying either a single curve or ncurve curves defined by the
       same number of control points. ndim can be 3 or 4. If 4, the 4-th
       coordinate is interpreted as a weight for that point.
    knots: (nknots) or (ncurve,nknots) float array: knot vector, containing the
       parameter values to be used in the nurbs definition. Remark that
       nknots must be larger than nctrl. The order of the curve is
       nknots-nctrl and the degree of the curve is order-1.
       If a single knot vector is given, the same is used for all curves.
       Otherwise, the number of knot vectors must match the number of nurbs
       curves.

    If color is given it is an (ncurves,3) array of RGB values.
    """
    nctrl, ndim = x.shape[-2:]
    nknots = asarray(knots).shape[-1]
    order = nknots-nctrl
    if  order > 8:
        utils.warn("warn_nurbs_curve")
        return

    if x.ndim == 2:
        x = x.reshape(-1, nctrl, ndim)
        if color is not None and color.ndim == 2:
            color = color.reshape(-1, nctrl, color.shape[-1])

    if color is not None:
        pf.debug('Coords shape: %s' % str(x.shape), pf.DEBUG.DRAW)
        pf.debug('Color shape: %s' % str(color.shape), pf.DEBUG.DRAW)
        if color.ndim == 1:
            pf.debug('Single color', pf.DEBUG.DRAW)
        elif color.ndim == 2 and color.shape[0] == x.shape[0]:
            pf.debug('Element color: %s colors' % color.shape[0], pf.DEBUG.DRAW)
        elif color.shape == x.shape[:-1] + (3,):
            pf.debug('Vertex color: %s colors' % str(color.shape[:-1]), pf.DEBUG.DRAW)
        else:
            raise ValueError("Number of colors (%s) should equal 1 or the number of curves(%s) or the number of curves * number of vertices" % (color.shape[0], x.shape[0]))

        pf.debug("Color shape = %s" % str(color.shape), pf.DEBUG.DRAW)
        if color.shape[-1] not in (3, 4):
            raise ValueError("Expected 3 or 4 color components")

    if color is not None:
        pf.debug("Final Color shape = %s" % str(color.shape), pf.DEBUG.DRAW)

    nurb = GLU.gluNewNurbsRenderer()
    if not nurb:
        raise RuntimeError("Could not create a new NURBS renderer")

    GLU.gluNurbsProperty(nurb, GLU.GLU_SAMPLING_TOLERANCE, samplingTolerance)

    mode = {3:GL.GL_MAP1_VERTEX_3, 4:GL.GL_MAP1_VERTEX_4}[ndim]

    if color is not None and color.ndim == 1:
        # Handle single color
        pf.debug('Set single color: OK', pf.DEBUG.DRAW)
        drawgl.glColor(color)
        color = None

    ki = knots
    for i, xi in enumerate(x):
        if color is not None and color.ndim == 2:
            # Handle element color
            drawgl.glColor(color[i])
        if knots.ndim > 1:
            ki = knots[i]
        GLU.gluBeginCurve(nurb)
        if color is not None and color.ndim == 3:
            # Handle vertex color
            ci = color[i]
            if ci.shape[-1] == 3:
                # gluNurbs always wants 4 colors
                ci = growAxis(ci, 1, axis=-1, fill=alpha)
            GLU.gluNurbsCurve(nurb, ki, ci, GL.GL_MAP1_COLOR_4)
        GLU.gluNurbsCurve(nurb, ki, xi, mode)
        GLU.gluEndCurve(nurb)

    GLU.gluDeleteNurbsRenderer(nurb)


def drawQuadraticCurves(x,e=None,color=None,alpha=1.0):
    """Draw a collection of quadratic curves.

    The geometry is specified by x or (x,e).
    x or x[e] is a (nlines,3,3) shaped array of coordinates.
    For each element a quadratic curve through its 3 points is drawn.

    This uses the drawNurbsCurves function for the actual drawing.
    The difference between drawQuadraticCurves(x) and drawNurbsCurves(x)
    is that in the former, the middle point is laying on the curve, while
    in the latter case, the middle point defines the tangents in the end
    points.

    If color is given it is an (nlines,3) array of RGB values.
    """
    pf.debug("drawQuadraticCurves", pf.DEBUG.DRAW)
    if e is None:
        #print("X SHAPE %s" % str(x.shape))
        nelems, nfaces, nplex = x.shape[:3]
        x = x.reshape(-1, nplex, 3)
    else:
        if e.ndim == 3:
            nelems, nfaces, nplex = e.shape
            e = e.reshape(-1, nplex)
        elif e.ndim == 2:
            nelems, nplex = e.shape
            nfaces = 1
        else:
            raise ValueError("Can not handle elems with shape: %s" % str(e.shape))

    if color is not None:
        if color.ndim == 2:
            pf.debug("COLOR SHAPE BEFORE MULTIPLEXING %s" % str(color.shape), pf.DEBUG.DRAW)
            color = multiplex(color, nfaces).reshape(-1, 3)
            pf.debug("COLOR SHAPE AFTER  MULTIPLEXING %s" % str(color.shape), pf.DEBUG.DRAW)
        if color.ndim > 2:
            color = color.reshape((nelems*nfaces,) + color.shape[-2:]).squeeze()
            pf.debug("COLOR SHAPE AFTER RESHAPING %s" % str(color.shape), pf.DEBUG.DRAW)

    if e is None:
        xx = x.copy()
    else:
        xx = x[e]

    #print xx.shape
    #print xx
    xx[..., 1,:] = 2*xx[..., 1,:] - 0.5*(xx[..., 0,:] + xx[..., 2,:])
    #print xx.shape
    #print xx
    knots = array([0., 0., 0., 1., 1., 1.])
    drawNurbsCurves(xx, knots, color=color, alpha=alpha)


_nurbs_renderers_ = []
def drawNurbsSurfaces(x,sknots,tknots,color=None,alpha=1.0,normals='auto',samplingTolerance=20.0):
    """Draw a collection of Nurbs surfaces.

    x: (ns,nt,ndim) or (nsurf,ns,nt,ndim) float array:
       (ns,nt) shaped control points array,
       specifying either a single surface or nsurf surfaces defined by the
       same number of control points. ndim can be 3 or 4. If 4, the 4-th
       coordinate is interpreted as a weight for that point.
    sknots: (nsk) or (nsurf,nsk) float array: knot vector, containing
       the parameter values to be used in the s direction of the surface.
       Remark that nsk must be larger than ns. The order of the surface
       in s-direction is nsk-ns and the degree of the s-curves is nsk-ns-1.
       If a single sknot vector is given, the same is used for all surfaces.
       Otherwise, the number of sknot vectors must match the number of nurbs
       surfaces.
    tknots: (ntk) or (nsurf,ntk) float array: knot vector, containing
       the parameter values to be used in the t direction of the surface.
       Remark that ntk must be larger than nt. The order of the surface
       in t-direction is ntk-nt and the degree of the t-curves is ntk-nt-1.
       If a single sknot vector is given, the same is used for all surfaces.
       Otherwise, the number of sknot vectors must match the number of nurbs
       surfaces.

    If color is given it is an (nsurf,3) array of RGB values.
    """
    from pyformex import timer
    t = timer.Timer()

    ns, nt, ndim = x.shape[-3:]
    nsk = asarray(sknots).shape[-1]
    ntk = asarray(tknots).shape[-1]
    sorder = nsk-ns
    torder = ntk-nt
    if sorder > 8 or torder > 8:
        utils.warn("warn_nurb_surface")
        return

    if x.ndim == 3:
        x = x.reshape(-1, ns, nt, ndim)
        if color is not None and color.ndim == 3:
            color = color.reshape(-1, ns, nt, color.shape[-1])

    if color is not None:
        pf.debug('Coords shape: %s' % str(x.shape), pf.DEBUG.DRAW)
        pf.debug('Color shape: %s' % str(color.shape), pf.DEBUG.DRAW)
        if color.ndim == 1:
            pf.debug('Single color', pf.DEBUG.DRAW)
        elif color.ndim == 2 and color.shape[0] == x.shape[0]:
            pf.debug('Element color: %s' % color.shape[0], pf.DEBUG.DRAW)
        elif color.shape == x.shape[:-1] + (3,):
            pf.debug('Vertex color: %s' % str(color.shape[:-1]), pf.DEBUG.DRAW)
        else:
            raise ValueError("Number of colors (%s) should equal 1 or the number of faces(%s) or the number of faces * number of vertices" % (color.shape[0], x.shape[0]))

        pf.debug("Color shape = %s" % str(color.shape), pf.DEBUG.DRAW)
        if color.shape[-1] not in (3, 4):
            raise ValueError("Expected 3 or 4 color components")

    if normals == 'auto':
        GL.glEnable(GL.GL_AUTO_NORMAL)
    else:
        GL.glDisable(GL.GL_AUTO_NORMAL)

    # The following uses:
    # x: (nsurf,ns,nt,4)
    # sknots: (nsknots) or (nsurf,nsknots)
    # tknots: (ntknots) or (nsurf,ntknots)
    # color: None or (4) or (nsurf,4) or (nsurf,ns,nt,4)
    # samplingTolerance

    if pf.options.fastnurbs:
        alpha=0.5
        x = x.astype(float32)
        sknots = sknots.astype(float32)
        tknots = tknots.astype(float32)
        if color is not None:
            color = color.astype(float32)

            if color.shape[-1] == 3:
                # gluNurbs always wants 4 colors
                color = growAxis(color, 3, axis=-1, fill=alpha)

        nb = drawgl.draw_nurbs_surfaces(x, sknots, tknots, color, alpha, samplingTolerance)

    else:
        nurb = GLU.gluNewNurbsRenderer()
        if not nurb:
            raise RuntimeError("Could not create a new NURBS renderer")

        GLU.gluNurbsProperty(nurb, GLU.GLU_SAMPLING_TOLERANCE, samplingTolerance)

        mode = {3:GL.GL_MAP2_VERTEX_3, 4:GL.GL_MAP2_VERTEX_4}[ndim]

        if color is not None and color.ndim == 1:
            # Handle single color
            pf.debug('Set single color: OK', pf.DEBUG.DRAW)
            drawgl.glColor(color)
            color = None

        si = sknots
        ti = tknots
        for i, xi in enumerate(x):
            if color is not None and color.ndim == 2:
                # Handle element color
                drawgl.glColor(color[i])
            if sknots.ndim > 1:
                si = sknots[i]
            if tknots.ndim > 1:
                ti = tknots[i]
            GLU.gluBeginSurface(nurb)
            if color is not None and color.ndim == 4:
                # Handle vertex color
                ci = color[i]
                if ci.shape[-1] == 3:
                    # gluNurbs always wants 4 colors
                    ci = growAxis(ci, 1, axis=-1, fill=alpha)
                GLU.gluNurbsSurface(nurb, si, ti, ci, GL.GL_MAP2_COLOR_4)
            GLU.gluNurbsSurface(nurb, si, ti, xi, mode)
            GLU.gluEndSurface(nurb)

        GLU.gluDeleteNurbsRenderer(nurb)

    print("drawNurbsSurfaces: %s seconds" % t.seconds())


def quad4_quad8(x):
    """_Convert an array of quad4 surfaces to quad8"""
    y = roll(x, -1, axis=-2)
    x5_8 = (x+y)/2
    return concatenate([x, x5_8], axis=-2)

def quad8_quad9(x):
    """_Convert an array of quad8 surfaces to quad9"""
    x9 = x[..., :4,:].sum(axis=-2)/2 - x[..., 4:,:].sum(axis=-2)/4
    return concatenate([x, x9[..., newaxis,:]], axis=-2)


def drawQuadraticSurfaces(x,e,color=None):
    """Draw a collection of quadratic surfaces.

    The geometry is specified by x or (x,e).
    x or x[e] is a (nsurf,nquad,3) shaped array of coordinates, where
    nquad is either 4,6,8 or 9
    For each element a quadratic surface through its nquad points is drawn.

    This uses the drawNurbsSurfaces function for the actual drawing.
    The difference between drawQuadraticSurfaces(x) and drawNurbsSurfaces(x)
    is that in the former, the internal point is laying on the surface, while
    in the latter case, the middle point defines the tangents in the middle
    points of the sides.

    If color is given it is an (nsurf,3) array of RGB values.
    """
    from pyformex import timer
    t = timer.Timer()
    pf.debug("drawQuadraticSurfaces", pf.DEBUG.DRAW)
    if e is None:
        nelems, nfaces, nplex = x.shape[:3]
        x = x.reshape(-1, nplex, 3)
    else:
        nelems, nfaces, nplex = e.shape[:3]
        e = e.reshape(-1, nplex)

    if color is not None:
        pf.debug('Color shape: %s' % str(color.shape), pf.DEBUG.DRAW)
        if color.ndim == 2:
            pf.debug("COLOR SHAPE BEFORE MULTIPLEXING %s" % str(color.shape), pf.DEBUG.DRAW)
            color = multiplex(color, nfaces).reshape(-1, 3)
            pf.debug("COLOR SHAPE AFTER  MULTIPLEXING %s" % str(color.shape), pf.DEBUG.DRAW)
        if color.ndim > 2:
            # BV REMOVED squeeze: may break some things
            color = color.reshape((nelems*nfaces,) + color.shape[-2:])#.squeeze()
            pf.debug("COLOR SHAPE AFTER RESHAPING %s" % str(color.shape), pf.DEBUG.DRAW)

    if e is None:
        xx = x.copy()
    else:
        xx = x[e]

    # Draw quad4 as quad4
    if xx.shape[-2] == 4:
        # Bilinear surface
        knots = array([0., 0., 1., 1.])
        xx = xx[..., [0, 3, 1, 2],:]
        xx = xx.reshape(-1, 2, 2, xx.shape[-1])
        if color is not None and color.ndim > 2:
            color = color[..., [0, 3, 1, 2],:]
            color = color.reshape(-1, 2, 2, color.shape[-1])
        drawNurbsSurfaces(xx, knots, knots, color)
        return

    # Convert quad8 to quad9
    if xx.shape[-2] == 8:
        xx = quad8_quad9(xx)

    # Convert quad9 to nurbs node order
    xx = xx[..., [0, 7, 3, 4, 8, 6, 1, 5, 2],:]
    xx = xx.reshape(-1, 3, 3, xx.shape[-1])
    if color is not None and color.ndim > 2:
        pf.debug("INITIAL COLOR %s" % str(color.shape), pf.DEBUG.DRAW)
        if color.shape[-2] == 8:
            color = quad8_quad9(color)
        color = color[..., [0, 7, 3, 4, 8, 6, 1, 5, 2],:]
        color = color.reshape(-1, 3, 3, color.shape[-1])
        pf.debug("RESHAPED COLOR %s" % str(color.shape), pf.DEBUG.DRAW)

    xx[..., 1,:] = 2*xx[..., 1,:] - 0.5*(xx[..., 0,:] + xx[..., 2,:])
    xx[..., 1,:,:] = 2*xx[..., 1,:,:] - 0.5*(xx[..., 0,:,:] + xx[..., 2,:,:])
    knots = array([0., 0., 0., 1., 1., 1.])
    drawNurbsSurfaces(xx, knots, knots, color)
    print("drawQuadraticSurfaces: %s seconds" % t.seconds())


def draw_faces(x,e,color=None,alpha=1.0,texture=None,texc=None,normals=None,lighting=False,avgnormals=False,objtype=-1):
    """Draw a collection of faces.

    (x,e) are one of:
    - x is a (nelems,nfaces,nplex,3) shaped coordinates and e is None,
    - x is a (ncoords,3) shaped coordinates and e is a (nelems,nfaces,nplex)
    connectivity array.

    Each of the nfaces sets of nplex points defines a polygon.

    If color is given it is either an (3,), (nelems,3), (nelems,faces,3)
    or (nelems,faces,nplex,3) array of RGB values.
    In the second case, this function will multiplex the colors, so that
    `nfaces` faces are drawn in the same color.
    This is e.g. convenient when drawing faces of a solid element.
    """
    pf.debug("draw_faces", pf.DEBUG.DRAW)
    if e is None:
        nelems, nfaces, nplex = x.shape[:3]
        x = x.reshape(-1, nplex, 3)
    else:
        nelems, nfaces, nplex = e.shape[:3]
        e = e.reshape(-1, nplex)

    if color is not None:
        if color.ndim == 2:
            pf.debug("COLOR SHAPE BEFORE MULTIPLEXING %s" % str(color.shape), pf.DEBUG.DRAW)
            color = multiplex(color, nfaces).reshape(-1, 3)
            pf.debug("COLOR SHAPE AFTER  MULTIPLEXING %s" % str(color.shape), pf.DEBUG.DRAW)
        if color.ndim > 2:
            color = color.reshape((nelems*nfaces,) + color.shape[-2:]).squeeze()
            pf.debug("COLOR SHAPE AFTER RESHAPING %s" % str(color.shape), pf.DEBUG.DRAW)

    drawPolygons(x, e, color, alpha, texture, texc, normals, lighting, avgnormals, objtype=objtype)



### End
