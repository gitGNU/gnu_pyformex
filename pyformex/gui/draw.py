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
"""Create 3D graphical representations.

The draw module provides the basic user interface to the OpenGL
rendering capabilities of pyFormex. The full contents of this module
is available to scripts running in the pyFormex GUI without the need
to import it.
"""
from __future__ import print_function


import pyformex as pf

from pyformex import utils
from pyformex import messages
from pyformex.gui import widgets

# Things that we want in the scripting language
Dialog = widgets.InputDialog
_I = widgets.simpleInputItem
_G = widgets.groupInputItem
_T = widgets.tabInputItem
from pyformex.script import *
from pyformex.opengl.colors import *
from pyformex.gui.toolbar import timeout
from pyformex.gui import image


import numpy
import os
import sys

#################### Interacting with the user ###############################


def closeGui():
    """Close the GUI.

    Calling this function from a script closes the GUI and terminates
    pyFormex.
    """
    pf.debug("Closing the GUI: currently, this will also terminate pyformex.", pf.DEBUG.GUI)
    pf.GUI.close()


def closeDialog(name):
    """Close the named dialog.

    Closes the InputDialog with the given name. If multiple dialogs are
    open with the same name, all these dialogs are closed.

    This only works for dialogs owned by the pyFormex GUI.
    """
    pf.GUI.closeDialog(name)


def showMessage(text,actions=['OK'],level='info',modal=True,align='00',**kargs):
    """Show a short message widget and wait for user acknowledgement.

    There are three levels of messages: 'info', 'warning' and 'error'.
    They differ only in the icon that is shown next to the test.
    By default, the message widget has a single button with the text 'OK'.
    The dialog is closed if the user clicks a button.
    The return value is the button text.
    """
    w = widgets.MessageBox(text,level=level,actions=actions,**kargs)
    if align == '--':
        w.move(100, 100)
    if modal:
        return w.getResults()
    else:
        w.show()
        return None


def showInfo(text,actions=['OK'],modal=True):
    """Show an informational message and wait for user acknowledgement."""
    return showMessage(text, actions, 'info', modal)

def warning(text,actions=['OK']):
    """Show a warning message and wait for user acknowledgement."""
    return showMessage(text, actions, 'warning')

def error(text,actions=['OK']):
    """Show an error message and wait for user acknowledgement."""
    return showMessage(text, actions, 'error')


def ask(question,choices=None,**kargs):
    """Ask a question and present possible answers.

    Return answer if accepted or default if rejected.
    The remaining arguments are passed to the InputDialog getResult method.
    """
    return showMessage(question,choices,'question',**kargs)


def ack(question,**kargs):
    """Show a Yes/No question and return True/False depending on answer."""
    return ask(question,['No', 'Yes'],**kargs) == 'Yes'


def showText(text,itemtype='text',actions=[('OK', None)],modal=True,mono=False):
    """Display a text in a dialog window.

    Creates a dialog window displaying some text. The dialog can be modal
    (blocking user input to the main window) or modeless.
    Scrollbars are added if the text is too large to display at once.
    By default, the dialog has a single button to close the dialog.

    Parameters:

    - `text`: a multiline text to be displayed. It can be plain text or html
      or reStructuredText (starts with '..').
    - `itemtype`: an InputItem type that can be used for text display. This
      should be either 'text' of 'info'.
    - `actions`: a list of action button definitions.
    - `modal`: bool: if True, a modal dialog is constructed. Else, the dialog
      is modeless.
    - `mono`: if True, a monospace font will be used. This is only useful for
      plain text, e.g. to show the output of an external command.

    Returns:

    :modal dialog: the result of the dialog after closing.
      The result is a dictionary with a single key: 'text' having the
      displayed text as a value. If an itemtype 'text' was used, this may
      be a changed text.
    :modeless dialog: the open dialog window itself.

    """
    if mono:
        font = "DejaVu Sans Mono"
    else:
        font = None
    w = Dialog(size=(0.75, 0.75),
        items=[_I('text', text, itemtype=itemtype, text='', font=font, size=(-1, -1))],
        modal=modal,
        actions=actions,
        caption='pyFormex Text Display',
        )
    if modal:
        return w.getResults()
    else:
        w.show()
        return w


def showFile(filename,mono=True,**kargs):
    """Display a text file.

    This will use the :func:`showText()` function to display a text read
    from a file.
    By default this uses a monospaced font.
    Other arguments may also be passed to ShowText.
    """
    try:
        f = open(filename, 'r')
    except IOError:
        return
    showText(f.read(),mono=mono,**kargs)
    f.close()


