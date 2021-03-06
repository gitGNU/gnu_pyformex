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
"""A collection of miscellaneous utility functions.

"""
from __future__ import absolute_import, division, print_function

import os
import re
import sys
import tempfile
import time
import random


import pyformex as pf
from pyformex.process import Process
# These are here to re-export them as utils functions
from pyformex import (zip, round, isFile, isString)
from pyformex.software import (hasModule, checkModule, requireModule,
                               hasExternal, checkExternal, checkVersion)
from pyformex.odict import OrderedDict
from pyformex.config import formatDict

shuffle = random.shuffle


# Some regular expressions
RE_digits = re.compile(r'(\d+)')

######### WARNINGS ##############

_warn_category = { 'U': UserWarning, 'D':DeprecationWarning }

def saveWarningFilter(message,module='',category=UserWarning):
    cat = inverseDict(_warn_category).get(category, 'U')
    oldfilters = pf.prefcfg['warnings/filters']
    newfilters = oldfilters + [(str(message), '', cat)]
    pf.prefcfg.update({'filters':newfilters}, name='warnings')
    pf.debug("Future warning filters: %s" % pf.prefcfg['warnings/filters'], pf.DEBUG.WARNING)


def filterWarning(message,module='',cat='U',action='ignore'):
    import warnings
    pf.debug("Filter Warning '%s' from module '%s' cat '%s'" % (message, module, cat), pf.DEBUG.WARNING)
    category = _warn_category.get(cat, Warning)
    warnings.filterwarnings(action, message, category, module)


def warn(message,level=UserWarning,stacklevel=3,data=None):
    import warnings
    from pyformex import messages
    # pass the data into the message
    messages._message_data = data
    warnings.warn(message, level, stacklevel)


def deprec(message,stacklevel=4,data=None):
    warn(message, level=DeprecationWarning, stacklevel=stacklevel, data=data)


def warning(message,level=UserWarning,stacklevel=3):
    """Decorator to add a warning to a function.

    Adding this decorator to a function will warn the user with the
    supplied message when the decorated function gets executed for
    the first time in a session.
    An option is provided to switch off this warning in future sessions.

    Decorating a function is done as follows::

      @utils.warning('This is the message shown to the user')
      def function(args):
          ...

    """
    import functools
    def decorator(func):
        def wrapper(*_args,**_kargs):
            warn(message,level=level,stacklevel=stacklevel)
            # For some reason these messages are not auto-appended to
            # the filters for the currently running program
            # Therefore we do it here explicitely
            filterWarning(str(message))
            return func(*_args,**_kargs)
        if level==UserWarning:
            functools.update_wrapper(wrapper,func)
        return wrapper
    return decorator


def deprecated(message,stacklevel=4):
    """Decorator to deprecate a function

    This is like :func:`warning`, but the level is set to DeprecationWarning.
    """
    return warning(message,level=DeprecationWarning,stacklevel=stacklevel)


def deprecated_by(old,new,stacklevel=4):
    """Decorator to deprecate a function by another one.

    Adding this decorator to a function will warn the user with a
    message that the `old` function is deprecated in favor of `new`,
    at the first execution of `old`.

    See also: :func:`deprecated`.
    """
    return deprecated("%s is deprecated: use %s instead" % (old,new),stacklevel=stacklevel)


def deprecated_future():
    """Decorator to warn that a function may be deprecated in future.

    See also: :func:`deprecated`.
    """
    return deprecated("This functionality is deprecated and will probably be removed in future, unless you explain to the developers why they should retain it.")


##########################################################################
## Running external commands ##
###############################

# Here are some pyFormex specific additions on top of the Process class

# The process of the last run command
last_command = None

def system(cmd,timeout=None,wait=True,verbose=False,raise_error=False,**kargs):
    """Execute an external command.

    This (and the more user oriented :func:`utils.command`) are the
    prefered way to execute external commands from inside pyFormex.

    Parameters:

    - `cmd`: a string with the command to be executed
    - `timeout`: float. If specified and > 0.0, the command will time out
      and be terminated or killed after the specified number of seconds.
    - `wait`: bool. If True (default), the caller waits for the Process
      to terminate. Setting this value to False will allow the caller to
      continue, but it will not be able to retrieve the standard output
      and standard error of the process.
    - `verbose`: bool. If True, some extra informative message are printed:
      - the command that will be run
      - an occurring timeout condition,
      - in case of a nonzero exit, the full stdout, exit status and stderr

    - `raise_error`: bool. If True, and verbose is True, and the command
      fails to execute or returns with a nonzero return code other than
      one cause by a timeout, an error is raised.

    Additional parameters can be specified and will be passed to the Popen
    constructor. See the Python documentation for full info.
    Some typical examples:

    - `shell`: bool: default False. If True, the command is run in a new shell.
      The `cmd` should then be specified exactly as it would be entered in a
      shell.
    - `stdout`: an open file object. The standard output of the command will
      be written to that file.
    - `stdin`: an open file object. The standard input of the command will
      be read from that file.

    Returns the Process used to run the command. This gives access to all
    its info, like the exit code, stdout and stderr, and whether the command
    timed out or not. See :class:`Process` for more info.
    This Process is also saved as the global variable
    :attr:`utils.last_command` to allow checking the outcome of the command
    from other places but the caller.
    """
    global last_command
    if verbose:
        print("Running command: %s" % cmd)
    last_command = P = Process(cmd,timeout,wait,**kargs)
    #P.run(timeout)
    if verbose:
        if P.timedout:
            print("Command terminated due to timeout (%ss)" % timeout)

        elif P.failed:
            print("The subprocess failed to start, probably because the executable does not exist or is not in your current PATH.")
            if raise_error:
                raise RuntimeError("Error while executing command:\n  %s" % cmd)

        elif P.sta != 0:
            print(P.out)
            print("Command exited with an error (exitcode %s)" % P.sta)
            print(P.err)
            if raise_error:
                raise RuntimeError("Error while executing command:\n  %s" % cmd)
    return P


def command(cmd,verbose=True,raise_error=True,**kargs):
    """Run an external command in a user friendly way.

    This is equivalent with the :func:`system` function but having
    verbose=True and raise_error=True by default.
    """
    pf.debug("Command: %s" % cmd, pf.DEBUG.INFO)
    return system(cmd,verbose=verbose,raise_error=raise_error,**kargs)


def lastCommandReport():
    """Produce a report about the last command.

    This is mostly useful in interactive work, to find out
    why a command failed.
    """
    P = last_command
    if P is None:
        return 'No external command has been run yet'
    s = "=" * 8 + " LAST COMMAND REPORT "
    s += "=" * (50-len(s)) + "\n"
    s += "%8s: %s\n" % ('cmd', P.cmd)
    shell = P.kargs.get('shell', False)
    if shell:
        s += "%8s: %s\n" % ('shell', shell)
    s += "%8s: %s\n" % ('status', P.sta)
    for p in [ 'stdin', 'stdout', 'stderr' ]:
        a = P.kargs.get(p, None)
        name = a.name if isFile(a) else ''
        txt = None
        if p[3:] in ['out', 'err']:
            txt = getattr(P, p[3:])
            if txt is None and isFile(a):
                try:
                    txt = open(a.name, 'r').read(2000)
                except:
                    pass
        if name or txt:
            s += "%8s: %s\n" % (p, name)
            if txt:
                s += txt
    if P.timeout:
        s += "%8s: %s (timedout: %s)\n" % ('timeout', P.timeout, P.timedout)
    s += "=" * 50 + "\n"
    return s


@deprecated_by('utils.runCommand','utils.command')
def runCommand(cmd,timeout=None,shell=True,**kargs):
    """Run an external command in a user friendly way.

    This is like with the utils.command, but with shell=True by default,
    and the return value is a tuple (P.sta,P.out) instead of the Process P.
    """
    P = command(cmd,timeout=timeout,shell=shell,**kargs)
    return P.sta, P.out.rstrip('\n')


def killProcesses(pids,signal=15):
    """Send the specified signal to the processes in list

    - `pids`: a list of process ids.
    - `signal`: the signal to send to the processes. The default (15) will
      try to terminate the process. See 'man kill' for more values.
    """
    for pid in pids:
        try:
            os.kill(pid, signal)
        except:
            pf.debug("Error in killing of process '%s'" % pid, pf.DEBUG.INFO)


def execSource(script,glob={}):
    """Execute Python code in another thread.

    - `script`: a string with executable Python code
    - `glob`: an optional gloabls dict specifying the environment in
      which the source code is executed.
    """
    pf.interpreter.locals = glob
    pf.interpreter.runsource(script, '<input>', 'exec')


