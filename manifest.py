#!/usr/bin/env python
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
#
"""manifest.py

This script creates the list of files to be included in
the pyFormex source distribution.
"""
from __future__ import print_function
import os,re

def prefixFiles(prefix,files):
    """Prepend a prefix to a list of filenames."""
    return [ os.path.join(prefix,f) for f in files ]

def matchMany(regexps,target):
    """Return multiple regular expression matches of the same target string."""
    return [re.match(r,target) for r in regexps]


def matchCount(regexps,target):
    """Return the number of matches of target to regexps."""
    return len([ m for m in matchMany(regexps,target) if m ])


def matchAny(regexps,target):
    """Check whether target matches any of the regular expressions."""
    return matchCount(regexps,target) > 0


def matchNone(regexps,target):
    """Check whether targes matches none of the regular expressions."""
    return matchCount(regexps,target) == 0


def listTree(path,listdirs=True,topdown=True,sorted=False,excludedirs=[],excludefiles=[],includedirs=[],includefiles=[],filtr=None):
    """List all files in path.

    If ``dirs==False``, directories are not listed.
    By default the tree is listed top down and entries in the same directory
    are unsorted.

    `exludedirs` and `excludefiles` are lists of regular expressions with
    dirnames, resp. filenames to exclude from the result.

    `includedirs` and `includefiles` can be given to include only the
    directories, resp. files matching any of those patterns.

    Note that 'excludedirs' and 'includedirs' force top down handling.
    """
    filelist = []
    if excludedirs or includedirs:
        topdown = True
    for root, dirs, files in os.walk(path, topdown=topdown):
        if sorted:
            dirs.sort()
            files.sort()
        if excludedirs:
            remove = [ d for d in dirs if matchAny(excludedirs,d) ]
            for d in remove:
                dirs.remove(d)
        if includedirs:
            remove = [ d for d in dirs if not matchAny(includedirs,d) ]
            for d in remove:
                dirs.remove(d)
        if listdirs and topdown:
            filelist.append(root)
        if excludefiles:
            files = [ f for f in files if not matchAny(excludefiles,f) ]
        if includefiles:
            files = [ f for f in files if matchAny(includefiles,f) ]
        filelist.extend(prefixFiles(root,files))
        if listdirs and not topdown:
            filelist.append(root)
    if filtr:
        filelist = [ f for f in filelist if filtr(f) ]
    return filelist


#NON_MANIFEST = [ f.strip('\n') for f in open('NONMANIFEST').readlines() ]


# pyFormex documentation (installed in the pyformex tree)
DOC_FILES = listTree(
    'pyformex/doc/html',listdirs=False,sorted=True,
    excludedirs=['.svn'],
    ) + listTree(
    'pyformex/doc',
    listdirs=False,sorted=True,
    excludedirs=['.svn','dutch','html'],
    includefiles=[
        'README',
        'Description',
        'COPYING',
        'ReleaseNotes',
        ],
    )


# pyFormex data files (installed in the pyformex tree)
DATA_FILES = listTree(
    'pyformex/data',listdirs=False,sorted=True,
    excludedirs=['.svn','benchmark','ply'],
    excludefiles=['.*\.pyc','.*~$','PTAPE.*'],
    includefiles=[
        'README',
        'template.py',
        'benedict_6\.jpg',
        'bifurcation\.off',
        'blippo\.pgf',
        'blippok\.ttf',
        'butterfly\.png',
        'fewgl\.js',
        'hesperia-nieve\.prop',
        'horse\.off',
        'horse\.pgf',
        'materials\.db',
        'sections\.db',
        'splines\.pgf',
        'supershape\.txt',
        'teapot\.off',
        'world\.jpg',
        'xtk_xdat\.gui\.js',
        ],
    ) + listTree(
    'pyformex/glsl',listdirs=False,sorted=True,
    includefiles=[
        '.*\.c',
        ],
    )

# scripts to install extra programs
EXTRA_FILES = listTree(
    'pyformex/extra',listdirs=True,sorted=True,
    includedirs=[
        'calpy',
        'dxfparser',
###        'freetype-py',  now included in pyformex
        'gts',
        'postabq',
        'pygl2ps',
        'tetgen',
        ],
    excludefiles=['.*~$','.*\.1\.rst'],
    includefiles=[
        'README',
        'Makefile',
        '.*\.sh$',
        '.*\.rst$',
        '.*\.patch$',
        '.*\.c$',
        '.*\.cc$',
        '.*\.h$',
        '.*\.i$',
        '.*\.py$',
        '.*\.1$',
        '.*\.pc$',
#        'freetype-py-0.4.1.tar.gz',
        ],
    )

# Data files to be installed outside the pyformex tree
# These are tuples (installdir,filelist)
OTHER_DATA = [
    ('share/pixmaps', [
        'pyformex/icons/pyformex-64x64.png',
        'pyformex/icons/pyformex.xpm',
        ]),
    ('share/applications', ['pyformex.desktop']),
    ('share/man/man1', [
        'pyformex/doc/pyformex.1',
        ]),
    # the full html documentation
    ## ('share/doc/pyformex/html',DOC_FILES),
    ]

DIST_FILES = [
    'README',
    'COPYING',
    'Description',
    'ReleaseNotes',
    'manifest.py',
    'setup.py',
    'setup.cfg',
    ] + \
    listTree('pyformex',listdirs=False,sorted=True,
             includedirs=['gui','plugins','opengl','fe'],
             includefiles=['.*\.py$','pyformex(rc)?$','pyformex.conf$'],
             excludefiles=['core.py','curvetools.py','backports.py'],
             ) + \
    listTree('pyformex/freetype',listdirs=False,sorted=True,
             includedirs=['ft_enums'],
             includefiles=['.*\.py$'],
             ) + \
    listTree('pyformex/icons',listdirs=False,sorted=True,
             includefiles=['README','.*\.xpm$','.*\.png$']
             ) + \
    listTree('pyformex/lib',listdirs=False,sorted=True,
             includefiles=['.*\.c$','.*\.py$']
             ) + \
    listTree('pyformex/bin',listdirs=False,sorted=True,
             excludefiles=['.*~$'],
             ) + \
    listTree('pyformex/examples',listdirs=False,sorted=True,
             excludedirs=['Demos'],
             excludefiles=['.*\.pyc','.*~$',
                           ],
             includefiles=['[_A-Z].*\.py$','apps.cat','README']
             ) + \
    DATA_FILES + \
    DOC_FILES + \
    EXTRA_FILES


for i in OTHER_DATA:
    DIST_FILES += i[1]


#print("# files: %s" % len(DIST_FILES))

if __name__ == '__main__':
    import sys

    todo = sys.argv[1:]
    if not todo:
        todo = ['doc','data','dist']

    #print(todo)
    #sys.exit()

    for a in todo:
        if a == 'doc':
            print("=========DOC_FILES=========")
            print('\n'.join(DOC_FILES))
        elif a == 'data':
            print("=========DATA_FILES========")
            print('\n'.join(DATA_FILES))
        elif a == 'other':
            print("=========OTHER_DATA========")
            for i in OTHER_DATA:
                print('\n'.join(i[1]))
        else:
            print("=========DIST_FILES========")
            print('\n'.join(DIST_FILES))

# End
