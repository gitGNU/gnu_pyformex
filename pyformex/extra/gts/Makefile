# $Id$
##
##  This file is part of pyFormex 0.8.5  (Sun Dec  4 21:24:46 CET 2011)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2011 (C) Benedict Verhegghe (benedict.verhegghe@ugent.be) 
##  Distributed under the GNU General Public License version 3 or later.
##
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
# Makefile for 'gts*' commands used by pyFormex
#
# You need: libgts-dev, libglib-2.0-dev, pkg-config 
#
############# SET THESE TO SUIT YOUR INSTALLATION ####################

# !! An environment variable DESTDIR can be set to specify a path for
# !! the installation tree. All install paths specified hereafter will
# !! then be relative to that installation path.
# !! An environment variable SU can be set to execute a program with
# !! root privileges. Examples are 'sudo' or 'gksu'. 

# root of the installation tree: this is a reasonable default
prefix:= /usr/local
# where to install the executable files
bindir:= $(prefix)/bin
# where to install library files
libdir:= $(prefix)/lib
# where to install the documentation
docdir:= $(prefix)/share/doc

#####################################################################

PKG:= pyformex-gts

BINDIR:= $(DESTDIR)$(bindir)
LIBDIR:= $(DESTDIR)$(libdir)
DOCDIR:= $(DESTDIR)$(docdir)

CC:= gcc
CXX:= g++
INSTALL:= $(SU) install
INSTALLBIN:= $(INSTALL) -m 0755
INSTALLDATA:= $(INSTALL) -m 0644

SRC= $(wildcard *.c)
PRG= $(addprefix gts, ${SRC:.c=})

FLAGS= `pkg-config --cflags --libs glib-2.0 gts`

.PHONY: all build install clean

build: $(PRG)

all: install clean

gts%: %.c
	$(CC) $(FLAGS) $< -o $@

install: $(PRG)
	$(INSTALLBIN) $(PRG) $(BINDIR)

clean:
	rm -f $(PRG)

# End