# $Id$
##
##  This file is part of pyFormex 1.0.2  (Thu Jun 18 15:35:31 CEST 2015)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2015 (C) Benedict Verhegghe (benedict.verhegghe@feops.com)
##  Distributed under the GNU General Public License 3 or later.
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
"""Basic pyFormex script functions

The :mod:`script` module provides the basic functions available
in all pyFormex scripts. These functions are available in GUI and NONGUI
applications, without the need to explicitely importing the :mod:`script`
module.
"""
from __future__ import absolute_import, division, print_function

############### Standard libraries first

import os
import sys
import re
import time
import shutil

############### DEBUGGING MEMORY LEAKS
#try:
#    from pympler import tracker
#    _memtracker = tracker.SummaryTracker()
#except:
#    _memtracker = None

################ pyFormex modules

import pyformex as pf
from pyformex import zip
from pyformex import formex
from pyformex import geomfile
from pyformex import utils
from pyformex.project import Project
from pyformex.geometry import Geometry

######################## more pyFormex stuff
# Imported here only to have them available in scripts
# Everything from utils is passed by default to scripts
from pyformex.olist import List
from pyformex.varray import Varray
from pyformex.formex import *
from pyformex.mesh import Mesh
from pyformex.trisurface import TriSurface
from pyformex.coordsys import CoordSys
from pyformex.curve import PolyLine, BezierSpline
from pyformex import simple


######################### Exceptions #########################################

class _Exit(Exception):
    """Exception raised to exit from a running script."""
    pass


############################# Globals for scripts ############################


def Globals():
    """Return the globals that are passed to the scripts on execution.

    When running pyformex with the --nogui option, this contains all the
    globals defined in the module formex (which include those from
    coords, arraytools and numpy.

    When running with the GUI, this also includes the globals from gui.draw
    (including those from gui.color).

    Furthermore, the global variable __name__ will be set to either 'draw'
    or 'script' depending on whether the script was executed with the GUI
    or not.
    """
    # :DEV it is not a good idea to put the pf.PF in the globals(),
    # because pf.PF may contain keys that are not acceptible as
    # Python names
    g = {}
    g.update(globals())
    if pf.GUI:
        from pyformex.gui import draw
        g.update(draw.__dict__)
    g.update(formex.__dict__)
    # Set module correct
    if pf.GUI:
        modname = '__draw__'
    else:
        modname = '__script__'
    g['__name__'] = modname
    return g


def export(dic):
    """Export the variables in the given dictionary."""
    pf.PF.update(dic)


def export2(names, values):
    """Export a list of names and values."""
    export(zip(names, values))


def forget(names):
    """Remove the global variables specified in list."""
    g = pf.PF
    for name in names:
        if name in g:
            del g[name]


def forgetAll():
    """Delete all the global variables."""
    pf.PF = {}


def rename(oldnames, newnames):
    """Rename the global variables in oldnames to newnames."""
    g = pf.PF
    for oldname, newname in zip(oldnames, newnames):
        if oldname in g:
            g[newname] = g[oldname]
            del g[oldname]


def listAll(clas=None,like=None,filtr=None,dic=None,sort=False):
    """Return a list of all objects in dictionay that match criteria.

    - dic: a dictionary object, defaults to pyformex.PF
    - clas: a class or list of classes: if specified, only instances of
      this/these class(es) will be returned
    - like: a string: if given, only object names starting with this string
      will be returned
    - filtr: a function taking an object name as parameter and returning True
      or False. If specified, only objects passing the test will be returned.

    The return value is a list of keys from dic.
    """
    if dic is None:
        dic = pf.PF

    names = dic.keys()
    if clas is not None:
        names = [ n for n in names if isinstance(dic[n], clas) ]
    if like is not None:
        names = [ n for n in names if n.startswith(like) ]
    if filtr is not None:
        names = [ n for n in names if filtr(n) ]
    if sort:
        names.sort()
    return names


def named(name):
    """Returns the global object named name."""
    if name in pf.PF:
        dic = pf.PF
    else:
        raise NameError("Name %s is not in pyformex.PF" % name)
    return dic[name]


