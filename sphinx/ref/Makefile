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

#
# Makefile for pyFormex reference manual sections
#
# The pyFormex project uses Sphinx for building its documentation.
# This Makefile creates an autodoc Sphinx file from the pyFormex source.
# It works using the py2rst.py script, because the autodoc functions
# of Sphinx are not yet powerful enough.
#

COREMODULES= adjacency arraytools attributes \
  collection config connectivity coords coordsys \
  elements field fileread filewrite flatkeydb formex \
  geometry geomfile geomtools \
  mesh multi mydict odict olist project \
  script sendmail simple software timer utils varray
GUIMODULES= appMenu colorscale draw \
  image imageViewer menu\
  toolbar viewport widgets
OPENGLMODULES= camera canvas colors decors drawable \
  objectdialog renderer sanitize scene shader \
  textext texture
PLUGINMODULES= calpy_itf cameratools ccxdat ccxinp curve datareader dxf export \
  fe fe_abq fe_post flavia \
  imagearray inertia isopar isosurface lima neu_exp nurbs objects \
  partition plot2d polygon polynomial \
  postproc properties pyformex_gts section2d sectionize \
  tetgen tools trisurface turtle units vascularsweepingmesher web webgl

AUTOREF= $(COREMODULES) $(GUIMODULES) $(OPENGLMODULES) $(PLUGINMODULES)
AUTOSRC= $(addsuffix .rst, ${AUTOREF})

MANUALREF = matrix
MANUALSRC = $(addsuffix .rst, ${MANUALREF})

PY2RST=../py2rst.py

.PHONY: ref

.SILENT:

# where to search for source files
PYFORMEXDIR=../pyformex
vpath %.py $(addprefix ../../pyformex, / /opengl/ /gui/ /plugins/)


all: ${AUTOSRC}

clean:
	rm -f ${AUTOSRC}

%.rst: %.py
	@${PY2RST} $< > $@


# End