def showDoc(obj=None,rst=True,modal=False):
    """Show the docstring of an object.

    Parameters:

    - `obj`: any object (module, class, method, function) that has a
      __doc__ attribute. If None is specified, the docstring of the current
      application is shown.
    - `rst`: bool. If True (default) the docstring is treated as being
      reStructuredText and will be nicely formatted accordingly.
      If False, the docstring is shown as plain text.
    """
    text = None
    if obj is None:
        if not pf.GUI.canPlay:
            return
        obj = pf.prefcfg['curfile']
        if utils.is_script(obj):
            #print "obj is a script"
            from pyformex.utils import getDocString
            text = getDocString(obj)
            obj = None
        else:
            from pyformex import apps
            obj = apps.load(obj)

    if obj:
        text = obj.__doc__

    if text is None:
        raise ValueError("No documentation found for object %s" % obj)

    text = utils.forceReST(text, underline=True)
    if pf.GUI.doc_dialog is None:
        if modal:
            actions=[('OK', None)]
        else:
            actions = [('Close', pf.GUI.close_doc_dialog)]
        pf.GUI.doc_dialog = showText(text, actions=actions, modal=modal)
    else:
        #
        # TODO: check why needed: without sometimes fails
        # RuntimeError: wrapped C/C++ object of %S has been deleted
        # probably when runall?
        #
        try:
            pf.GUI.doc_dialog.updateData({'text':text})
            # pf.GUI.doc_dialog.show()
            pf.GUI.doc_dialog.raise_()
            pf.GUI.doc_dialog.update()
            pf.app.processEvents()
        except:
            pass


def editFile(fn,exist=False):
    """Load a file into the editor.

    Parameters:

    - `fn`: filename. The corresponding file is loaded into the editor.
    - `exist`: bool. If True, only existing filenames will be accepted.

    Loading a file in the editor is done by executing an external command with
    the filename as argument. The command to be used can be set in the
    configuration. If none is set, pyFormex will try to lok at the `EDITOR`
    and `VISUAL` environment settings.

    The main author of pyFormex uses 'emacsclient' as editor command,
    to load the files in a running copy of Emacs.
    """
    print("Edit File: %s" % fn)
    if pf.cfg['editor']:
        if exist and not os.path.exists(fn):
            return
        utils.system('%s %s' % (pf.cfg['editor'], fn),wait=False)
    else:
        warning('No known editor was found or configured')


# widget and result status of the widget in askItems() function
_dialog_widget = None
_dialog_result = None

def askItems(items,timeout=None,**kargs):
    """Ask the value of some items to the user.

    Create an interactive widget to let the user set the value of some items.
    The items are specified as a list of dictionaries. Each dictionary
    contains the input arguments for a widgets.InputItem. It is often
    convenient to use one of the _I, _G, ot _T functions to create these
    dictionaries. These will respectively create the input for a
    simpleInputItem, a groupInputItem or a tabInputItem.

    For convenience, simple items can also be specified as a tuple.
    A tuple (key,value) will be transformed to a dict
    {'key':key, 'value':value}.

    See the widgets.InputDialog class for complete description of the
    available input items.

    A timeout (in seconds) can be specified to have the input dialog
    interrupted automatically and return the default values.

    The remaining arguments are keyword arguments that are passed to the
    widgets.InputDialog.getResult method.

    Returns a dictionary with the results: for each input item there is a
    (key,value) pair. Returns an empty dictionary if the dialog was canceled.
    Sets the dialog timeout and accepted status in global variables.
    """
    global _dialog_widget, _dialog_result

    w = widgets.InputDialog(items,**kargs)

    _dialog_widget = w
    _dialog_result = None
    res = w.getResults(timeout)
    _dialog_widget = None
    _dialog_result = w.result()
    return res


def currentDialog():
    """Returns the current dialog widget.

    This returns the dialog widget created by the askItems() function,
    while the dialog is still active. If no askItems() has been called
    or if the user already closed the dialog, None is returned.
    """
    return _dialog_widget

def dialogAccepted():
    """Returns True if the last askItems() dialog was accepted."""
    return _dialog_result == widgets.ACCEPTED

def dialogRejected():
    """Returns True if the last askItems() dialog was rejected."""
    return _dialog_result == widgets.REJECTED

def dialogTimedOut():
    """Returns True if the last askItems() dialog timed out."""
    return _dialog_result == widgets.TIMEOUT