##########################################################################
## File types ##
################

#def all_image_extensions():
#    """Return a list with all known image extensions."""
#    imgfmt = []


file_description = OrderedDict([
    ('all', 'All files (*)'),
    ('ccx', 'CalCuliX files (*.dat *.inp)'),
    ('gz',  'Compressed files (*.gz *.bz2)'),
    ('dcm', 'DICOM images (*.dcm)'),
    ('dxf', 'AutoCAD .dxf files (*.dxf)'),
    ('dxfall', 'AutoCAD .dxf or converted(*.dxf *.dxftext)'),
    ('dxftext', 'Converted AutoCAD files (*.dxftext)'),
    ('flavia', 'flavia results (*.flavia.msh *.flavia.res)'),
    ('gts', 'GTS files (*.gts)'),
    ('html', 'Web pages (*.html)'),
    ('icon', 'Icons (*.xpm)'),
    ('img', 'Images (*.png *.jpg *.jpeg *.eps *.gif *.bmp)'),
    ('inp', 'Abaqus or CalCuliX input files (*.inp)'),
    ('neu', 'Gambit Neutral files (*.neu)'),
    ('obj', 'Wavefront OBJ files (*.obj)'),
    ('off', 'Geomview object files (*.off)'),
    ('pgf', 'pyFormex geometry files (*.pgf)'),
    ('png', 'PNG images (*.png)'),
    ('postproc', 'Postproc scripts (*_post.py *.post)'),
    ('pyformex', 'pyFormex scripts (*.py *.pye)'),
    ('pyf', 'pyFormex projects (*.pyf)'),
    ('smesh', 'Tetgen surface mesh files (*.smesh)'),
    ('stl', 'STL files (*.stl)'),
    ('stlb', 'Binary STL files (*.stl)'),  # Use only for output
    ('surface', 'Surface models (*.off *.gts *.stl *.neu *.smesh *.vtp *.vtk)'),
    ('tetgen', 'Tetgen files (*.poly *.smesh *.ele *.face *.edge *.node *.neigh)'),
    ('vtk', 'All VTK types (*.vtk *.vtp)'),
    ('vtp', 'vtkPolyData file (*.vtp)'),
])


def splitFileDescription(fdesc,compr=False):
    """Split a file descriptor.

    A file descriptor is a string consisting of an initial part followed
    by a second part enclosed in parentheses.
    The second part is a space separated list of glob patterns. An example
    file descriptor is 'file type text (\*.ext1 \*.ext2)'.
    The values of :attr:`utils.file_description` all have this format.

    This function splits the file descriptor in two parts: the leading text
    and a list of global patterns.

    Parameters:

    - `ftype`: a file descriptor string.
    - `compr`: bool. If True, the compressed file types are automatically
      added.

    Returns a tuple:

    - `desc`: the file type description text
    - `ext`: a list of strings each starting with a '.'.

    >>> splitFileDescription(file_description['img'])
    ('Images ', ['.png', '.jpg', '.jpeg', '.eps', '.gif', '.bmp'])
    >>> splitFileDescription(file_description['pgf'],compr=True)
    ('pyFormex geometry files ', ['.pgf', '.pgf.gz', '.pgf.bz2'])
    """
    import re
    desc,ext,dummy = re.compile('[()]').split(fdesc)
    ext = [ e.lstrip('*') for e in ext.split(' ') ]
    if compr:
        ext = addCompressedTypes(ext)
    return desc,ext


def fileExtensionsFromFilter(fdesc,compr=False):
    """Return the list of file extensions from a given filter.

    Parameters:

    - `fdesc`: one of the values in :attr:`utils.file_description`.

    Returns a list of strings starting with a '.'.

    >>> fileExtensionsFromFilter(file_description['ccx'])
    ['.dat', '.inp']
    >>> fileExtensionsFromFilter(file_description['ccx'],compr=True)
    ['.dat', '.dat.gz', '.dat.bz2', '.inp', '.inp.gz', '.inp.bz2']
    """
    return splitFileDescription(fdesc,compr)[1]


def fileExtensions(ftype,compr=False):
    """Return the list of file extensions from a given type.

    ftype is one of the keys in :attr:`utils.file_description`.

    Returns a list of strings starting with a '.'.

    >>> fileExtensions('pgf')
    ['.pgf']
    >>> fileExtensions('pgf',compr=True)
    ['.pgf', '.pgf.gz', '.pgf.bz2']
    """
    return fileExtensionsFromFilter(file_description[ftype],compr)


def fileTypes(ftype,compr=False):
    """Return the list of file extension types for a given type.

    This is like fileExtensions, but the strings do not have the
    leading dot and are guaranteed to be lower case.

    Returns a list of normalized file types.

    >>> fileTypes('pgf')
    ['pgf']
    >>> fileTypes('pgf',compr=True)
    ['pgf', 'pgf.gz', 'pgf.bz2']
    """
    return [ normalizeFileType(e) for e in fileExtensions(ftype,compr) ]


def addCompressedTypes(ext):
    """Add the defined compress types to a list of extensions

    >>> addCompressedTypes(['.ccx','.inp'])
    ['.ccx', '.ccx.gz', '.ccx.bz2', '.inp', '.inp.gz', '.inp.bz2']
    """
    from . import olist
    ext =  [ [e] + [ e+ec for ec in ['.gz','.bz2'] ] for e in ext ]
    return olist.flatten(ext)


def fileDescription(ftype,compr=False):
    """Return a description of the specified file type(s).

    Parameters:

    - `ftype`: a string or a list of strings. If it is a list, the return
      value will be a list of the corresponding return values for each of
      the strings in it. Each input string is converted to lower case
      and represents a file type. It can be one of the following:

      - a key in the :attr:`file_description` dict: the corresponding value
        will be returned (see Examples below).
      - a string of only alphanumerical characters: it will be interpreted
        as a file extension and the corresponding return value is
        ``FTYPE files (*.ftype)``
      - any other string is returned as as: this allows the user to compose
        his filters himself.

    Examples:

    >>> print(formatDict(file_description))
    all = 'All files (*)'
    ccx = 'CalCuliX files (*.dat *.inp)'
    gz = 'Compressed files (*.gz *.bz2)'
    dcm = 'DICOM images (*.dcm)'
    dxf = 'AutoCAD .dxf files (*.dxf)'
    dxfall = 'AutoCAD .dxf or converted(*.dxf *.dxftext)'
    dxftext = 'Converted AutoCAD files (*.dxftext)'
    flavia = 'flavia results (*.flavia.msh *.flavia.res)'
    gts = 'GTS files (*.gts)'
    html = 'Web pages (*.html)'
    icon = 'Icons (*.xpm)'
    img = 'Images (*.png *.jpg *.jpeg *.eps *.gif *.bmp)'
    inp = 'Abaqus or CalCuliX input files (*.inp)'
    neu = 'Gambit Neutral files (*.neu)'
    obj = 'Wavefront OBJ files (*.obj)'
    off = 'Geomview object files (*.off)'
    pgf = 'pyFormex geometry files (*.pgf)'
    png = 'PNG images (*.png)'
    postproc = 'Postproc scripts (*_post.py *.post)'
    pyformex = 'pyFormex scripts (*.py *.pye)'
    pyf = 'pyFormex projects (*.pyf)'
    smesh = 'Tetgen surface mesh files (*.smesh)'
    stl = 'STL files (*.stl)'
    stlb = 'Binary STL files (*.stl)'
    surface = 'Surface models (*.off *.gts *.stl *.neu *.smesh *.vtp *.vtk)'
    tetgen = 'Tetgen files (*.poly *.smesh *.ele *.face *.edge *.node *.neigh)'
    vtk = 'All VTK types (*.vtk *.vtp)'
    vtp = 'vtkPolyData file (*.vtp)'
    <BLANKLINE>
    >>> fileDescription('img')
    'Images (*.png *.jpg *.jpeg *.eps *.gif *.bmp)'
    >>> fileDescription(['stl','all'])
    ['STL files (*.stl)', 'All files (*)']
    >>> fileDescription('doc')
    'DOC files (*.doc)'
    >>> fileDescription('inp')
    'Abaqus or CalCuliX input files (*.inp)'
    >>> fileDescription('*.inp')
    '*.inp'
    >>> fileDescription(['stl','all'],compr=True)
    ['STL files  (*.stl *.stl.gz *.stl.bz2)', 'All files  (* *.gz *.bz2)']

    """
    if isinstance(ftype, list):
        return [fileDescription(f,compr) for f in ftype]
    ftype = ftype.lower()
    if ftype in file_description:
        ret = file_description[ftype]
    elif ftype.isalnum():
        ret = "%s files (*.%s)" % (ftype.upper(), ftype)
    else:
        return ftype
    if compr:
        desc,ext = splitFileDescription(ret,compr)
        ext = [ '*'+e for e in ext ]
        ret = "%s (%s)" % (desc, ' '.join(ext))
    return ret


