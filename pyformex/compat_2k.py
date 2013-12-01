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
"""pyFormex compatibility module for Python2.x

The compatibility modules for different Python versions are intended
to wrap code changes between the versions into functions located at
a single place.

Note that we can not implement this as a single module and test for
the Python version inside that module. The differences between the
versions might cause compilation to fail.
"""
from __future__ import print_function

import sys
if (sys.hexversion & 0xFFFF0000) < 0x02070000:

    # Need at least Python 2.7
    # Note that the second line in the frame below is longer.
    # That is intentionally !!
    print("""
##################################################################
##  Requirement Error! This is Python %s.%s, however as of        ##
##  version 1.0, pyFormex requires at Python 2.7 or higher.     ##
##  The best thing you can do is install Python 2.7.            ##
##  Alternatively, you can use an older version of pyFormex,    ##
##  but then you will miss all recent and future improvements.  ##
##################################################################
""" % (sys.version_info.major, sys.version_info.minor))
    sys.exit()

from future_builtins import zip
# Force future_builtins zip on all modules
__builtins__['zip'] = zip

def execFile(f,*args,**kargs):
    return execfile(f,*args,**kargs)


def userInput(*args,**kargs):
    return raw_input(*args,**kargs)



# End
