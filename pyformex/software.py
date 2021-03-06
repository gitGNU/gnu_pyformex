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
"""software.py

A module to help with detecting required software and helper software,
and to check the versions of it.

This module is currently experimental. It contains some old functions
moved here from utils.py.
"""
from __future__ import absolute_import, division, print_function

import pyformex as pf
from pyformex.odict import OrderedDict
from distutils.version import LooseVersion as SaneVersion
import os
import sys
import re

# Python modules we know how to use
# Do not include pyformex or python here: they are predefined
# and could be erased by the detection
# The value is a sequence of:
#   - module name
#   - module name to load the version
#   - a sequence of attributes to get the version
# If empty, the attribute is supposed to be '__version__'
# If module name is an empty string, it is supposed to be equal to our alias
known_modules = {
    'calpy': (),
    'dicom': (),
    'docutils': (),
    'gdcm': ('', '', 'GDCM_VERSION'),
    'gl2ps': ('', '', 'GL2PS_VERSION'),
    'gnuplot': ('Gnuplot',),
#    'ipython': ('IPython',),
#    'ipython-qt': ('IPython.frontend.qt',),
    'matplotlib': (),
    'numpy': (),
    'pil': ('PIL', 'PIL', 'VERSION'),
    'pyopengl': ('OpenGL',),
    'pyqt4': ('PyQt4.QtCore', 'PyQt4', 'QtCore', 'QT_VERSION_STR'),
    'pyqt4gl': ('PyQt4.QtOpenGL', 'PyQt4', 'QtCore', 'QT_VERSION_STR'),
    'pyside': ('PySide',),
    'scipy': (),
    'vtk': ('', '', 'VTK_VERSION'),
     }

known_externals = {
# BEWARE ! Because utils.system now does not use a new shell by default,
# commands that require a shell should spawn the shell with the command
# as a -c parameter (see e.g. tetgen)

#  NOTE: abaqus command may hang longtime on checking the license server
#    'abaqus': ('abaqus info=sys|head -n2|tail -n1', 'Abaqus (\S+)'),
    'admesh': ('admesh --version', 'ADMesh - version (\S+)'),
    'calculix': ('ccx -v', '.*version (\S+)'),
    'calix': ('calix --version', 'CALIX-(\S+)'),
    'calpy': ('calpy --version', 'Calpy (\S+)'),
    'dxfparser': ('pyformex-dxfparser --version', 'dxfparser (\S+)'),
    'ffmpeg': ('ffmpeg -version', '[fF][fF]mpeg version (\S+)'),
    'freetype': ('freetype-config --ftversion', '(\S+)'),
    'gts': ('gtsset -h', 'Usage(:) '),
    'gts-bin': ('gts2stl -h', 'Usage(:) '),
    'gts-extra': ('gtsinside -h', 'Usage(:) '),
    'imagemagick': ('import -version', 'Version: ImageMagick (\S+)'),
    'postabq': ('pyformex-postabq -V', 'postabq (\S+).*'),
    'python': ('python --version', 'Python (\\S+)'),
    'recordmydesktop': ('recordmydesktop --version', 'recordMyDesktop v(\S+)'),
    'tetgen': ("sh -c 'tetgen -h |fgrep Version'", 'Version (\S+)'),
    'units': ('units --version', 'GNU Units version (\S+)'),
    'vmtk': ('vmtk --help', 'Usage(:)\s+vmtk.*'),
    }


if pf.PY3:
    # Some detect commands fail on Python3
    del known_externals['calculix']
    del known_externals['postabq']
    del known_externals['recordmydesktop']
    del known_externals['vmtk']

# versions of detected modules
the_version = {
    'pyformex': pf.__version__.split()[0],
    'python': sys.version.split()[0],
    }
# versions of detected external commands
the_external = {}

def checkVersion(name,version,external=False):
    """Checks a version of a program/module.

    name is either a module or an external program whose availability has
    been registered.
    Default is to treat name as a module. Add external=True for a program.

    Return value is -1, 0 or 1, depending on a version found that is
    <, == or > than the requested values.
    This should normally understand version numbers in the format 2.10.1
    Returns -2 if no version found.
    """
    if external:
        ver = hasExternal(name)
    else:
        ver = hasModule(name)
    if not ver:
        return -2
    if SaneVersion(ver) > SaneVersion(version):
        return 1
    elif SaneVersion(ver) == SaneVersion(version):
        return 0
    else:
        return -1


