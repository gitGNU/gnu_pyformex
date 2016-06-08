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
from pyformex import utils
from pyformex.opengl import colors
from pyformex.olist import List, intersection
from pyformex.mydict import Dict
from pyformex.arraytools import checkFloat, checkArray, checkInt
from pyformex.mesh import Mesh
from pyformex.attributes import Attributes
from pyformex.geometry import Geometry

import numpy as np
import os
import glob

exported_webgl = None

# Formatting a controller for an attribute
#   %N will be replaced with name of object,
#   %A will be replaced with name of attribute,

controller_format = {
    'visible': "add(%N,'%A')",
    'opacity': "add(%N,'%A',0,1)",
    'color': "addColor(%N,'%A')"
}

default_control = ['visible', 'opacity', 'color', 'face opacity', 'face color',
    'show edges', 'edge opacity', 'edge color',
    'show wires', 'wire opacity', 'wire color']

def saneSettings(k):
    """Sanitize sloppy settings for JavaScript output"""
    ok = {}
    try:
        ok['color'] = checkArray(k['color'], (3,), 'f')
    except:
        try:
            c = checkInt(k['color'][0])
            print("COLOR INDEX %s" % c)
            colormap = pf.canvas.settings.colormap
            ok['color'] = colormap[c % len(colormap)]
        except:
            print("Unexpected color: %s" % k['color'])

    try:
        ok['alpha'] = checkFloat(k['alpha'], 0., 1.)
    except:
        pass
    try:
        ok['caption'] = str(k['caption'])
    except:
        pass
    try:
        ok['control'] = intersection(k['control'], controller_format.keys())
    except:
        pass
    return ok


def properties(o):
    """Return properties of an object

    properties are public attributes (not starting with an '_') that
    are not callable.
    """
    keys = [ k for k in sorted(dir(o)) if not k.startswith('_') and not callable(getattr(o, k)) ]
    return utils.selectDict(o.__dict__, keys)