def askFile(cur=None,filter='all',exist=True,multi=False,compr=False,change=True,timeout=None,caption=None,sidebar=None):
    """Ask for a file name or multiple file names using a file dialog.

    Parameters:

    - `cur`: directory or filename. Specifies the starting point of the
      selection dialog. All the files in the specified directory (or the
      file's directory) matching the `filter` will be presented to the user.
      If cur is a file, it will be set as the initial selection.
    - `filter`: string or list of strings. Specifies a (set of) filter(s) to
      be applied on the files in the selected directory. This allows to
      narrow down the selection possibilities. The `filter` argument is passed
      through the :func:`utils.fileDescription` function to create the
      actual filter set. If multiple filters are included, the user can
      select the appropriate one from the dialog.
    - `multi`: bool. If True, allows the user to pick multiple file names
      in a single operation.
    - `compr`: bool. If True, the specified pattern will be extended with
      the corresponding compressed file types.
    - `change`: bool. If True (default), the current working directory will
      be changed to the parent directory of the selection.
    - `caption`: string. This string will be displayed as the dialog title
      instead of the default one.
    - `timeout`: float. If specified, the dialog will timeout after the
      specified number of seconds.
    - `caption`: string. If specified, it will be displayed as the FileDialog
      title.
    - `sidebar`: list of paths. If specified, these will be added to the
      sidebar (in addition to the configured paths).

    Returns the result of the file dialog. If the user accepted the selection,
    this will be a Dict with at least a key 'fn' holding the selected
    filename(s): a single file name is if `multi` is False, or a list of file
    names if `multi` is True. If the user canceled the selection process,
    an empty dict is returned.
    """
    if cur is None:
        cur = pf.cfg['workdir']
    if os.path.isdir(cur):
        fn = ''
    else:
        fn = os.path.basename(cur)
        cur = os.path.dirname(cur)
    if filter == 'pgf':
        w = widgets.GeometryFileDialog(cur, filter, exist, compr=compr, caption=caption,sidebar=sidebar)
    else:
        w = widgets.FileDialog(cur, filter, exist, multi=multi, compr=compr, caption=caption, sidebar=sidebar)
    if fn:
        w.selectFile(fn)
    res = w.getResults(timeout)
    if res:

        fn = res.fn
        fs = w.selectedNameFilter()
        if not exist and not multi:
            # Check and force extension for single new file
            okext = utils.fileExtensionsFromFilter(fs)
            print("Accepted extensions: %s" % okext)
            ok = False
            for ext in okext:
                if fn.endswith(ext):
                    ok = True
                    break
            if not ok:
                fn += okext[0]
            res['fn'] = fn

        if fn and change:
            if multi:
                cur = fn[0]
            else:
                cur = fn
            cur = os.path.dirname(cur)
            chdir(cur)
    pf.GUI.update()
    pf.app.processEvents()
    return res


def askFilename(*args,**kargs):
    """Ask for a file name or multiple file names using a file dialog.

    This functions takes the same parameters as :func:`askFile`, and is
    functionally equivalent to it. However, in case of an accepted dialog
    it only returns the filename(s) and in case of a canceled dialog it
    returns None.
    """
    res = askFile(*args,**kargs)
    if res:
        return res['fn']
    else:
        return None


def askNewFilename(cur=None,filter="All files (*.*)",compr=False,timeout=None,caption=None,sidebar=None):
    """Ask a single new filename.

    This is a convenience function for calling askFilename with the
    arguments exist=False.
    """
    return askFilename(cur=cur, filter=filter, exist=False, multi=False, compr=compr, timeout=timeout, caption=caption, sidebar=sidebar)


def askDirname(path=None,change=True,byfile=False,caption=None):
    """Interactively select a directory and change the current workdir.

    The user is asked to select a directory through the standard file
    dialog. Initially, the dialog shows all the subdirectories in the
    specified path, or by default in the current working directory.

    The selected directory becomes the new working directory, unless the
    user canceled the operation, or the change parameter was set to False.
    """
    if path is None:
        path = pf.cfg['workdir']
    if not os.path.isdir(path):
        path = os.path.dirname(path)
    if byfile:
        dirmode = 'auto'
    else:
        dirmode = True
    fn = widgets.FileDialog(path, '*', dir=dirmode,caption=caption).getFilename()
    if fn:
        if not os.path.isdir(fn):
            fn = os.path.dirname(fn)
        if change:
            chdir(fn)
    pf.GUI.update()
    pf.app.processEvents()
    return fn


def askImageFile(fn=None,compr=False):
    if not fn:
        fn = pf.cfg['pyformexdir']
    return askFilename(fn, filter=['img', 'all'], multi=False, exist=True)


def checkWorkdir():
    """Ask the user to change the current workdir if it is not writable.

    Returns True if the new workdir is writable.
    """
    workdir = os.getcwd()
    ok = os.access(workdir, os.W_OK)
    if not ok:
        warning("Your current working directory (%s) is not writable. Change your working directory to a path where you have write permission." % workdir)
        askDirname()
        ok = os.access(os.getcwd(), os.W_OK)
    return ok


logfile = None     # the log file