##########################################################################
## Filenames ##
###############


def splitFilename(filename,accept_ext=None,reject_ext=None):
    """Split a file name in dir,base,ext tuple.

    Parameters:

    - `filename`: a filename, possibly including a directory path
    - `accept_ext`: optional list of acceptable extension strings.
      If specified, only extensions appearing in this list will be
      recognized as such, while other ones will be made part of the
      base name.
    - `reject_ext`: optional list of unacceptable extension strings.
      If specified, extensions appearing in this list will not be
      recognized as such, and be made part of the base name.

    Returns a tuple dir,base,ext:

    - `dir`: the directory path, not including the final path separator (unless
      it is the only one). If the filename starts with a single path separator,
      `dir` will consist of that single separator. If the filename does not
      contain a path separator, `dir` will be an empty string.
    - `base`: filename without the extension. It can only be empty if the
      input is an empty string.
    - `ext`: file extension: This is the part of the filename starting from
      the last '.' character that is not the first character of the filename.
      If the filename does not contain a '.' character or the only '.'
      character is also the first character of the filename (after the last
      path separator), the extension is an empty string. If not empty, it
      always starts with a '.'. A filename with

    Examples:

      >>> splitFilename("cc/dd/aa.bb")
      ('cc/dd', 'aa', '.bb')
      >>> splitFilename("cc/dd/aa.")
      ('cc/dd', 'aa', '.')
      >>> splitFilename("..//aa.bb")
      ('..', 'aa', '.bb')
      >>> splitFilename("aa.bb")
      ('', 'aa', '.bb')
      >>> splitFilename("aa/bb")
      ('aa', 'bb', '')
      >>> splitFilename("aa/bb/")
      ('aa/bb', '', '')
      >>> splitFilename("/aa/bb")
      ('/aa', 'bb', '')
      >>> splitFilename(".bb")
      ('', '.bb', '')
      >>> splitFilename("/")
      ('/', '', '')
      >>> splitFilename(".")
      ('', '.', '')
      >>> splitFilename("")
      ('', '', '')
      >>> splitFilename("cc/dd/aa.bb",accept_ext=['.aa','.cc'])
      ('cc/dd', 'aa.bb', '')
      >>> splitFilename("cc/dd/aa.bb",reject_ext=['.bb'])
      ('cc/dd', 'aa.bb', '')
    """
    dirname, basename = os.path.split(filename)
    basename, ext = os.path.splitext(basename)
    if accept_ext and ext not in accept_ext or \
       reject_ext and ext in reject_ext:
        basename, ext = basename+ext, ''
    return dirname, basename, ext


def buildFilename(dirname,basename,ext=''):
    """Build a filename from a directory path, filename and optional extension.

    The dirname and basename are joined using the system path separator,
    and the extension is added at the end. Note that no '.' is added between
    the basename and the extension. While the extension will normally
    start with a '.', this function can also be used to add another tail
    to the filename.

    This is a convenience function equivalent with::

      os.path.join(dirname,basename) + ext

    """
    return os.path.join(dirname, basename) + ext


def changeExt(filename,ext,accept_ext=None,reject_ext=None):
    """Change the extension of a file name.

    This function splits the specified file name in a base name and an
    extension, replaces the extension with the specified one, and returns
    the reassembled file name.
    If the filename has no extension part, the specified extension is just
    appended.

    Parameters:

    - `fn`: file name, possibly including a directory path and extension
    - `ext`: string: required extension of the output file name. The string
      should start with a '.'.
    - `accept_ext`, `reject_ext`: lists of strings starting with a '.'.
      These have the same meaning as in :func:`splitFilename`.

    Returns a file name with the specified extension.

    .. note: If the specified extension does not start with a '.', a dot
       is prepended. This feature is retained for compatibility reasons
       but may be removed in future. New code should only use extensions
       starting with a dot.

    Example:

    >>> changeExt('image.png','.jpg')
    'image.jpg'
    >>> changeExt('image','.jpg')
    'image.jpg'
    >>> changeExt('image','jpg') # Deprecated
    'image.jpg'
    >>> changeExt('image.1','.jpg')
    'image.jpg'
    >>> changeExt('image.1','.jpg',reject_ext=['.1'])
    'image.1.jpg'
    """
    if not ext.startswith('.'):
        ext = ".%s" % ext
    dirname, basename, oldext = splitFilename(filename, accept_ext, reject_ext)
    return buildFilename(dirname, basename, ext)


def tildeExpand(fn):
    """Perform tilde expansion on a filename.

    Bash, the most used command shell in Linux, expands a '~' in arguments
    to the users home direction.
    This function can be used to do the same for strings that did not receive
    the bash tilde expansion, such as strings in the configuration file.
    """
    return fn.replace('~', os.environ['HOME'])


def normalizeFileType(ftype):
    """Normalize a filetype string.

    The string is converted to lower case and a leading dot is removed.
    This makes it fit for use with a filename extension.

    Example:

    >>> normalizeFileType('pdf')
    'pdf'
    >>> normalizeFileType('.pdf')
    'pdf'
    >>> normalizeFileType('PDF')
    'pdf'
    >>> normalizeFileType('.PDF')
    'pdf'

    """
    ftype = ftype.lower()
    if len(ftype) > 0 and ftype[0] == '.':
        ftype = ftype[1:]
    return ftype


def splitExt(fname):
    """Split a file name in a=name and extension.

    The extension is the part of the file name starting from the last dot.
    However, if the file extension is '.gz' or '.bz2', and the filename
    contains another dot, the extension is set to the filename part after
    starting at the penultimate dot.
    This allows for transparent handling of compressed files.

    Returns a tuple (name,ext).

    Example:

    >>> splitExt('pyformex')
    ('pyformex', '')
    >>> splitExt('pyformex.pgf')
    ('pyformex', '.pgf')
    >>> splitExt('pyformex.pgf.gz')
    ('pyformex', '.pgf.gz')
    >>> splitExt('pyformex.gz')
    ('pyformex', '.gz')
    """
    name, ext = os.path.splitext(fname)
    if ext in [ '.gz', '.bz2' ]:
        name,ext1 = os.path.splitext(name)
        if ext1:
            ext = ext1 + ext
    return name, ext


def fileTypeFromExt(fname):
    """Derive the file type from the file name.

    The derived file type is the file extension part as obtained by
    :func:`splitExt` without the leading dot and in lower case.

    Example:

    >>> fileTypeFromExt('pyformex')
    ''
    >>> fileTypeFromExt('pyformex.pgf')
    'pgf'
    >>> fileTypeFromExt('pyformex.pgf.gz')
    'pgf.gz'
    >>> fileTypeFromExt('pyformex.gz')
    'gz'
    """
    return normalizeFileType(splitExt(fname)[1])


def fileTypeComprFromExt(fname):
    """Derive the file type and compression from the file name.

    This derives the uncompressed file type and the compression type
    from the file name extension.

    It first computes fileTypeFromExt(fname) and then splits it in the
    pure filetype and the compression type.

    Returns a tuple:

    - `filetype`: the file type of the uncompressed file
    - `compressed`: the compression type: either '', '.gz' or '.bz2'.
      If the file was uncompressed, this is an empty string.

    Example:

    >>> fileTypeComprFromExt('pyformex')
    ('', '')
    >>> fileTypeComprFromExt('pyformex.pgf')
    ('pgf', '')
    >>> fileTypeComprFromExt('pyformex.pgf.gz')
    ('pgf', 'gz')
    >>> fileTypeComprFromExt('pyformex.gz')
    ('gz', '')
    """
    ext = fileTypeFromExt(fname)
    ext,gz = os.path.splitext(ext)
    if gz.startswith('.'):
        gz = gz[1:]
    return ext,gz


def projectName(fn):
    """Derive a project name from a file name.

    The project name is the basename of the file without the extension.
    It is equivalent with splitFilename(fn)[1]
    """
    return splitExt(os.path.basename(fn))[0]


def fileSize(fn):
    """Return the size in bytes of the file fn"""
    return os.path.getsize(fn)


