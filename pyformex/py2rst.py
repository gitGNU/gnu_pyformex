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

"""Extract info from a Python module and shipout in sphinx .rst format.

This script automatically extracts class & function docstrings and argument
list from a module and ships out the information in a format that can be
used by the Sphinx document preprocessor.

It includes parts from the examples in the Python library reference manual
in the section on using the parser module. Refer to the manual for a thorough
discussion of the operation of this code.

Usage:  py2rst.py PYTHONFILE [> outputfile.tex]
"""
from __future__ import absolute_import, print_function
import sys

_debug = False

from pyformex.utils import underlineHeader

import inspect



############# Output formatting ##########################


def indent(s,n):
    """Indent all lines of a multinline string with n blanks."""
    return '\n'.join([ ' '*n + si for si in s.split('\n') ])


def split_doc(docstring):
    try:
        s = docstring.split('\n')
        shortdoc = s[0]
        if len(s) > 2:
            longdoc = '\n'.join(s[2:])
        else:
            longdoc = ''
        return shortdoc.strip('"'),longdoc.strip('"')
    except:
        return '',''


def sanitize(s):
    """Sanitize a string for LaTeX."""
    for c in '#&%':
        s = s.replace('\\'+c,c)
        s = s.replace(c,'\\'+c)
    ## for c in '{}':
    ##     s = s.replace('\\'+c,c)
    ##     s = s.replace(c,'\\'+c)
    return s



out = ''

def ship_start():
    global out
    out = ''

def ship(s):
    global out
    out += s
    out += '\n'


def debug(s):
    if _debug:
        ship('.. DEBUG:'+str(s))

def ship_module(name,docstring):
    shortdoc,longdoc = split_doc(docstring)
    ship(""".. $%s$  -*- rst -*-
.. pyformex reference manual --- %s
.. CREATED WITH pyformex --docmodule: DO NOT EDIT

.. include:: <isonum.txt>
.. include:: ../defines.inc
.. include:: ../links.inc

.. _sec:ref-%s:

:mod:`%s` --- %s
%s

.. automodule:: %s
   :synopsis: %s""" % ('Id',name,name,name,shortdoc,'='*(12+len(name)+len(shortdoc)),name,shortdoc))

def ship_end():
    ship("""

.. moduleauthor:: pyFormex project (http://pyformex.org)

.. End
""")


def ship_functions(members=[]):
    if members:
        ship("""   :members: %s""" % (','.join(members)))

def ship_class(name,members=[]):
    ship("""
   .. autoclass:: %s
      :members: %s""" % (name,','.join(members)))

def ship_section_init(secname,modname):
    ship(indent('\n'+underlineHeader("%s defined in module %s" % (secname,modname),'~')+'\n',3))


############# Info selection ##########################


def filter_local(name,fullname):
    """Filter definitions to include in doc

    We only include names defined in the module itself, except
    for the gui.draw module, where we also include the defines from
    openg.draw
    """
    return name.__module__ == fullname or (fullname == 'pyformex.gui.draw' and name.__module__ == 'pyformex.opengl.draw')


def filter_names(info):
    return [ i for i in info if not i[0].startswith('_') ]

def filter_docstrings(info):
    return [ i for i in info if not (i[1].__doc__ is None or i[1].__doc__.startswith('_')) ]

def filter_module(info,modname):
    return [ i for i in info if i[1].__module__ == modname]

def function_key(i):
    return i[1].func_code.co_firstlineno

def class_key(i):
    obj = i[1]
    try:
        key = inspect.getsourcelines(obj)[1]
    except:
        # occasionally, inspect does not find the source code
        # return a large number then
        key = 999999
    return key


def do_class(name,obj):
    # get class methods #
    methods = inspect.getmembers(obj,inspect.ismethod)
    methods = filter_names(methods)
    methods = filter_docstrings(methods)
    methods = sorted(methods,key=function_key)
    names = [ f[0] for f in methods ]
    ship_class(name,names)



def do_module(modname):
    """Retrieve information from the parse tree of a source file.

    filename
        Name of the file to read Python source code from.
    """
    if modname.startswith('pyformex.'):
        fullname = modname
    else:
        fullname = 'pyformex.'+modname
    module = __import__(fullname, fromlist=[None])
    #modname = inspect.getmodulename(filename)
    #print "MODULE %s" % modname
    #print("SYSPATH: %s" % sys.path)
    #print
    #module = __import__(modname)
    #filename = module.__file__
    #print(filename)
    #print inspect.getmoduleinfo(filename)
    #print(inspect.getmembers(module,inspect.isclass))
    #print([c[1].__module__ for c in inspect.getmembers(module,inspect.isclass)])
    classes = [ c for c in inspect.getmembers(module,inspect.isclass) if filter_local(c[1],fullname) ]
    classes = filter_names(classes)
    classes = filter_docstrings(classes)
    #print classes
    #return
    #print [ class_key(i) for i in classes ]
    classes = sorted(classes,key=class_key)
    #print classes

    # Functions #
    functions = [ c for c in inspect.getmembers(module,inspect.isfunction) if filter_local(c[1],fullname) ]
    functions = filter_names(functions)
    functions = filter_docstrings(functions)
    functions = sorted(functions,key=function_key)
    #print "FUNCTIONS"
    names = [ f[0] for f in functions ]
    #print names

    # Shipout

    ship_start()
    ship_module(modname,module.__doc__)
    #print names
    ship_functions(names)
    ship_section_init('Classes',modname)
    for c in classes:
        do_class(*c)
    ship_section_init('Functions',modname)
    ship_end()

    sys.__stdout__.write(out)


## def export(module_list,debug=False):
##     """Create a reference manual for the listed pyFormex modules.

##     module_list: list of modules

##     For each module in the input list, a ref manual in sphinx .rst format
##     is exported. THe manual contains autogenerated documentation for
##     all the classes, methods and functions in the module that have a
##     docstring that does not start with '_'.

##     """
##     global _debug
##     _debug = debug

##     sys.stdout = sys.stderr

##     for modname in module_list:
##         print("==== %s =====\n" % modname)
##         try:
##             module = sys.modules[modname]
##             do_module(module)



# End