def printMessage(s):
    """Print a message on the message board.

    If a logfile was opened, the message is also written to the log file.
    """
    if logfile is not None:
        logfile.write(str(s)+'\n')
    pf.GUI.board.write(str(s))
    pf.GUI.update()
    pf.app.processEvents()


def delay(s=None):
    """Get/Set the draw delay time.

    Returns the current setting of the draw wait time (in seconds).
    This drawing delay is obeyed by drawing and viewing operations.

    A parameter may be given to set the delay time to a new value.
    It should be convertable to a float.
    The function still returns the old setting. This may be practical
    to save that value to restore it later.
    """
    saved = pf.GUI.drawwait
    if s is not None:
        pf.GUI.drawwait = float(s)
    return saved


def wait(relock=True):
    """Wait until the drawing lock is released.

    This uses the drawing lock mechanism to pause. The drawing lock
    ensures that subsequent draws are retarded to give the user the time
    to view. The use of this function is prefered over that of
    :func:`pause` or :func:`sleep`, because it allows your script to
    continue the numerical computations while waiting to draw the next
    screen.

    This function can be used to retard other functions than `draw` and `view`.
    """
    pf.GUI.drawlock.wait()
    if relock:
        pf.GUI.drawlock.lock()


# Functions corresponding with control buttons

def play(refresh=False):
    """Start the current script or if already running, continue it.

    """
    if len(pf.scriptlock) > 0:
        # An application is running
        if pf.GUI.drawlock.locked:
            pf.GUI.drawlock.release()

    else:
        # Start current application
        runAny(refresh=refresh)


def replay():
    """Replay the current app.

    This works pretty much like the play() function, but will
    reload the current application prior to running it.
    This function is especially interesting during development
    of an application.
    If the current application is a script, then it is equivalent with
    play().
    """
    appname = pf.cfg['curfile']
    play(refresh=utils.is_app(appname))



def fforward():
    """Releases the drawing lock mechanism indefinely.

    Releasing the drawing lock indefinely means that the lock will not
    be set again and your script will execute till the end.
    """
    pf.GUI.drawlock.free()


#
# IDEA: The pause() could display a progress bar showing how much time
# is left in the pause,
# maybe also with buttons to repeat, pause indefinitely, ...
#
def pause(timeout=None,msg=None):
    """Pause the execution until an external event occurs or timeout.

    When the pause statement is executed, execution of the pyformex script
    is suspended until some external event forces it to proceed again.
    Clicking the PLAY, STEP or CONTINUE button will produce such an event.

    - `timeout`: float: if specified, the pause will only last for this
      many seconds. It can still be interrupted by the STEP buttons.

    - `msg`: string: a message to write to the board to explain the user
      about the pause
    """
    from pyformex.gui.drawlock import Repeater
    def _continue_():
        return not pf.GUI.drawlock.locked

    if msg is None and timeout is None:
        msg = "Use the Play/Step/Continue button to proceed"

    pf.debug("Pause (%s): %s" % (timeout, msg), pf.DEBUG.SCRIPT)
    if msg:
        print(msg)

    pf.GUI.enableButtons(pf.GUI.actions, ['Step', 'Continue'], True)
    pf.GUI.drawlock.release()
    if pf.GUI.drawlock.allowed:
        pf.GUI.drawlock.locked = True
    if timeout is None:
        timeout = widgets.input_timeout
    R = Repeater(_continue_, timeout, sleep=0.1)
    R.start()
    pf.GUI.drawlock.release()


################### EXPERIMENTAL STUFF: AVOID! ###############


def sleep(duration,granularity=0.01):
    from pyformex.gui.drawlock import Repeater
    R = Repeater(None, duration, sleep=granularity)
    R.start()


########################## print information ################################


def printbbox():
    print(pf.canvas.bbox)

def printviewportsettings():
    pf.GUI.viewports.printSettings()

def reportCamera():
    print(pf.canvas.camera.report())


#################### camera ##################################

def zoom_factor(factor=None):
    if factor is None:
        factor = pf.cfg['gui/zoomfactor']
    return float(factor)

def pan_factor(factor=None):
    if factor is None:
        factor = pf.cfg['gui/panfactor']
    return float(factor)

def rot_factor(factor=None):
    if factor is None:
        factor = pf.cfg['gui/rotfactor']
    return float(factor)

def zoomIn(factor=None):
    pf.canvas.camera.zoomArea(1./zoom_factor(factor))
    pf.canvas.update()
def zoomOut(factor=None):
    pf.canvas.camera.zoomArea(zoom_factor(factor))
    pf.canvas.update()

def panRight(factor=None):
    pf.canvas.camera.transArea(-pan_factor(factor), 0.)
    pf.canvas.update()
def panLeft(factor=None):
    pf.canvas.camera.transArea(pan_factor(factor), 0.)
    pf.canvas.update()