def findIcon(name):
    """Return the file name for an icon with given name.

    If no icon file is found, returns the question mark icon.
    """
    #print("Looking for icon %s" % name)
    for icondir in pf.cfg['gui/icondirs']:
        for icontype in pf.cfg['gui/icontypes']:
            fname = buildFilename(icondir, name, icontype)
            if os.path.exists(fname):
                #print("Found icon %s" % fname)
                return fname

    #print("NOT FOUND: use default")
    return buildFilename(pf.cfg['icondir'], 'question.xpm')


def listIconNames(dirs=None,types=None):
    """Return the list of available icons by their name.

    - `dirs`: list of paths. If specified, only return names from these
      directories.
    - `types`: list of strings, each starting with a dot.
      If specified, only return names of icons matching any of
      these file types.
    """
    if dirs is None:
        dirs = pf.cfg['gui/icondirs']
    if types is None:
        types = pf.cfg['gui/icontypes']
    types = [ '.+\\'+t for t in types]
    icons = []
    for icondir in dirs:
        files = listFiles(icondir)
        files = [ projectName(f) for f in files if matchAny(types, f) ]
        icons.extend(files)
    return icons


##########################################################################
## File lists ##
################

def prefixFiles(prefix, files):
    """Prepend a prefix path to a list of filenames."""
    return [ os.path.join(prefix, f) for f in files ]


def unPrefixFiles(prefix, files):
    """Remove a prefix path from a list of filenames.

    The given prefix path is removed from all filenames that start with
    the prefix. Other filenames are untouched.
    Only full path components are removed.
    The changed files are guaranteed not to start with a '/'.

    Returns the modified list.

    Examples:

    >>> unPrefixFiles('/home',['/home/user1','/home//user2','/home2/user','/root'])
    ['user1', 'user2', '/home2/user', '/root']
    """
    if not prefix.endswith('/'):
        prefix += '/'
    n = len(prefix)
    return [ s[n:].lstrip('/') if s.startswith(prefix) else s for s in files ]


def matchMany(regexps, target):
    """Return multiple regular expression matches of the same target string."""
    return [re.match(r, target) for r in regexps]


def matchCount(regexps, target):
    """Return the number of matches of target to  regexps."""
    return len([_f for _f in matchMany(regexps, target) if _f])


def matchAny(regexps, target):
    """Check whether target matches any of the regular expressions."""
    return matchCount(regexps, target) > 0


def matchNone(regexps, target):
    """Check whether target matches none of the regular expressions."""
    return matchCount(regexps, target) == 0


def matchAll(regexps, target):
    """Check whether targets matches all of the regular expressions."""
    return matchCount(regexps, target) == len(regexps)


def listDir(path):
    """List the contents of the specified directory path.

    Returns a tuple (dirs,files), where dirs is the list of subdirectories
    in the path, and files is the list of files. Either of the lists can be
    empty. If the path does not exist or is not accessible, two empty
    lists are returned.
    """
    try:
        return next(os.walk(path))[1:]
    except:
        return [],[]


def listDirs(path):
    """List the subdirectories in the specified directory path.

    Returns a list with the names of all directory type entries in the
    specified path. If there are no directories, or the path does not
    exist or is not accessible, returns an empty list.

    This is syntactic sugar for `listDir(path)[0]`.
    """
    return listDir(path)[0]


def listFiles(path):
    """Return the files of the specified directory path.

    Returns a list with the names of all file type entries in the
    specified path. If there are no files, or the path does not
    exist or is not accessible, returns an empty list.

    This is syntactic sugar for `listDir(path)[0]`.
    """
    return listDir(path)[1]


def listTree(path,listdirs=True,topdown=True,sorted=False,excludedirs=[],excludefiles=[],includedirs=[],includefiles=[],symlinks=True):
    """List all files in path.

    If ``listdirs==False``, directories are not listed.
    By default the tree is listed top down and entries in the same directory
    are unsorted.

    `exludedirs` and `excludefiles` are lists of regular expressions with
    dirnames, resp. filenames to exclude from the result.

    `includedirs` and `includefiles` can be given to include only the
    directories, resp. files matching any of those patterns.

    Note that 'excludedirs' and 'includedirs' force top down handling.

    If `symlinks` is set False, symbolic links are removed from the list.
    """
    filelist = []
    if excludedirs or includedirs:
        topdown = True
    for root, dirs, files in os.walk(path, topdown=topdown):
        if sorted:
            dirs.sort()
            files.sort()
        if excludedirs:
            remove = [ d for d in dirs if matchAny(excludedirs, d) ]
            for d in remove:
                dirs.remove(d)
        if includedirs:
            remove = [ d for d in dirs if not matchAny(includedirs, d) ]
            for d in remove:
                dirs.remove(d)
        if listdirs and topdown:
            filelist.append(root)
        if excludefiles:
            files = [ f for f in files if not matchAny(excludefiles, f) ]
        if includefiles:
            files = [ f for f in files if matchAny(includefiles, f) ]
        filelist.extend(prefixFiles(root, files))
        if listdirs and not topdown:
            filelist.append(root)
    if not symlinks:
        filelist = [ f for f in filelist if not os.path.islink(f) ]
    return filelist


def removeFile(filename):
    """Remove a file, ignoring error when it does not exist."""
    if os.path.exists(filename):
        os.remove(filename)


def removeTree(path,top=True):
    """Remove all files below path. If top==True, also path is removed."""
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    if top:
        os.rmdir(path)


def sourceFiles(relative=False,symlinks=True,extended=False):
    """Return a list of the pyFormex source .py files.

    - `symlinks`: if False, files that are symbolic links are retained in the
      list. The default is to remove them.
    - `extended`: if True, the .py files in all the paths in the configured
      appdirs and scriptdirs are also added.
    """
    path = pf.cfg['pyformexdir']
    if relative:
        path = os.path.relpath(path)
    files = listTree(path, listdirs=False, sorted=True,
                     includedirs=pf.cfg['sourcedirs'],
                     includefiles=['.*\.py$'], symlinks=symlinks)
    if extended:
        searchdirs = [ i[1] for i in pf.cfg['appdirs'] + pf.cfg['scriptdirs'] ]
        for path in set(searchdirs):
            if os.path.exists(path):
                files += listTree(path, listdirs=False, sorted=True,
                                  includefiles=['.*\.py$'], symlinks=symlinks)
    return files


def grepSource(pattern,options='',relative=True):
    """Finds pattern in the pyFormex source .py files.

    Uses the `grep` program to find all occurrences of some specified
    pattern text in the pyFormex source .py files (including the examples).
    Extra options can be passed to the grep command. See `man grep` for
    more info.

    Returns the output of the grep command.
    """
    opts = options.split(' ')
    if '-a' in opts:
        opts.remove('-a')
        options = ' '.join(opts)
        extended = True
    else:
        extended = False
    files = sourceFiles(relative=relative, extended=extended, symlinks=False)
    cmd = "grep %s '%s' %s" % (options, pattern, ' '.join(files))
    P = system(cmd, verbose=True)
    if not P.sta:
        return P.out


def moduleList(package='all'):
    """Return a list of all pyFormex modules.
    This is like :func:`listSource`, but returns the files in a
    Python module syntax, and does not include the __init__ modules
    in the packages.
    """
    modules = [ fn[:-3].replace('pyformex/','',1).replace('/','.') for fn in sourceFiles(relative=True) ]
    if package == 'core':
        modules = [ m for m in modules if not '.' in m ]
    elif package != 'all':
        modules = [ m for m in modules if m.startswith(package+'.') ]
    if pf.PY3:
        if 'compat_2k' in modules:
            modules.remove('compat_2k')
    else:
        if 'compat_3k' in modules:
            modules.remove('compat_3k')
    return modules


def diskSpace(path,units=None,ndigits=2):
    """Returns the amount of diskspace of a file system.

    Parameters:

    - `path`: a path name inside the file system to be probed.
    - `units`,`ndigits`: if `untis` is specified, the sizes will be reported
      in this units. See :func:`humanSize` for details`.
      The default is to report the number of bytes.

    Returns the total, used and available disk space for the
    file system containing the given path.

    Notice that used + available does not necessarily equals total,
    because a file system may (and usually does) have reserved blocks.
    """
    stat = os.statvfs(os.path.realpath(path))
    total = stat.f_blocks * stat.f_frsize
    avail = stat.f_bavail * stat.f_frsize
    used = (stat.f_blocks - stat.f_bfree) * stat.f_frsize
    if units:
        total = humanSize(total,units,ndigits)
        avail = humanSize(avail,units,ndigits)
        used = humanSize(used,units,ndigits)
    return total, used, avail


