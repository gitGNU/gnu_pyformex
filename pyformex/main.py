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

# This is the only pyFormex module that is imported by the main script,
# so this is the place to put startup code
"""pyFormex main module

This module contains the main function of pyFormex, which is run by the
startup script.
"""
from __future__ import absolute_import, division, print_function

import sys, os
import pyformex as pf
from pyformex.config import Config
from pyformex import utils
from pyformex import software

###########################  main  ################################

def filterWarnings():
    pf.debug("Current warning filters: %s" % pf.cfg['warnings/filters'], pf.DEBUG.WARNING)
    try:
        for w in pf.cfg['warnings/filters']:
            utils.filterWarning(*w)
    except:
        pf.debug("Error while processing warning filters: %s" % pf.cfg['warnings/filters'], pf.DEBUG.WARNING)


def refLookup(key):
    """Lookup a key in the reference configuration."""
    try:
        return pf.refcfg[key]
    except:
        pf.debug("!There is no key '%s' in the reference config!"%key, pf.DEBUG.CONFIG)
        return None


def prefLookup(key):
    """Lookup a key in the user's preferences configuration."""
    return pf.prefcfg[key]


def printcfg(key):
    try:
        print("!! refcfg[%s] = %s" % (key, pf.refcfg[key]))
    except KeyError:
        pass
    print("!! cfg[%s] = %s" % (key, pf.cfg[key]))


def remove_pyFormex(pyformexdir, executable):
    """Remove the pyFormex installation."""
    if pf.installtype == 'D':
        print("It looks like this version of pyFormex was installed from a distribution package. You should use your distribution's package tools to remove the pyFormex installation.")
        return

    if pf.installtype in 'SG':
        print("It looks like you are running pyFormex directly from a source tree at %s. I will not remove it. If you have enough privileges, you can just remove the whole source tree from the file system." % pyformexdir)
        return


    print("""
BEWARE!
This procedure will remove the complete pyFormex installation!
You should only use this on a pyFormex installed with 'python setup.py install'.
If you continue, pyFormex will exit and you will not be able to run it again.
The pyFormex installation is in: %s
The pyFormex executable script is: %s
You will need proper permissions to actually delete the files.
""" % (pyformexdir, executable))
    s = pf.userInput("Are you sure you want to remove pyFormex? yes/NO: ")
    if s == 'yes':
        bindir = os.path.dirname(executable)
        import glob
        script = os.path.join(bindir, 'pyformex')
        scripts = glob.glob(script+'-*')
        extra_gts = [ 'gtscoarsen', 'gtsinside', 'gtsrefine', 'gtsset', 'gtssmooth' ]
        extra = [ os.path.join(bindir, p) for p in extra_gts ]
        egginfo = "%s-%s*.egg-info" % (pyformexdir, pf.__version__.replace('~', '_'))
        egginfo = glob.glob(egginfo)
        prefixdir = os.path.commonprefix(['/usr/local', pyformexdir])
        print(pyformexdir, prefixdir)
        datadir = os.path.join(prefixdir, 'share')
        data = utils.prefixFiles(datadir, ['man/man1/pyformex.1',
                                          'applications/pyformex.desktop',
                                          'pixmaps/pyformex-64x64.png',
                                          'pixmaps/pyformex.xpm'])
        other_files = [ script ] + scripts + extra + egginfo + data
        print("Removing pyformex tree %s" % pyformexdir)
        print("Removing other files %s" % other_files)
        utils.removeTree(pyformexdir)
        for f in other_files:
            if os.path.exists(f):
                print("Removing %s" % f)
                try:
                    os.remove(f)
                except:
                    print("Could not remove %s" % f)
            else:
                print("No such file: %s" % f)

        print("\nBye, bye! I won't be back until you reinstall me!")
    elif s.startswith('y') or s.startswith('Y'):
        print("You need to type exactly 'yes' to remove me.")
    else:
        print("Thanks for letting me stay this time.")
    sys.exit()