def getcfg(name):
    """Return a value from the configuration."""
    return pf.cfg.get(name, None)


#################### Interacting with the user ###############################

def ask(question,choices=None,default=''):
    """Ask a question and present possible answers.

    If no choices are presented, anything will be accepted.
    Else, the question is repeated until one of the choices is selected.
    If a default is given and the value entered is empty, the default is
    substituted.
    Case is not significant, but choices are presented unchanged.
    If no choices are presented, the string typed by the user is returned.
    Else the return value is the lowest matching index of the users answer
    in the choices list. Thus, ask('Do you agree',['Y','n']) will return
    0 on either 'y' or 'Y' and 1 on either 'n' or 'N'.
    """
    if choices:
        question += " (%s) " % ', '.join(choices)
        choices = [ c.lower() for c in choices ]
    while True:
        res = pf.userInput(question)
        if res == '' and default:
            res = default
        if not choices:
            return res
        try:
            return choices.index(res.lower())
        except ValueError:
            pass

def ack(question):
    """Show a Yes/No question and return True/False depending on answer."""
    return ask(question, ['Y', 'N']) == 0


def error(message):
    """Show an error message and wait for user acknowlegement."""
    print("pyFormex Error: "+message)
    if not ack("Do you want to continue?"):
        exit()

def warning(message):
    print("pyFormex Warning: "+message)
    if not ack("Do you want to continue?"):
        exit()

def showInfo(message):
    print("pyFormex Info: "+message)


system = utils.system
command = utils.command


########################### PLAYING SCRIPTS ##############################

exitrequested = False
starttime = 0.0
scriptInit = None # can be set to execute something before each script


def autoExport(g):
    """Autoexport globals from script/app globals.

    g: dict holding the globals dict from a script/app run enviroment.

    This exports some objects from the script/app runtime globals
    to the pf.PF session globals directory.
    The default is to export all instances of class Geometry.

    This can be customized in the script/app by setting the global
    variable `autoglobals`. If set to a value that evaluates to
    False, no autoexport will be done. If set to True, the default
    autoexport will be done: all instances of :class:`geometry`.
    If set to a list of names, only the specified names will be exported.
    Furthermore, a global variable `autoclasses` may be set
    to a list of class names. All global instances of the specified classes
    will be exported.

    Remember that the variables need to be globals in your script/app
    in order to be autoexported, and that autoglobals feature needs to
    be enabled in your configuration.
    """
    ag = g.get('autoglobals',True)
    if ag:
        if ag is True:
            # default autoglobals: all Geometry instances
            ag = [ Geometry ]
        an = []
        for a in ag:
            if isinstance(a,str) and a in g:
                an.append(a)
            elif isinstance(a,type):
                try:
                    an.extend(listAll(clas=a, dic=g))
                except:
                    pass
        if an:
            an = sorted(list(set(an)))
            print("Autoglobals: %s" % ', '.join(an))
            pf.PF.update([(k, g[k]) for k in an])


def scriptLock(id):
    global _run_mode
    if id == '__auto/script__':
        pf.scriptMode = 'script'
    elif id == '__auto/app__':
        pf.scriptMode = 'app'

    pf.debug("Setting script lock %s" %id, pf.DEBUG.SCRIPT)
    pf.scriptlock |= {id}

def scriptRelease(id):
    pf.debug("Releasing script lock %s" %id, pf.DEBUG.SCRIPT)
    pf.scriptlock -= {id}
    pf.scriptMode = None