class WebGL(object):
    """A class to export a 3D scene to WebGL.

    Exporting a WebGL model creates:

    - a HTML file calling some Javascript files. This file can be viewed
      in a WebGL enabled browser (Firefox, Chrome, Safari)
    - a Javascript file describing the model. This file relies an other
      Javascript files to do the actual rendering and provide control menus.
      The default rendering script is
      http://feops.ugent.be/pub/webgl/fewgl.js and the gui toolkit is
      http://get.goXTK.com/xtk_xdat.gui.js.
      The user can replace them with scripts of his choice.
    - a number of geometry files in pyFormex PGF format. These are normally
      created automatically by the exportScene method. The user can optionally
      add other files.

    An example of its usage can be found in the WebGL example.

    Parameters:

    - `name`: string: the base name for the created HTML and JS files.
    - `scripts`: a list of URLs pointing to scripts that will be needed
      for the rendering of the scene.
    - `bgcolor`: string: the background color of the rendered page. This
      can be the name of a color or a hexadecimal WEB color string like
      '#F0A0F0'.
    - `title`: string: an optional title to be set in the .html file. If not
      specified, the `name` is used.
    - `description`, `keywords`, `author`: strings: if specified, these
      will be added as meta tags to the generated .html file. The first two
      have defaults if not specified.
    - `htmlheader`: string: a string to be included in the header section
      of the exported html file. It should be  al legal html string.
    - `jsheader`: string: a string to be included at the start of
      the javascript file. It should be a legal javascript text.
      Usually, it is only used to insert comments, in which case
      all lines should start with '//', or the whole text should
      be included in a '/*', '*/' pair.
    - `dataformat`: string: the extension of the data files used for storing
      the geometry. This should be an extension supported by the webgl
      rendering script. The default (http://feops.ugent.be/pub/webgl/fewgl.js)
      will always support pyFormex native formats '.pgf' and '.pgf.gz'.
      Some other formats (like .stl) may also be supported, but the use of
      the native formats is prefered, because they are a lot smaller.
      Default is to use the compressed '.pgf.gz' format.
    - `urlprefix`: string: if specified, this string gets prepended to the
      exported .js filename in the .html file, and to the datafiles in the
      exported .js file. This can be used to serve the models from a web
      server, where the html code is generated dynamically and the model
      script and data can not be kept in the same location as the html.
    - `gui`: bool: if True, a gui will be added to the model,
      allowing some features to be changed interactively.
    - `cleanup`: bool: if True, files in the output directory (the current
      work directory) starting with the specified base name and having a name
      structure used by the exported, will be deleted from the file system.
      Currently, this includes files with name patterns NAME.html*, NAME.js*
      NAME_*.pgf* and NAME_*.stl*.

    """

    def __init__(self,
                 name='Scene1',
                 scripts=None,
                 bgcolor='white',
                 title=None,
                 description=None,
                 keywords=None,
                 author=None,
                 htmlheader=None,
                 jsheader=None,
                 pgfheader=None,
                 sep='',
                 dataformat='.pgf.gz',
                 urlprefix=None,
                 gui=True,
                 cleanup=False,
                 ):
        """Create a new (empty) WebGL model."""

        if not scripts:
            if pf.cfg['webgl/devel']:
                scripts = ['fewgl.js' ]
                if gui:
                    scripts.append('xtk_xdat.gui.js')
                scripts = [
                    'file://' + os.path.join(pf.cfg['webgl/devpath'], f)
                    for f in scripts
                    ]
            else:
                scripts = [ pf.cfg['webgl/script'] ]
                if gui:
                    scripts.append(pf.cfg['webgl/guiscript'])
        self.scripts = scripts
        print("WebGL scripts: %s" % self.scripts)
        self.name = str(name)
        if title is None:
            title = 'WebGL model %s, created by pyFormex' % name
        if description is None:
            description = title
        if keywords is None:
            keywords = "pyFormex, WebGL, FEops, XTK, HTML, JavaScript"
        self.title = title
        self.description = description
        self.keywords = keywords
        self.author = author
        self.jsfile = None
        self.htmlheader = htmlheader
        self.jsheader = jsheader
        self.pgfheader = pgfheader
        self.sep = sep
        self.dataformat = dataformat
        self.urlprefix = urlprefix
        self.scenes = []
        if cleanup:
            existing = glob.glob(self.name+'.html') + glob.glob(self.name+'.js') + glob.glob(self.name+'_*.pgf*') + glob.glob(self.name+'_*.stl*')
            print("Removing existing files: %s" % existing)
            for f in existing:
                os.remove(f)


    def addScene(self,name=None,camera=True):
        """Add the current OpenGL scene to the WebGL model.

        This method adds all the geometry in the current viewport to
        the WebGL model. By default it will also add the current camera
        and export the scene as a completed WebGL model with the given
        name.

        Parameters:

        - `name`: a string with the name of the model for the current
          scene. When multiple scenes are exported, they will be identified
          by this name. This name is also used as the basename for the
          exported geometry files. For a single scene export, the name may
          be omitted, and will then be set equal to the name of the WebGL
          exporter. If no name is specified, the model is not exported.
          This allows the user to add more scenes to the same model, and
          then to explicitely export it with :func:`exportScene`.
        - `camera`: bool: if True, sets the current viewport camera as the
          camera in the WebGL model.
        """
        self._actors = List()
        self._gui = []
        self._camera = None

        cv = pf.canvas
        self.bgcolor = cv.settings.bgcolor
        print("Exporting %s actors from current scene" % len(cv.actors))
        sorted_actors = [ a for a in cv.actors if a.opak ] + [ a for a in cv.actors if not a.opak ]
        for i, a in enumerate(sorted_actors):
            o = a.object
            atype = type(a).__name__
            otype = type(o).__name__
            pf.debug("Actor %s: %s %s Shape=(%s,%s) Color=%s"% (i, atype, otype, o.nelems(), o.nplex(), a.color), pf.DEBUG.WEBGL)
            self.addActor(a)

        if camera:
            ca = cv.camera
            self.setCamera(focus=ca.focus, position=ca.eye, up=ca.upvector)

        if name:
            self.exportScene(name)


    def addActor(self, actor):
        """Add an actor to the model.

        The actor's drawable objects are added to the WebGL model
        as a list.
        The actor's controller attributes are added to the controller gui.
        """
        drawables = []
        controllers = []

        # add drawables
        for i, d in enumerate(actor.drawable):
            attrib = Attributes(d, default=actor)
            attrib.file = '%s_s%s_%s%s' % (self.name,len(self.scenes),actor.name,self.dataformat)
            # write the object to a .pgf file
            # we do not store the back faces, reuse the front faces file instead
            if not attrib.name.endswith('_back'):
                coords = np.asarray(attrib.vbo)
                if attrib.ibo is not None:
                    elems = np.asarray(attrib.ibo)
                else:
                    nelems, nplex = coords.shape[:2]
                    elems = np.arange(nelems*nplex).reshape(nelems, nplex).astype(np.int32)
                coords = coords.reshape(-1, 3)
                obj = Mesh(coords, elems)
                if attrib.nbo is not None:
                    normals = np.asarray(attrib.nbo).reshape(-1, 3)
                    obj.setNormals(normals[elems])
                if attrib.cbo is not None:
                    if attrib.useObjectColor != 0:
                        # skip the fake cbo buffer
                        pass
                    else:
                        color = np.asarray(attrib.cbo).reshape(-1, 3)
                        obj.attrib(color=color[elems])
                #print("WRITING %s" % attrib.name)
                Geometry.write(obj, attrib.file, sep=self.sep)

            # add missing attributes
            if attrib.lighting is None:
                attrib.lighting = pf.canvas.settings.lighting
            if attrib.useObjectColor is None:
                attrib.useObjectColor = 1
                attrib.color = pf.canvas.settings.fgcolor
            if attrib.alpha is None:
                attrib.alpha = pf.canvas.settings.transparency
            drawables.append(attrib)

        # add controllers
        if actor.control is not None:
            control = actor.control
        elif pf.cfg['webgl/autogui']:
            # Add autogui
            control = default_control
        if len(control) > 0:
            for attrib in drawables:
                name = attrib.name.split('_')[-1]
                if 'show ' + name in control:
                    controllers.append((attrib.name, 'show ' + name, 'visible'))
                if name[:-1] + ' opacity' in control:
                    controllers.append((attrib.name, name[:-1] + ' opacity', 'opacity'))
                if name[:-1] + ' color' in control and attrib.useObjectColor:
                    controllers.append((attrib.name, name[:-1] + ' color', 'color'))

        # add faces if there are drawables for the front and back faces
        names = [ attrib.name for attrib in drawables ]
        #print("NAMES: %s" % names)
        if actor.name+'_front' in names and actor.name+'_back' in names:
            #print("ADDING FACES CONTROL")
            attrib = Attributes(dict(name=actor.name+'_faces', children=[actor.name+'_front', actor.name+'_back']))
            contr = []
            if 'show faces' in control:
                contr.append((attrib.name, 'show faces', 'visible'))
            if 'face opacity' in control:
                contr.append((attrib.name, 'face opacity', 'opacity'))
                attrib.alpha = drawables[names.index(actor.name+'_front')].alpha
            if 'face color' in control and drawables[names.index(actor.name+'_front')].useObjectColor:
                contr.append((attrib.name, 'face color', 'color'))
                # use frontface color
                attrib.useObjectColor = drawables[names.index(actor.name+'_front')].useObjectColor
                attrib.color = drawables[names.index(actor.name+'_front')].color
            drawables.append(attrib)
            controllers = contr + controllers
            names.remove(actor.name+'_front')
            names.remove(actor.name+'_back')
            names.append(actor.name+'_faces')

        # add actor
        attrib = Attributes(dict(name=actor.name, children=names))
        contr = []
        if 'visible' in control:
            contr.append((attrib.name, 'visible', 'visible'))
        drawables.append(attrib)
        controllers = contr + controllers

        self._actors.append(drawables)
        if len(controllers) > 0:
            self._gui.append((actor.name, actor.caption, controllers))


    def setCamera(self,**kargs):
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


    def format_actor (self, actor):
        """Export an actor in Javascript format for fewgl."""
        s = ""
        for attr in actor:
            name = attr.name
            s += "var %s = new X.mesh();\n" % name
            if len(attr.children) > 0:
                s += "%s.children = new Array();\n" % name
                for child in attr.children:
                    s += "%s.children.push(%s);\n" % (name, child)
            if attr.file is not None:
                if self.urlprefix:
                    url = self.urlprefix + attr.file
                else:
                    url = attr.file
                s += "%s.file = '%s';\n" % (name, url)
            if attr.caption is not None:
                s += "%s.caption = '%s';\n" % (name, attr.caption)
            if attr.useObjectColor == 2 and attr.drawface == -1:
                # we have back faces with different color
                s += "%s.color = %s;\n" % (name, list(attr.objectBkColor))
            elif attr.useObjectColor > 0 and attr.objectColor is not None:
                # front faces or back faces same color as front
                s += "%s.color = %s;\n" % (name, list(attr.objectColor))
            if attr.alpha is not None:
                s += "%s.opacity = %s;\n" % (name, attr.alpha)
            if attr.lighting is not None:
                s += "%s.lighting = %s;\n" % (name, str(bool(attr.lighting)).lower())
            if attr.cullface is not None:
                s += "%s.cullface = '%s';\n" % (name, attr.cullface)
            if attr.magicmode is not None:
                s += "%s.magicmode = '%s';\n" % (name, str(bool(attr.magicmode)).lower())
            if len(attr.children) == 0:
                s += "r.add(%s);\n" % name
            s += "\n"
        return s


    def format_gui_controller(self, name, attr):
        """Format a single controller"""
        if attr in controller_format:
            return controller_format[attr].replace('%N', name).replace('%A', attr)
        else:
            raise ValueError("Controller for attribute '%s' not implemented")


    def format_gui(self):
        """Create the controller GUI script"""
        s = """
r.onShowtime = function() {
var gui = new dat.GUI();
the_controls = gui;
"""
        for name, caption, attrs in self._gui:
            guiname = "gui_%s" % name
            if not caption:
                caption = name
            s += "var %s = gui.addFolder('%s');\n" % (guiname, caption)
            for objname, name, attr in attrs:
                cname = "%s_%s" % (guiname, "".join(name.split()))
                s += "var %s = %s.%s.name('%s');\n" % (cname, guiname, self.format_gui_controller(objname, attr), name)

        # add camera controls
        guiname = "gui_camera"
        s += """
var %s = gui.addFolder('Camera');
var %s_reset = %s.add(r.camera,'reset');
""".replace('%s', guiname)

        # add global controls
        s += """
var gui_global = gui.addFolder('Global');
var gui_global_alphablend = gui_global.add(r,'toggleAlphablend');
"""

        s += "}\n"
        return s


    def start_js(self,name):
        """Export the start of the js file.

        Parameters:

        - `name`: string: the name of the model that will be shown
          by default when displaying the webgl html page

        This function should only be executed once, before any
        other export functions. It is called automatically by
        the first call to exportScene.
        """
        jsname = utils.changeExt(self.name, '.js')
        print("Exporting WebGL script to %s" % os.path.abspath(jsname))
        if self.urlprefix:
            jsurl = self.urlprefix + jsname
            print("Include it in the .html page as '%s'" % jsurl)
        else:
            jsurl = jsname
        self.scripts.append(jsurl)

        self.jsfile = open(jsname, 'w')
        s = "// Script generated by %s\n" % pf.fullVersion()
        if self.jsheader:
            s += str(self.jsheader)
        s += """
var the_renderer;
var the_controls;

window.onload = function() {
show%s();
}
"""% name
        self.jsfile.write(s)


    def exportScene(self,name=None):
        """Export the current OpenGL scene to the WebGL model.

        Parameters:

        - `name`: string: the name of the model in the current
          scene. When multiple scenes are exported, they will be identified
          by this name. This name is also used as the basename for the
          exported geometry files. For a single scene export, the name may
          be omitted, and will then be set equal to the name of the WebGL
          exporter.

        """
        if name is None:
            name = self.name

        if self.jsfile is None:
            self.start_js(name)

        s = """
show%s = function(renderer) {
if (typeof renderer === 'undefined') {
if (the_renderer != null) the_renderer.destroy();
var r = new X.renderer3D();
the_renderer = r;
} else {
r = renderer
}
if (the_controls != null) the_controls.destroy();
r.config.ORDERING_COMPARATOR = 'ID';
r.init();

""" % name
        js_alphablend = str(pf.canvas.settings.alphablend).lower()
        s += "r.setAlphablend(%s);\n" % js_alphablend

        s += '\n'.join([self.format_actor(a) for a in self._actors ])
        if self._gui:
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
        self.jsfile.write(s)
        self.scenes.append(name)


    def export(self,body='',createdby=-1):
        """Finish the export by creating the html file.

        Parameters:

        - `body`: an HTML section to be put in the body
        - `createdby`: int. If not zero, a logo 'Created by pyFormex'
          will appear on the page. If > 0, it specifies the width of the
          logo field. If < 0, the logo will be displayed on its natural
          width.

        Returns the full path of the create html file.
        """
        if self.jsfile:
            htmlname = utils.changeExt(self.jsfile.name, '.html')
            self.jsfile.close()
            body = ''

            if createdby:
                if isinstance(createdby, int):
                    width = createdby
                else:
                    width = 0
                body += createdBy(width)

            if len(self.scenes) > 1:
                body += createSceneButtons(self.scenes)

            exported_webgl = createWebglHtml(
                htmlname,self.scripts,self.bgcolor,body,
                self.description,self.keywords,self.author,self.title)
            print("Exported WebGL model to %s" % exported_webgl)
            return exported_webgl



