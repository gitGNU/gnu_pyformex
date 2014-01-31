# $Id$
##
##  This file is part of pyFormex
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
"""Tools to access files from the web

This module provides some convenience functions to access files from the
web. It is currently highly biased to downloading 3D models from archive3d.net,
unzipping the files, and displaying the .3ds models included.

"""
from __future__ import print_function

from pyformex import utils
import urllib
import os

def download(url,tgt=None):
    """Download a file with a known url

    If no tgt is specified, a temp one is created.
    The user is responsible to delete it.
    The full path to the file is returned.
    """
    if tgt is None:
        tgt = utils.tempName()
    urllib.urlretrieve(url,tgt)
    fn = os.path.abspath(tgt)
    print("File downloaded to %s" % fn)
    return fn


def zipList(filename):
    """List the files in a zip archive

    Returns a list of file names
    """
    from zipfile import ZipFile
    zfil = ZipFile(filename,'r')
    return zfil.namelist()


def zipExtract(filename,members=None):
    """Extract the specified member(s) from the zip file.

    The default extracts all.
    """
    from zipfile import ZipFile
    zfil = ZipFile(filename,'r')
    if members is None:
        zfil.extractAll()
    elif isinstance(members,(str,unicode)):
        zfil.extract(members)
    else:
        zfil.extractAll(members=members)



def find3ds(fn):
    """Return the .3ds files in a zip file"""
    files = zipList(fn)
    return [ f for f in files if f.lower().endswith('.3ds') ]


def show3ds(fn):
    """Import and show a 3ds file

    Import a 3ds file, render it, and export it to th GUI
    """
    from pyformex.plugins.vtk_itf import import3ds
    from pyformex.gui.draw import draw,export
    name = utils.projectName(fn)
    geom = import3ds(fn)
    draw(geom)
    export({name:geom})


def show3dzip(fn):
    """Show the .3ds models in a zip file.

    fn: a zip file contiaining one or more .3ds models.
    """
    for f in find3ds(fn):
        print("Extracting %s" % f)
        zipExtract(fn,f)
        show3ds(f)


def download3d(id):
    """Download a file fron archive3d.net by id number."""
    url = "http://archive3d.net/?a=download&do=get&id=%s" % id
    fn = download(url)
    return fn


def show3d(id):
    """Show a model from the archive3d.net database.

    id: string: the archive3d id number
    """
    fn = download3d(id)
    show3dzip(fn)


# End