def savePreferences():
    """Save the preferences.

    The name of the preferences file is determined at startup from
    the configuration files, and saved in ``pyformex.preffile``.
    If a local preferences file was read, it will be saved there.
    Otherwise, it will be saved as the user preferences, possibly
    creating that file.
    If ``pyformex.preffile`` is None, preferences are not saved.
    """
    if pf.preffile is None:
        return

    # Create the user conf dir
    prefdir = os.path.dirname(pf.preffile)
    if not os.path.exists(prefdir):
        try:
            os.makedirs(prefdir)
        except:
            print("The path where your user preferences should be stored can not be created!\nPreferences are not saved!")
            return


    # Cleanup up the prefcfg
    del pf.prefcfg['__ref__']

    # Currently erroroneously processed, therefore not saved
    del pf.prefcfg['render']['light0']
    del pf.prefcfg['render']['light1']
    del pf.prefcfg['render']['light2']
    del pf.prefcfg['render']['light3']

    pf.debug("="*60, pf.DEBUG.CONFIG)
    pf.debug("!!!Saving config:\n%s" % pf.prefcfg, pf.DEBUG.CONFIG)

    try:
        pf.prefcfg.write(pf.preffile)
        res = "Saved"
    except:
        res = "Could not save"
    pf.debug("%s preferences to file %s" % (res, pf.preffile), pf.DEBUG.CONFIG)
    return res=="Saved"


def apply_config_changes(cfg):
    """Apply incompatible changes in the configuration

    cfg is the user configuration that is to be saved.
    """
    # Safety checks
    if not isinstance(cfg['warnings/filters'], list):
        cfg['warnings/filters'] = []

    # Adhoc changes
    if isinstance(cfg['gui/dynazoom'], str):
        cfg['gui/dynazoom'] = [ cfg['gui/dynazoom'], '' ]

    for i in range(8):
        t = "render/light%s"%i
        try:
            cfg[t] = dict(cfg[t])
        except:
            pass

    for d in [ 'scriptdirs', 'appdirs' ]:
        if d in cfg:
            scriptdirs = []
            for i in cfg[d]:
                if i[1] == '' or os.path.isdir(i[1]):
                    scriptdirs.append(tuple(i))
                elif i[0] == '' or os.path.isdir(i[0]):
                    scriptdirs.append((i[1], i[0]))
            cfg[d] = scriptdirs

    # Rename settings
    for old, new in [
        ('history', 'gui/scripthistory'),
        ('gui/history', 'gui/scripthistory'),
        ('raiseapploadexc', 'showapploaderrors'),
        ('webgl/xtkscript', 'webgl/script'),
        ]:
        if old in cfg.keys():
            if new not in cfg.keys():
                cfg[new] = cfg[old]
            del cfg[old]

    # Delete settings
    for key in [
        'input/timeout', 'filterwarnings',
        'render/ambient', 'render/diffuse', 'render/specular', 'render/emission',
        'render/material', 'canvas/propcolors', 'Save changes', 'canvas/bgmode',
        'canvas/bgcolor2', '_save_',
        ]:
        if key in cfg.keys():
            print("DELETING CONFIG VARIABLE %s" % key)
            del cfg[key]


def list_modules(pkgs):
    """List the Python modules in the specified pyFormex packages.

    Parameters:

    - `pkgs`: a list of pyFormex package names. The package name is a
      subdirectory of the main pyformex package. Two special package names
      are recognized:

      - 'core': list the modules in the top level pyformex package
      - 'all': list all pyformex packages

    """
    for subpkg in pkgs:
        #print("### %s ###" % subpkg)
        files = utils.moduleList(subpkg)
        print('\n'.join(files))


def run_pytest(modules):
    """Run the pytests for the specified pyFormex modules.

    Parameters:

    - `modules`: a list of pyFormex modules in Python notation,
      relative to the pyformex package. If an empty list is supplied,
      all available pytests will be run.

    Test modules are stored under the path `pf.cfg['testdir']`, with the
    same hierarchy as the pyFormex source modules, and are named
    `test_MODULE.py`, where MODULE is the corresponding source module.

    """
    try:
        import pytest
    except:
        print("Can not import pytest")
        pass
    testpath = pf.cfg['testdir']
    if not modules:
        pytest.main(testpath)
    else:
        print("Running pytests for modules %s" % modules)
        for m in modules:
            path = m.split('.')
            path[-1] = 'test_' + path[-1] + '.py'
            path.insert(0,testpath)
            path = '/'.join(path)
            if os.path.exists(path):
                pytest.main(path)
            else:
                print("No such test module: %s" % path)