def playScript(scr,name=None,filename=None,argv=[],pye=False):
    """Play a pyformex script scr. scr should be a valid Python text.

    There is a lock to prevent multiple scripts from being executed at the
    same time. This implies that pyFormex scripts can currently not be
    recurrent.
    If name is specified, set the global variable pyformex.scriptName to it
    when the script is started.
    If filename is specified, set the global variable __file__ to it.
    """
    utils.warn('print_function')
    global starttime
    global exitrequested

    # (We only allow one script executing at a time!)
    # and scripts are non-reentrant
    if len(pf.scriptlock) > 0:
        print("!!Not executing because a script lock has been set: %s" % pf.scriptlock)
        return 1

    scriptLock('__auto/script__')
    exitrequested = False

    if pf.GUI:
        pf.GUI.startRun()

    # Read the script, if a file was specified
    if not isinstance(scr, (str,unicode)):
        # scr should be an open file/stream
        if filename is None:
            filename = scr.name
        scr = scr.read() + '\n'

    # Get the globals
    g = Globals()
    if filename:
        g.update({'__file__':filename})
    g.update({'argv':argv})

    # BV: Should we continue support for this?
    if pye:
        n = (len(scr)+1) // 2
        scr = utils.mergeme(scr[:n], scr[n:])

    # Now we can execute the script using these collected globals
    pf.scriptName = name
    exitall = False

    if pf.DEBUG.MEM:
        memu = memUsed()
        vmsiz = vmSize()
        pf.debug("MemUsed = %s; vmSize = %s" % (memu, vmsiz), pf.DEBUG.MEM)

    if filename is None:
        filename = '<string>'

    # Execute the code
    #starttime = time.clock()
    try:
        pf.interpreter.locals.update(g)
        pf.interpreter.runsource(scr, filename, 'exec')

    except SystemExit:
        print ("EXIT FROM SCRIPT")

    finally:
        # honour the exit function
        if 'atExit' in g:
            atExit = g['atExit']
            try:
                atExit()
            except:
                pf.debug('Error while calling script exit function', pf.DEBUG.SCRIPT)

        if pf.cfg['autoglobals']:
            if pf.console:
                g = pf.console.interpreter.locals
            autoExport(g)
        scriptRelease('__auto/script__') # release the lock
        if pf.GUI:
            pf.GUI.stopRun()

    pf.debug("MemUsed = %s; vmSize = %s" % (memUsed(), vmSize()), pf.DEBUG.MEM)
    pf.debug("Diff MemUsed = %s; diff vmSize = %s" % (memUsed()-memu, vmSize()-vmsiz), pf.DEBUG.MEM)

    if exitall:
        pf.debug("Calling quit() from playscript", pf.DEBUG.SCRIPT)
        quit()

    return 0


def force_finish():
    pf.scriptlock = set() # release all script locks (in case of an error)
    #print(pf.scriptlock)


def breakpt(msg=None):
    """Set a breakpoint where the script can be halted on a signal.

    If an argument is specified, it will be written to the message board.

    The exitrequested signal is usually emitted by pressing a button in the GUI.
    """
    global exitrequested
    if exitrequested:
        if msg is not None:
            print(msg)
        exitrequested = False # reset for next time
        raise SystemExit


def raiseExit():
    pf.debug("RAISING SystemExit", pf.DEBUG.SCRIPT)
    if pf.GUI:
        pf.GUI.drawlock.release()
    raise _Exit("EXIT REQUESTED FROM SCRIPT")


def enableBreak(mode=True):
    if pf.GUI:
        pf.GUI.enableButtons(pf.GUI.actions, ['Stop'], mode)


def stopatbreakpt():
    """Set the exitrequested flag."""
    global exitrequested
    exitrequested = True


def convertPrintSyntax(filename):
    """Convert a script to using the print function"""
    P = utils.system("2to3 -f print -wn %s" % filename)
    if P.sta:
        # Conversion error: show what is going on
        print(P.out)
    return P.sta == 0


def checkPrintSyntax(filename):
    """Check whether the script in the given files uses print function syntax.

    Returns the compiled object if no error was found during compiling.
    Returns the filename if an error was found and correction has been
    attempted.
    Raises an exception if an error is found and no correction attempted.
    """
    with open(filename, 'r') as f:
        try:
            script = f.read()
            scr = compile(script, filename, 'exec')
            return scr
        except SyntaxError as err:
            if re.compile('.*print +[^ (]').match(err.text):
                ans = pf.warning("""..

Syntax error in line %s of %s::

  %s

It looks like your are using a print statement instead of the print function.
In order to prepare you for the future (Python3), pyFormex already enforces
the use of the print function.
This means that you have to change any print statement from::

    print something

into a print function call::

    print(something)

You can try an automatic conversion with the command::

    2to3 -f print -%s

If you want, I can run this command for you now. Beware though!
This will overwrite the contents of file %s.

Also, the automatic conversion is not guaranteed to work, because
there may be other errors.
""" % (err.lineno, err.filename, err.text, filename, filename), actions=['Not this time', 'Convert now'],)
                if ans == 'Convert now':
                    print(ans)
                    if convertPrintSyntax(filename):
                        print("Script properly converted, now running the converted script")
                        return filename
                raise


