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
"""View and manipulate 3D models in your browser.

This module defines some classes and function to help with the creation
of WebGL models. A WebGL model can be viewed directly from a compatible
browser (see http://en.wikipedia.org/wiki/WebGL).

A WebGL model typically consists out of an HTML file and a Javascript file,
possibly also some geometry data files. The HTML file is loaded in the
browser and starts the Javascript program, responsible for rendering the
WebGL scene.
"""
from __future__ import print_function

import pyformex as pf
from gui import colors
import utils
from olist import List, intersection
from mydict import Dict
import os
from numpy import asarray,arange,int32
from arraytools import checkFloat,checkArray,checkInt
from mesh import Mesh


# Formatting a controller for an attribute
#   %N will be replaced with name of object,
#   %A will be replaced with name of attribute,

controller_format = {
    'visible': "add(%N,'%A')",
    'opacity': "add(%N,'%A',0,1)",
    'color': "addColor(%N,'%A')"
}


def saneSettings(k):
    """Sanitize sloppy settings for JavaScript output"""
    ok = {}
    try:
        ok['color'] = checkArray(k['color'],(3,),'f')
    except:
        try:
            c = checkInt(k['color'][0])
            print("COLOR INDEX %s" % c)
            colormap = pf.canvas.settings.colormap
            ok['color'] = colormap[c % len(colormap)]
        except:
            print("Unexpected color: %s" % k['color'])

    try:
        ok['alpha'] = checkFloat(k['alpha'],0.,1.)
    except:
        pass
    try:
        ok['caption'] = str(k['caption'])
    except:
        pass
    try:
        ok['control'] = intersection(k['control'],controller_format.keys())
    except:
        pass
    return ok


def properties(o):
    """Return properties of an object

    properties are public attributes (not starting with an '_') that
    are not callable.
    """
    keys = [ k for k in sorted(dir(o)) if not k.startswith('_') and not callable(getattr(o,k)) ]
    return utils.selectDict(o.__dict__,keys)



class WebGL(List):
    """A 3D geometry model for export to WebGL.

    The WebGL class provides a limited model to be easily exported as
    a complete WebGL model, including the required HTML, Javascript
    and data files.

    Currently the following features are included:

    - create a new WebGL model
    - add the current scene to the model
    - add Geometry to the model (including color and transparency)
    - set the camera position
    - export the model

    An example of its usage can be found in the WebGL example.

    The create model uses the XTK toolkit from http://www.goXTK.com.
    """

    def __init__(self,name='Scene1'):
        """Create a new (empty) WebGL model."""
        List.__init__(self)
        self._camera = None
        if pf.cfg['webgl/devel']:
            self.scripts = [
                os.path.join(pf.cfg['webgl/devpath'],'lib/closure-library/closure/goog/base.js'),
                os.path.join(pf.cfg['webgl/devpath'],'xtk-deps.js')
                ]
        else:
            self.scripts = [ pf.cfg['webgl/xtkscript'], pf.cfg['webgl/guiscript'] ]
        print("WebGL scripts: %s" % self.scripts)
        self.gui = []
        self.name = str(name)


    def objdict(self,clas=None):
        """Return a dict with the objects in this model.

        Returns a dict with the name:object pairs in the model. Objects
        that have no name are disregarded.
        """
        obj = [ o for o in self if hasattr(o,'name') ]
        if clas:
            obj = [ o for o in obj if isinstance(o,clas) ]
        print("OBJDICT: %s" % len(obj))
        print([type(o) for o in obj])
#        print(obj)
        return obj


    def addScene(self):
        """Add the current OpenGL scene to the WebGL model.

        This method add all the geometry in the current viewport to
        the WebGL model.
        """
        cv = pf.canvas
        print("Exporting %s actors from current scene" % len(cv.actors))
        for i,a in enumerate(cv.actors):
            o = a.object
            atype = type(a).__name__
            otype = type(o).__name__
            #print("Actor %s: %s %s Shape=(%s,%s) Color=%s"% (i,atype,otype,o.nelems(),o.nplex(),a.color))
            self.addActor(a)
        ca = cv.camera