def humanSize(size,units,ndigits=-1):
    """Convert a number to a human size.

    Large numbers are often represented in a more human readable
    form using k, M, G prefixes. This function returns the input
    size as a number with the specified prefix.

    Parameters:

    - `size`: a number (integer or float)
    - `units`: string specifying the target units. The first character should
      be one of k,K,M,G,T,P,E,Z,Y. 'k' and 'K' are equivalent. A second
      character 'i' can be added to use binary (K=1024) prefixes instead of
      decimal (k=1000).
    - `ndigits`: integer. If >= 0, the result is rounded to
      the specified number of decimal digits.

    Returns: a float value rounded to `ndigits` digits.

    Example:

    >>> humanSize(1234567890,'k')
    1234567.89
    >>> humanSize(1234567890,'M',0)
    1235.0
    >>> humanSize(1234567890,'G',3)
    1.235
    >>> humanSize(1234567890,'Gi',3)
    1.15
    """
    size = float(size)
    order = '.KMGTPEZY'.find(units[0].upper())
    if units[1:2] == 'i':
        scale = 1024.
    else:
        scale = 1000.
    size = size / scale**order
    if ndigits >= 0:
        size = round(size,ndigits)
    return size


##########################################################################
## Temporary Files ##
#####################


tempFile = tempfile.NamedTemporaryFile
tempDir = tempfile.mkdtemp

def tempName(*args,**kargs):
    """Create a temporary file.

    Creates a temporary file by calling :func:`tempfile.mkstemp` with the
    specified arguments and returns the file name. It is equivalent with::

      tempfile.mkstemp(*args,**kargs)[1]

    The user is responsible for removing the temporary file.

    Example:

    >>> tmp = tempName('.txt')
    >>> s = open(tmp,'w').write('hallo')
    >>> s = open(tmp,'r').read()
    >>> os.remove(tmp)
    >>> print(s)
    hallo

    """
    return tempfile.mkstemp(*args,**kargs)[1]


###################### locale ###################

def setSaneLocale(localestring=''):
    """Set a sane local configuration for LC_NUMERIC.

    `localestring` is the locale string to be set, e.g. 'en_US.UTF-8'

    This will change the ``LC_ALL`` setting to the specified string,
    and set the ``LC_NUMBERIC`` to 'C'.

    Changing the LC_NUMERIC setting is a very bad idea! It makes floating
    point values to be read or written with a comma instead of a the decimal
    point. Of course this makes input and output files completely incompatible.
    You will often not be able to process these files any further and
    create a lot of troubles for yourself and other people if you use an
    LC_NUMERIC setting different from the standard.

    Because we do not want to help you shoot yourself in the foot, this
    function always sets ``LC_NUMERIC`` back to a sane value and we
    call this function when pyFormex is starting up.
    """
    import locale
    locale.setlocale(locale.LC_ALL, localestring)
    locale.setlocale(locale.LC_NUMERIC, 'C')
    locale.setlocale(locale.LC_COLLATE, 'C')

##########################################################################
## Text conversion  tools ##
############################

def strNorm(s):
    """Normalize a string.

    Text normalization removes all '&' characters and converts it to lower case.

    >>> strNorm("&MenuItem")
    'menuitem'

    """
    return str(s).replace('&', '').lower()


_punct_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.:]+')

def slugify(text, delim='-'):
    """Convert a string into a URL-ready readable ascii text.

    Example:
    >>> slugify("http://example.com/blog/[Some] _ Article's Title--")
    'http-example-com-blog-some-article-s-title'
    >>> slugify("&MenuItem")
    'menuitem'

    """
    import unicodedata
    text = unicode(text)
    result = []
    for word in _punct_re.split(text.lower()):
        word = unicodedata.normalize('NFKD', word).encode('ascii', 'ignore')
        if word:
            result.append(word)
    return delim.join(result)

###################### ReST conversion ###################

#try:
# be quiet, because the import is done early
if checkModule('docutils', quiet=True):
    from docutils.core import publish_string
    def rst2html(text,writer='html'):
        return publish_string(text, writer_name=writer)
#except ImportError:
else:
    def rst2html(text,writer='html'):
        return """.. note:
   This is a reStructuredText message, but it is currently displayed
   as plain text, because it could not be converted to html.
   If you install python-docutils, you will see this text (and other
   pyFormex messages) in a much nicer layout!

""" + text


def forceReST(text,underline=False):
    """Convert a text string to have it recognized as reStructuredText.

    Returns the text with two lines prepended: a line with '..'
    and a blank line. The text display functions will then recognize the
    string as being reStructuredText. Since the '..' starts a comment in
    reStructuredText, it will not be displayed.

    Furthermore, if `underline` is set True, the first line of the text
    will be underlined to make it appear as a header.
    """
    if underline:
        text = underlineHeader(text)
    return "..\n\n" + text


def underlineHeader(s,char='-'):
    """Underline the first line of a text.

    Adds a new line of text below the first line of s. The new line
    has the same length as the first, but all characters are equal to
    the specified char.

    >>> print(underlineHeader("Hello World"))
    Hello World
    -----------

    """
    i = s.find('\n')
    if i < 0:
        i = len(s)
    return s[:i] + '\n' + char*i + s[i:]


def framedText(text,padding=[0,2,0,2],border=[1,2,1,2],margin=[0,0,0,0],
               borderchar='####', cornerchar=None,width=None,adjust='l'):
    """Create a text with a frame around it.

    - `adjust`: 'l', 'c' or 'r': makes the text lines be adjusted to the
      left, center or right.

    >>> print(framedText("Hello World,\\nThis is me calling",adjust='c'))
    ##########################
    ##     Hello World,     ##
    ##  This is me calling  ##
    ##########################

    """
    lines = text.splitlines()
    maxlen = max([len(l) for l in lines])
    if adjust == 'c':
        lines = [l.center(maxlen) for l in lines]
    elif adjust == 'r':
        lines = [l.rjust(maxlen) for l in lines]
    else:
        lines = [l.ljust(maxlen) for l in lines]
    prefix = ' '*margin[3] + borderchar[3]*border[3] + ' '*padding[3]
    suffix = ' '*padding[1] + borderchar[1]*border[1] + ' '*margin[1]
    width = len(prefix)+maxlen+len(suffix)
    s = []
    for i in range(margin[0]):
        s.append('')
    for i in range(border[0]):
        s.append(borderchar[0]*width)
    for i in range(padding[0]):
        s.append(prefix+' '*maxlen+suffix)
    for l in lines:
        s.append(prefix+("%"+str(maxlen)+"s") % l+suffix)
    for i in range(padding[2]):
        s.append(prefix+' '*maxlen+suffix)
    for i in range(border[2]):
        s.append(borderchar[2]*width)
    for i in range( margin[2]):
        s.append('')
    return '\n'.join(s)


def prefixText(text,prefix):
    """Add a prefix to all lines of a text.

    - `text`: multiline string
    - `prefix`: string: prefix to insert at the start of all lines of text.

    >>> print(prefixText("line1\\nline2","** "))
    ** line1
    ** line2

    """
    return '\n'.join([ prefix+line for line in text.split('\n') ])


def versaText(obj):
    """Versatile text creator

    This functions converts any input into a (multiline) string.
    Currently, different inputs are treated as follows:

    - string: return as is,
    - function: use the output of the function as input,
    - anything else: use str() or repr() on the object.

    >>> versaText("Me")
    'Me'
    >>> versaText(1)
    '1'
    >>> versaText(len("Me"))
    '2'
    >>> versaText({1:"Me"})
    "{1: 'Me'}"
    """
    if callable(obj):
        obj = obj()
    if not isinstance(obj,str):
        try:
            obj = str(obj)
        except:
            obj = repr(obj)
    return obj


###################### file conversion ###################


def dos2unix(infile):
    """Convert a text file to unix line endings."""
    return system("sed -i 's|$|\\r|' %s" % infile)

def unix2dos(infile,outfile=None):
    """Convert a text file to dos line endings."""
    return system("sed -i 's|\\r||' %s" % infile)