def runScript(fn,argv=[]):
    """Play a formex script from file fn.

    fn is the name of a file holding a pyFormex script.
    A list of arguments can be passed. They will be available under the name
    argv. This variable can be changed by the script and the resulting argv
    is returned to the caller.
    """
    from pyformex.timer import Timer
    t = Timer()
    msg = "Running script (%s)" % fn
    if pf.GUI:
        pf.GUI.scripthistory.add(fn)
        pf.GUI.board.write(msg, color='red')
    else:
        print(msg)
    pf.debug("  Executing with arguments: %s" % argv, pf.DEBUG.SCRIPT)
    pye = fn.endswith('.pye')
    if pf.GUI and getcfg('check_print'):
        pf.debug("Testing script for use of print function", pf.DEBUG.SCRIPT)
        scr = checkPrintSyntax(fn)
        #
        # TODO: if scr is a compiled object, we could just execute it
        #

    res = playScript(open(fn, 'r'), fn, fn, argv, pye)
    pf.debug("  Arguments left after execution: %s" % argv, pf.DEBUG.SCRIPT)
    msg = "Finished script %s in %s seconds" % (fn, t.seconds())
    if pf.GUI:
        pf.GUI.board.write(msg, color='red')
    else:
        print(msg)
    return res


def runApp(appname,argv=[],refresh=False,lock=True,check=True):
    """Run a pyFormex application.

    A pyFormex application is a Python module that can be loaded in
    pyFormex and that contains a function 'run()'. Running the application
    is equivalent to executing this function.

    Parameters:

    - `appname`: name of the module in Python dot notation. The module should
    live in a path included the the a file holding a pyFormex script.

    - `argv`: list of arguments. This variable can be changed by the app
    and the resulting argv will be returned to the caller.

    Returns the exit value of the run function. A zero value is supposed
    to mean a normal exit.
    """
    global exitrequested
    if check and len(pf.scriptlock) > 0:
        print("!!Not executing because a script lock has been set: %s" % pf.scriptlock)
        return

    from pyformex import apps
    from pyformex.timer import Timer
    t = Timer()
    print("Loading application %s with refresh=%s" % (appname, refresh))
    app = apps.load(appname, refresh=refresh)
    if app is None:
        errmsg = "An  error occurred while loading application %s" % appname
        if pf.GUI:
            if apps._traceback and pf.cfg['showapploaderrors']:
                print(apps._traceback)

            from pyformex.gui import draw
            fn = apps.findAppSource(appname)
            if os.path.exists(fn):
                errmsg += "\n\nYou may try executing the application as a script,\n  or you can load the source file in the editor."
                res = draw.ask(errmsg, choices=['Run as script', 'Load in editor', "Don't bother"])
                if res[0] in 'RL':
                    if res[0] == 'L':
                        draw.editFile(fn)
                    elif res[0] == 'R':
                        pf.GUI.setcurfile(fn)
                        draw.runScript(fn)
            else:
                errmsg += "and I can not find the application source file."
                draw.error(errmsg)
        else:
            error(errmsg)

        return

    if hasattr(app, '_opengl2') and not app._opengl2:
        pf.warning("This Example can not yet be run under the pyFormex opengl2 engine.\n")
        return

    if hasattr(app, '_status') and app._status == 'unchecked':
        pf.warning("This looks like an Example script that has been automatically converted to the pyFormex Application model, but has not been checked yet as to whether it is working correctly in App mode.\nYou can help here by running and rerunning the example, checking that it works correctly, and where needed fixing it (or reporting the failure to us). If the example runs well, you can change its status to 'checked'")

    if lock:
        scriptLock('__auto/app__')
    msg = "Running application '%s' from %s" % (appname, app.__file__)
    pf.scriptName = appname
    if pf.GUI:
        pf.GUI.startRun()
        pf.GUI.apphistory.add(appname)
        pf.GUI.board.write(msg, color='green')
    else:
        print(msg)
    pf.debug("  Passing arguments: %s" % argv, pf.DEBUG.SCRIPT)
    app._args_ = argv
    try:
        try:
            res = app.run()
        except SystemExit:
            print ("EXIT FROM APP")
            pass
        except:
            raise
    finally:
        if hasattr(app, 'atExit'):
            app.atExit()
        if pf.cfg['autoglobals']:
            g = app.__dict__
            autoExport(g)
        if lock:
            scriptRelease('__auto/app__') # release the lock
        if pf.GUI:
            pf.GUI.stopRun()

    pf.debug("  Arguments left after execution: %s" % argv, pf.DEBUG.SCRIPT)
    msg = "Finished %s in %s seconds" % (appname, t.seconds())
    if pf.GUI:
        pf.GUI.board.write(msg, color='green')
    else:
        print(msg)
    pf.debug("Memory: %s" % vmSize(), pf.DEBUG.MEM)
    return res


