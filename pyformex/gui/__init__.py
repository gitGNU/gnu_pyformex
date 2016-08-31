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
"""pyFormex GUI module initialization.

This module is intended to form a single access point to the Python
wrappers for the QT libraries, which form the base of the pyFormex GUI.
By using a single access point, we can better deal with API changes
in the wrappers.

All pyFormex modules accessing QT libraries should do this by importing
from this module.

This module also detects the underlying windowing system.
Currently, the pyFormex GUI is only guaranteed on X11.
For other systems, a warning will be printed that some things may not work.
"""
from __future__ import absolute_import, division, print_function


import pyformex as pf
from pyformex import utils

# We need this to keep sphinx happy when building the docs
bindings = pf.cfg.get('gui/bindings','pyside')
#print("BINDINGS %s" % bindings)

if bindings.lower() != 'pyqt4' and utils.hasModule('pyside'):
    from PySide import QtCore, QtGui, QtOpenGL
    from PySide.QtCore import Signal
    from PySide.QtCore import Slot
    pf.options.pyside = True

elif bindings.lower() != 'pyside' and utils.hasModule('pyqt4'):
    import sip
    try:
        sip.setapi('QDate', 2)
        sip.setapi('QDateTime', 2)
        sip.setapi('QString', 2)
        sip.setapi('QTextStream', 2)
        sip.setapi('QTime', 2)
        sip.setapi('QUrl', 2)
        sip.setapi('QVariant', 2)
    except ValueError as e:
        raise RuntimeError('Could not set PyQt4 API version (%s)' % e)

    from PyQt4 import QtCore, QtGui, QtOpenGL
    from PyQt4.QtCore import pyqtSignal as Signal
    from PyQt4.QtCore import pyqtSlot as Slot
    pf.options.pyside = False

else:
    raise ValueError("\n"+"*"*40+"\nThe pyFormex GUI requires PySide or PyQt4.\nI could not find neither of them, so I can not continue.\nInstall PySide or PyQt4 (including its OpenGL component) and then retry."+"\n"+"*"*40)


try:
    QtGui.QColor.setAllowX11ColorNames(True)
    pf.X11 = True
except:
    print("WARNING: THIS IS NOT AN X11 WINDOW SYSTEM!")
    print("SOME THINGS MAY NOT WORK PROPERLY!")
    pf.X11 = False


#from pyformex.opengl import canvas


# End
