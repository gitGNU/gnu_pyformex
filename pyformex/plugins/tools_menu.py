# $Id$
##
##  This file is part of pyFormex 1.0.2  (Thu Jun 18 15:35:31 CEST 2015)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2015 (C) Benedict Verhegghe (benedict.verhegghe@feops.com)
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

"""tools_menu.py

Graphic Tools plugin menu for pyFormex.
"""
from __future__ import print_function

import pyformex as pf
from pyformex import utils
from pyformex.gui import menu
from pyformex.plugins import objects

from pyformex.formex import *
from pyformex.gui.draw import *
from pyformex.plugins.geometry_menu import autoName
from pyformex.plugins.tools import *
from pyformex.trisurface import TriSurface
from pyformex.geomtools import rotationAngle



def editFormex(F, name):
    """Edit a Formex"""
    items = [('coords', repr(array(F.coords)), 'text')]
    if F.prop is not None:
        items.append(('prop', repr(array(F.prop)), 'text'))
    items.append(('eltype', F.eltype))
    res = askItems(items)
    if res:
        x = eval(res['coords'])
        p = res.get('eltype', None)
        if isinstance(p, str):
            p = eval(p)
        e = res['eltype']

        print(x)
        print(p)
        print(e)
        F.__init__(x, F.prop, e)

Formex.edit = editFormex


def command():
    """Execute an interactive command."""
    res = askItems([('command', '', 'text')])
    if res:
        cmd = res['command']
        print("Command: %s" % cmd)
        exec(cmd)

##################### database tools ##########################

def _init_():
    global database, _drawables
    database = pf.GUI.database
    _drawables = pf.GUI.selection['geometry']


def printall():
    """Print all global variable names."""
    print(listAll(sort=True))


def printval():
    """Print selected global variables."""
    database.ask()
    database.printval()


def printbbox():
    """Print selected global variables."""
    database.ask()
    database.printbbox()


def keep_():
    """Forget global variables."""
    database.ask()
    database.keep()


def forget_():
    """Forget global variables."""
    database.ask()
    database.forget()


def create():
    """Create a new global variable with default initial contents."""
    res = askItems([('name', '')])
    if res:
        name = res['name']
        if name in database:
            warning("The variable named '%s' already exists!")
        else:
            export({name:'__initial__'})


def edit():
    """Edit a global variable."""
    database.ask(mode='single')
    F = database.check(single=True)
    if F is not None:
        name = database.names[0]
        if hasattr(F, 'edit'):
            # Call specialized editor
            F.edit(name)
        else:
            # Use general editor
            res = askItems([(name, repr(F), 'text')])
            if res:
                print(res)
                pf.PF.update(res)


def rename_():
    """Rename a global variable."""
    database.ask(mode='single')
    F = database.check(single=True)
    if F is not None:
        oldname = database.names[0]
        res = askItems([('Name', oldname)], caption = 'Rename variable')
        if res:
            name = res['Name']
            export({name:F})
            database.forget()
            database.set(name)


def delete_all():
    printall()
    if ack("Are you sure you want to unrecoverably delete all global variables?"):
        forgetAll()




def dos2unix():
    fn = askFilename(multi=True)
    if fn:
        for f in fn:
            print("Converting file to UNIX: %s" % f)
            utils.dos2unix(f)


def unix2dos():
    fn = askFilename(multi=True)
    if fn:
        for f in fn:
            print("Converting file to DOS: %s" % f)
            utils.unix2dos(f)



##################### planes ##########################

planes = objects.DrawableObjects(clas=Plane)
pname = autoName(Plane)

def editPlane(plane, name):
    res = askItems([('Point', list(plane.point())),
                    ('Normal', list(plane.normal())),
                    ('Size', (list(plane.size()[0]), list(plane.size()[1])))],
                   caption = 'Edit Plane')
    if res:
        plane.P = res['Point']
        plane.n = res['Normal']
        plane.s = res['Size']

Plane.edit = editPlane


