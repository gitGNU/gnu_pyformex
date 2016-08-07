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
"""pyFormex core module initialisation.

This module initializes the pyFormex global variables and
defines a few essential functions.
It is the very first thing that is executed when starting pyFormex.
It is loaded even before main.
"""
from __future__ import print_function

import os, sys
import time, datetime

__prog__ = "pyformex"
__version__ = "1.0.2-a6"
__revision__ = __version__

Copyright = 'Copyright (C) 2004-2016 Benedict Verhegghe'
Url = 'http://pyformex.org'
Description = "pyFormex is a tool for generating, manipulating and transforming large geometrical models of 3D structures by sequences of mathematical transformations."

# set start date/time
StartTime = datetime.datetime.now()

startup_messages = ''
startup_warnings = ''  # may be overridden in compat_?k below

#########  Check Python version #############

# intended Python version
# Dropping support for pre 2.7 will help migration to 3.x
minimal_version = 0x02070000
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
#     'G' : unreleased version running from GIT sources: no installation
#           required. This is set if directory containing the
#           pyformex start script is a git repository.
#     'R' : normal (source) Release, i.e. tarball (default). Installation
#           is done with 'python setup.py install' in the unpacked source.
#           The builtin pyFormex removal is activated.
#     'D' : Distribution package of a released version, official or not
#           (e.g. Debian package). The distribution package tools should
#           be used to install/uninstall. The builtin pyFormex removal is
#           deactivated.
#

installtype = 'R'

pyformexdir = os.path.dirname(__file__)
parentdir = os.path.dirname(pyformexdir)
if os.path.exists(os.path.join(parentdir, '.git')):
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

    def run_cmd(cmd):
        """Run command"""
        import subprocess
        P = subprocess.Popen(cmd,stdout=subprocess.PIPE,shell=True,universal_newlines=True)
        out,err = P.communicate()
        return P.returncode,out,err

    def set_revision():
        global __revision__
        cmd = 'cd %s && git describe --always' % pyformexdir
        sta,out,err = run_cmd(cmd)
        if sta == 0:
            __revision__ = out.split('\n')[0].strip()
        else:
            print("Could not set revision")

    def set_branch():
        cmd = 'cd %s && git symbolic-ref -q HEAD' % pyformexdir
        sta,out,err = run_cmd(cmd)
        if sta == 0:
            branch = out.split('\n')[0].split('/')[-1]
        else:
            print("Could not set branch name")

    set_revision()
    set_branch()


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

cfg = {}           # the current session configuration
prefcfg = None     # the preferenced configuration
refcfg = None      # the reference configuration
preffile = None    # the file where the preferenced configuration will be saved

PF = {}            # explicitely exported globals

scriptName = None
scriptlock = set()
scriptMode = None


# define default of warning and error
warning = print
error = print

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
          PROJECT, WEBGL, MULTI, LEGACY, OPENGL2, PLUGIN, UNICODE, FONT, \
          VTK = \
          [ 2 ** i for i in range(28) ]

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