def panUp(factor=None):
    pf.canvas.camera.transArea(0., -pan_factor(factor))
    pf.canvas.update()
def panDown(factor=None):
    pf.canvas.camera.transArea(0., pan_factor(factor))
    pf.canvas.update()

def rotRight(factor=None):
    pf.canvas.camera.rotate(rot_factor(factor), 0, 1, 0)
    pf.canvas.update()
def rotLeft(factor=None):
    pf.canvas.camera.rotate(-rot_factor(factor), 0, 1, 0)
    pf.canvas.update()
def rotUp(factor=None):
    pf.canvas.camera.rotate(-rot_factor(factor), 1, 0, 0)
    pf.canvas.update()
def rotDown(factor=None):
    pf.canvas.camera.rotate(rot_factor(factor), 1, 0, 0)
    pf.canvas.update()
def twistLeft(factor=None):
    pf.canvas.camera.rotate(rot_factor(factor), 0, 0, 1)
    pf.canvas.update()
def twistRight(factor=None):
    pf.canvas.camera.rotate(-rot_factor(factor), 0, 0, 1)
    pf.canvas.update()
def barrelRoll(n=36):
    d = 360./n
    t = 2./n
    for i in range(n):
        twistRight(d)
        sleep(t)
def transLeft(factor=None):
    val = pan_factor(factor) * pf.canvas.camera.dist
    pf.canvas.camera.translate(-val, 0, 0, pf.cfg['draw/localaxes'])
    pf.canvas.update()
def transRight(factor=None):
    val = pan_factor(factor) * pf.canvas.camera.dist
    pf.canvas.camera.translate(+val, 0, 0, pf.cfg['draw/localaxes'])
    pf.canvas.update()
def transDown(factor=None):
    val = pan_factor(factor) * pf.canvas.camera.dist
    pf.canvas.camera.translate(0, -val, 0, pf.cfg['draw/localaxes'])
    pf.canvas.update()
def transUp(factor=None):
    val = pan_factor(factor) * pf.canvas.camera.dist
    pf.canvas.camera.translate(0, +val, 0, pf.cfg['draw/localaxes'])
    pf.canvas.update()
def dollyIn(factor=None):
    pf.canvas.camera.dolly(1./zoom_factor(factor))
    pf.canvas.update()
def dollyOut(factor=None):
    pf.canvas.camera.dolly(zoom_factor(factor))
    pf.canvas.update()

def lockCamera():
    pf.canvas.camera.lock()
def unlockCamera():
    pf.canvas.camera.lock(False)


def zoomRectangle():
    """Zoom a rectangle selected by the user."""
    pf.canvas.zoom_rectangle()
    pf.canvas.update()


def getRectangle():
    """Zoom a rectangle selected by the user."""
    r = pf.canvas.get_rectangle()
    print(r)
    pf.canvas.update()


def zoomBbox(bb):
    """Zoom thus that the specified bbox becomes visible."""
    pf.canvas.setCamera(bbox=bb)
    pf.canvas.update()


def zoomObj(object):
    """Zoom thus that the specified object becomes visible.

    object can be anything having a bbox() method or a list thereof.
    """
    zoomBbox(coords.bbox(object))


def zoomAll():
    """Zoom thus that all actors become visible."""
    zoomBbox(pf.canvas.sceneBbox())


# Can this be replaced with zoomIn/Out?
def zoom(f):
    """Zoom with a factor f

    A factor > 1.0 zooms out, a factor < 1.0 zooms in.
    """
    pf.canvas.zoom(f)
    pf.canvas.update()


def focus(point):
    """Move the camera focus to the specified point.

    Parameters:

    - `point`: float(3,) or alike

    The camera focus is set to the specified point, while keeping
    a parallel camera direction and same zoom factor.
    The specified point becomes the center of the screen and
    the center of camera rotations.
    """
    pf.canvas.camera.focus = point
    pf.canvas.camera.setArea(0.,0.,1.,1.,True,center=True)
    pf.canvas.update()