def createPlaneCoordsPointNormal():
    res = askItems([('Name', pname.next()),
                    ('Point', (0., 0., 0.)),
                    ('Normal', (1., 0., 0.)),
                    ('Size', ((1., 1.), (1., 1.)))],
                   caption = 'Create a new Plane')
    if res:
        name = res['Name']
        p = res['Point']
        n = res['Normal']
        s = res['Size']
        P = Plane(p, n, s)
        export({name:P})
        draw(P)


def createPlaneCoords3Points():
    res = askItems([('Name', pname.next()),
                    ('Point 1', (0., 0., 0.)),
                    ('Point 2', (0., 1., 0.)),
                    ('Point 3', (0., 0., 1.)),
                    ('Size', ((1., 1.), (1., 1.)))],
                   caption = 'Create a new Plane')
    if res:
        name = res['Name']
        p1 = res['Point 1']
        p2 = res['Point 2']
        p3 = res['Point 3']
        s = res['Size']
        pts=[p1, p2, p3]
        P = Plane(pts, size=s)
        export({name:P})
        draw(P)


def createPlaneVisual3Points():
    res = askItems([('Name', pname.next()),
                    ('Size', ((1., 1.), (1., 1.)))],
                   caption = 'Create a new Plane')
    if res:
        name = res['Name']
        s = res['Size']
        picked = pick('point')
        pts = getCollection(picked)
        pts = asarray(pts).reshape(-1, 3)
        if len(pts) == 3:
            P = Plane(pts, size=s)
            export({name:P})
            draw(P)
        else:
            warning("You have to pick exactly three points.")


################# Create Selection ###################

selection = None

def set_selection(obj_type, **kargs):
    global selection
    selection = None
    selection = pick(obj_type, **kargs)
    print(selection)


def query(mode):
    set_selection(mode)
    print(report(selection))

def pick_actors():
    set_selection('actor')
def pick_elements():
    print(_drawables.names)
    set_selection('element')
def pick_points(**kargs):
    set_selection('point',  **kargs)
def pick_edges():
    set_selection('edge')

def query_actors():
    query('actor')
def query_elements():
    query('element')
def query_points():
    query('point')
def query_edges():
    query('edge')        
    
def pickSinglePoint():
    """Pick a single point and return Actor index, Actor type, Point index and Point coordinates.
    
    A point is selected with left click and accepted (returned) with right click or ENTER.
    If your selection is empty it asks you to re-select until you get a valid selection.
    You can escape the picking without selecting a point by pushing Cancel on GUI 
    or ESC on Keyboard. In this case a None is returned.
    
    Examples:
    
    A = draw(obj)
    pf.canvas.pickable  = [A] # you can only pick points of obj
    pic = pickSinglePoint()
    pf.canvas.pickable  = None
    """
    while True:
        print ('pick one single point')
        K = pickPoints(filter='single')
        if pf.canvas.selection_accepted == False:
            warning('you want to ESCAPE the picking functionality')
            return None
        elif len(K.keys()) == 1 and len(K[K.keys()[0]]) == 1:
            k = K.keys()[0]
            v = K[k]
            p = v[0]
            A = pf.canvas.actors[k]
            x = A.points()
            return k, A.getType(), p, x[p]
        else:
            showInfo("Invalid picking: try again")


## GDS: in tools.py the reportDistances is no longer used
def query_distances(color='magenta'):
    """Distance of one to many points.
    
    The distance query is repeated until you push on ESC or click on Cancel
    """
    while True:
        s = "*** Distance report *** \n"
        out = pickSinglePoint()
        if out == None:
            break
        Anum, Atype, Pnum, p0 = out
        s += "From actor %s point %s\n" % (Anum, Pnum)
        print ('pick one or multiple points or ESC')
        set_selection('point', filter='single')
        K = selection
        if K == None:
            break        
        s += "To points [x, y, z] magnitude: \n"
        D = []
        for k in K.keys():
            v = K[k]
            A = pf.canvas.actors[k]
            x = A.points()
            for p in v:
                d = x[p] - p0
                ld = length(d)
                s += "actor %s, point %s: [%s, %s, %s] %s \n" % (k, p, d[0], d[1], d[2], ld)
                d=drawMarks([(p0+x[p])*0.5], ['%.2e'%ld], size=20, color=color, bbox='last', view=None)
                D.append([d])
                d=draw(Formex([[p0, x[p]]]), linewidth=3, color=color, bbox='last', view=None)
                D.append([d])
        print (s)
        pause(2.0)
        [undraw(d) for d in D]