def runAny(appname=None,argv=[],step=False,refresh=False,remember=True):
    """Run the current pyFormex application or script file.

    Parameters:

    - `appname`: either the name of a pyFormex application (app) or a file
      containing a pyFormex script. An app name is specified in Python
      module syntax (package.subpackage.module) and the path to the package
      should be in the configured app paths.

    This function does nothing if no appname/filename is passed or no current
    script/app was set.
    If arguments are given, they are passed to the script. If `step` is True,
    the script is executed in step mode. The 'refresh' parameter will reload
    the app.
    """
    if appname is None:
        appname = pf.cfg['curfile']
    if not appname:
        return

    if scriptInit:
        scriptInit()

    if pf.GUI and remember:
        pf.GUI.setcurfile(appname)

    if utils.is_script(appname):
        return runScript(appname, argv)
    else:
        return runApp(appname, argv, refresh)


def exit(all=False):
    """Exit from the current script or from pyformex if no script running."""
    if len(pf.scriptlock) > 0:
        if all:
            utils.warn("warn_exit_all")
            pass
        else:
            # This is the only exception we can use in script mode
            # to stop the execution
            raise SystemExit


def quit():
    """Quit the pyFormex program

    This is a hard exit from pyFormex. It is normally not called
    directly, but results from an exit(True) call.
    """
    if pf.app and pf.app_started: # quit the QT app
        pf.debug("draw.exit called while no script running", pf.DEBUG.SCRIPT)
        pf.app.quit() # closes the GUI and exits pyformex
    else: # the QT app didn't even start
        sys.exit(0) # use Python to exit pyformex


def processArgs(args):
    """Run the application without gui.

    Arguments are interpreted as names of script files, possibly interspersed
    with arguments for the scripts.
    Each running script should pop the required arguments from the list.
    """
    res = 0
    while len(args) > 0:
        fn = args.pop(0)
        if fn == '-c':
            # next arg is a script
            txt = args.pop(0)
            res = playScript(txt,name='__inline__')
        else:
            res = runAny(fn, args,remember=False)
        if res:
            print("Error during execution of script/app %s" % fn)

    return res


def setPrefs(res,save=False):
    """Update the current settings (store) with the values in res.

    res is a dictionary with configuration values.
    The current settings will be update with the values in res.

    If save is True, the changes will be stored to the user's
    configuration file.
    """
    pf.debug("Accepted settings:\n%s"%res, pf.DEBUG.CONFIG)
    for k in res:
        pf.cfg[k] = res[k]
        if save and pf.prefcfg[k] != pf.cfg[k]:
            pf.prefcfg[k] = pf.cfg[k]

    pf.debug("New settings:\n%s"%pf.cfg, pf.DEBUG.CONFIG)
    if save:
        pf.debug("New preferences:\n%s"%pf.prefcfg, pf.DEBUG.CONFIG)