##        self.camera(focus=[0.,0.,0.],position=ca.eye-ca.focus,up=ca.upvector)
        self.camera(focus=ca.focus,position=ca.eye,up=ca.upvector)


    def addActor(self,actor):
        """Add an actor to the model.
        
        The actor's drawable objects are added to the WebGL model
        as a list.
        The actor's controller attributes are added to the controller gui.
        """
        from attributes import Attributes
        drawables = []
        controllers = []
        # add drawables
        for i,d in enumerate(actor.drawable):
            attrib = Attributes(d,default=actor)
            coords = asarray(attrib.vbo)
            if attrib.ibo is not None:
                elems = asarray(attrib.ibo)
            else:
                nelems,nplex = coords.shape[:2]
                elems = arange(nelems*nplex).reshape(nelems,nplex).astype(int32)
            coords = coords.reshape(-1,3)
            obj = Mesh(coords,elems)
            if attrib.nbo is not None:
                normals = asarray(attrib.nbo).reshape(-1,3)
                obj.setNormals(normals[elems])
            if attrib.cbo is not None:
                colors = asarray(attrib.cbo).reshape(-1,3)
                obj.color = colors[elems]
            attrib.file = '%s_%s.pgf' % (self.name,attrib.name)
            from geometry import Geometry
            Geometry.write(obj,attrib.file,'')
            drawables.append(attrib)
        self.append(drawables)
        # add controllers
        if actor.control is not None:
            control = actor.control
        elif pf.cfg['webgl/autogui']:
            # Add autogui