## GDS: in tools.py the reportAngles is no longer used
def query_angle(color='magenta'):
    """Angle defined by 3D points.
    
    The angle query is repeated until you push on ESC or click on Cancel
    """
    while True:
        showInfo("Pick 3 points, one at a time or ESC")
        out =  pickSinglePoint()
        if out == None:
            break
        Anum, Atype, Pnum, p0 = out
        out =  pickSinglePoint()
        if out == None:
            break
        Anum, Atype, Pnum, p1 = out
        out =  pickSinglePoint()
        if out == None:
            break
        Anum, Atype, Pnum, p2 = out
        angle, n = rotationAngle(A=p0-p1,B=p2-p1,m=None,angle_spec=DEG)
        angle, n = angle[0], n[0]
        s = "*** Angle report ***\n"
        s += '%s degrees around rotation axis [%s, %s, %s]'%(angle, n[0], n[1], n[2])
        print (s)
        D = []
        d=draw(Formex([[p0, p1]]), linewidth=3, color=color, bbox='last', view=None)
        D.append([d])
        d=draw(Formex([[p1, p2]]), linewidth=3, color=color, bbox='last', view=None)
        D.append([d])
        d=drawMarks([(p0+p2)*0.5], ['%.1f'%angle], size=20, color=color, bbox='last', view=None)
        D.append([d])
        pause(2.0)
        [undraw(d) for d in D]


def getCameraCS(origin='global'):
    """Return the coordinate system of the camera

    origin can be the origin of the global coordinate system (default)
    or the focus of the camera
    """
    cam = pf.canvas.camera
    cz = cam.axis
    cy = cam.upvector
    cx = cross(cy,cz)
    CS = CoordSys(points=Coords([cx, cy, cz, [0.,0.,0.]]))
    if origin == 'global':
        return CS
    elif origin == 'focus':
        return CS.translate(cam.focus)
    else:
        raise ValueError, 'origin should be either global or focus'


def toCameraCS(p):
    """ Reposition a geometry from global to camera coordinate system
    
    Returns:
    - the repositioned geometry
    - the camera coordinate system
    """ 
    camCS = getCameraCS(origin='global')
    return  p.transformCS(CoordSys(), camCS), camCS


def fromCameraCS(p):
    """ Reposition a geometry from camera to global coordinate system
    
    Returns:
    - the repositioned geometry
    - the camera coordinate system
    """ 
    camCS = getCameraCS(origin='global')
    return p.transformCS(camCS,CoordSys()), camCS


def isPerspective():
    import pyformex as pf
    cam = pf.canvas.camera
    return cam.perspective


def create_point():
    """Returns a point anywhere on the screen.
    
    You need the perspective OFF, otherwise it will set it OFF and re-run the function. 
    You can escape the create_point without creating a point by pushing ESC on Keyboard. 
    In this case a None is returned. 
    """
    from pyformex.plugins.tools_menu import isPerspective
    while True:
        print ('left click somewhere on the screen')
        print ('ESC to escape')
        p = pf.canvas.idraw(mode='point', npoints=1, zplane=0., func=None, coords=None, preview=True)
        if pf.canvas.draw_accepted == False:
            warning('you want to ESCAPE the drawing functionality')
            return None
        elif len(p) == 1:
            p = p[0]
            if isPerspective():
                showInfo("You can not pick 2D points if perspective is on. Please re-pick now.")
                perspective(False)
                return create_point()
            else:
                return p
        else:
            showInfo("Invalid drawing: try again")