def flyAlong(path,upvector=[0., 1., 0.],sleeptime=None):
    """Fly through the current scene along the specified path.

    - `path`: a plex-2 or plex-3 Formex (or convertibel to such Formex)
      specifying the paths of camera eye and center (and upvector).
    - `upvector`: the direction of the vertical axis of the camera, in case
      of a 2-plex camera path.
    - `sleeptime`: a delay between subsequent images, to slow down
      the camera movement.

    This function moves the camera through the subsequent elements of the
    Formex. For each element the first point is used as the center of the
    camera and the second point as the eye (the center of the scene looked at).
    For a 3-plex Formex, the third point is used to define the upvector
    (i.e. the vertical axis of the image) of the camera. For a 2-plex
    Formex, the upvector is constant as specified in the arguments.
    """
    try:
        if not isinstance(path, Formex):
            path = path.toFormex()
        if not path.nplex() in (2, 3):
            raise ValueError
    except:
        raise ValueError("The camera path should be (convertible to) a plex-2 or plex-3 Formex!")

    nplex = path.nplex()
    if sleeptime is None:
        sleeptime = pf.cfg['draw/flywait']
    saved = delay(sleeptime)
    saved1 = pf.GUI.actions['Continue'].isEnabled()
    pf.GUI.enableButtons(pf.GUI.actions, ['Continue'], True)

    for elem in path:
        eye, center = elem[:2]
        if nplex == 3:
            upv = elem[2] - center
        else:
            upv = upvector
        pf.canvas.camera.lookAt(eye, center, upv)
        wait()
        pf.canvas.display()
        pf.canvas.update()
        image.saveNext()

    delay(saved)
    pf.GUI.enableButtons(pf.GUI.actions, ['Continue'], saved1)
    pf.canvas.camera.focus = center
    pf.canvas.camera.dist = length(center-eye)
    pf.canvas.update()


#################### viewports ##################################

### BEWARE FOR EFFECTS OF SPLITTING pf.canvas and pf.canvas if these
### are called from interactive functions!


def viewport(n=None):
    """Select the current viewport.

    n is an integer number in the range of the number of viewports,
    or is one of the viewport objects in pyformex.GUI.viewports

    if n is None, selects the current GUI viewport for drawing
    """
    if n is not None:
        pf.canvas.update()
        pf.GUI.viewports.setCurrent(n)
    pf.canvas = pf.GUI.viewports.current


def nViewports():
    """Return the number of viewports."""
    return len(pf.GUI.viewports.all)

def layout(nvps=None,ncols=None,nrows=None,pos=None,rstretch=None,cstretch=None):
    """Set the viewports layout."""
    pf.GUI.viewports.changeLayout(nvps, ncols, nrows, pos, rstretch, cstretch)
    viewport()

def addViewport():
    """Add a new viewport."""
    pf.GUI.viewports.addView()
    viewport()

def removeViewport():
    """Remove the last viewport."""
    if nViewports() > 1:
        pf.GUI.viewports.removeView()
    viewport()

def linkViewport(vp, tovp):
    """Link viewport vp to viewport tovp.

    Both vp and tovp should be numbers of viewports.
    """
    pf.GUI.viewports.link(vp, tovp)
    viewport()

####################

def updateGUI():
    """Update the GUI."""
    pf.GUI.update()
    pf.canvas.update()
    pf.app.processEvents()


######### Highlighting ###############
#
# Most highlight functions have been moved to canvas.py
# They are retained here for compatibility, but should be deprecated
#


def highlightActor(actor):
    """Highlight an actor in the scene."""
    pf.canvas.highlightActor(actor)
    pf.canvas.update()


def removeHighlight():
    """Remove the highlights from the current viewport"""
    pf.canvas.removeHighlight()
    pf.canvas.update()