##            control = controller_format.keys()
            control = []
            for name in ['frontfaces','backfaces','faces','edges','wires'] :
                control.extend(['show '+name,name[:-1]+' opacity',name[:-1]+' color'])
        if len(control) > 0:
            for attrib in drawables:
                name = attrib.name.split('_')[-1]
                if 'show ' + name in control:
                    controllers.append((attrib.name,'show ' + name,'visible'))
                if name[:-1] + ' opacity' in control:
                    controllers.append((attrib.name,name[:-1] + ' opacity','opacity'))
                if name[:-1] + ' color' in control and attrib.colormode < 2:
                    controllers.append((attrib.name,name[:-1] + ' color','color'))
        if len(controllers) > 0:
            self.gui.append((actor.name,actor.caption,controllers))


    def camera(self,**kargs):
        """Set the camera position and direction.

        This takes two (optional) keyword parameters:

        - `position=`: specify a list of 3 coordinates. The camera will
          be positioned at that place, and be looking at the origin.
          This should be set to a proper distance from the scene to get
          a decent result on first display.
        - `upvector=`: specify a list of 3 components of a vector indicating
          the upwards direction of the camera. The default is [0.,1.,0.].
        """
        self._camera = Dict(kargs)


    def format_actor(self,actor):
        """Export an actor in XTK Javascript format."""
        s = ""
        for attrib in actor:
            name = attrib.name
            s += "var %s = new X.mesh();\n" % name
            if attrib.file is not None:
                s += "%s.file = '%s';\n" % (name,attrib.file)
            if attrib.caption is not None:
                s += "%s.caption = '%s';\n" % (name,attrib.caption)
            if attrib.colormode < 2:
                if attrib.color is not None:
                    s += "%s.color = %s;\n" % (name,list(attrib.color))
                else:
                    s += "%s.color = %s;\n" % (name,list(pf.canvas.settings.fgcolor))
            if attrib.alpha is not None:
                s += "%s.opacity = %s;\n" % (name,attrib.alpha)
            else:
                s += "%s.opacity = %s;\n" % (name,pf.canvas.settings.transparency)
            if attrib.lighting is not None:
                s += "%s.lighting = %s;\n" % (name,str(bool(attrib.lighting)).lower())
            else:
                s += "%s.lighting = %s;\n" % (name,str(bool(pf.canvas.settings.lighting)).lower())
            if attrib.cullface is not None:
                s += "%s.cullface = '%s';\n" % (name,attrib.cullface)
            if attrib.magicmode is not None:
                s += "%s.magicmode = '%s';\n" % (name,str(bool(attrib.magicmode)).lower())
            s += "r.add(%s);\n\n" % name
        return s


    def format_gui_controller(self,name,attr):
        """Format a single controller"""
        if attr in controller_format:
            return controller_format[attr].replace('%N',name).replace('%A',attr)
        else:
            raise ValueError,"Controller for attribute '%s' not implemented"


    def format_gui(self):
        """Create the controller GUI script"""
        s = """
r.onShowtime = function() {
var gui = new dat.GUI();
"""
        for name,caption,attrs in self.gui:
            guiname = "gui_%s" % name
            if not caption:
                caption = name
            s += "var %s = gui.addFolder('%s');\n" % (guiname,caption)
            for objname,name,attr in attrs:
                cname = "%s_%s" % (guiname,"".join(name.split()))
                s += "var %s = %s.%s.name('%s');\n" % (cname,guiname,self.format_gui_controller(objname,attr),name)
            #s += "%s.open();\n" % guiname


        # add camera gui
        guiname = "gui_camera"
        s += """
var %s = gui.addFolder('Camera');
var %s_reset = %s.add(r.camera,'reset');
""".replace('%s',guiname)


        s += "}\n"
        return s


    def exportPGF(self,fn,sep=''):
        """Export the current scene to a pgf file"""
        from plugins.geometry_menu import writeGeometry
        res = writeGeometry(self.objdict(),fn,sep=sep)
        return res


    def export(self,name=None,title=None,description=None,keywords=None,author=None,createdby=False):
        """Export the WebGL scene.

        Parameters:

        - `name`: a string that will be used for the filenames of the
          HTML, JS and STL files.
        - `title`: an optional title to be set in the .html file. If not
          specified, the `name` is used.

        You can also set the meta tags 'description', 'keywords' and
        'author' to be included in the .html file. The first two have
        defaults if not specified.

        Returns the name of the exported htmlfile.
        """
        if name is None:
            name = self.name
        if title is None:
            title = '%s WebGL example, created by pyFormex' % name
        if description is None:
            description = title
        if keywords is None:
            keywords = "pyFormex, WebGL, XTK, HTML, JavaScript"

        s = """// Script generated by %s

window.onload = function() {
var r = new X.renderer3D();
r.config.ORDERING_ENABLED = false;
r.init();

""" % pf.fullVersion()
        s += '\n'.join([self.format_actor(a) for a in self ])
        if self.gui:
            s += self.format_gui()
        if self._camera:
            s += '\n'
            if 'position' in self._camera:
                s +=  "r.camera.position = %s;\n" % list(self._camera.position)
            if 'focus' in self._camera:
                s +=  "r.camera.focus = %s;\n" % list(self._camera.focus)
            if 'up' in self._camera:
                s +=  "r.camera.up = %s;\n" % list(self._camera.up)
        s += """
r.render();
};
"""
        jsname = utils.changeExt(name,'.js')
        with open(jsname,'w') as jsfile:
            jsfile.write(s)
        print("Exported WebGL script to %s" % os.path.abspath(jsname))

        # TODO: setting DOCTYTPE makes browser initial view not good
        # s = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
        s = """<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<meta name="generator" content="%s">
<meta name="description" content="%s">
<meta name="keywords" content="%s">
""" % (pf.fullVersion(),description,keywords)
        if author:
            s += '<meta name="author" content="%s">\n' % author
        s += "<title>%s</title>\n" % title

        if self.gui:
            self.scripts.append(pf.cfg['webgl/guiscript'])
        self.scripts.append(jsname)

        for scr in self.scripts:
            s += '<script type="text/javascript" src="%s"></script>\n' % scr

        s += """
</head>
<body>"""
        if createdby:
            if type(createdby) is int:
                width = ' width="%s%%"' % createdby
            else:
                width = ''
            s += """<div id='pyformex' style='position:absolute;top:10px;left:10px;'>
<a href='http://pyformex.org' target=_blank><img src='http://pyformex.org/images/pyformex_createdby.png' border=0%s></a>
</div>""" % width
        s += """</body>
</html>
"""
        htmlname = utils.changeExt(jsname,'.html')
        with open(htmlname,'w') as htmlfile:
            htmlfile.write(s)
        print("Exported WebGL model to %s" % os.path.abspath(htmlname))

        return htmlname


def surface2webgl(S,name,caption=None):
    """Create a WebGL model of a surface

    - `S`: TriSurface
    - `name`: basename of the output files
    - `caption`: text to use as caption
    """
    W = WebGL()
    W.add(obj=S,file=name)
    s = S.dsize()
    W.view(position=[0.,0.,s])
    W.export(name,caption)


# End