def gzip(filename,gzipped=None,remove=True,level=5,compr='gz'):
    """Compress a file in gzip/bzip2 format.

    Parameters:

    - `filename`: input file name
    - `gzipped`: output file name. If not specified, it will be set to
      the input file name + '.' + `compr`. An existing output file will be
      overwritten.
    - `remove`: if True (default), the input file is removed after
      succesful compression
    - `level`: an integer from 1..9: gzip/bzip2 compression level.
      Higher values result in smaller files, but require longer compression
      times. The default of 5 gives already a fairly good compression ratio.
    - `compr`: 'gz' or 'bz2': the compression algorithm to be used.
      The default is 'gz' for gzip compression. Setting to 'bz2' will use
      bzip2 compression.

    Returns the name of the compressed file.
    """
    if gzipped is None:
        gzipped = filename+'.'+compr
    if compr == 'gz':
        import gzip
        gz = gzip.GzipFile(gzipped, 'wb', compresslevel=level)
    elif compr == 'bz2':
        import bz2
        gz = bz2.BZ2File(gzipped, 'wb', compresslevel=level)
    else:
        raise ValueError("`compr` should be 'gz' or 'bz2'")
    with open(filename,'rb') as fil:
        gz.write(fil.read())
    gz.close()
    if remove:
        removeFile(filename)
    return gzipped


def gunzip(filename,unzipped=None,remove=True,compr='gz'):
    """Uncompress a file in gzip/bzip2 format.

    Parameters:

    - `filename`: compressed input file name (usually ending in '.gz' or
      '.bz2')
    - `unzipped`: output file name. If not specified and `filename` ends with
      '.gz' or '.bz2', it will be set to the `filename` with the '.gz' or
      '.bz2' removed.
      If an empty string is specified or it is not specified and `filename`
      does not end in '.gz' or '.bz2', the name of a temporary file is
      generated. Since you will normally want to read something from the
      decompressed file, this temporary file is not deleted after closing.
      It is up to the user to delete it (using the returned file name) when
      he is ready with it.
    - `remove`: if True (default), the input file is removed after
      succesful decompression. You probably want to set this to False when
      decompressing to a temporary file.
    - `compr`: 'gz' or 'bz2': the compression algorithm used in the input
      file. If `filename` ends with either '.gz' or '.bz2', it is automatically
      set from the extension. Else, the default 'gz' is used.

    Returns the name of the decompressed file.
    """
    if filename.endswith('.gz'):
        compr = 'gz'
    if filename.endswith('.bz2'):
        compr = 'bz2'
    if compr == 'gz':
        import gzip
        gz = gzip.GzipFile(filename, 'rb')
    elif compr == 'bz2':
        import bz2
        gz = bz2.BZ2File(filename, 'rb')
    else:
        raise ValueError("`compr` should be 'gz' or 'bz2'")
    if unzipped is None and filename.endswith('.'+compr):
        unzipped = filename[:-(len(compr)+1)]
    if unzipped:
        fil = open(unzipped, 'wb')
    else:
        fil = tempFile(prefix='gunzip-', delete=False)
        unzipped = fil.name
    fil.write(gz.read())
    gz.close()
    fil.close()
    if remove:
        removeFile(filename)
    return unzipped


class File(object):
    """Transparent file compression.

    This class is a context manager providing transparent file compression
    and decompression. It is commonly used in a `with` statement, as follows::

      with File('filename.ext','w') as f:
          f.write('something')
          f.write('something more')

    This will create an uncompressed file with the specified name, write some
    things to the file, and close it. The file can be read back similarly::

      with File('filename.ext','r') as f:
          for line in f:
              print(f)

    Because File is a context manager, the file is closed automatically when
    leaving the `with` block.

    By specifying a filename ending with '.gz' or '.bz2', the file will be
    compressed (on writing) or decompressed (on reading) automatically.
    The code can just stay the same as above.

    Parameters:

    - `filename`: string: name of the file to open.
      If the filename ends with '.gz' or '.bz2', transparent (de)compression
      will be used, with gzip or bzip2 compression algorithms respectively.
    - `mode`: string: file open mode: 'r' for read, 'w' for write or 'a' for
      append mode. See also the documentation for Python's open function.
      For compressed files, append mode is not yet available.
    - `compr`: string, one of 'gz' or 'bz2': identifies the compression
      algorithm to be used: gzip or bzip2. If the file name is ending with
      '.gz' or '.bz2', `compr` is set automatically from the extension.
    - `level`: an integer from 1..9: gzip/bzip2 compression level.
      Higher values result in smaller files, but require longer compression
      times. The default of 5 gives already a fairly good compression ratio.
    - `delete_temp`: bool: if True (default), the temporary files needed to
      do the (de)compression are deleted when the File instance is closed.

    The File class can also be used outside a `with` statement. In that case
    the user has to open and close the File himself. The following are more
    or less equivalent with the above examples (the `with` statement is
    better at handling exceptions)::

      fil = File('filename.ext','w')
      f = fil.open()
      f.write('something')
      f.write('something more')
      fil.close()

    This will create an uncompressed file with the specified name, write some
    things to the file, and close it. The file can be read back similarly::

      fil = File('filename.ext','r')
      f = fil.open()
      for line in f:
          print(f)
      fil.close()

    """

    def __init__(self,filename,mode,compr=None,level=5,delete_temp=True):
        if filename.endswith('.gz') and compr is None:
            compr = 'gz'
        if filename.endswith('.bz2') and compr is None:
            compr = 'bz2'

        self.name = filename
        self.tmpfile = None
        self.tmpname = None
        self.mode = mode
        self.compr = compr
        self.level = level
        self.delete = delete_temp
        self.file = None


    def open(self):
        """Open the File in the requested mode.

        This can be used to open a File object outside a `with`
        statement. It returns a Python file object that can be used
        to read from or write to the File. It performs the following:

        - If no compression is used, ope the file in the requested mode.
        - For reading a compressed file, decompress the file to a temporary
          file and open the temporary file for reading.
        - For writing a compressed file, open a tem[porary file for writing.

        See the documentation for the :class:`File` class for an example of
        its use.
        """
        if not self.compr:
            # Open an uncompressed file:
            # - just open the file with specified mode
            self.file = open(self.name,self.mode)

        elif self.mode[0:1] in 'ra':
            # Open a compressed file in read or append mode:
            # - first decompress file
            self.tmpname = gunzip(self.name, unzipped='', remove=False)
            # - then open the decompressed file in read/append mode
            self.file = open(self.tmpname,self.mode)

        else:
            # Open a compressed file in write mode
            # - open a temporary file (to be compressed after closing)
            self.tmpfile = tempFile(prefix='File-', delete=False)
            self.tmpname = self.tmpfile.name
            self.file = self.tmpfile.file

        return self.file


    # this is needed to make this a context manager
    __enter__ = open


    def close(self):
        """Close the File.

        This can be used to close the File if it was not opened using a
        `with` statement. It performs the following:

        - The underlying file object is closed.
        - If the file was opened in write or append mode and compression is
          requested, the file is compressed.
        - If a temporary file was in use and delete_temp is True,
          the temporary file is deleted.

        See the documentation for the :class:`File` class for an example of
        its use.

        """
        self.file.close()
        if self.compr and self.mode[0:1] in 'wa':
            # - compress the resulting file
            gzip(self.tmpname,gzipped=self.name,remove=True,compr=self.compr,level=self.level)
        if self.tmpname and self.delete:
            removeFile(self.tmpname)


    def __exit__(self,exc_type, exc_value, traceback):
        """Close the File

        """
        if exc_type is None:
            self.close()
            return True

        else:
            # An exception occurred
            if self.file:
                self.file.close()

            if self.tmpfile:
                self.tmpfile.close()

            if self.tmpname and self.delete:
                removeFile(self.tmpname)

            return False


    def reopen(self,mode='r'):
        """Reopen the file, possibly in another mode.

        This allows e.g. to read back data from a just saved file
        without having to destroy the File instance.

        Returns the open file object.
        """
        self.close()
        self.mode = mode
        return self.open()


# These two functions are undocumented for a reason. Believe me! BV
def splitme(s):
    return s[::2], s[1::2]
def mergeme(s1, s2):
    return ''.join([a+b for a, b in zip(s1, s2)])


def mtime(fn):
    """Return the (UNIX) time of last change of file fn."""
    return os.stat(fn).st_mtime


def timeEval(s,glob=None):
    """Return the time needed for evaluating a string.

    s is a string with a valid Python instructions.
    The string is evaluated using Python's eval() and the difference
    in seconds between the current time before and after the evaluation
    is printed. The result of the evaluation is returned.

    This is a simple method to measure the time spent in some operation.
    It should not be used for microlevel instructions though, because
    the overhead of the time calls. Use Python's timeit module to measure
    microlevel execution time.
    """
    start = time.time()
    res = eval(s, glob)
    stop = time.time()
    print("Timed evaluation: %s seconds" % (stop-start))
    return res