def query_point2D(color='magenta'):
    """2D point coordinates based on current camera
    
    It prints the horizontal and vertical positions from the global origin 
    along the horizontal and vertical directions of the camera. 
    The horizontal direction of the camera is the cross product of 
    camera axis (focus-eye) and camera upvector. 
    The vertical direction of the camera is the upvector. 
    Push on ESC to terminate, otherwise it repeats.
    """
    while True:
        P = create_point()
        if P==None:
            break
        D0 = draw(P, color=color, bbox='last', view=None)
        p, CS = toCameraCS(P)
        b, c, d = p[0]*CS.u, p[0]*CS.u + p[1]*CS.v, p[1]*CS.v
        D1 = draw(Formex([[CS.o, b], [b, c], [c, d], [d, CS.o]]), color=color, bbox='last', view=None)
        D2 = drawMarks([b*0.5, d*0.5], ['%.2e'%p[0], '%.2e'%p[1]], size=20, color=color, bbox='last', view=None)
        s = "*** Point 2D report ***\n"
        s += 'H %f V %f'%(p[0], p[1])
        print (s)
        pause(2.0)
        [undraw(D) for D in [D0, D1, D2]]


def query_distance2D(color='magenta'):
    """2D distance between 2 points based on current camera
    
    It prints the 2D distance and also the horizontal
    and vertical components based on the current camera.
    Push on ESC to terminate, otherwise it repeats.
    """
    while True:
        print ('starting point')
        p0 = create_point()
        if p0==None:
            break
        p0c, CS0 = toCameraCS(p0)
        h0,v0 = p0c[:2]
        D0 = draw(p0, color=color, bbox='last', view=None)
        print ('end point')
        p1 = create_point()
        if p1==None:
            break
        p1c, CS1 = toCameraCS(p1)
        h1,v1 = p1c[:2]
        D1 = draw(p1, color=color, bbox='last', view=None)
        if abs(CS1.w - CS0.w).sum(axis=0)>1.e-5: # zcam is the camera axis
            warning('You can not perform 2D measurements if you rotate the camera')
            [undraw(D) for D in [D0, D1]]
            return
        d = length(p1-p0)
        print (p0, p1)
        D2=drawMarks([(p0+p1)*0.5], ['%.2e'%d], size=20, color=color, bbox='last', view=None)
        D3=draw(Formex([[p0, p1]]), linewidth=3, color=color, bbox='last', view=None)
        s = "*** Distance 2D report ***\n"
        s += "[H %s, V %s] %s \n" % (h1-h0, v1-v0, d)
        print (s)
        pause(2.0)
        [undraw(D) for D in [D0, D1, D2, D3]]


def query_angle2D(color='magenta'):
    """Planar angle based on current camera plane.
    
    It prints the planar angle on the current camera plane.
    Push on ESC to terminate, otherwise it repeats.
    """
    while True:
        print("Pick 3 points in 2D")
        print("Pick point on first ray")
        p0 = create_point()
        if p0==None:
            break
        w0 = getCameraCS().w
        D0 = draw(p0, color=color, bbox='last', view=None)
        print("Pick the vertex")
        p1 = create_point()
        if p1==None:
            break
        w1 = getCameraCS().w
        D1 = draw(p1, color=color, bbox='last', view=None)
        if abs(w1 - w0).sum(axis=0)>1.e-5:
            warning('You can not perform 2D measurements if you rotate the camera')
            [undraw(D) for D in [D0, D1]]
            return
        print("Pick point on second ray")
        p2 = create_point()
        if p2==None:
            break
        w2 = getCameraCS().w
        D2 = draw(p2, color=color, bbox='last', view=None)
        if abs(w2 - w0).sum(axis=0)>1.e-5:
            warning('You can not perform 2D measurements if you rotate the camera')
            [undraw(D) for D in [D0, D1, D2]]
            return
        angle = rotationAngle(A=p0-p1,B=p2-p1,m=w0,angle_spec=DEG)
        angle = angle[0]
        D3=draw(Formex([[p0, p1]]), linewidth=3, color=color, bbox='last', view=None)
        D4=draw(Formex([[p1, p2]]), linewidth=3, color=color, bbox='last', view=None)
        D5=drawMarks([(p0+p2)*0.5], ['%.1f'%angle], size=20, color=color, bbox='last', view=None)
        s = "*** Angle 2D report ***\n"
        s += '%s degrees around camera axis'%angle
        print (s)
        pause(2.0)
        [undraw(D) for D in [D0, D1, D2, D3, D4, D5]]
 