def doctest_module(module):
    """Run the doctests in the module's docstrings.

    module is a pyFormex module dotted path. The leading pyformex.
    may be omitted. numpy's floating point print precision is set to
    two decimals, to allow consisten tests independent of machine precision.
    """
    import doctest
    # Note that a non-empty fromlist is needed to make the
    # __import__ function always return the imported module
    # even if a dotted path is specified
    import numpy as np
    np.set_printoptions(precision=2,suppress=True)
    if not module.startswith('pyformex.'):
        module = 'pyformex.' + module
    mod = __import__(module, fromlist=[None])
    return doctest.testmod(mod)


def doc_module(module):
    """Print autogenerated documentation for the module.

    module is a pyFormex module dotted path. The leading pyformex.
    may be omitted.
    """
    from . import py2rst
    return py2rst.do_module(module)


###########################  app  ################################

def run(argv=[]):
    """The pyFormex main function.

    After pyFormex launcher script has correctly set up the Python import
    paths, this function is executed. It is responsible for reading the
    configuration file(s), processing the command line options and starting
    the application.

    The basic configuration file is 'pyformexrc' located in the pyFormex
    main directory. It should always be present and be left unchanged.
    If you want to make changes, copy (parts of) this file to another location
    where you can change them. Then make sure pyFormex reads you modifications
    file. By default, pyFormex will try to read the following
    configuration files if they are present (and in this order)::

        default settings:     <pyformexdir>/pyformexrc   (always loaded)
        system-wide settings: /etc/pyformex.conf
        user settings:        <configdir>/pyformex/pyformex.conf
        local settings        $PWD/.pyformexrc

    Also, an extra config file can be specified in the command line, using
    the --config option. The system-wide and user settings can be skipped
    by using the --nodefaultconfig option.

    Config files are loaded in the above order. Settings always override
    those loaded from a previous file.

    When pyFormex exits, the preferences that were changed are written to the
    last read config file. Changed settings are those that differ from the
    settings obtained after loading all but the last config file.
    If none of the optional config files exists, a new user settings file
    will be created, and an error will occur if the <configdir> path is
    not writable.

    """
    # Process options
    import argparse
    parser = argparse.ArgumentParser(
        prog = pf.__prog__,
#        usage = "%(prog)s [<options>] [ [ scriptname [scriptargs] ] ...]",
        description = pf.Description,
        epilog = "More info on http://pyformex.org",
#        formatter = optparse.TitledHelpFormatter(),
        )
    MO = parser.add_argument
    MO("--version",
       action='version',version = pf.fullVersion())
    MO("--gui",
       action="store_true", dest="gui", default=None,
       help="Start the GUI (this is the default when no scriptname argument is given)",
       )
    MO("--nogui",
       action="store_false", dest="gui", default=None,
       help="Do not start the GUI (this is the default when a scriptname argument is given)",
       )
    MO("--nocanvas",
       action="store_false", dest="canvas", default=True,
       help="Do not add an OpenGL canvas to the GUI (this is for development purposes only!)",
       )
    MO("--interactive",
       action="store_true", dest="interactive", default=False,
       help="Go into interactive mode after processing the command line parameters. This is implied by the --gui option.",
       )
    MO("--uselib", action="store_true", dest="uselib", default=None,
       help="Use the pyFormex C lib if available. This is the default.",
       )
    MO("--nouselib",
       action="store_false", dest="uselib", default=None,
       help="Do not use the pyFormex C-lib.",
       )
    MO("--config",
       action="store", dest="config", default=None,
       help="Use file CONFIG for settings. This file is loaded in addition to the normal configuration files and overwrites their settings. Any changes will be saved to this file.",
       )
    MO("--nodefaultconfig",
       action="store_true", dest="nodefaultconfig", default=False,
       help="Skip the default site and user config files. This option can only be used in conjunction with the --config option.",
       )
    MO("--redirect",
       action="store_true", dest="redirect", default=None,
       help="Redirect standard output to the message board (ignored with --nogui)",
       )
    MO("--noredirect",
       action="store_false", dest="redirect",
       help="Do not redirect standard output to the message board.",
       )
    MO("--debug",
       action="store", dest="debug", default='',
       help="Display debugging information to sys.stdout. The value is a comma-separated list of (case-insensitive) strings corresponding with the attributes of the DebugLevels class. The individual values are OR-ed together to produce a final debug value. The special value 'all' can be used to switch on all debug info.",
       )
    MO("--debuglevel",
       action="store", dest="debuglevel", type=int, default=0,
       help="Display debugging info to sys.stdout. The value is an int with the bits of the requested debug levels set. A value of -1 switches on all debug info. If this option is used, it overrides the --debug option.",
       )
    MO("--mesa",
       action="store_true", dest="mesa", default=False,
       help="Force the use of software 3D rendering through the mesa libs. The default is to use hardware accelerated rendering whenever possible. This flag can be useful when running pyFormex remotely on another host. The hardware accelerated version will not work over remote X.",
       )
    MO("--dri",
       action="store_true", dest="dri", default=None,
       help="Use Direct Rendering Infrastructure. By default, direct rendering will be used if available.",
       )
    MO("--nodri",
       action="store_false", dest="dri", default=None,
       help="Do not use the Direct Rendering Infrastructure. This may be used to turn off the direc rendering, e.g. to allow better capturing of images and movies.",
       )
    MO("--opengl",
       action="store", dest="opengl", default='2.0',
       help="Force the usage of an OpenGL version. The version should be specified as a string 'a.b'. The default is 2.0",
       )
    MO("--shader",
       action="store", dest="shader", default='',
       help="An extra string to add into the name of the shader programs, located in pyformex/data. The value will be added in before the '.c' extension.",
       )
    MO("--newviewports",
       action="store_true", dest="newviewports", default=False,
       help="Use the new multiple viewport canvas implementation. This is an experimental feature only intended for developers.",
       )
    MO("--testcamera",
       action="store_true", dest="testcamera", default=False,
       help="Print camera settings whenever they change.",
       )
    MO("--memtrack",
       action="store_true", dest="memtrack", default=False,
       help="Track memory for leaks. This is only for developers.",
       )
    MO("--fastnurbs",
       action="store_true", dest="fastnurbs", default=False,
       help="Test C library nurbs drawing: only for developers!",
       )
    MO("--pyside",
       action="store_true", dest="pyside", default=None,
       help="Use the PySide bindings for QT4 libraries",
       )
    MO("--pyqt4",
       action="store_false", dest="pyside", default=None,
       help="Use the PyQt4 bindings for QT4 libraries",
       )
    MO("--oldabq",
       action="store_true", dest="oldabq", default=False,
       help="Use the old fe_abq (from 1.0.0) interface. Default is to use the new one.",
       )
    MO("--unicode",
       action="store_true", dest="unicode", default=False,
       help="Allow unicode filenames. Beware: this is experimental!",
       )
    MO("args",
       action="store",  nargs='*',  metavar='FILE',
       help="pyFormex script files to be executed on startup",
       )
    MO("--listfiles",
       action="store_true", dest="listfiles", default=False,
       help="List the pyFormex Python source files and exit.",
       )
    MO("--listmodules",
       action="store", dest="listmodules", default=None, metavar='PKG', nargs='*',
       help="List the Python modules in the specified pyFormex subpackage and exit. Specify 'core' to just list the modules in the pyFormex top level. Specify 'all' to list all modules. The default is to list the modules in core, lib, plugins, gui, opengl.",
       )
    MO("--search",
       action="store_true", dest="search", default=False,
       help="Search the pyformex source for a specified pattern and exit. This can optionally be followed by -- followed by options for the grep command and/or '-a' to search all files in the extended search path. The final argument is the pattern to search. '-e' before the pattern will interprete this as an extended regular expression. '-l' option only lists the names of the matching files.",
       )
    MO("--remove",
       action="store_true", dest="remove", default=False,
       help="Remove the pyFormex installation and exit. This option only works when pyFormex was installed from a tarball release using the supplied install procedure. If you install from a distribution package (e.g. Debian), you should use your distribution's package tools to remove pyFormex. If you run pyFormex directly from SVN sources, you should just remove the whole checked out source tree.",
       )
    MO("--whereami",
       action="store_true", dest="whereami", default=False,
       help="Show where the pyformex package is installed and exit.",
       )
    MO("--detect",
       action="store_true", dest="detect", default=False,
       help="Show detected helper software and exit.",
       )
    MO("--doctest",
       action="store", dest="doctest", default=None, metavar='MODULE', nargs='*',
       help="Run the docstring tests for the specified pyFormex modules and exit. MODULE name is specified in Python syntax, relative to pyformex package (e.g. coords, plugins.curve).",
       )
    MO("--pytest",
       action="store", dest="pytest", default=None, metavar='MODULE', nargs='*',
       help="Run the pytest tests for the specified pyFormex modules and exit. MODULE name is specified in Python syntax, relative to pyformex package (e.g. coords, plugins.curve).",
       )
    MO("--docmodule",
       action="store", dest="docmodule", default=None, metavar='MODULE', nargs='*',
       help="Print the autogenerated documentation for module MODULE and exit. This is mostly useful during the generation of the pyFormex reference manual, as the produced result still needs to be run through the Sphinx documentation generator. MODULE is the name of a pyFormex module (Python syntax).",
       )

    pf.options = parser.parse_args(argv)
    args = pf.options.args
    pf.print_help = parser.print_help

    # Set debug level
    if pf.options.debug and not pf.options.debuglevel:
        pf.options.debuglevel = pf.debugLevel(pf.options.debug.split(','))

    # Check for invalid options
    if pf.options.nodefaultconfig and not pf.options.config:
        print("\nInvalid options: --nodefaultconfig but no --config option\nDo pyformex --help for help on options.\n")
        sys.exit()

    pf.debug("Options: %s" % pf.options, pf.DEBUG.ALL)

    ########## Load default configuration ##################################

    # Create a config instance
    pf.cfg = Config()
    # Fill in the pyformexdir, homedir variables
    # (use a read, not an update)
    if os.name == 'posix':
        homedir = os.environ['HOME']
    elif os.name == 'nt':
        homedir = os.environ['HOMEDRIVE']+os.environ['HOMEPATH']
    pf.cfg.read("pyformexdir = '%s'\n" % pf.pyformexdir)
    pf.cfg.read("homedir = '%s'\n" % homedir)

    # Read the defaults (before the options)
    defaults = os.path.join(pf.pyformexdir, "pyformexrc")
    pf.cfg.read(defaults)

    # The default user config path (do not change!)
    pf.cfg['userprefs'] = os.path.join(pf.cfg['userconfdir'], 'pyformex.conf')

    ########## Process special options which do not start pyFormex #######

    if pf.options.pytest is not None:
        run_pytest(pf.options.pytest)
        return

    if pf.options.doctest is not None:
        for a in pf.options.doctest:
            doctest_module(a)
        return

    if pf.options.docmodule is not None:
        for a in pf.options.docmodule:
            doc_module(a)
        return

    if pf.options.remove:
        remove_pyFormex(pf.pyformexdir, pf.executable)
        return

    if pf.options.whereami: # or pf.options.detect :
        pf.options.debuglevel |= pf.DEBUG.INFO

    if pf.options.detect:
        print("Detecting installed helper software")
        print(software.reportSoftware())

    pf.debug("pyformex executable is %s" % pf.executable, pf.DEBUG.INFO)
    pf.debug("I found pyFormex installed in %s " %  pf.pyformexdir, pf.DEBUG.INFO)
    pf.debug("Current Python sys.path: %s" % sys.path, pf.DEBUG.INFO)
    #sys.exit()

    if pf.options.whereami or pf.options.detect :
        return

    ########### Migrate the user configuration files ####################

    # Migrate the user preferences to the new place under $HOME/.config
    if not os.path.exists(pf.cfg['userprefs']):
        # Check old place
        olduserprefs = os.path.join(homedir, '.pyformex', 'pyformexrc')
        if os.path.exists(olduserprefs):
            print("Migrating your user preferences\n  from %s\n  to %s" % (olduserprefs, pf.cfg['userprefs']))
            try:
                import shutil
                olddir = os.path.dirname(olduserprefs)
                newdir = pf.cfg['userconfdir']
                # Move old user conf file to new and link back
                oldfile = os.path.join(olddir, 'pyformexrc')
                newfile = os.path.join(olddir, 'pyformex.conf')
                print("Moving %s to %s" % (oldfile, newfile))
                shutil.move(oldfile, newfile)
                newfile = 'pyformex.conf'
                print("Symlinking %s to %s" % (newfile, oldfile))
                os.symlink(newfile, oldfile)
                # Move old config dir to new and link back to old
                print("Moving %s to %s" % (olddir, newdir))
                shutil.move(olddir, newdir)
                print("Symlinking %s to %s" % (newdir, olddir))
                os.symlink(newdir, olddir)

            except:
                raise RuntimeError("Error while trying to migrate your user configuration\nTry moving the config files yourself.\nYou may also remove the config directories %s\n and %s alltogether\s to get a fresh start with default config." % (olddir, newdir))

    ########### Load the user configuration  ####################

    # Set the config files
    if pf.options.nodefaultconfig:
        sysprefs = []
        userprefs = []
    else:
        sysprefs = [ pf.cfg['siteprefs'] ]
        userprefs = [ pf.cfg['userprefs'] ]
        if os.path.exists(pf.cfg['localprefs']):
            userprefs.append(pf.cfg['localprefs'])

    sysprefs = list(filter(os.path.exists, sysprefs))
    userprefs = list(filter(os.path.exists, userprefs))

    if pf.options.config:
        userprefs.append(utils.tildeExpand(pf.options.config))

    if len(userprefs) == 0:
        # We should always have a place to store the user preferences
        userprefs = [ pf.cfg['userprefs'] ]

    # Use last one to save preferences
    pf.debug("System Preference Files: %s" % sysprefs, pf.DEBUG.CONFIG)
    pf.debug("User Preference Files: %s" % userprefs, pf.DEBUG.CONFIG)
    pf.preffile = os.path.abspath(userprefs.pop())

    # Read sysprefs as reference
    for f in sysprefs:
        pf.debug("Reading config file %s" % f, pf.DEBUG.CONFIG)
        pf.cfg.read(f)

    # Set this as reference config
    pf.refcfg = pf.cfg
    pf.debug("="*60, pf.DEBUG.CONFIG)
    pf.debug("RefConfig: %s" % pf.refcfg, pf.DEBUG.CONFIG)
    pf.cfg = Config(default=refLookup)

    # Read userprefs as reference
    for f in userprefs:
        if os.path.exists(f):
            pf.debug("Reading config file %s" % f, pf.DEBUG.CONFIG)
            pf.cfg.read(f)
        else:
            pf.debug("Skip non-existing config file %s" % f, pf.DEBUG.CONFIG)
    if os.path.exists(pf.preffile):
        pf.debug("Reading config file %s" % pf.preffile, pf.DEBUG.CONFIG)
        pf.cfg.read(pf.preffile)
    else:
        # Create the config file
        pf.debug("Creating config file %s" % pf.preffile, pf.DEBUG.CONFIG)
        basedir = os.path.dirname(pf.preffile)
        if not os.path.exists(basedir):
            os.makedirs(basedir)
        open(pf.preffile,'a').close()

    # Set this as preferences config
    pf.prefcfg = pf.cfg
    pf.debug("="*60, pf.DEBUG.CONFIG)
    pf.debug("Config: %s" % pf.prefcfg, pf.DEBUG.CONFIG)
    pf.cfg = Config(default=prefLookup)

    # Fix incompatible changes in configuration
    apply_config_changes(pf.prefcfg)

    ####################################################################
    ## Post config initialization ##

    # process non-starting options dependent on config

    if pf.options.search or pf.options.listfiles:
        extended = False
        if len(args) > 0:
            opts = [ a for a in args if a.startswith('-') ]
            args = [ a for a in args if not a in opts ]
            if '-a' in opts:
                opts.remove('-a')
                extended = True
        if pf.options.search:
            search = args.pop(0)
        if len(args) > 0:
            files = args
        else:
            files = utils.sourceFiles(relative=True, extended=extended)
        if pf.options.listfiles:
            print('\n'.join(files))
        else:
            if "'" in search:
                search.replace("'", "\'")
            print("SEARCH = [%s]" % search)
            cmd = 'grep %s "%s" %s' % (' '.join(opts), search, ''.join([" '%s'" % f for f in files]))
            os.system(cmd)
        return

    if pf.options.listmodules is not None:
        #print(pf.options.listmodules)
        if not pf.options.listmodules:
            pf.options.listmodules = [ 'core', 'lib', 'plugins', 'gui', 'opengl' ]
        list_modules(pf.options.listmodules)
        return

    # Start normal pyformex program (gui or nogui)

    # process options that override the config

    if pf.options.pyside is not None:
        pf.cfg['gui/bindings'] = 'PySide' if pf.options.pyside else 'PyQt4'

    if pf.options.redirect is not None:
        pf.cfg['gui/redirect'] = pf.options.redirect
    delattr(pf.options, 'redirect') # avoid abuse

    if pf.options.uselib is None:
        pf.options.uselib = pf.cfg['uselib']

    ###################################################################


    # Set default --nogui if first remaining argument is a pyformex script.
    if pf.options.gui is None:
        pf.options.gui = not (len(args) > 0 and utils.is_pyFormex(args[0]))

    if pf.options.gui:
        pf.options.interactive = True

    # Initialize the libraries
    pf.print3("Trying to import the libraries")
    pf.print3(sys.path)
    from pyformex import lib

    # If we run from a checked out source repository, we should
    # run the source_clean procedure.
    if pf.installtype in 'SG':
        source_clean = os.path.join(pf.pyformexdir, 'source_clean')
        if os.path.exists(source_clean):
            try:
                utils.system(source_clean)
            except:
                print("Error while executing %s, we ignore it and continue" % source_clean)

    # TODO:
    # without this, we get a crash. Maybe config related?
    pf.cfg['gui/startup_warning'] = None

    ###### We have the config and options all set up ############
    filterWarnings()

    def _format_warning(message,category,filename,lineno,line=None):
        """Replace the default warnings.formatwarning

        This allows the warnings being called using a simple mnemonic
        string. The full message is then found from the message module.
        """
        from pyformex import messages
        message = messages.getMessage(message)
        message = """..

pyFormex Warning
================
%s

`Called from:` %s `line:` %s
""" % (message, filename, lineno)
        if line:
            message += "%s\n" % line
        return message


    import warnings
    if pf.cfg['warnings/deprec']:
        # activate DeprecationWarning (since 2.7 default is ignore)
        warnings.simplefilter('default', DeprecationWarning)

    if pf.cfg['warnings/nice']:
        warnings.formatwarning = _format_warning


    software.checkModule('numpy', fatal=True)

    # Make sure pf.PF is a Project
    from pyformex.project import Project
    pf.PF = Project()

    utils.setSaneLocale()

    # Set application paths
    pf.debug("Loading AppDirs", pf.DEBUG.INFO)
    from pyformex import apps
    apps.setAppDirs()

    # Start the GUI if needed
    # Importing the gui should be done after the config is set !!
    #print(pf.options)
    if pf.options.gui:
        if pf.options.mesa:
            os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
        from pyformex.gui import guimain
        pf.debug("GUI version", pf.DEBUG.INFO)
        res = guimain.startGUI(args)
        if res != 0:
            print("Could not start the pyFormex GUI: %s" % res)
            return res # EXIT

    # Display the startup warnings and messages
    if pf.startup_warnings:
        if pf.cfg['startup_warnings']:
            pf.warning(pf.startup_warnings)
        else:
            print(pf.startup_warnings)
    if pf.startup_messages:
        print(pf.startup_messages)

    if pf.options.debuglevel & pf.DEBUG.INFO:
        # NOTE: inside an if to avoid computing the report when not printed
        pf.debug(utils.reportSoftware(), pf.DEBUG.INFO)

    #
    # Qt4 may have changed the locale.
    # Since a LC_NUMERIC setting other than C may cause lots of troubles
    # with reading and writing files (formats become incompatible!)
    # we put it back to a sane setting
    #
    utils.setSaneLocale()

    # Prepend the autorun script
    ar = pf.cfg.get('autorun', '')
    if ar and os.path.exists(ar):
        args[0:0] = [ ar ]

    # remaining args are interpreted as scripts/apps and their parameters
    res = 0
    if args:
        pf.debug("Remaining args: %s" % args, pf.DEBUG.INFO)
        from pyformex.script import processArgs
        res = processArgs(args)

        if res:
            if pf.options.gui:
                print("There was an error while executing a script")
            else:
                return res # EXIT

    else:
        pf.debug("stdin is a tty: %s" % sys.stdin.isatty(), pf.DEBUG.INFO)
        # Play script from stdin
        # Can we check for interactive session: stdin connected to terminal?
        #from script import playScript
        #playScript(sys.stdin)

    # after processing all args, go into interactive mode
    if pf.options.gui and pf.app:
        res = guimain.runGUI()

    ## elif pf.options.interactive:
    ##     print("Enter your script and end with CTRL-D")
    ##     from script import playScript
    ##     playScript(sys.stdin)

    #Save the preferences that have changed
    savePreferences()

    # Exit
    return res


# End
