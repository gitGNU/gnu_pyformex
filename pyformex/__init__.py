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
"""pyFormex core module initialisation.

This module initializes the pyFormex global variables and
defines a few essential functions.
It is the very first thing that is executed when starting pyFormex.
It is loaded even before main.
"""
from __future__ import print_function

__version__ = "1.0.0~a1"
__revision__ = __version__

Copyright = 'Copyright (C) 2004-2013 Benedict Verhegghe'
Url = 'http://pyformex.org'
Description = "pyFormex is a tool for generating, manipulating and transforming large geometrical models of 3D structures by sequences of mathematical transformations."

# set start date/time
import time, datetime
StartTime = datetime.datetime.now()

startup_messages = ''
startup_warnings = ''  # may be overridden in compat_?k below

#########  Check Python version #############

# intended Python version
minimal_version = 0x02060000
target_version = 0x02070000
future_version = 0x03000000

def major(v):
    """Return the major component of version"""
    return v >> 24

def minor(v):
    """Return the minor component of version"""
    return (v & 0x00FF0000) >> 16

def human_version(v):
    """Return the human readable string for version"""
    return "%s.%s" % (major(v),minor(v))

import sys

if sys.hexversion < minimal_version:
    # Older than minimal
    startup_warnings += """
#######################################################################
##  Your Python version is %s, but pyFormex requires Python >= %s. ##
##  We advice you to upgrade your Python version. Getting pyFormex   ##
##  running on Python versions from 2.5 is possible but may require  ##
##  minor adjustements. Older versions are more problematic.         ##
#######################################################################
""" % (human_version(sys.hexversion), human_version(minimal_version))
    print(startup_warnings)
    sys.exit()

if sys.hexversion & 0xFFFF0000 > target_version:
    # Major,minor newer than target:
    startup_warnings += """
#######################################################################
##  Your Python version is %s, but pyFormex has only been tested    ##
##  with Python <= %s. We expect pyFormex to run correctly with     ##
##  your Python version, but if you encounter problems, please       ##
##  contact the developers at http://pyformex.org.                   ##
#######################################################################
""" % (human_version(sys.hexversion), human_version(minimal_version))
    #print(startup_warnings)

# Compatibility with Python2 and Python3
# We keep these in separate modules, because the ones for 2k might
# not compile in 3k and vice-versa.
if sys.hexversion < 0x03000000:
    from pyformex.compat_2k import *
else:
    from pyformex.compat_3k import *


#### Detect install type ########

# Install type.
# This can have the followig values:
#     'R' : normal (source) release, i.e. tarball (default)
#     'D' : Debian package of a relesed version
#     'G' : unreleased version running from GIT sources
#     'S' : unreleased version running from SVN sources (obsolete)
#
installtype = 'R'

import os
pyformexdir = os.path.dirname(__file__)
#print("PYFORMEXDIR = %s" % pyformexdir)
if os.path.exists(os.path.join(os.path.dirname(pyformexdir), '.git')):
    installtype = 'G'


########## import libraries ##############


libraries = [ 'misc_', 'nurbs_', 'drawgl_' ]

if installtype in 'SG':
    # Running from source tree: check if compiled libraries are up-to-date
    libdir = os.path.join(pyformexdir, 'lib')

    def checkLibraries():
        #print "Checking pyFormex libraries"
        msg = ''
        for lib in libraries:
            src = os.path.join(libdir, lib+'.c')
            obj = os.path.join(libdir, lib+'.so')
            if not os.path.exists(obj) or os.path.getmtime(obj) < os.path.getmtime(src):
                msg += "\nThe compiled library '%s' is not up to date!" % lib
        return msg


    msg = checkLibraries()
    if msg:
        # Try rebyuilding
        print("Rebuilding pyFormex libraries, please wait")
        cmd = "cd %s/..; make lib" % pyformexdir
        os.system(cmd)
        msg = checkLibraries()

    if msg:
        # No success
        msg += """

I had a problem rebuilding the libraries in %s/lib.
You should probably exit pyFormex, fix the problem first and then restart pyFormex.
""" % pyformexdir
    startup_warnings += msg


# Set the proper revision number when running from git sources
if installtype=='G':
    branch = None
    from pyformex import utils
    try:
        #print("Check whether %s is a git source" % pyformexdir)
        cmd = 'cd %s && git describe --always' % pyformexdir
        #print(cmd)
        P = utils.system(cmd,shell=True)
        #print(P.sta,P.out,P.err)
        if P.sta == 0:
            __revision__ = P.out.split('\n')[0].strip()
    except:
        print("Could not set revision number")
        pass

    # Set branch name if we are in a git repository
    try:
        cmd = 'cd %s && git symbolic-ref --short -q HEAD' % pyformexdir
        P = utils.system(cmd, shell=True)
        if P.sta == 0:
            branch = P.out.split('\n')[0]
    except:
        print("Could not set branch name")
        pass

    del branch, cmd, P


def Version():
    """Return a string with the pyFormex name and version"""
    return 'pyFormex %s' % __version__


def fullVersion():
    """Return a string with the pyFormex name, version and revision"""
    return "%s (%s)" % (Version(), __revision__)

# The GUI parts
app_started = False
interactive = False
app = None         # the Qapplication
GUI = None         # the GUI QMainWindow
canvas = None      # the OpenGL Drawing widget controlled by the running script
#board = None      # the message board
console = None     # alternate Python console

# initialize some global variables used for communication between modules

# the options found on the command line
# this is replaced with the options read from the command line
# but we define it here with an attribute debuglevel, so that we can
# use debug (unintentionally) before the debuglevel is set

class options:
    debuglevel = 0  # Make sure we can use



print_help = None  # the function to print(the pyformex help text (pyformex -h))

cfg = {}         # the current session configuration
prefcfg = None     # the preferenced configuration
refcfg = None      # the reference configuration
preffile = None    # the file where the preferenced configuration will be saved

PF = {}            # explicitely exported globals
#_PF_ = {}          # globals that will be offered to scripts

scriptName = None
scriptlock = set()
scriptMode = None


# define last rescue versions of message, warning and debug
def message(s):
    print(s)

warning = message
error = message

class DebugLevels(object):
    """A class with debug levels.

    This class holds the defined debug levels as attributes.
    Each debug level is a binary value with a single bit set (a power of 2).
    Debug levels can be combined with & (AND), | (OR) and ^ (XOR).
    Two extra values are defined: None swtiches off all debugging, All
    activates all debug levels.

    """
    ALL = -1
    NONE = 0
    INFO, WARNING, OPTION, CONFIG, DETECT, MEM, SCRIPT, GUI, MENU, DRAW, \
          CANVAS, OPENGL, LIB, MOUSE, APPS, IMAGE, MISC, ABQ, WIDGET, \
          PROJECT, WEBGL, MULTI, LEGACY, OPENGL2, PLUGIN, UNICODE, = \
          [ 2 ** i for i in range(26) ]

try:
    # Python2 stores the local variable 'i'
    delattr(DebugLevels, 'i')
except:
    # Python3 seems not to store it
    pass

DEBUG = DebugLevels

def debugLevel(sl):
    lev = 0
    for l in sl:
        try:
            lev |= getattr(DEBUG, l.upper())
        except:
            pass
    return lev


def debug(s,level=DEBUG.ALL):
    """Print a debug message"""
    try: # to make sure that debug() can be used before options are set
        if options.debuglevel & level:
            raise
        pass
    except:
        print("DEBUG(%s): %s" % (level, str(s)))

def debugt(s, level):
    """Print a debug message with timer"""
    debug("%s: %s" % (time.time(), s))




# End