def report_selection():
    if selection is None:
        warning("You need to pick something first.")
        return
    print(report(selection))


def edit_point(pt):
    x, y, z = pt
    dia = None
    def close():
        dia.close()
    def accept():
        dia.acceptData()
        res = dia.results
        return [ res[i] for i in 'xyz' ]

    dia = widgets.InputDialog(
        items = [_I(x=x, y=y, z=z),]
        )
    dia.show()


def edit_points(K):
    if K.obj_type == 'point':
        for k in K.keys():
            o = pf.canvas.actors[k].object
            n =  _drawables.names[k]
            ind = K[k]
            print("CHANGING points %s of object %s" % (ind, n))
            print(o[ind])


def setpropCollection(K, prop):
    """Set the property of a collection.

    prop should be a single non-negative integer value or None.
    If None is given, the prop attribute will be removed from the objects
    in collection even the non-selected items.
    If a selected object does not have a setProp method, it is ignored.
    """
    if K.obj_type == 'actor':
        obj = [ pf.canvas.actors[i] for i in K.get(-1, []) ]
        for o in obj:
            if hasattr(o, 'setProp'):
                o.setProp(prop)

    elif K.obj_type in ['element', 'point']:
        for k in K.keys():
            a = pf.canvas.actors[k]
            o = a.object
            ## print "SETPROP ACTOR %s" % type(o)
            ## print _drawables
            ## n = _drawables.names[k]
            ## print "SETPROP DRAWABLE %s" % n
            ## O = named(n)
            ## print 'From actor: %s' % id(o)
            ## print 'From name: %s' % id(O)
            ## if id(o) != id(O):
            ##     raise RuntimeError("The id of the drawn object does not match the selection"
            if prop is None:
                o.setProp(prop)
            elif hasattr(o, 'setProp'):
                if not hasattr(o, 'prop') or o.prop is None:
                    o.setProp(0)
                o.prop[K[k]] = prop
                o.setProp(o.prop)
                a.setColor(o.prop)
                ## a.redraw(mode=pf.canvas.rendermode) # GDS this redraw does not exist
                pf.canvas.removeActor([a]) # GDS
                pf.canvas.addActor(a) # GDS


def setprop_selection():
    """Set the property of the current selection.

    A property value is asked from the user and all items in the selection
    that have property have their value set to it.
    """
    if selection is None:
        warning("You need to pick something first.")
        return
    print(selection)
    res = askItems([['property', 0]],
                   caption = 'Set Property Number for Selection (negative value to remove)')
    if res:
        prop = int(res['property'])
        if prop < 0:
            prop = None
        setpropCollection(selection, prop)
        removeHighlight()


def focus_selection(K=None):
    """Focus on the specified or current selection.

    """
    removeHighlight()
    if K is None:
        K = selection
    if K is None:
        warning("You need to pick some points first.")
        return
    print(K)
    if K.obj_type != 'point':
        warning("You need to pick some points first.")
        return
    X = []
    for k in K.keys():
        a = pf.canvas.actors[k]
        o = a.object
        x = o.coords[K[k]]
        X.append(x.center())
    X = Coords(X).center()
    focus(X)


