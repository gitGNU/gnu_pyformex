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
"""pyFormex plugins initialisation.

This module contains the functions to detect and load the pyFormex
plugin menus.
"""
from __future__ import absolute_import, division, print_function


import pyformex as pf
from types import ModuleType

# The following imports help with reading back old projects
# (We moved these modules from plugins to core)
from pyformex import project
from pyformex import mesh


def load(plugin):
    """Load the named plugin"""
    # import is done here to defer loading until possible
    __import__('pyformex.plugins.'+plugin)
    module = globals().get(plugin, None)
    if isinstance(module, ModuleType) and hasattr(module, 'show_menu'):
        module.show_menu()


def refresh(plugin):
    """Reload the named plugin"""
    __import__('pyformex.plugins.'+plugin)
    module = globals().get(plugin, None)
    if isinstance(module, ModuleType) and hasattr(module, 'show_menu'):
        reload(module)
    else:
        pf.error("No such module: %s" % plugin)


def find_plugin_menus():
    """Return a list of plugin menus in the pyFormex 'plugins' directory.

    """
    ## import os
    ## import utils
    ## plugindir = os.path.join(pf.cfg['pyformexdir'],'plugins')
    ## files = utils.listTree(plugindir,listdirs=False,excludedirs=['.*'],includefiles=['.*_menu.py$'])
    ## files = [ os.path.basename(f) for f in files ]
    ## files = [ os.path.splitext(f)[0] for f in files ]
    ## print files
    ## return files
    ## #
    ## # This will be replaced with a directory search
    ## #
    # We prefer a fixed order of plugin menus
    return [
        'geometry_menu',
        'formex_menu',
        'surface_menu',
        'tools_menu',
        'draw2d_menu',
        'nurbs_menu',
        'dxf_menu',
        'bifmesh_menu',
        'jobs_menu',
        'postproc_menu',
        ]

plugin_menus = find_plugin_menus()


def pluginMenus():
    """Return a list of plugin name and description.

    Returns a list of tuples (name,description).
    The name is the base name of the corresponding module file.
    The description is the text string displayed to the user. It is
    a beautified version of the plugin name.
    """
    return [ (name, name.capitalize().replace('_', ' ')) for name in plugin_menus ]


def create_plugin_menu(parent=None,before=None):
    from pyformex.gui import menu
    loadmenu = menu.Menu('&Load plugins', parent=parent, before=before)
    loadactions = menu.ActionList(function=load, menu=loadmenu)
    for name, text in pluginMenus():
        loadactions.add(name, icon=None, text=text)

    return loadactions


def loadConfiguredPlugins(ok_plugins=None):
    if ok_plugins is None:
        ok_plugins = pf.cfg['gui/plugins']
        pf.debug("Configured plugins: %s" % ok_plugins,pf.DEBUG.PLUGIN)
    for p in plugin_menus:
        pf.debug("Plugin menu: %s" % p,pf.DEBUG.PLUGIN)
        if p in ok_plugins:
            pf.debug("  Loading plugin menu: %s" % p,pf.DEBUG.PLUGIN)
            load(p)
        else:
            pf.debug("  Closing plugin menu: %s" % p,pf.DEBUG.PLUGIN)
            module = globals().get(p, None)
            if hasattr(module, 'close_menu'):
                module.close_menu()


#################### EXPERIMENTAL STUFF BELOW !! ################

from pyformex.odict import OrderedDict

_registered_plugins = OrderedDict()

def show_menu(name,before='help'):
    """Show the menu."""
    if not pf.GUI.menu.action(_menu):
        create_menu(before=before)

def close_menu(name):
    """Close the menu."""
    name.replace('_menu', '')
    print("CLOSING MENU %s" % name)
    pf.GUI.menu.removeItem(name)


def register_plugin_menu(name,menudata,before=['help']):
    menudata.extend([
        ("---", None),
#        ("&Reload Menu",reload_menu,{'data':name}),
        ("&Close Menu", close_menu, {'data':name}),
        ])
    w = menu.Menu(name, items=menudata, parent=pf.GUI.menu, before=before[0])
    _registered_plugins[name] = w
    return w


def reload_menu(name):
    """Reload the menu."""
    before = pf.GUI.menu.nextitem(_menu)
    print("Menu %s was before %s" % (_menu, before))
    close_menu()
    from pyformex import plugins
    plugins.refresh('draw2d')
    show_menu(before=before)
    setDrawOptions({'bbox':'last'})
    print(pf.GUI.menu.actionList())

# End
