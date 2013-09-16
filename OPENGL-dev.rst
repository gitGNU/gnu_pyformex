.. -*- rst -*-

..
  This file is part of the pyFormex project.
  pyFormex is a tool for generating, manipulating and transforming 3D
  geometrical models by sequences of mathematical operations.
  Home page: http://pyformex.org
  Project page:  https://savannah.nongnu.org/projects/pyformex/
  Copyright (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
  Distributed under the GNU General Public License version 3 or later.


  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see http://www.gnu.org/licenses/.

.. |date| date::

..
  This document is written in ReST. To see a nicely formatted PDF version
  you can compile this document with the rst2pdf command.


The new OpenGL engine for pyFormex 1.0
======================================

For pyFormex 1.0 we are developing a new OpenGL rendering engine, that will
make use of shader programs. These can be loaded on a Graphics Processing Unit
(GPU) allowing a speedup on machines with high end graphics cards.

The new engine is under development in the branch 'opengl' and can already be
used for most basic drawing tasks. While things (like text and texture
rendering) are still missing, we feel that the time has come to put the new 
engine at the disposal of all developers for testing.

While developers could already follow the new branch now, most are probably
still using the old master branch. Developments made in the master branch
where then merged regularly into the opengl branch. Also, some changes for
the opengl branch were merged back into the master. 

Because this two way merging is becoming to much of a burden, we decided to
very soon give up on the old master branch, and make the opengl branch the
new master. The old branch will be kept in the repository under the name
pyformex_0. It will be kept for maintenance on the old pyFormex 0.x series,
but no new developments will be added in that branch. If you are not developing
but using pyFormex 0.x in a productive environment, you may choose to 
check out that branch instead of staying on the master.

Once the new master branch is place (and you have checked it out), you can
still run the old engine, by using the --gl1 option on the pyformex command
line. This enables us to run both versions from the same working tree.

The old engine should function almost exactly like in the current (old)
master branch. It will be kept in the new master branch until we have had
the time to implement and check the working of all parts of the new engine. 
We will not do large efforts however to keep it
exactly like the engine in the old master branch, nor like the new engine.

What to do after the master branch has been switched?
-----------------------------------------------------

- If you want to keep using the old pyFormex 0.x tree for a long time, check out
  the pyformex_0 branch::

    git fetch
    git co pyformex_0

- If you want to follow the new master branch::

    git pull

  Now you can run the old engine::
    pyformex --gl1

  or the new::
    pyformex --gl2

  Note the the new engine is the default in the new master branch.
  If you prefer a desktop menu item or button to start the old engine,
  you can create one as follows::

    ./install-pyformex-dev-desktop-link GL1

  On startup pyFormex will only check for an already running instance of the
  same version. Thus you can easily run both versions next to each other on
  the screen, execute the same script, and see if any behavior is different.
    
  You are invited to do so, and to report the differences. This will help us
  with speeding up the development of the new engine.



..