def countLines(fn):
    """Return the number of lines in a text file."""
    P = system(["wc", fn])
    if P.sta == 0:
        return int(P.out.split()[0])
    else:
        return 0



##########################################################################
##  Miscellaneous            ##
###############################


def userName():
    """Find the name of the user."""
    P = system('id -un')
    return P.out


def is_script(appname):
    """Checks whether an application name is rather a script name"""
    return appname.endswith('.py') or appname.endswith('.pye')


def is_app(appname):
    return not is_script(appname)

is_pyFormex = is_script


def getDocString(scriptfile):
    """Return the docstring from a script file.

    This actually returns the first multiline string (delimited by
    triple double quote characters) from the file.
    It does relies on the script file being structured properly and
    indeed including a doctring at the beginning of the file.
    """
    fil = open(scriptfile, 'r')
    s = fil.read()
    i = s.find('"""')
    if i >= 0:
        j = s.find('"""', i+1)
        if j >= i+3:
            return s[i+3:j]
    return ''


def hsorted(l):
    """Sort a list of strings in human order.

    When human sort a list of strings, they tend to interprete the
    numerical fields like numbers and sort these parts numerically,
    instead of the lexicographic sorting by the computer.

    Returns the list of strings sorted in human order.

    Example:
    >>> hsorted(['a1b','a11b','a1.1b','a2b','a1'])
    ['a1', 'a1.1b', 'a1b', 'a2b', 'a11b']
    """
    def human(s):
        s = RE_digits.split(s)+['0']
        return list(zip(s[0::2], [int(i) for i in s[1::2]]))
    return sorted(l, key=human)


def numsplit(s):
    """Split a string in numerical and non-numerical parts.

    Returns a series of substrings of s. The odd items do not contain
    any digits. The even items only contain digits.
    Joined together, the substrings restore the original.

    The number of items is always odd: if the string ends or starts with a
    digit, the first or last item is an empty string.

    Example:

    >>> print(numsplit("aa11.22bb"))
    ['aa', '11', '.', '22', 'bb']
    >>> print(numsplit("11.22bb"))
    ['', '11', '.', '22', 'bb']
    >>> print(numsplit("aa11.22"))
    ['aa', '11', '.', '22', '']
    """
    return RE_digits.split(s)


def splitDigits(s,pos=-1):
    """Split a string at a sequence of digits.

    The input string is split in three parts, where the second part is
    a contiguous series of digits. The second argument specifies at which
    numerical substring the splitting is done. By default (pos=-1) this is
    the last one.

    Returns a tuple of three strings, any of which can be empty. The
    second string, if non-empty is a series of digits. The first and last
    items are the parts of the string before and after that series.
    Any of the three return values can be an empty string.
    If the string does not contain any digits, or if the specified splitting
    position exceeds the number of numerical substrings, the second and
    third items are empty strings.

    Example:

    >>> splitDigits('abc123')
    ('abc', '123', '')
    >>> splitDigits('123')
    ('', '123', '')
    >>> splitDigits('abc')
    ('abc', '', '')
    >>> splitDigits('abc123def456fghi')
    ('abc123def', '456', 'fghi')
    >>> splitDigits('abc123def456fghi',0)
    ('abc', '123', 'def456fghi')
    >>> splitDigits('123-456')
    ('123-', '456', '')
    >>> splitDigits('123-456',2)
    ('123-456', '', '')
    >>> splitDigits('')
    ('', '', '')
    """
    g = numsplit(s)
    n = len(g)
    i = 2*pos
    if i >= -n and i+1 < n:
        if i >= 0:
            i += 1
        #print(g,i,n)
        return ''.join(g[:i]), g[i], ''.join(g[i+1:])
    else:
        return s, '', ''


# BV: We could turn this into a generator
class NameSequence(object):
    """A class for autogenerating sequences of names.

    The name is a string including a numeric part, which is incremented
    at each call of the 'next()' method.

    The constructor takes name template and a possible extension as arguments.
    If the name starts with a non-numeric part, it is taken as a constant
    part.
    If the name ends with a numeric part, the next generated names will
    be obtained by incrementing this part. If not, a string '-000' will
    be appended and names will be generated by incrementing this part.

    If an extension is given, it will be appended as is to the names.
    This makes it possible to put the numeric part anywhere inside the
    names.

    Example:

    >>> N = NameSequence('abc.98')
    >>> [ next(N) for i in range(3) ]
    ['abc.98', 'abc.99', 'abc.100']
    >>> N = NameSequence('abc-8x.png')
    >>> [ next(N) for i in range(3) ]
    ['abc-8x.png', 'abc-9x.png', 'abc-10x.png']
    >>> NameSequence('abc','.png').next()
    'abc-000.png'
    >>> N = NameSequence('/home/user/abc23','5.png')
    >>> [ next(N) for i in range(2) ]
    ['/home/user/abc235.png', '/home/user/abc245.png']
    """

    def __init__(self,name,ext=''):
        """Create a new NameSequence from name,ext."""
        prefix, number, suffix = splitDigits(name)
        if len(number) > 0:
            self.nr = int(number)
            format = "%%0%dd" % len(number)
        else:
            self.nr = 0
            format = "-%03d"
        self.name = prefix+format+suffix+ext

    def __next__(self):
        """Return the next name in the sequence"""
        fn = self.name % self.nr
        self.nr += 1
        return fn
    next = __next__

    def peek(self):
        """Return the next name in the sequence without incrementing."""
        return self.name % self.nr

    def glob(self):
        """Return a UNIX glob pattern for the generated names.

        A NameSequence is often used as a generator for file names.
        The glob() method returns a pattern that can be used in a
        UNIX-like shell command to select all the generated file names.
        """
        i = self.name.find('%')
        j = self.name.find('d', i)
        return self.name[:i]+'*'+self.name[j+1:]

    def files(self,sort=hsorted):
        """Return a (sorted) list of files matching the name pattern.

        A function may be specified to sort/filter the list of file names.
        The function should take a list of filenames as input. The output
        of the function is returned. The default sort function will sort
        the filenames in a human order.
        """
        import glob
        files = glob.glob(self.glob())
        if callable(sort):
            files = sort(files)
        return files


def prefixDict(d,prefix=''):
    """Prefix all the keys of a dict with the given prefix.

    - `d`: a dict where all the keys are strings.
    - `prefix`: a string

    The return value is a dict with all the items of d, but where the
    keys have been prefixed with the given string.
    """
    return dict([ (prefix+k, v) for k, v in d.items() ])


def subDict(d,prefix='',strip=True):
    """Return a dict with the items whose key starts with prefix.

    - `d`: a dict where all the keys are strings.
    - `prefix`: a string
    - `strip`: if True (default), the prefix is stripped from the keys.

    The return value is a dict with all the items from d whose key starts
    with prefix. The keys in the returned dict will have the prefix
    stripped off, unless strip=False is specified.
    """
    if strip:
        return dict([ (k.replace(prefix, '', 1), v) for k, v in d.items() if k.startswith(prefix)])
    else:
        return dict([ (k, v) for k, v in d.items() if k.startswith(prefix)])


def selectDict(d, keys, remove=False):
    """Return a dict with the items whose key is in keys.

    - `d`: a dict.
    - `keys`: a set of key values, can be a list or another dict.
    - `remove`: if True, the selected keys are removed from the input dict.

    Returns a dict with all the items from d whose key is in keys.
    See :func:`removeDict` for the complementary operation.

    Example:

    >>> d = dict([(c,c*c) for c in range(4)])
    >>> selectDict(d,[2,0])
    {0: 0, 2: 4}
    >>> print(d)
    {0: 0, 1: 1, 2: 4, 3: 9}
    >>> selectDict(d,[2,0,6],remove=True)
    {0: 0, 2: 4}
    >>> print(d)
    {1: 1, 3: 9}
    """
    keys = set(d) & set(keys)
    sel = dict([ (k, d[k]) for k in keys ])
    if remove:
        for k in keys:
            del d[k]
    return sel


def removeDict(d, keys):
    """Remove a set of keys from a dict.

    - `d`: a dict
    - `keys`: a set of key values

    The return value is a dict with all the items from `d` whose key
    is not in `keys`.
    This is the complementary operation of selectDict.

    Example:

    >>> d = dict([(c,c*c) for c in range(6)])
    >>> removeDict(d,[4,0])
    {1: 1, 2: 4, 3: 9, 5: 25}
    """
    return dict([ (k, d[k]) for k in set(d)-set(keys) ])