def pick(mode='actor',filter=None,oneshot=False,func=None,pickable=None,prompt=None):
    """Enter interactive picking mode and return selection.

    See :func:`Canvas.pick` for more details.
    This function differs in that it provides default highlighting
    during the picking operation and a OK/Cancel buttons to stop
    the picking operation.

    Parameters:

    - `mode`: defines what to pick : one of 'actor', 'element', 'face',
      'edge', 'point' or 'number'.
      'face' and 'edge' are only available for Mesh type geometry.
    - `filter`: one of the `selection_filters`. The default picking filter is
      activated on entering the pick mode. All available filters are
      presented in a combobox.
    - `oneshot`: if True, the function returns as soon as the user ends
      a picking operation. The default is to let the user
      modify his selection and only to return after an explicit
      cancel (ESC or right mouse button).
    - `func`: if specified, this function will be called after each
      atomic pick operation. The Collection with the currently selected
      objects is passed as an argument. This can e.g. be used to highlight
      the selected objects during picking.
    - `pickable`: a list of Actors to pick from. The default is to use
      a list with all Actors having the pickable=True attribute (which is
      the default for newly constructed Actors).
    - `prompt`: the text printed to prompt the user to start picking. If None,
      a default prompt is printed. Specify an empty string to avoid printing
      a prompt.

    Returns a (possibly empty) Collection with the picked items.
    After return, the value of the pf.canvas.selection_accepted variable
    can be tested to find how the picking operation was exited:
    True means accepted (right mouse click, ENTER key, or OK button),
    False means canceled (ESC key, or Cancel button). In the latter case,
    the returned Collection is always empty
    """
    subsel_values = { 'any': 'any vertex', 'all': 'all vertices' }

    def _set_selection_filter(s):
        """Set the selection filter mode

        This function is used to change the selection filter from the
        selection InputCombo widget.
        s is one of the strings in selection_filters.
        """
        s = str(s)
        if pf.canvas.pick_mode is not None and s in pf.canvas.selection_filters:
            pf.canvas.start_selection(None, s)


    def _set_subsel_mode(val):
        """Toggle the value of the subsel mode"""
        pf.canvas.pick_mode_subsel = str(val)[:3]


    if pf.canvas.pick_mode is not None:
        warning("You need to finish the previous picking operation first!")
        return

    if mode not in pf.canvas.getPickModes():
        warning("Invalid picking mode: %s. Expected one of %s." % (mode, pf.canvas.getPickModes()))
        return

    pick_buttons = widgets.ButtonBox('Selection:', [('Cancel', pf.canvas.cancel_selection), ('OK', pf.canvas.accept_selection)])

    if mode == 'element':
        filters = pf.canvas.selection_filters
    else:
        filters = pf.canvas.selection_filters[:3]
    filter_combo = widgets.InputCombo('Filter:', None, choices=filters, onselect=_set_selection_filter)
    if filter is not None and filter in pf.canvas.selection_filters:
        filter_combo.setValue(filter)

    if mode in [ 'actor', 'element', 'face', 'edge' ]:
        txt = subsel_values[pf.canvas.pick_mode_subsel]
        #subsel_button = widgets.ButtonBox('Pick by ', [(txt, _toggle_subsel_mode), ])
        subsel_button = widgets.InputCombo('Pick by ', txt, choices=subsel_values.values(), onselect=_set_subsel_mode)
    else:
        subsel_button = None

    if func is None:
        func = pf.canvas.highlight_funcs.get(mode, None)

    if prompt is None:
        prompt = "Pick: Mode %s; Filter %s" % (mode,filter)
    if prompt:
        print(prompt)

    pf.GUI.statusbar.addWidget(pick_buttons)
    pf.GUI.statusbar.addWidget(filter_combo)
    if subsel_button:
        pf.GUI.statusbar.addWidget(subsel_button)
    try:
        sel = pf.canvas.pick(mode, oneshot, func, filter, pickable)
    finally:
        # cleanup
        if pf.canvas.pick_mode is not None:
            pf.canvas.finish_selection()
        pf.GUI.statusbar.removeWidget(pick_buttons)
        pf.GUI.statusbar.removeWidget(filter_combo)
        if subsel_button:
            pf.GUI.statusbar.removeWidget(subsel_button)
    return sel


# These are undocumented, and deprecated: use pick() instead
def pickActors(filter=None,oneshot=False,func=None):
    return pick('actor', filter, oneshot, func)

def pickElements(filter=None,oneshot=False,func=None):
    return pick('element', filter, oneshot, func)

def pickPoints(filter=None,oneshot=False,func=None):
    return pick('point', filter, oneshot, func)

def pickEdges(filter=None,oneshot=False,func=None):
    return pick('edge', filter, oneshot, func)


def pickNumbers(marks=None):
    if marks:
        pf.canvas.numbers = marks
    return pf.canvas.pickNumbers()


def pickFocus():
    """Enter interactive focus setting.

    This enters interactive point picking mode and
    sets the focus to the center of the picked points.
    """
    K = pick('point',oneshot=True)
    removeHighlight()
    if K:
        X = []
        for k in K.keys():
            a = pf.canvas.actors[k]
            o = a.object
            x = o.points()[K[k]]
            X.append(x.center())
        X = Coords(X).center()
        focus(X)


LineDrawing = None
edit_modes = ['undo', 'clear', 'close']


def set_edit_mode(s):
    """Set the drawing edit mode."""
    s = str(s)
    if s in edit_modes:
        pf.canvas.edit_drawing(s)


def drawLinesInter(mode ='line',single=False,func=None):
    """Enter interactive drawing mode and return the line drawing.

    See viewport.py for more details.
    This function differs in that it provides default displaying
    during the drawing operation and a button to stop the drawing operation.

    The drawing can be edited using the methods 'undo', 'clear' and 'close', which
    are presented in a combobox.
    """
    if pf.canvas.drawing_mode is not None:
        warning("You need to finish the previous drawing operation first!")
        return
    if func is None:
        func = showLineDrawing
    drawing_buttons = widgets.ButtonBox('Drawing:', [('Cancel', pf.canvas.cancel_drawing), ('OK', pf.canvas.accept_drawing)])
    pf.GUI.statusbar.addWidget(drawing_buttons)
    edit_combo = widgets.InputCombo('Edit:', None, choices=edit_modes, onselect=set_edit_mode)
    pf.GUI.statusbar.addWidget(edit_combo)
    lines = pf.canvas.drawLinesInter(mode, single, func)
    pf.GUI.statusbar.removeWidget(drawing_buttons)
    pf.GUI.statusbar.removeWidget(edit_combo)
    return lines


