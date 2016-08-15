#
##
##  Copyright (C) 2011 John Doe (j.doe@somewhere.org)
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

"""pyFormex Script/App Template

This is a template file to show the general layout of a pyFormex
script or app.

A pyFormex script is just any simple Python source code file with
extension '.py' and is fully read and execution at once.

A pyFormex app can be a '.py' of '.pyc' file, and should define a function
'run()' to be executed by pyFormex. Also, the app should import anything that
it needs.

This template is a common structure that allows the file to be used both as
a script or as an app, with almost identical behavior.

For more details, see the user guide under the `Scripting` section.

The script starts by preference with a docstring (like this),
composed of a short first line, then a blank line and
one or more lines explaining the intention of the script.

If you distribute your script/app, you should set the copyright holder
at the start of the file and make sure that you (the copyright holder) has
the intention/right to distribute the software under the specified
copyright license (GPL3 or later).
"""
# This helps in getting used to future Python print syntax
from __future__ import print_function

# The pyFormex modeling language is defined by everything in
# the gui.draw module (if you use the GUI). For execution without
# the GUI, you should import from pyformex.script instead.
from pyformex.gui.draw import *

# Definitions
def run():
    """Main function.

    This is automatically executed on each run of an app.
    """
    print("This is the pyFormex template script/app")


# Code in the outer scope:
# - for an app, this is only executed on loading (module initialization).
# - for a script, this is executed on each run.

print("This is the initialization code of the pyFormex template script/app")

# The following is to make script and app behavior alike
# When executing a script in GUI mode, the global variable __name__ is set
# to 'draw', thus the run method defined above will be executed.

if __name__ == '__draw__':
    print("Running as a script")
    run()


# End