def hasModule(name,check=False):
    """Test if we have the named module available.

    Returns a nonzero (version) string if the module is available,
    or an empty string if it is not.

    By default, the module is only checked on the first call.
    The result is remembered in the the_version dict.
    The optional argument check==True forces a new detection.
    """
    if name in the_version and not check:
        return the_version[name]
    else:
        return checkModule(name)


def requireModule(name,version=None,comp='ge'):
    """Ensure that the named Python module/version is available.

    Checks that the specified module is available, and that its version
    number is not lower than the specified version.
    If no version is specified, any version is ok.

    The default comparison operator 'ge' can be replaced with one of:
    'eq', 'ge', 'gt', 'le', 'lt', 'ne'.

    Returns if the required module/version could be loaded, else an
    error is raised.
    """
    import operator
    ver = hasModule(name)
    if not ver:
        if name in known_modules:
            # Get the correct name, if different from our alias
            try:
                realname = known_modules[name][0]
                if realname:
                    name = realname
            except:
                pass
            attr = 'required'
        else:
            attr = 'unknown'
        errmsg = "Could not load %s module '%s'" % (attr, name)
        errmsg = """..

**Module %s not found!**

You activated some functionality requiring
the Python module '%s'.
However, the module '%s' could not be loaded.
Probably it is not installed on your system.
""" % (name, name, name)
        pf.error(errmsg)
        raise ValueError(errmsg)

    else:
        if version is not None:
            op = getattr(operator,comp)
            if not op(checkVersion(name, version),0):
                errmsg = """..

**Version of module %s (%s) does not meet requirements (%s %s)!**

You activated some functionality using the Python module '%s'.
However, the required version for that module could not be loaded.
""" % (name, ver, comp, version, name)
                pf.error(errmsg)
                raise ValueError(errmsg)


def checkAllModules():
    """Check the existence of all known modules.

    """
    [ checkModule(n, quiet=True) for n in known_modules ]


def checkModule(name,ver=(),fatal=False,quiet=False):
    """Check if the named Python module is available, and record its version.

    ver is a tuple of:

    - modname: name of the module to test import
    - vername: name of the module holding the version string
    - more fields are consecutive attributes leading to the version string

    The obtained version string is returned, empty if the module could not
    be loaded.
    The (name,version) pair is also inserted into the the_version dict.

    If fatal=True, pyFormex will abort if the module can not be loaded.
    """
    if len(ver) == 0 and name in known_modules:
        ver = known_modules[name]

    modname = name
    if len(ver) > 0  and len(ver[0]) > 0:
        modname = ver[0]

    try:
        if not quiet:
            pf.debug(modname, pf.DEBUG.DETECT)
        m = __import__(modname)
        if not quiet:
            pf.debug(m, pf.DEBUG.DETECT)
        if len(ver) > 1 and len(ver[1]) > 0:
            modname = ver[1]
            m = __import__(modname)
            if not quiet:
                pf.debug(m, pf.DEBUG.DETECT)
        ver = ver[2:]
        if len(ver) == 0:
            ver = ('__version__',)
        for a in ver:
            m = getattr(m, a)
            if not quiet:
                pf.debug(m, pf.DEBUG.DETECT)

    except:
        # failure: unexisting or unregistered modules
        if fatal:
            raise
        m = ''

    # If the attribute is a callable, call it
    if callable(m):
        m = m()
        # if a tuple is returned, turned it into a string
        if isinstance(m,tuple):
            m = '.'.join(map(str,m))
    # make sure version is a string (e.g. gl2ps uses a float!)
    m = str(m)
    _congratulations(name, m, 'module', fatal, quiet=quiet)
    the_version[name] = m
    return m