def showLineDrawing(L):
    """Show a line drawing.

    L is usually the return value of an interactive draw operation, but
    might also be set by the user.
    """
    global LineDrawing
    if LineDrawing:
        undecorate(LineDrawing)
        LineDrawing = None
    if L.size != 0:
        LineDrawing = decors.Lines(L, color='yellow', linewidth=3)
        decorate(LineDrawing)


def exportWebGL(fn,createdby=50,**kargs):
    """Export the current scene to WebGL.

    Parameters:

    - `fn` : string: the (relative or absolute) filename of the .html, .js
      and .pgf files comprising the WebGL model. It can contain a directory
      path and an any extension. The latter is dropped and not used.
    - `createdby`: int: width in pixels of the 'Created by pyFormex' logo
      appearing on the page. If < 0, the logo is displayed at its natural
      width. If 0, the logo is suppressed.
    - `**kargs`: any other keyword parameteris passed to the
      :class:`WebGL` initialization. The `name` can not be specified: it
      is derived from the `fn` parameter.

    Returns the absolute pathname of the generated .html file.
    """
    if not pf.options.opengl2:
        return
    from pyformex.plugins.webgl import WebGL
    print("Exporting current scene to %s" % fn)
    pf.GUI.setBusy()
    if os.path.isabs(fn):
        chdir(os.path.dirname(fn))
    fn = os.path.basename(fn)
    name = utils.projectName(fn)
    W = WebGL(name=name,**kargs)
    W.addScene(name)
    fn = W.export(createdby=createdby)
    pf.GUI.setBusy(False)
    return fn


the_multiWebGL = None

def multiWebGL(name=None,fn=None,title=None,description=None,keywords=None,author=None,createdby=50):
    """Export the current scene to WebGL.

    fn is the (relative or absolute) pathname of the .html and .js files to be
    created.

    When the export is finished, returns the absolute pathname of the
    generated .html file. Else, returns None.
    """
    global the_multiWebGL

    from pyformex.plugins.webgl import WebGL
    ret = None
    pf.GUI.setBusy()
    if fn is not None:
        if the_multiWebGL is not None:
            the_multiWebGL.export()
            the_multiWebGL = None

        print("OK",the_multiWebGL)

        if os.path.isabs(fn):
            chdir(os.path.dirname(fn))
        fn = os.path.basename(fn)
        proj = utils.projectName(fn)
        print("PROJECT %s" % proj)
        the_multiWebGL = WebGL(proj, title=title, description=description, keywords=keywords, author=author)

    if the_multiWebGL is not None:
        if name is not None:
            print("Exporting current scene to %s" % the_multiWebGL.name)
            the_multiWebGL.addScene(name)

        elif fn is None: # No name, and not just starting
            print("Finishing export of %s" % the_multiWebGL.name)
            ret = the_multiWebGL.export(createdby=createdby)
            the_multiWebGL = None

    pf.GUI.setBusy(False)
    return ret


def showURL(url):
    """Show an URL in the browser

    - `url`: url to load
    """
    from pyformex.gui.helpMenu import help
    help(url)


def showHTML(fn=None):
    """Show a local .html file in the browser

    - `fn`: name of a local .html file. If unspecified, a FileDialog
      dialog is popped up to select a file.
    """
    if not fn:
        fn = askFilename(filter='html')
    if fn:
        showURL('file:%s' % fn)


################################

def setLocalAxes(mode=True):
    pf.cfg['draw/localaxes'] = mode
def setGlobalAxes(mode=True):
    setLocalAxes(not mode)


def resetGUI():
    """Reset the GUI to its default operating mode.

    When an exception is raised during the execution of a script, the GUI
    may be left in a non-consistent state.
    This function may be called to reset most of the GUI components
    to their default operating mode.
    """
    ## resetPick()
    pf.GUI.resetCursor()
    pf.GUI.enableButtons(pf.GUI.actions, ['Play', 'Step'], True)
    pf.GUI.enableButtons(pf.GUI.actions, ['Continue', 'Stop'], False)


###########################################################################
# import opengl specific drawing functions
#
try:
    if pf.options.opengl2:
        from pyformex.opengl.draw import *
    else:
        from pyformex.legacy.draw import *
except:
    raise
    #pass

###########################################################################
# Make _I, _G and _T be included when doing 'from gui.draw import *'
#

__all__ = [ n for n in globals().keys() if not n.startswith('_')] + ['_I', '_G', '_T']

#### End