########################## print information ################################


def printall():
    """Print all Formices in globals()"""
    print("Formices currently in globals():\n%s" % listAll(clas=formex.Formex))


def printglobals():
    print(Globals())


def printglobalnames():
    print(sorted(Globals().keys()))


def printconfig():
    print("Reference Configuration: " + str(pf.refcfg))
    print("Preference Configuration: " + str(pf.prefcfg))
    print("User Configuration: " + str(pf.cfg))


def printdetected():
    print(utils.reportSoftware())


def printLoadedApps():
    from pyformex import apps, sys
    loaded = apps.listLoaded()
    refcnt = [ sys.getrefcount(sys.modules[k]) for k in loaded ]
    print(', '.join([ "%s (%s)" % (k, r) for k, r in zip(loaded, refcnt)]))


def printEnv():
    """Print the environment."""
    print(utils.formatDict(os.environ.data))


# THis is not a good way of computing memory usage
def vmSize():
    import os
    return int(os.popen('ps h o vsize %s'%os.getpid()).read().strip())

def memUsed():
    return utils.memory_report()['MemUsed']

def printVMem(msg='MEMORY'):
    print('%s: VmSize=%skB'%(msg, vmSize()))


### Utilities

def isWritable(path):
    """Check that the specified path is writable.

    BEWARE: this only works if the path exists!
    """
    return os.access(path, os.W_OK)


def chdir(path,create=False):
    """Change the current working directory.

    If path exists and it is a directory name, make it the current directory.
    If path exists and it is a file name, make the containing directory the
    current directory.
    If path does not exist and create is True, create the path and make it the
    current directory. If create is False, raise an Error.

    Parameters:

    - `path`: pathname of the directory or file. If it is a file, the name of
      the directory holding the file is used. The path can be an absolute
      or a relative pathname. A '~' character at the start of the pathname will
      be expanded to the user's home directory.

    - `create`: bool. If True and the specified path does not exist, it will
      be created. The default is to do nothing if the specified path does
      not exist.

    The changed to current directory is stored in the user's preferences
    for persistence between pyFormex invocations.

    """
    path = utils.tildeExpand(path)
    if os.path.exists(path):
        if not os.path.isdir(path):
            path = os.path.dirname(os.path.abspath(path))
    else:
        if create:
            mkdir(path)
        else:
            raise OsError("The path %s does not exist" % path)
    try:
        os.chdir(path)
        setPrefs({'workdir':path}, save=True)
    except:
        pass
    pwdir()
    if pf.GUI:
        pf.GUI.setcurdir()


def pwdir():
    """Print the current working directory.

    """
    print("Current workdir is %s" % os.getcwd())


def mkdir(path, clear=False, new=False):
    """Create a directory.

    Create a directory, including any needed parent directories.
    Any part of the path may already exist.

    - `path`: pathname of the directory to create, either an absolute
      or relative path. A '~' character at the start of the pathname will
      be expanded to the user's home directory.
    - `clear`: bool. If True, and the directory already exists, its contents
      will be deleted.
    - `new`: bool. If True, requires the directory to be a new one. An error
      will be raised if the path already exists.

    The following table gives an overview of the actions for different
    combinations of the parameters:

    ======   ====  ====================  =============
    clear    new   path does not exist   path exists
    ======   ====  ====================  =============
    F        F     kept as is            newly created
    T        F     emptied               newly created
    T/F      T     raise                 newly created
    ======   ====  ====================  =============

    If succesful, returns the tilde-expanded path of the directory.
    Raises an exception in the following cases:

    - the directory could not be created,
    - `clear` is True, and the existing directory could not be cleared,
    - `new` is False, `clear` is False, and the existing path is not a directory,
    - `new` is True, and the path exists.

    """
    path = utils.tildeExpand(path)
    if new and os.path.exists(path):
        raise OsError("Path already exists: %s" % path)
    if clear:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    if sys.hexversion >= 0x03040100:
        os.makedirs(path, exist_ok=not new)
    else:
        try:
            os.makedirs(path)
        except OSError:
            if not os.path.isdir(path):
                raise