def hasExternal(name,force=False):
    """Test if we have the external command 'name' available.

    Returns a nonzero string if the command is available,
    or an empty string if it is not.

    The external command is only checked on the first call.
    The result is remembered in the the_external dict.
    """
    if name in the_external and not force:
        return the_external[name]
    else:
        return checkExternal(name)


def requireExternal(name):
    """Ensure that the named external program is available.

    If the module is not available, an error is raised.
    """
    if not hasExternal(name):
        if name in known_externals:
            # Get the correct name, if different from our alias
            try:
                realname = known_modules[name][0]
                if realname:
                    name = realname
            except:
                pass
            attr = 'required'
        else:
            attr = 'unknown'
        errmsg = """..

**Program %s not found!**

You activated some functionality requiring
the external program '%s'.
However, '%s' was not found on your system.
""" % (name, name, name)
        pf.error(errmsg)
        raise ValueError(errmsg)


def checkAllExternals():
    """Check the existence of all known externals.

    Returns a dict with all the known externals, detected or not.
    The detected ones have a non-zero value, usually the version number.
    """
    #print("CHECKING ALL EXTERNALS")
    [ checkExternal(n, quiet=True) for n in known_externals.keys() ]
    return the_external


def checkExternal(name,command=None,answer=None,quiet=False):
    """Check if the named external command is available on the system.

    name is the generic command name,
    command is the command as it will be executed to check its operation,
    answer is a regular expression to match positive answers from the command.
    answer should contain at least one group. In case of a match, the
    contents of the match will be stored in the the_external dict
    with name as the key. If the result does not match the specified answer,
    an empty value is inserted.

    Usually, command will contain an option to display the version, and
    the answer re contains a group to select the version string from
    the result.

    As a convenience, we provide a list of predeclared external commands,
    that can be checked by their name alone.
    """
    from pyformex import utils

    if command is None or answer is None:
        cmd, ans = known_externals.get(name, (name, '(.+)\n'))
        if command is None:
            command = cmd
        if answer is None:
            answer = ans

    pf.debug("Check %s\n%s" % (name, command), pf.DEBUG.DETECT)
    P = utils.system(command)
    pf.debug("Status:\n%s\nStdout:\n%s\nStderr:\n%s" % (P.sta, P.out, P.err), pf.DEBUG.DETECT)
    version = ''
    # Beware: some programs write their version to stderr, others to stdout
    m = None
    if P.out:
        m = re.match(answer, P.out)
    if m is None and P.err:
        m = re.match(answer, P.err)
    if m:
        version = str(m.group(1))
    _congratulations(name, version, 'program', quiet=quiet)
    the_external[name] = version
    return str(version)


def _congratulations(name,version,typ='module',fatal=False,quiet=False,severity=2):
    """Report a detected module/program."""
    if version:
        if not quiet:
            pf.debug("Congratulations! You have %s (%s)" % (name, version), pf.DEBUG.DETECT)
    else:
        if not quiet or fatal:
            pf.debug("ALAS! I could not find %s '%s' on your system" % (typ, name), pf.DEBUG.DETECT)
        if fatal:
            pf.error("Sorry, I'm getting out of here....")
            sys.exit()


def Libraries():
    from pyformex.lib import accelerated
    return [ m.__name__ for m in accelerated ]


def Shaders():
    """Return a list of the available GPU shader programs.

    Shader programs are in the pyformex/glsl directory and consist
    at least of two files:
    'vertex_shader_SHADER.c' and 'fragment_shader_SHADER.c'.
    This function will return a list of all the SHADER filename parts
    currently available. The default shader programs do not have the
    '_SHADER' part and will not be contained in this list.
    """
    from pyformex import utils
    files = utils.listTree(pf.cfg['shaderdir'],listdirs=False, sorted=True,
        includefiles=['vertex_shader_.*\.c$', 'fragment_shader_.*\.c$'])
    files = [ os.path.basename(f) for f in files ]
    vshaders = [ f[14:-2] for f in files if f.startswith('v') ]
    fshaders = [ f[16:-2] for f in files if f.startswith('f') ]
    shaders = set(vshaders) & set(fshaders)
    return sorted(shaders)