def grow_selection():
    if selection is None:
        warning("You need to pick something first.")
        return
    print(selection)
    res = askItems([('mode', 'node', 'radio', ['node', 'edge']),
                    ('nsteps', 1),
                    ],
                   caption = 'Grow method',
                   )
    if res:
        growCollection(selection,**res)
    print(selection)
    pf.canvas.highlightElements(selection)


def partition_selection():
    """Partition the current selection and show the result."""
    if selection is None:
        warning("You need to pick something first.")
        return
    if not selection.obj_type in ['actor', 'element']:
        warning("You need to pick actors or elements.")
        return
    for A in pf.canvas.actors:
        if not A.getType() == TriSurface:
            warning("Currently I can only partition TriSurfaces." )
            return
    partitionCollection(selection)
    pf.canvas.highlightPartitions(selection)


def get_partition():
    """Select some partitions from the current selection and show the result."""
    if selection is None:
        warning("You need to pick something first.")
        return
    if not selection.obj_type in ['partition']:
        warning("You need to partition the selection first.")
        return
    res = askItems([['property', [1]]],
                 caption='Partition property')
    if res:
        prop = res['property']
        getPartition(selection, prop)
        pf.canvas.highlightPartitions(selection)


def export_selection():
    if selection is None:
        warning("You need to pick something first.")
        return
    sel = getCollection(selection)
    if len(sel) == 0:
        warning("Nothing to export!")
        return
    options = ['List', 'Single items']
    default = options[0]
    if len(sel) == 1:
        default = options[1]
    res = askItems([
        _I('Export with name', ''),
        _I('Export as', default, itemtype='radio', choices=options),
        ])
    if res:
        name = res['Export with name']
        opt = res['Export as'][0]
        if opt == 'L':
            export({name:sel})
        elif opt == 'S':
            export(dict([ (name+"-%s"%i, v) for i, v in enumerate(sel)]))


def actor_dialog():
    print("actor_dialog")
    if selection is None or not selection.obj_type == 'actor':
        warning("You need to pick some actors first.")
        return

    actors = [ pf.canvas.actors[i] for i in selection.get(-1, []) ]
    print("Creating actor dialog for %s actors" % len(actors))
    actorDialog(selection.get(-1, []))


###############################################################

def sendMail():
    from pyformex import sendmail
    sender = pf.cfg['mail/sender']
    if not sender:
        warning("You have to configure your email settings first")
        return

    res = askItems([
        _I('sender', sender, text="From:", readonly=True),
        _I('to', '', text="To:"),
        _I('cc', '', text="Cc:"),
        _I('subject', '', text="Subject:"),
        _I('text', '', itemtype='text', text="Message:"),
       ])
    if not res:
        return

    msg = sendmail.print(**res)
    print(msg)
    to = res['to'].split(',')
    cc = res['cc'].split(',')
    sendmail.sendmail(message=msg, sender=res['sender'], to=to+cc)
    print("Mail has been sent to %s" % to)
    if cc:
        print("  with copy to %s" % cc)

###################### images #############################

def selectImage(extra_items=[]):
    """Open a dialog to read an image file.

    """
    global image
    from pyformex.gui.widgets import ImageView
    from pyformex.plugins.imagearray import resizeImage

    # some default values
    filename = getcfg('datadir')+'/butterfly.png'
    w, h = 200, 200
    image = None # the loaded image
    diag = None # the image dialog

    # construct the image previewer widget
    viewer = ImageView(filename, maxheight=h)

    def select_image(field):
        """Helper function to load and preview image"""
        fn = askImageFile(field.value())
        if fn:
            viewer.showImage(fn)
            load_image(fn)
        return fn

    def load_image(fn):
        """Helper function to load the image and set its size in the dialog"""
        global image
        image = resizeImage(fn)
        if image.isNull():
            warning("Could not load image '%s'" % fn)
            return None

        w, h = image.width(), image.height()
        print("size = %sx%s" % (w, h))

        diag = currentDialog()
        if diag:
            diag.updateData({'nx':w,'ny':h})

        maxsiz = 40000.
        if w*h > maxsiz:
            scale = sqrt(maxsiz/w/h)
            w = int(w*scale)
            h = int(h*scale)
        return w, h

    res = askItems([
        _I('filename', filename, text='Image file', itemtype='button', func=select_image),
        _I('viewer', viewer, itemtype='widget'),  # the image previewing widget
        _I('nx', w, text='width'),
        _I('ny', h, text='height'),
        ] + extra_items)

    if not res:
        return None,None

    if image is None:
        print("Loading image")
        load_image(res['filename'])

    image = resizeImage(image, res['nx'], res['ny'])
    return image, res


