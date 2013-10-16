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

The new engine is under development in the 'master' branch in a subdirectory
'opengl' and can already be used for most basic drawing tasks.
Some things (like texture rendering) are still missing though.

Currently, both the old and the new engine are available from the master
branch, and will remain so for quite some time. The engine is selectable
by a --gl1 or --gl2 option on the command line.
New features will likely only appear in the new gl2 engine, and some things
in gl1 might get broken over time and not be fixed anymore. So you are invited
to gradually switch over to the new engine as it becomes fully functional.
For now, the old engine remains the default, but at some point the default will
be switched to the new engine.

If you have an old script that does no longer run with any of the --gl options, you can consider running an older version. By preference you do this from an installed release package (either tar.gz of .deb).
But if you need to fix some old source, you can still checkout the old branch (git co 0.9). However, *no future development work* should be done on that branch ,only Problem fixing.

Also, no new commits should be pushed on the opengl branch: all gl2 development should now be done in the master branch.

You can help speed up the development of the new engine by testing your code and/or some of the examples in both engines, and report any differences and malfunctioning. With this in mind we have added the possibility of two global variables
in the examples: _opengl2 and _opengl2_comments. The first one should be set True if the example runs, False if it doesn't. The second can be used in case there remain some issues with a running example. The value is a (multiline) string with any comments describing the issue. General issues, occurring for many examples, should be listed below in this file. Should first check here before adding to the example itself.

To help in testing both engines, you can create two desktop starters.
The install-pyformex-dev-desktop-link script has been extended with some features: you can now directly add the command line options.

Thus you could create the following two start buttons::

  ./install-pyformex-dev-desktop-link GL1 --gl1 --redirect
  ./install-pyformex-dev-desktop-link GL2 --gl2 --redirect --config=~/.config/pyformex/pyformex-GL2.conf

Notice that the `--redirect` option is not added automatically.
The addition of a `--config` option in the second keeps a separate configuration file for the GL2 engine. In this way, on a large enough screen, you can run both versions next to each other, e.g. one on the left half and one on the right half of the screen. You can then run the same code in both versions and compare the results. Anything not identical should be fixed or reported, unless there is some reason for it to be different (e.g. an improvement in the new engine).


OpenGL2 issues
==============

- In lighted scenes, there is generally not enough light.
- Automatic coloring according to property does not (always?) work.
  You need to add the following to the draw statement::

    color='prop'

- Texture drawing is not implemented yet (can/should we re-activate some
  old actor drawing to enable this?)

..