def detectedSoftware(all=True):
    """Return a dict with all detected helper software"""
    if all:
        checkAllModules()
        checkAllExternals()

    system, host, release, version, arch = os.uname()
    soft = {
        'System': OrderedDict([
            ('pyFormex_version', the_version['pyformex']),
            ('pyFormex_installtype', pf.installtype),
            ('pyFormex_fullversion', pf.fullVersion()),
            ('pyFormex_libraries', ', '.join(Libraries())),
            ('pyFormex_shaders', ', '.join(Shaders())),
            ('Python_version', the_version['python']),
            ('Python_fullversion', sys.version.replace('\n', ' ')),
            ('System', system),
            ('Host', host),
            ('Release', release),
            ('Version', version),
            ('Arch', arch),
            ]),
        'Modules': the_version,
        'Externals': the_external,
        }
    return soft


def reportSoftware(soft=None,header=None):
    from pyformex import utils
    notfound = '** Not Found **'
    def format_dict(d,sort=True):
        s = ''
        keys = d.keys()
        if sort:
            keys = sorted(keys)
        for k in keys:
            v = d[k]
            if not v:
                v = notfound
            s += "  %s (%s)\n" % ( k, v)
        return s

    if soft is None:
        soft = detectedSoftware()
    s = ""
    if header:
        header = str(header)
        s += utils.underlineHeader(header)
    for key, desc, sort in [
        ('System', 'Installed System', False),
        ('Modules', 'Detected Python Modules', True),
        ('Externals', 'Detected External Programs', True)
        ]:
        s += "\n%s:\n" % desc
        s += format_dict(soft[key], sort=sort)
    return s


def fmtDict(d,name=None):
    s = str(d)
    out = ''
    if name:
        out += name
        out += ' = '
    i = j = ind = 0
    while j < len(s):
        print(i,j,s[i:j+1])
        if s[j] == '{':
            out += s[i:j+1]
            ind += 4
            out += '\n' + ' '*ind
            i = j+1
        j = j + 1
    return out


def formatDict(d,indent=4):
    """Format a dict in nicely formatted Python source representation.

    Each (key,value) pair is formatted on a line of the form::

       key = value

    If all the keys are strings containing only characters that are
    allowed in Python variable names, the resulting text is a legal
    Python script to define the items in the dict. It can be stored
    on a file and executed.

    This format is the storage format of the Config class.
    """
    s = "{\n"
    for k, v in d.items():
        s += "%s'%s' : " % (' '*indent,k)
        if isinstance(v, dict):
            s += formatDict(v,indent+4)
        else:
            s += "%r" % v
        s += ",\n"
    s += "%s}" % (' '*indent)
    return s


import operator
comparators = {
    '==': operator.__eq__,
    '!=': operator.__ne__,
    '>' : operator.__gt__,
    '>=': operator.__ge__,
    '<' : operator.__lt__,
    '<=': operator.__le__,
    }

re_Required = re.compile('(?P<cmp>(==|!=|([<>]=?)))? *(?P<require>.*)')

def compareVersion(has,want):
    """Check whether a detected version matches the requirements.

    has is the version string detected.
    want is the required version string, possibly preceded by one
    of the doubly underscored comparison operators: __gt__, etc.
    If no comparison operator is specified, '__eq__' is assumed.

    Note that any tail behind x.y.z version is considered to be later
    version than x.y.z.

    Returns the result of the comparison: True or False
    Examples:

      >>> compareVersion('2.7','2.4.3')
      False
      >>> compareVersion('2.7','>2.4.3')
      True
      >>> compareVersion('2.7','>= 2.4.3')
      True
      >>> compareVersion('2.7','>= 2.7-rc3')
      False
      >>> compareVersion('2.7-rc4','>= 2.7-rc3')
      True

    """
    if not has:
        return False
    m = re_Required.match(want)
    if not m:
        return False

    d = m.groupdict()
    want = d['require']
    comp = d['cmp']
    if comp is None:
        comp = '=='
    has = SaneVersion(has)
    want = SaneVersion(want)
    return comparators[comp](has,want)