def refreshDict(d, src):
    """Refresh a dict with values from another dict.

    The values in the dict d are update with those in src.
    Unlike the dict.update method, this will only update existing keys
    but not add new keys.
    """
    d.update(selectDict(src, d))


def inverseDict(d):
    return dict([(v, k) for k, v in d.items()])


def selectDictValues(d, values):
    """Return the keys in a dict which have a specified value

    - `d`: a dict where all the keys are strings.
    - `values`: a list/set of values.

    The return value is a list with all the keys from d whose value
    is in keys.

    Example:

    >>> d = dict([(c,c*c) for c in range(6)])
    >>> selectDictValues(d,range(10))
    [0, 1, 2, 3]
    """
    return [ k for k in d if d[k] in values ]


def dictStr(d,skipkeys=[]):
    """Convert a dict to a string.

    This is much like dict.__str__, but formats all keys as
    strings and prints the items with the keys sorted.

    This function is can be used as replacement for the __str__
    method od dict-like classes.

    A list of strings skipkeys kan be specified, to suppress the
    printing of some special key values.
    """
    s = [ "'%s': %r" % item for item in d.items() if item[0] not in skipkeys ]
    return '{' + ', '.join(sorted(s)) + '}'


class DictDiff(object):
    """A class to compute the difference between two dictionaries

    Parameters:

    - `current_dict`: dict
    - `past_dict`: dict

    The differences are reported as sets of keys:
    - items added
    - items removed
    - keys same in both but changed values
    - keys same in both and unchanged values
    """
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.current_keys, self.past_keys = [
            set(d.keys()) for d in (current_dict, past_dict)
        ]
        self.intersect = self.current_keys.intersection(self.past_keys)

    def added(self):
        """Return the keys in current_dict but not in past_dict"""
        return self.current_keys - self.intersect

    def removed(self):
        """Return the keys in past_dict but not in current_dict"""
        return self.past_keys - self.intersect

    def changed(self):
        """Return the keys for which the value has changed"""
        return set(o for o in self.intersect
                   if self.past_dict[o] != self.current_dict[o])

    def unchanged(self):
        """Return the keys with same value in both dicts"""
        return set(o for o in self.intersect
                   if self.past_dict[o] == self.current_dict[o])


    def equal(self):
        """Return True if both dicts are equivalent"""
        return len(self.added() | self.removed() | self.changed()) == 0


    def report(self):
        return """Dict difference report:
    (1) items added : %s
    (2) items removed : %s
    (3) keys same in both but changed values : %s
    (4) keys same in both and unchanged values : %s
""" % (', '.join(self.added()), ', '.join(self.removed()), ', '.join(self.changed()), ', '.join(self.unchanged()))


def stuur(x,xval,yval,exp=2.5):
    """Returns a (non)linear response on the input x.

    xval and yval should be lists of 3 values:
    ``[xmin,x0,xmax], [ymin,y0,ymax]``.
    Together with the exponent exp, they define the response curve
    as function of x. With an exponent > 0, the variation will be
    slow in the neighbourhood of (x0,y0).
    For values x < xmin or x > xmax, the limit value ymin or ymax
    is returned.
    """
    xmin, x0, xmax = xval
    ymin, y0, ymax = yval
    if x < xmin:
        return ymin
    elif x < x0:
        xr = float(x-x0) / (xmin-x0)
        return y0 + (ymin-y0) * xr**exp
    elif x < xmax:
        xr = float(x-x0) / (xmax-x0)
        return y0 + (ymax-y0) * xr**exp
    else:
        return ymax


def listAllFonts():
    """List all fonts known to the system.

    Returns a sorted list of path names to all the font files
    found on the system.

    This uses fontconfig and will produce a warning if fontconfig is not
    installed.
    """
    cmd = "fc-list : file | sed 's|.*file=||;s|:||'"
    P = system(cmd, shell=True)
    if P.sta:
        warning("fc-list could not find your font files.\nMaybe you do not have fontconfig installed?")
        fonts = []
    else:
        fonts = sorted([ f.strip() for f in P.out.split('\n') ])
        if not fonts[0]:
            fonts = fonts[1:]
    return fonts


def is_mono_font(fontfile,size=24):
    "Test whether a fontfile is a fixed width font or not"""
    from pyformex import freetype as ft
    face = ft.Face(fontfile)
    return face.is_fixed_width


def listMonoFonts():
    """List all monospace fonts files found on the system."""
    fonts = [ f for f in listAllFonts() if f.endswith('.ttf') ]
    fonts = [ f for f in fonts if is_mono_font(f) ]
    return sorted(fonts)


def defaultMonoFont():
    """Return a default monospace font for the system."""
    fonts = listMonoFonts()
    if not fonts:
        raise ValueError("I could not find any monospace font file on your system")
    for f in fonts:
        if f.endswith('DejaVuSansMono.ttf'):
            return f
    return fonts[0]


###########################################################################


def currentScript():
    """Return the text of the script in execution, if any.

    If a script file is currently being executed, returns the text of that
    script, else returns an empty string.
    """
    if pf.scriptMode == 'script' and os.path.exists(pf.scriptName):
        return open(pf.scriptName).read()
    else:
        return ''


def procInfo(title):
    print(title)
    print('module name: %s' %  __name__)
    print('parent process: %s' % os.getppid())
    print('process id: %s' % os.getpid())


def interrogate(item):
    """Print useful information about item."""
    from pyformex.odict import OrderedDict
    info = OrderedDict()
    if hasattr(item, '__name__'):
        info["NAME:    "] =  item.__name__
    if hasattr(item, '__class__'):
        info["CLASS:   "] = item.__class__.__name__
    info["ID:      "] = id(item)
    info["TYPE:    "] = type(item)
    info["VALUE:   "] = repr(item)
    info["CALLABLE:"] = callable(item)
    if hasattr(item, '__doc__'):
        doc = getattr(item, '__doc__')
        doc = doc.strip()   # Remove leading/trailing whitespace.
        firstline = doc.split('\n')[0]
        info["DOC:     "] = firstline
    for i in info.items():
        print("%s %s"% i)


def memory_report(keys=None):
    """Return info about memory usage"""
    import gc
    gc.collect()
    P = system('cat /proc/meminfo')
    res = {}
    for line in str(P.out).split('\n'):
        try:
            k, v = line.split(':')
            k = k.strip()
            v = v.replace('kB', '').strip()
            res[k] = int(v)
        except:
            break
    res['MemUsed'] = res['MemTotal'] - res['MemFree'] - res['Buffers'] - res['Cached']
    if keys:
        res = selectDict(res, keys)
    return res


def memory_diff(mem0,mem1,tag=None):
    m0 = mem0['MemUsed']/1024.
    m1 = mem1['MemUsed']/1024.
    m2 = m1 - m0
    m3 = mem1['MemFree']/1024.
    print("%10.1f MB before; %10.1f MB after; %10.1f MB used; %10.1f MB free; %s" % (m0, m1, m2, m3, tag))


_mem_state = None
def memory_track(tag=None,since=None):
    global _mem_state
    if since is None:
        since = _mem_state
    new_mem_state = memory_report()
    if tag and _mem_state is not None:
        memory_diff(since, new_mem_state, tag)
    _mem_state = new_mem_state
    return _mem_state


def totalMemSize(o, handlers={}, verbose=False):
    """Return the approximate total memory footprint of an object.

    This function returns the approximate total memory footprint of an
    object and all of its contents.

    Automatically finds the contents of the following builtin containers and
    their subclasses:  tuple, list, deque, dict, set and frozenset.
    To search other containers, add handlers to iterate over their contents:

        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}

    Adapted from http://code.activestate.com/recipes/577504/
    """
    from sys import getsizeof, stderr
    from itertools import chain
    from pyformex.collections import deque
    try:
        from reprlib import repr
    except ImportError:
        pass

    dict_handler = lambda d: chain.from_iterable(d.items())
    all_handlers = {tuple: iter,
                    list: iter,
                    deque: iter,
                    dict: dict_handler,
                    set: iter,
                    frozenset: iter,
                   }
    all_handlers.update(handlers)     # user handlers take precedence
    seen = set()                      # track which object id's have already been seen
    default_size = getsizeof(0)       # estimate sizeof object without __sizeof__

    def sizeof(o):
        if id(o) in seen:       # do not double count the same object
            return 0
        seen.add(id(o))
        s = getsizeof(o, default_size)

        if verbose:
            print(s, type(o), repr(o), file=stderr)

        for typ, handler in all_handlers.items():
            if isinstance(o, typ):
                s += sum([sizeof(i) for i in handler(o)])
                break
        return s

    return sizeof(o)


### End