def createSceneButtons(scenes):
    body = "<div style='position:absolute;top:150px;left:10px;'>"
    for name in scenes:
        body += "<button onclick='show%s()'>Show %s</button><br />" % (name,name)
    body += "</div>"
    return body


def createdBy(width=0):
    """Return a div html element with the created by pyFormex logo"""
    if width > 0:
        width = ' width="%s%%"' % width
    else:
        width = ''
    return """<div id='pyformex' style='position:absolute;top:10px;left:10px;'>
<a href='%s' target=_blank><img src='%s' border=0%s></a>
</div>""" % (pf.cfg['webgl/logo_link'],pf.cfg['webgl/logo'],width)


def createWebglHtml(name,scripts=[],bgcolor='white',body='',
                    description='WebGL model', keywords="pyFormex, WebGL",
                    author='', title='pyFormex WebGL model',header=''):
    """Create a html file for a WebGL model.

    Returns the absolute pathname to the created HTML file.
    """
    s = """<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<meta name="generator" content="%s">
""" % pf.fullVersion()
    if description:
        s += '<meta name="description" content="%s">\n' % description
    if keywords:
        s += '<meta name="keywords" content="%s">\n' % keywords
    if author:
        s += '<meta name="author" content="%s">\n' % author
    s += "<title>%s</title>\n" % title
    if header:
        s += header

    for scr in scripts:
        s += '<script type="text/javascript" src="%s"></script>\n' % scr

    s += """
</head>
<body bgcolor='%s'>
%s
</body>
</html>
""" % (colors.WEBcolor(bgcolor),body)

    with open(name, 'w') as htmlfile:
        htmlfile.write(s)
    return os.path.abspath(name)