def checkItem(has, want):
    if has == want:
        return 'Matching'
    if not has:
        return 'Missing'
    if has and not want:
        return 'Unwanted'
    has = SaneVersion(has)
    want = SaneVersion(want)
    print(("HAS %s; WANT %s" % (has, want)))
    if has == want:
        return 'Matching'
    if has < want:
        return 'Too Old'
    if has > want:
        return 'Too Recent'


def checkItem2(has,want):
    if compareVersion(has,want):
        return 'OK'
    else:
        return 'FAIL'


def checkDict(has, want):
    return [ (k, has[k], want[k], checkItem2(has[k], want[k])) for k in want.keys()]


def checkSoftware(req,report=False):
    """Check that we have the matching components

    Returns True or False.
    If report=True, also returns a string with a full report.
    """
    from pyformex import utils
    soft = detectedSoftware()
    comp = []
    for k in req:
        comp.extend(checkDict(soft[k], req[k]))
    print(comp)
    result = all([ s[3] == 'OK' for s in comp ])
    if report:
        s = utils.underlineHeader("%30s %15s %15s %10s\n" % ("Item", "Found", "Required", "OK?"))
        for item in comp:
            s += "%30s %15s %15s %10s\n" % item
        s += "RESULT=%s\n" % ('OK' if result else 'FAIL')
        return result,s
    else:
        return result


def registerSoftware(req):
    """Register the current values of required software"""
    from pyformex import utils
    soft = detectedSoftware()
    reg = {}
    for k in req:
        reg[k] = utils.selectDict(soft[k], req[k].keys())
    return reg


def soft2config(soft):
    """Convert software collection to config"""
    from pyformex import utils
    from pyformex import config
    conf = config.Config()
    for k in soft:
        conf.update(utils.prefixDict(soft[k], k+'/'))
    return conf


def config2soft(conf):
    """Convert software collection from config"""
    from pyformex import utils
    soft = {}
    for k in ['System', 'Modules', 'Externals']:
        soft[k] = utils.subDict(conf, prefix=k+'/')
    return soft


def storeSoftware(soft,fn,mode='pretty'):
    """Store the software collection on file."""
    if mode == 'pretty':
        with open(fn, 'w') as fil:
            fil.write("soft = "+formatDict(soft)+'\n')
    elif mode == 'python':
        with open(fn, 'w') as fil:
            fil.write("soft=%r\n" % soft)
    elif mode == 'config':
        conf = soft2config(soft)
        conf.write(fn)
    elif mode == 'pickle':
        from pyformex import pickle
        print(("PICKLING", soft))
        pickle.dump(soft, open(fn, 'w'))


def readSoftware(fn,mode='python'):
    """Read the software collection from file.

    - `mode` = 'pretty': readable, editable
    - `mode` = 'python': readable, editable
    - `mode` = 'config': readable, editable
    - `mode` = 'pickle': binary
    """
    from pyformex import config
    if mode == 'python':
        print((os.path.abspath(fn)))
        with open(fn, 'r') as fil:
            exec(fil.read())
    elif mode == 'config':
        conf = config.Config(fn)
        soft = config2soft(conf)
    elif mode == 'pickle':
        from pyformex import pickle
        soft = pickle.load(open(fn, 'r'))
    return soft


#### execute as pyFormex script for testing ########

if __name__ in ["draw","script"] :

    Required = {
        'System': {
            'pyFormex_installtype': 'R',
            },
        'Modules': {
            'pyformex': '>= 0.9.1',
            'python': '>= 2.7.3',
            'matplotlib': '1.1.1',
            },
        'Externals': {
            'admesh': '>= 0.95',
            },
        }

    soft = detectedSoftware()
    print((reportSoftware(header="Detected Software")))
    print('\n ')
    print((reportSoftware(Required, header="Required Software")))
    print('\n ')

    print('CHECK')
    ok,report = checkSoftware(Required,True)
    print(report)

    reg = registerSoftware(Required)
    print("REGISTER")
    print(formatDict(reg))

    storeSoftware(reg, 'checksoft.py')
    req = readSoftware('checksoft.py')
    print('CHECK REGISTERED')
    print(formatDict(req))

    ok,report = checkSoftware(req,True)
    print(report)


# End
