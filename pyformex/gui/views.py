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
"""Predefined camera viewing directions

"""
from __future__ import print_function


built_in_views = {
    'front': (0., 0., 0.),
    'back': (180., 0., 0.),
    'right': (90., 0., 0.),
    'left': (270., 0., 0.),
    'top': (0., 90., 0.),
    'bottom': (0., -90., 0.),
    'iso0': (45., 45., 0.),
    'iso1': (45., 135., 0.),
    'iso2': (45., 225., 0.),
    'iso3': (45., 315., 0.),
    'iso4': (-45., 45., 0.),
    'iso5': (-45., 135., 0.),
    'iso6': (-45., 225., 0.),
    'iso7': (-45., 315., 0.),
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
       dict.__init__(self, data)
       self['iso'] = self['iso0']


    def get(self, name):
        """Get the angles for a named view.

        Returns a tuple of angles (longitude, latitude, twist) if the
        named view was defined, or None otherwise
        """
        return dict.get(self, name, None)


view_angles = ViewAngles()

def getAngles(name):
    return view_angles.get(name)


# End