def mkpdir(path):
    """Make sure the parent directory of path exists.

    """
    return mkdir(os.path.dirname(path))



def runtime():
    """Return the time elapsed since start of execution of the script."""
    return time.clock() - starttime


def startGui(args=[]):
    """Start the gui"""
    if pf.GUI is None:
        pf.debug("Starting the pyFormex GUI", pf.DEBUG.GUI)
        from pyformex.gui import guimain
        if guimain.startGUI(args) == 0:
            guimain.runGUI()


#
# OBSOLETE : we do not have a revision number anymore
#
## def checkRevision(rev,comp='>='):
##     """Check the pyFormex revision number.

##     - rev: a positive integer.
##     - comp: a string specifying a comparison operator.

##     By default, this function returns True if the pyFormex revision
##     number is equal or larger than the specified number.

##     The comp argument may specify another comparison operator.

##     If pyFormex is unable to find its revision number (this is the
##     case on very old versions) the test returns False.
##     """
##     try:
##         cur = int(utils.splitStartDigits(pf.__revision__)[0])
##         return eval("%s %s %s" % (cur, comp, rev))
##     except:
##         return False


## def requireRevision(rev,comp='>='):
##     """Require a specified pyFormex revision number.

##     The arguments are like checkRevision. However, this function will
##     raise an error if the requirement fails.
##     """
##     if not checkRevision(rev, comp):
##         raise RuntimeError("Your current pyFormex revision (%s) does not pass the test %s %s" % (pf.__revision__, comp, rev))


## print("REVISION: %s" % pf.__revision__)


################### read and write files #################################

def writeGeomFile(filename,objects,sep=' ',mode='w',shortlines=False,**kargs):
    """Save geometric objects to a pyFormex Geometry File.

    A pyFormex Geometry File can store multiple geometrical objects in a
    native format that can be efficiently read back into pyformex.
    The format is portable over different pyFormex versions and
    even to other software.

    - `filename`: the name of the file to be written. If it ends with '.gz'
      or '.bz2', the file will be compressed with gzip or bzip2, respectively.
    - `objects`: a list or a dictionary. If it is a dictionary,
      the objects will be saved with the key values as there names.
      Objects that can not be exported to a Geometry File will be
      silently ignored.
    - `mode`: can be set to 'a' to append to an existing file.
    - `sep`: the string used to separate data. If set to an empty
      string, the data will be written in binary format and the resulting file
      will be smaller but less portable.
    - `kargs`: more arguments are passed to :meth:`geomfile.GeometryFile.write`.

    Returns the number of objects written to the file.
    """
    print("Writing PGF file '%s'" % os.path.abspath(filename))
    f = geomfile.GeometryFile(filename, mode, sep=sep,**kargs)
    # TODO: shis option could goto into GeometryFile
    if shortlines:
        f.fmt = {'i':'%i ','f':'%f '}
    nobj = f.write(objects)
    f.close()
    return nobj


def readGeomFile(filename,count=-1):
    """Read a pyFormex Geometry File.

    A pyFormex Geometry File can store multiple geometrical objects in a
    native format that can be efficiently read back into pyformex.
    The format is portable over different pyFormex versions and
    even to other software.

    - `filename`: the name of an existing pyFormex Geometry File. If the
      filename ends on '.gz', it is considered to be a gzipped file and
      will be uncompressed transparently during the reading.

    Returns a dictionary with the geometric objects read from the file.
    If object names were stored in the file, they will be used as the keys.
    Else, default names will be provided.
    """
    print("Reading PGF file '%s'" % os.path.abspath(filename))
    f = geomfile.GeometryFile(filename, 'r')
    objects = f.read(count)
    return objects


# Always create an interpreter

import code
pf.interpreter = code.InteractiveInterpreter(Globals())


############# deprecated functions ##################

@utils.deprecated_by('script.message','print')
def message(*args):
    print(*args)

#### End