def surface2webgl(S,name,caption=None):
    """Create a WebGL model of a surface

    - `S`: TriSurface
    - `name`: basename of the output files
    - `caption`: text to use as caption
    """
    W = WebGL()
    W.add(obj=S, file=name)
    s = S.dsize()
    W.view(position=[0., 0., s])
    W.export(name, caption)


def createMultiWebGL():
    """Creates a multimodel WebGL from single WebGL models"""
    models = askFilename(filter=['html','js'],multi=True)
    if not models:
        return
    combined = askNewFilename(filter=['html','js'],caption="Enter name of the combined model")
    if not combined:
        return
    fout = open(utils.changeExt(combined,'js'),'w')

    print("""// Script generated by %s
var the_renderer;
var the_menu;
window.onload = function() {
show%s()
}
""" % (pf.fullVersion(),utils.projectName(models[0])),file=fout)

    body = webgl.createdBy()
    body += "<div style='position:absolute;top:150px;left:10px;'>"
    for model in models:
        name = utils.projectName(model)
        body += "<button onclick='show%s()'>Show %s</button><br />" % (name,name)
        print('',file=fout)
        print("show%s = function() {" % name,file=fout)
        fn = utils.changeExt(model,'js')
        f = open(fn,'r')
        s = f.readlines()
        f.close()
        while len(s) > 0:
            line = s.pop(0)
            if line.startswith("window.onload = function"):
                break
        line = s.pop(0)
        if line.startswith("var r = new X.renderer3D"):
            print("""if (the_menu != null) the_menu.destroy();
if (the_renderer != null) the_renderer.destroy();
the_renderer = new X.renderer3D();
var r = the_renderer;
""",file=fout)
        else:
            raise ValueError("Invalid WebGL script %s" % fn)

        while len(s) > 0:
            line = s.pop(0)
            print(line,file=fout)
            if line.startswith("var gui = new dat.GUI"):
                print("the_menu = gui;",file=fout)
    fout.close()
    body += "</div>"

    fn = webgl.createWebglHtml(
        utils.changeExt(combined,'html'),
        scripts=[
            pf.cfg['webgl/script'],
            pf.cfg['webgl/guiscript'],
            utils.changeExt(combined,'js')
            ],
        body=body
        )

    if ack("Show the scene in your browser?"):
        showHTML(fn)

# End