def showImage():
    clear()
    im,res = selectImage()
    if im:
        drawImage(im)

def showImage3D():
    clear()
    im, res = selectImage([_I('pixel cell', choices=['dot', 'quad'])])
    if im:
        drawImage3D(im, pixel=res['pixel cell'])


################### menu #################

_menu = 'Tools'

def create_menu():
    """Create the Tools menu."""
    _init_()
    MenuData = [
        ('Global &Variables', [
            ('  &List All', printall),
            ('  &Select', database.ask),
            ('  &Print Value', printval),
            ('  &Print BBox', printbbox),
            ('  &Draw', _drawables.ask),
            ('  &Create', create),
            ('  &Change Value', edit),
            ('  &Rename', rename_),
            ('  &Keep', keep_),
            ('  &Delete', forget_),
            ('  &Delete All', delete_all),
            ]),
        ("---", None),
        ('&Execute pyFormex command', command),
        ("&DOS to Unix", dos2unix, dict(tooltip="Convert a text file from DOS to Unix line terminators")),
        ("&Unix to DOS", unix2dos),
        ("Send &Mail", sendMail),
        ("---", None),
        ("&Create Plane", [
            ("Coordinates",
                [("Point and normal", createPlaneCoordsPointNormal),
                ("Three points", createPlaneCoords3Points),
                ]),
            ("Visually",
                [("Three points", createPlaneVisual3Points),
                ]),
            ]),
        ("&Select Plane", planes.ask),
        ("&Draw Selection", planes.draw),
        ("&Forget Selection", planes.forget),
        ("---", None),
        ("Show an &Image file on the canvas", showImage),
        ("Show an &Image file as Formex", showImage3D),
        ("---", None),
        ('&Pick', [
            ("&Actors", pick_actors),
            ("&Elements", pick_elements),
            ("&Points", pick_points),
            ("&Edges", pick_edges),
            ]),
        ('&With picked', [
            ('&Create Report', report_selection),
            ('&Set Property', setprop_selection),
            ('&Grow', grow_selection),
            ('&Partition', partition_selection),
            ('&Get Partition', get_partition),
            ('&Export', export_selection),
            ('&Focus', focus_selection),
            ('&Actor dialog', actor_dialog),
            ]),
        ('&Edit Points', edit_points),
        ("&Remove Highlights", removeHighlight),
        ("---", None),
        ('&Query', [
            ('&Actors', query_actors),
            ('&Elements', query_elements),
            ('&Points', query_points),
            ('&Edges', query_edges),
            ('&Distances', query_distances),
            ('&Angle', query_angle),
            ('&Point 2D', query_point2D),
            ('&Distance 2D', query_distance2D), 
            ('&Angle 2D', query_angle2D), 
            ]),
        ("---", None),
        ('&Reload', reload_menu),
        ("&Close", close_menu),
        ]
    return menu.Menu(_menu, items=MenuData, parent=pf.GUI.menu, before='help')


def show_menu():
    """Show the menu."""
    if not pf.GUI.menu.item(_menu):
        create_menu()


def close_menu():
    """Close the menu."""
    pf.GUI.menu.removeItem(_menu)


def reload_menu():
    """Reload the menu."""
    close_menu()
    show_menu()


####################################################################
######### What to do when the script is executed ###################

if __name__ == '__draw__':

    reload_menu()

# End
