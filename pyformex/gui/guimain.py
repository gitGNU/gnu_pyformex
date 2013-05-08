# $Id$
##
##  This file is part of pyFormex 0.9.0  (Mon Mar 25 13:52:29 CET 2013)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2012 (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
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
"""Graphical User Interface for pyFormex.

This module contains the main functions responsible for constructing
and starting the pyFormex GUI.
"""
from __future__ import print_function

import pyformex as pf
import code
from pyformex.gui import signals

import sys,utils

# If we get here, either PyQt4 or PySide are imported
#utils.checkModule('pyqt4',fatal=True)
utils.checkModule('pyopengl',fatal=True)

import os.path

from gui import QtCore, QtGui

import menu
import cameraMenu
import fileMenu
import appMenu
import prefMenu
import toolbar
import canvas
import viewport

import script
import draw
import widgets
import drawlock
import views

import warnings

import guifunc


############### General Qt utility functions #######

## might go to a qtutils module

def Size(widget):
    """Return the size of a widget as a tuple."""
    s = widget.size()
    return s.width(),s.height()

def Pos(widget):
    """Return the position of a widget as a tuple."""
    p = widget.pos()
    return p.x(),p.y()

def MaxSize(*args):
    """Return the maximum of a list of sizes"""
    return max([i[0] for i in args]),max([i[1] for i in args])

def MinSize(*args):
    """Return the maximum of a list of sizes"""
    return min([i[0] for i in args]),min([i[1] for i in args])

def printpos(w,t=None):
    print("%s %s x %s" % (t,w.x(),w.y()))
def sizeReport(w,t=None):
    return "%s %s x %s" % (t,w.width(),w.height())


def hasDRI():
    """Check whether the OpenGL canvas has DRI enabled."""
    viewport.setOpenGLFormat()
    dri = viewport.opengl_format.directRendering()
    return dri

################# Message Board ###############


      
#        self.setReadOnly(True)
        



class Board(QtGui.QTextEdit):

        class InteractiveInterpreter(code.InteractiveInterpreter):

            def __init__(self, locals):
                code.InteractiveInterpreter.__init__(self, locals)

            def runIt(self, command,filename='',symbol='single'):
                code.InteractiveInterpreter.runsource(self, command,filename,symbol)

            def runItcode(self, command):
                a = code.InteractiveInterpreter.runcode(self, command)
              

            def compileit(self, source, filename, symbol):
                return code.compile_command(source, filename, symbol)



        def __init__(self, parent=None):

            super(Board, self).__init__(parent)

            sys.stdout = self
            #sys.stderr = self
            self.refreshMarker = False # to change back to >>> from ...
            self.multiLine = False # code spans more than one line
            self.command = '' # command to be ran
            self.history = [] # list of commands entered
            self.historyIndex = -1
            self.interpreterLocals = {}

            self.setAcceptRichText(False)
            self.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Sunken)
            self.setMinimumSize(24,24)
            self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.MinimumExpanding)
            
            #self.buffer = ''
            font = QtGui.QFont("DejaVu Sans Mono")
            #font.setStyle(QtGui.QFont.StyleNormal)
            self.setFont(font)
            self.stdout = self.stderr = None # redirected streams


            # initilize interpreter with self locals
            self.initInterpreter(locals())        

        def write(self,s,color=None):
            """Write a string to the message board.

            If a color is specified, the text is shown in the specified
            color, but the default board color remains unchanged.
            """
            if color:
                savecolor = self.textColor()
                self.setTextColor(QtGui.QColor(color))
            else:
                savecolor = None
            # A single blank character seems to be generated by a print
            # instruction containing a comma: skip it
            if s == ' ':
                return
            #self.buffer += '[%s:%s]' % (len(s),s)
            if len(s) > 0:
                if not s.endswith("\n"):                   
                    s += '\n'
                self.insertPlainText(s)
                textCursor = self.textCursor()
                textCursor.movePosition(QtGui.QTextCursor.End)
                self.setTextCursor(textCursor)
            if savecolor:
                self.setTextColor(savecolor)
            self.ensureCursorVisible()


        def save(self,filename):
            """Save the contents of the board to a file"""
            fil = open(filename,'w')
            fil.write(self.toPlainText())
            fil.close()


        def flush(self):
            self.update()


        def redirect(self,onoff):
            """Redirect standard and error output to this message board"""
            if onoff:
                sys.stderr.flush()
                sys.stdout.flush()
                self.stderr = sys.stderr
                self.stdout = sys.stdout
                sys.stderr = self
                sys.stdout = self
            else:
                if self.stderr:
                    sys.stderr = self.stderr
                if self.stdout:
                    sys.stdout = self.stdout
                self.stderr = None
                self.stdout = None



        def printBanner(self):
            self.write(sys.version)
            self.write(' on ' + sys.platform + '\n')
            msg = 'Type !hist for a history view and !hist(n) history index recall'
            self.write(msg + '\n')


        def marker(self):
            if self.multiLine:
                self.insertPlainText('... ')
            else:
                self.insertPlainText('>>> ')

        def initInterpreter(self, interpreterLocals=None):
            if interpreterLocals:
                # when we pass in locals, we don't want it to be named "self"
                # so we rename it with the name of the class that did the passing
                # and reinsert the locals back into the interpreter dictionary
                selfName = interpreterLocals['self'].__class__.__name__
                interpreterLocalVars = interpreterLocals.pop('self')
                self.interpreterLocals[selfName] = interpreterLocalVars
            else:
                self.interpreterLocals = interpreterLocals
            self.interpreter = self.InteractiveInterpreter(self.interpreterLocals)

        def updateInterpreterLocals(self, newLocals):
            self.interpreter.locals = newLocals


        def clearCurrentBlock(self):
            # block being current row
            length = len(self.document().lastBlock().text()[4:])
            if length == 0:
                return None
            else:
                # should have a better way of doing this but I can't find it
                [self.textCursor().deletePreviousChar() for x in xrange(length)]
            return True

        def recallHistory(self):
            # used when using the arrow keys to scroll through history
            self.clearCurrentBlock()
            if self.historyIndex <> -1:
                self.insertPlainText(self.history[self.historyIndex])
            return True

        def customCommands(self, command):

            if command == '!hist': # display history
                self.append('') # move down one line
                # vars that are in the command are prefixed with ____CC and deleted
                # once the command is done so they don't show up in dir()
                backup = self.interpreterLocals.copy()
                history = self.history[:]
                history.reverse()
                for i, x in enumerate(history):
                    iSize = len(str(i))
                    delta = len(str(len(history))) - iSize
                    line = line = ' ' * delta + '%i: %s' % (i, x) + '\n'
                    self.write(line)
                self.updateInterpreterLocals(backup)
                return True
            import re
            if re.match('!hist\(\d+\)', command): # recall command from history
                backup = self.interpreterLocals.copy()
                history = self.history[:]
                history.reverse()
                index = int(command[6:-1])
                self.clearCurrentBlock()
                command = history[index]
                if command[-1] == ':':
                    self.multiLine = True
                self.write(command)
                self.updateInterpreterLocals(backup)
                return True

            return False

        def keyPressEvent(self, event):

            if event.key() == QtCore.Qt.Key_Escape:
                # proper exit
                self.interpreter.runIt('exit()')

            if event.key() == QtCore.Qt.Key_Down:
                if self.historyIndex == len(self.history):
                    self.historyIndex -= 1
                try:
                    if self.historyIndex > -1:
                        self.historyIndex -= 1
                        self.recallHistory()
                    else:
                        self.clearCurrentBlock()
                except:
                    pass
                return None

            if event.key() == QtCore.Qt.Key_Up:
                try:
                    if len(self.history) - 1 > self.historyIndex:
                        self.historyIndex += 1
                        self.recallHistory()
                    else:
                        self.historyIndex = len(self.history)
                except:
                    pass
                return None

            if event.key() == QtCore.Qt.Key_Home:
                # set cursor to position 4 in current block. 4 because that's where
                # the marker stops
                blockLength = len(self.document().lastBlock().text()[4:])
                lineLength = len(self.document().toPlainText())
                position = lineLength - blockLength
                textCursor = self.textCursor()
                textCursor.setPosition(position)
                self.setTextCursor(textCursor)
                return None

            if event.key() in [QtCore.Qt.Key_Left, QtCore.Qt.Key_Backspace]:
                # don't allow deletion of marker
                if self.textCursor().positionInBlock() == 4:
                    return None

            if event.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
                # set cursor to end of line to avoid line splitting
                textCursor = self.textCursor()
                position = len(self.document().toPlainText())
                textCursor.setPosition(position)
                self.setTextCursor(textCursor)

                line = str(self.document().lastBlock().text())[4:] # remove marker
                line.rstrip()
                self.historyIndex = -1

                if self.customCommands(line):
                    return None
                else:
                    try:
                        line[-1]
                        self.haveLine = True
                        if line[-1] == ':':
                            self.multiLine = True
                        self.history.insert(0, line)
                    except:
                        self.haveLine = False

                    if self.haveLine and self.multiLine: # multi line command
                        self.command += line + '\n' # + command and line
                        self.append('') # move down one line
                        self.marker() # handle marker style
                        return None

                    if self.haveLine and not self.multiLine: # one line command
                        self.command = line # line is the command
                        self.append('') # move down one line
                        self.interpreter.runIt(self.command)
                        self.command = '' # clear command
                        self.marker() # handle marker style
                        return None

                    if self.multiLine and not self.haveLine: # multi line done
                        self.append('') # move down one line
                        self.interpreter.runIt(self.command)
                        self.command = '' # clear command
                        self.multiLine = False # back to single line
                        self.marker() # handle marker style
                        return None

                    if not self.haveLine and not self.multiLine: # just enter
                        self.append('')
                        self.marker()
                        return None
                    return None

            # allow all other key events
            super(Board, self).keyPressEvent(event)



#####################################
################# GUI ###############
#####################################


def toggleAppScript():
    import apps
    appname = pf.cfg['curfile']
    if utils.is_script(appname):
        appdir = apps.findAppDir(os.path.dirname(appname))
        if appdir:
            appname = os.path.basename(appname)
            if appname.endswith('.py'):
                appname = appname[:-3]
            pkgname = appdir.pkg
            appname = "%s.%s" % (pkgname,appname)
            pf.GUI.setcurfile(appname)
        else:
            pf.warning("This script is not in an application directory.\n\nYou should add the directory path '%s' to the application paths before you can run this file as an application.")

    else:
        fn = apps.findAppSource(appname)
        if os.path.exists(fn):
            pf.GUI.setcurfile(fn)
        else:
            pf.warning("I can not find the source file for this application.")


class Gui(QtGui.QMainWindow):
    """Implements a GUI for pyformex."""

    toolbar_area = { 'top': QtCore.Qt.TopToolBarArea,
                     'bottom': QtCore.Qt.BottomToolBarArea,
                     'left': QtCore.Qt.LeftToolBarArea,
                     'right': QtCore.Qt.RightToolBarArea,
                     }



    def __init__(self,windowname,size=(800,600),pos=(0,0),bdsize=(0,0)):
        """Constructs the GUI.

        The GUI has a central canvas for drawing, a menubar and a toolbar
        on top, and a statusbar at the bottom.
        """
        pf.debug('Creating Main Window',pf.DEBUG.GUI)
        self.on_exit = []
        QtGui.QMainWindow.__init__(self)
        self.fullscreen = False
        self.setWindowTitle(windowname)
        # add widgets to the main window


        # The status bar
        pf.debug('Creating Status Bar',pf.DEBUG.GUI)
        self.statusbar = self.statusBar()
        #self.statusbar.setSizePolicy(QtGui.QSizePolicy.Minimum,QtGui.QSizePolicy.Minimum)
        #self.statusbar.setFixedHeight(32)
        #self.statusbar.setContentsMargins(0,0,0,0)
        #widgets.addEffect(self.statusbar,color=(255,0,0))
        self.curproj = widgets.ButtonBox('Project:',[('None',fileMenu.openExistingProject)])
        self.curfile = widgets.ButtonBox('',[('Script:',toggleAppScript),('None',fileMenu.openScript)])
        self.curdir = widgets.ButtonBox('Cwd:',[('None',draw.askDirname)])
        self.canPlay = False
        self.canEdit = False

        # The menu bar
        pf.debug('Creating Menu Bar',pf.DEBUG.GUI)
        self.menu = menu.MenuBar('TopMenu')
        self.setMenuBar(self.menu)

        # The toolbar
        pf.debug('Creating ToolBar',pf.DEBUG.GUI)
        self.toolbar = self.addToolBar('Top ToolBar')
        self.editor = None

        # Create a box for the central widget
        self.box = QtGui.QWidget()
        self.setCentralWidget(self.box)
        self.boxlayout = QtGui.QVBoxLayout()
        self.boxlayout.setContentsMargins(*pf.cfg['gui/boxmargins'])
        self.box.setLayout(self.boxlayout)
        #self.box.setFrameStyle(qt.QFrame.Sunken | qt.QFrame.Panel)
        #self.box.setLineWidth(2)
        # Create a splitter
        self.splitter = QtGui.QSplitter()
        self.boxlayout.addWidget(self.splitter)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.show()

        # self.central is the central widget of the main window
        # self.viewports is its layout, containing multiple viewports
        pf.debug('Creating Central Widget',pf.DEBUG.GUI)
        self.central = QtGui.QWidget()
        self.central.autoFillBackground()
          #self.central.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Sunken)
        self.central.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.MinimumExpanding)
        self.central.resize(*pf.cfg['gui/size'])

        self.viewports = viewport.MultiCanvas(parent=self.central)
        self.centralgrid = QtGui.QGridLayout()
        self.centralgrid.addLayout(self.viewports,0,0)
        self.central.setLayout(self.centralgrid)

        # Create the message board
        self.board = Board()
        #self.board.setPlainText(pf.Version()+' started')
        # Put everything together
        self.splitter.addWidget(self.central)
        self.splitter.addWidget(self.board)
        #self.splitter.setSizes([(800,200),(800,600)])
        self.box.setLayout(self.boxlayout)

        # Create the top menu
        pf.debug('Creating Menus',pf.DEBUG.GUI)
        menudata = menu.createMenuData()
        self.menu.insertItems(menudata)
        # ... and the toolbar
        self.actions = toolbar.addActionButtons(self.toolbar)

        # timeout button
        toolbar.addTimeoutButton(self.toolbar)

        self.menu.show()

        # Define Toolbars

        pf.debug('Creating Toolbars',pf.DEBUG.GUI)
        self.camerabar = self.updateToolBar('camerabar','Camera ToolBar')
        self.modebar = self.updateToolBar('modebar','RenderMode ToolBar')
        self.viewbar = self.updateToolBar('viewbar','Views ToolBar')
        self.toolbars = [self.camerabar, self.modebar, self.viewbar]

        ###############  CAMERA menu and toolbar #############
        if self.camerabar:
            toolbar.addCameraButtons(self.camerabar)
            toolbar.addPerspectiveButton(self.camerabar)

        ###############  RENDERMODE menu and toolbar #############
        modes = [ 'wireframe', 'smooth', 'smoothwire', 'flat', 'flatwire' ]
        if pf.cfg['gui/modemenu']:
            mmenu = QtGui.QMenu('Render Mode')
        else:
            mmenu = None

        #menutext = '&' + name.capitalize()
        self.modebtns = menu.ActionList(
            modes,guifunc.renderMode,menu=mmenu,toolbar=self.modebar)

        # Add the toggle type buttons
        if self.modebar:
            toolbar.addTransparencyButton(self.modebar)
        if self.modebar and pf.cfg['gui/lightbutton']:
            toolbar.addLightButton(self.modebar)
        if self.modebar and pf.cfg['gui/normalsbutton']:
            toolbar.addNormalsButton(self.modebar)
        if self.modebar and pf.cfg['gui/shrinkbutton']:
            toolbar.addShrinkButton(self.modebar)

        if mmenu:
            # insert the mode menu in the viewport menu
            pmenu = self.menu.item('viewport')
            pmenu.insertMenu(pmenu.item('background color'),mmenu)

        ###############  VIEWS menu ################
        if pf.cfg['gui/viewmenu']:
            if pf.cfg['gui/viewmenu'] == 'main':
                parent = self.menu
                before = 'help'
            else:
                parent = self.menu.item('camera')
                before = parent.item('---')
            self.viewsMenu = menu.Menu('&Views',parent=parent,before=before)
        else:
            self.viewsMenu = None

        defviews = pf.cfg['gui/defviews']
        views = [ v[0] for v in defviews ]
        viewicons = [ v[1] for v in defviews ]

        self.viewbtns = menu.ActionList(
            views,self.setView,
            menu=self.viewsMenu,
            toolbar=self.viewbar,
            icons = viewicons
            )

        ## TESTING SAVE CURRENT VIEW ##

        self.saved_views = {}
        self.saved_views_name = utils.NameSequence('View')

        if self.viewsMenu:
            name = self.saved_views_name.next()
            self.menu.item('camera').addAction('Save View',self.saveView)


        # Restore previous pos/size
        pf.debug('Restore size/pos',pf.DEBUG.GUI)
        self.resize(*size)
        self.move(*pos)
        self.board.resize(*bdsize)

        pf.debug('Set Curdir',pf.DEBUG.GUI)
        self.setcurdir()

        # redirect standard/error output if option set
        #
        # TODO: we should redirect it to a buffer and
        # wait until GUI shown, then show in board
        # else show on stdout/err

        #self.board.redirect(pf.cfg['gui/redirect'])

        if pf.options.debuglevel:
            s = sizeReport(self,'DEBUG: Main:') + \
                sizeReport(self.central,'DEBUG: Canvas:') + \
                sizeReport(self.board,'DEBUG: Board:')
            pf.debug(s,pf.DEBUG.GUI)

        # Drawing lock
        self.drawwait = pf.cfg['draw/wait']
        self.drawlock = drawlock.DrawLock()

        # Materials and Lights database
        self.materials = canvas.createMaterials()
        ## for m in self.materials:
        ##     print self.materials[m]

        # Modeless child dialogs
        self.doc_dialog = None
        pf.debug('Done initializing GUI',pf.DEBUG.GUI)

        # Set up signal/slot connections
        self.signals = signals.Signals()
        self.signals.FULLSCREEN.connect(self.fullScreen)

        # Set up hot keys: hitting the key will emit the corresponding signal
        self.hotkey  = {
            QtCore.Qt.Key_F2: self.signals.SAVE,
            QtCore.Qt.Key_F5: self.signals.FULLSCREEN,
            }


    def close_doc_dialog(self):
        """Close the doc_dialog if it is open."""
        if self.doc_dialog is not None:
            self.doc_dialog.close()
            self.doc_dialog = None


    def saveView(self,name=None,addtogui=True):
        """Save the current view and optionally create a button for it.

        This saves the current viewport ModelView and Projection matrices
        under the specified name.

        It adds the view to the views Menu and Toolbar, if these exist and
        do not have the name yet.
        """
        if name is None:
            name = self.saved_views_name.next()
        self.saved_views[name] = (pf.canvas.camera.m,None)
        if name not in self.viewbtns.names():
            iconpath = os.path.join(pf.cfg['icondir'],'userview')+pf.cfg['gui/icontype']
            self.viewbtns.add(name,iconpath)


    def applyView(self,name):
        """Apply a saved view to the current camera.

        """
        m,p = self.saved_views.get(name,(None,None))
        if m is not None:
            self.viewports.current.camera.loadModelView(m)


    def createView(self,name,angles):
        """Create a new view and add it to the list of predefined views.

        This creates a named view with specified angles or, if the name
        already exists, changes its angles to the new values.

        It adds the view to the views Menu and Toolbar, if these exist and
        do not have the name yet.
        """
        if name not in self.viewbtns.names():
            iconpath = os.path.join(pf.cfg['icondir'],'userview')+pf.cfg['gui/icontype']
            self.viewbtns.add(name,iconpath)
        views.view_angles[name] = angles


    def setView(self,view):
        """Change the view of the current GUI viewport, keeping the bbox.

        view is the name of one of the defined views.
        """
        view = str(view)
        if view in self.saved_views:
            self.applyView(view)
        else:
            self.viewports.current.setCamera(angles=view)
        self.viewports.current.update()


    def updateAppdirs(self):
        appMenu.reloadMenu()


    def updateToolBars(self):
        for t in ['camerabar','modebar','viewbar']:
            self.updateToolBar(t)


    def updateToolBar(self,shortname,fullname=None):
        """Add a toolbar or change its position.

        This function adds a toolbar to the GUI main window at the position
        specified in the configuration. If the toolbar already exists, it is
        moved from its previous location to the requested position. If the
        toolbar does not exist, it is created with the given fullname, or the
        shortname by default.

        The full name is the name as displayed to the user.
        The short name is the name as used in the config settings.

        The config setting for the toolbar determines its placement:
        - None: the toolbar is not created
        - 'left', 'right', 'top' or 'bottom': a separate toolbar is created
        - 'default': the default top toolbar is used and a separator is added.
        """
        area = pf.cfg['gui/%s' % shortname]
        try:
            toolbar = getattr(self,shortname)
        except:
            toolbar = None

        if area:
            area = self.toolbar_area.get(area,4) # default is top
            # Add/reposition the toolbar
            if toolbar is None:
                if fullname is None:
                    fullname = shortname
                toolbar = QtGui.QToolBar(fullname,self)
            self.addToolBar(area,toolbar)
        else:
            if toolbar is not None:
                self.removeToolBar(toolbar)
                toolbar = None

        return toolbar


    def addStatusBarButtons(self):
        self.statusbar.addWidget(self.curproj)
        self.statusbar.addWidget(self.curfile)
        self.statusbar.addWidget(self.curdir)
        r = self.statusbar.childrenRect()
        self.statusbar.setFixedHeight(r.height()+4)


    def addInputBox(self):
        self.input = widgets.InputString('Input:','')
        self.statusbar.addWidget(self.input)


    def toggleInputBox(self,onoff=None):
        if onoff is None:
            onoff = self.input.isHidden()
        self.input.setVisible(onoff)


    def addCoordsTracker(self):
        self.coordsbox = widgets.CoordsBox()
        self.statusbar.addPermanentWidget(self.coordsbox)


    def toggleCoordsTracker(self,onoff=None):
        def track(x,y,z):
            X,Y,Z = pf.canvas.unProject(x,y,z,True)
            print("%s --> %s" % ((x,y,z),(X,Y,Z)))
            pf.GUI.coordsbox.setValues([X,Y,Z])

        if onoff is None:
            onoff = self.coordsbox.isHidden()
        if onoff:
            func = track
        else:
            func = None
        for vp in self.viewports.all:
            vp.trackfunc = func
        self.coordsbox.setVisible(onoff)


    def maxCanvasSize(self):
        """Return the maximum canvas size.

        The maximum canvas size is the size of the central space in the
        main window, occupied by the OpenGL viewports.
        """
        return Size(pf.GUI.central)


    def showEditor(self):
        """Start the editor."""
        if not hasattr(self,'editor'):
            self.editor = Editor(self,'Editor')
            self.editor.show()
            self.editor.setText("Hallo\n")

    def closeEditor(self):
        """Close the editor."""
        if hasattr(self,'editor'):
            self.editor.close()
            self.editor = None


    def setcurproj(self,project=''):
        """Show the current project name."""
        if project:
            project = os.path.basename(project)
        self.curproj.setText(project)


    def setcurfile(self,appname):
        """Set the current application or script.

        appname is either an application module name or a script file.
        """
        is_app = not utils.is_script(appname)
        if is_app:
            # application
            label = 'App:'
            name = appname
            import apps
            app = apps.load(appname)
            if app is None:
                self.canPlay = False
                try:
                    self.canEdit = os.path.exists(apps.findAppSource(appname))
                except:
                    self.canEdit = False
            else:
                self.canPlay = hasattr(app,'run')
                self.canEdit = os.path.exists(apps.findAppSource(app))
        else:
            # script file
            label = 'Script:'
            name = os.path.basename(appname)
            self.canPlay = self.canEdit = utils.is_pyFormex(appname) or appname.endswith('.pye')

        pf.prefcfg['curfile'] = appname
        #self.curfile.label.setText(label)
        self.curfile.setText(label,0)
        self.curfile.setText(name,1)
        self.enableButtons(self.actions,['Play','Info'],self.canPlay)
        self.enableButtons(self.actions,['Edit'],self.canEdit)
        self.enableButtons(self.actions,['ReRun'],is_app and(self.canEdit or self.canPlay))
        self.enableButtons(self.actions,['Step','Continue'],False)
        icon = 'ok' if self.canPlay else 'notok'
        self.curfile.setIcon(QtGui.QIcon(QtGui.QPixmap(os.path.join(pf.cfg['icondir'],icon)+pf.cfg['gui/icontype'])),1)


    def setcurdir(self):
        """Show the current workdir."""
        dirname = os.getcwd()
        shortname = os.path.basename(dirname)
        self.curdir.setText(shortname)
        self.curdir.setToolTip(dirname)


    def setBusy(self,busy=True,force=False):
        if busy:
            #pf.app.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
            pf.app.setOverrideCursor(QtCore.Qt.WaitCursor)
        else:
            pf.app.restoreOverrideCursor()
        self.processEvents()


    def resetCursor(self):
        """Clear the override cursor stack.

        This will reset the application cursor to the initial default.
        """
        while pf.app.overrideCursor():
            pf.app.restoreOverrideCursor()
        self.processEvents()


    def keyPressEvent(self,e):
        """Top level key press event handler.

        Events get here if they are not handled by a lower level handler.
        Every key press arriving here generates a WAKEUP signal, and if a
        dedicated signal for the key was installed in the keypress table,
        that signal is emitted too.
        Finally, the event is removed.
        """
        key = e.key()
        pf.debug('Key %s pressed' % key,pf.DEBUG.GUI)
        self.signals.WAKEUP.emit()
        signal = self.hotkey.get(key,None)
        if signal is not None:
            signal.emit()
        e.ignore()


    def XPos(self):
        """Get the main window position from the xwininfo command.

        The (Py)Qt4 position does not get updated when
        changing the window size from the left.
        This substitute function will find the correct position from
        the xwininfo command output.
        """
        res = xwininfo(self.winId())
        ax,ay,rx,ry = [ int(res[key]) for key in [
            'Absolute upper-left X','Absolute upper-left Y',
            'Relative upper-left X','Relative upper-left Y',
            ]]
        return ax-rx,ay-ry


    def XGeometry(self):
        """Get the main window position and size from the xwininfo command.

        """
        res = xwininfo(self.winId())
        x,y,w,h = [ int(res[key]) for key in [
            'Absolute upper-left X','Absolute upper-left Y',
            'Width','Height',
            ]]
        return x,y,w,h


    def writeSettings(self):
        """Store the GUI settings"""
        pf.debug('Store current settings',pf.DEBUG.CONFIG)
        # FIX QT4 BUG
        # Make sure QT4 has position right
        self.move(*self.XPos())

        # store the history and main window size/pos
        pf.prefcfg['gui/scripthistory'] = pf.GUI.scripthistory.files
        pf.prefcfg['gui/apphistory'] = pf.GUI.apphistory.files

        pf.prefcfg.update({'size':Size(pf.GUI),
                           'pos':Pos(pf.GUI),
                           'bdsize':Size(pf.GUI.board),
                           },name='gui')

# THESE FUNCTION SHOULD BECOME app FUNCTIONS


    def setStyle(self,style):
        """Set the main application style."""
        style = QtGui.QStyleFactory().create(style)
        pf.app.setStyle(style)
        self.update()


    def setFont(self,font):
        """Set the main application font.

        font is either a QFont or a string resulting from the
        QFont.toString() method
        """
        if not isinstance(font,QtGui.QFont):
            f = QtGui.QFont()
            f.fromString(font)
            font = f
        pf.app.setFont(font)
        self.update()


    def setFontFamily(self,family):
        """Set the main application font family to the given family."""
        font = pf.app.font()
        font.setFamily(family)
        self.setFont(font)


    def setFontSize(self,size):
        """Set the main application font size to the given point size."""
        font = pf.app.font()
        font.setPointSize(int(size))
        self.setFont(font)


    def setAppearence(self):
        """Set all the GUI appearence elements.

        Sets the GUI appearence from the current configuration values
        'gui/style', 'gui/font', 'gui/fontfamily', 'gui/fontsize'.
        """
        style = pf.cfg['gui/style']
        font = pf.cfg['gui/font']
        family = pf.cfg['gui/fontfamily']
        size = pf.cfg['gui/fontsize']
        if style:
            self.setStyle(style)
        if font:
            self.setFont(font)
        if family:
            self.setFontFamily(family)
        if size:
            self.setFontSize(size)


    def processEvents(self):
        """Process interactive GUI events."""
        #saved = pf.canvas
        #print "SAVED script canvas %s" % pf.canvas
        #pf.canvas = self.viewports.current
        #print "SET script canvas %s" % pf.canvas
        if pf.app:
            pf.app.processEvents()
        #pf.canvas = saved
        #print "RESTORED script canvas %s" % pf.canvas


    def findDialog(self,name):
        """Find the InputDialog with the specified name.

        Returns the list with maching dialogs, possibly empty.
        """
        return self.findChildren(widgets.InputDialog,str(name))


    def closeDialog(self,name):
        """Close the InputDialog with the specified name.

        Closest all the InputDialogs with the specified caption
        owned by the GUI.
        """
        for w in self.findDialog(name):
            w.close()


    # This should go to a toolbar class
    def enableButtons(self,toolbar,buttons,enable):
        """Enable or disable a button in a toolbar.

        toolbar is a toolbar dict.
        buttons is a list of button names.
        For each button in the list:

        - If it exists in toolbar, en/disables the button.
        - Else does nothing
        """
        for b in buttons:
            if b in toolbar:
                toolbar[b].setEnabled(enable)


    def startRun(self):
        """Change the GUI when an app/script starts running.

        This method enables/disables the parts of the GUI that should or
        should not be available while a script is running
        It is called by the application executor.
        """
        self.drawlock.allow()
        pf.canvas.update()
        self.enableButtons(self.actions,['ReRun'],False)
        self.enableButtons(self.actions,['Play','Step','Continue','Stop'],True)
        # by default, we run the script in the current GUI viewport
        pf.canvas = pf.GUI.viewports.current
        pf.app.processEvents()


    def stopRun(self):
        """Change the GUI when an app/script stops running.

        This method enables/disables the parts of the GUI that should or
        should not be available when no script is being executed.
        It is called by the application executor when an application stops.
        """
        self.drawlock.release()
        pf.canvas.update()
        self.enableButtons(self.actions,['Play','ReRun'],True)
        self.enableButtons(self.actions,['Step','Continue','Stop'],False)
        # acknowledge viewport switching
        pf.canvas = pf.GUI.viewports.current
        pf.app.processEvents()


    def cleanup(self):
        """Cleanup the GUI (restore default state)."""
        pf.debug('GUI cleanup',pf.DEBUG.GUI)
        self.drawlock.release()
        pf.canvas.cancel_selection()
        pf.canvas.cancel_draw()
        draw.clear_canvas()
        #draw.wakeup()
        self.setBusy(False)


    def onExit(self,func):
        """Register a function for execution on exit"""
        self.on_exit.append(func)


    def closeEvent(self,event):
        """Override the close event handler.

        We override the default close event handler for the main
        window, to allow the user to cancel the exit.
        """
        #
        # DEV: things going wrong during the event handler are hard to debug!
        # You can add those things to a function and add the function to a
        # menu for testing. At the end of the file helpMenu.py there is an
        # example (commented out).
        #
        pf.GUI.cleanup()
        if pf.options.gui:
            script.force_finish()
        if exitDialog():
            self.drawlock.free()
            dooze = pf.cfg['gui/dooze']
            if dooze > 0:
                print("Exiting in %s seconds" % dooze)
                draw.sleep(dooze)
            # force reset redirect
            sys.stderr.flush()
            sys.stdout.flush()
            sys.stderr = sys.__stderr__
            sys.stdout = sys.__stdout__
            pf.debug("Executing registered exit functions",pf.DEBUG.GUI)
            for f in self.on_exit:
                pf.debug(f,pf.DEBUG.GUI)
                f()
            self.writeSettings()
            event.accept()
        else:
            event.ignore()


    def fullScreen(self):
        """Toggle the canvas full screen mode.

        Fullscreen mode hides all the components of the main window, except
        for the central canvas, maximizes the main window, and removes the
        window decorations, thus leaving only the OpenGL canvas on the full
        screen. (Currently there is also still a small border remaining.)

        This mode is activated by pressing the F5 key. A second F5 press
        will revert to normal display mode.
        """
        hide = [self.board,self.statusbar,self.toolbar,self.menu] + self.toolbars
        if self.fullscreen:
            # already fullscreen: go back to normal mode
            for w in hide:
                w.show()
            self.boxlayout.setContentsMargins(*pf.cfg['gui/boxmargins'])
            self.showNormal()
        else:
            # goto fullscreen
            for w in hide:
                w.hide()
            self.boxlayout.setContentsMargins(0,0,0,0)
            self.showFullScreen()
        self.update()
        self.fullscreen = not self.fullscreen
        pf.app.processEvents()



def exitDialog():
    """Show the exit dialog to the user.

    """
    confirm = pf.cfg['gui/exitconfirm']
    ## print "confirm = %s" % confirm
    ## print "pf.PF.filename = %s" % pf.PF.filename
    ## print "pf.PF.hits = %s" % pf.PF.hits

    if confirm == 'never':
        return True

    if confirm == 'smart' and (pf.PF.filename is None or pf.PF.hits == 0):
        return True

    print("Project variable changes: %s" % pf.PF.hits)
    print("pyFormex globals: %s" % pf.PF.keys())

    save_opts = ['To current project file','Under another name','Do not save']
    res = draw.askItems(
        [ draw._I('info',itemtype='label',value="You have unsaved global variables. What shall I do?"),
          draw._I('save',itemtype='vradio',choices=save_opts,text='Save the current globals'),
          draw._I('reopen',pf.cfg['openlastproj'],text="Reopen the project on next startup"),
          ],
        caption='pyFormex exit dialog')

    if not res:
        # Cancel the exit
        return False

    save = save_opts.index(res['save'])
    if save == 0:
        fileMenu.saveProject()
    elif save == 1:
        fileMenu.saveAsProject()

    if not res['reopen']:
        fileMenu.closeProject(save=False,clear=False)

    return True


def fullscreen():
    pf.GUI.fullScreen()


def xwininfo(windowid=None,name=None):
    """Returns the X window info parsed as a dict.

    Either the windowid or the window name has to be specified.
    """
    import re
    cmd = 'xwininfo %s 2> /dev/null'
    if windowid is not None:
        args = " -id %s" % windowid
    elif name is not None:
        args = " -name '%s'" % name
    else:
        raise ValueError,"Either windowid or name have to be specified"

    sta,out,err = utils.system(cmd % args)
    res = {}
    if not sta:
        for line in out.split('\n'):
            s = line.split(':')
            if len(s) < 2:
                s = s[0].strip().split(' ')
            if len(s) < 2:
                continue
            elif len(s) > 2:
                if s[0] == 'xwininfo':
                    s = s[-2:] # remove the xwininfo string
                    t = s[1].split()
                    s[1] = t[0] # windowid
                    name = ' '.join(t[1:]).strip().strip('"')
                    res['Window name'] = name
            if s[0][0] == '-':
                s[0] = s[0][1:]
            res[s[0].strip()] = s[1].strip()

    return res


def pidofxwin(windowid):
    """Returns the PID of the process that has created the window.

    Remark: Not all processes store the PID information in the way
    it is retrieved here. In many cases (X over network) the PID can
    not be retrieved. However, the intent of this function is just to
    find a dangling pyFormex process, and should probably work on
    a normal desktop configuration.
    """
    import re
    sta,out = utils.runCommand('xprop -id %s _NET_WM_PID' % windowid,verbose=False)
    m = re.match("_NET_WM_PID\(.*\)\s*=\s*(?P<pid>\d+)",out)
    if m:
        pid = m.group('pid')
        #print "Found PID %s" % pid
        return int(pid)

    return None


def windowExists(windowname):
    """Check if a GUI window with the given name exists.

    On X-Window systems, we can use the xwininfo command to find out whether
    a window with the specified name exists.
    """
    return not os.system('xwininfo -name "%s" > /dev/null 2>&1' % windowname)


def windowId():
    """Return the X windowid of the main pyFormex window."""
    info = QtGui.QX11Info()
    print(info)
    print("%x" % info.appRootWindow())



def findOldProcesses(max=16):
    """Find old pyFormex GUI processes still running.

    There is a maximum to the number of processes that can be detected.
    16 will suffice largely, because there is no sane reason to open that many
    pyFormex GUI's on the same screen.

    Returns the next available main window name, and a list of
    running pyFormex GUI processes, if any.
    """
    windowname = pf.Version()
    count = 0
    running = []

    while count < max:
        info = xwininfo(name=windowname)
        if info:
            name = info['Window name']
            windowid = info['Window id']
            if name == windowname:
                pid = pidofxwin(windowid)
            else:
                pid = None
            # pid control needed for invisible windows on ubuntu
            if pid:
                running.append((windowid,name,pid))
                count += 1
                windowname = '%s (%s)' % (pf.Version(),count)
            else:
                break
        else:
            break

    return windowname,running


def killProcesses(pids):
    """Kill the processes in the pids list."""
    warning = """..

Killing processes
-----------------
I will now try to kill the following processes::

    %s

You can choose the signal to be sent to the processes:

- KILL (9)
- TERM (15)

We advice you to first try the TERM(15) signal, and only if that
does not seem to work, use the KILL(9) signal.
""" % pids
    actions = ['Cancel the operation','KILL(9)','TERM(15)']
    answer = draw.ask(warning,actions)
    if answer == 'TERM(15)':
        utils.killProcesses(pids,15)
    elif answer == 'KILL(9)':
        utils.killProcesses(pids,9)

########################
# Main application
########################


class Application(QtGui.QApplication):
    """The interactive Qt4 application"""

    def __init__(self,args):
        QtGui.QApplication.__init__(self,args)


    def currentStyle(self):
        return self.style().metaObject().className()[1:-5]


    def getStyles(self):
        return map(str,QtGui.QStyleFactory().keys())


def startGUI(args):
    """Create the QT4 application and GUI.

    A (possibly empty) list of command line options should be provided.
    QT4 wil remove the recognized QT4 and X11 options.
    """
    # This seems to be the only way to make sure the numeric conversion is
    # always correct
    #
    QtCore.QLocale.setDefault(QtCore.QLocale.c())
    #
    #pf.options.debug = -1
    pf.debug("Arguments passed to the QApplication: %s" % args,pf.DEBUG.INFO)
    pf.app = Application(args)
    #
    pf.debug("Arguments left after constructing the QApplication: %s" % args,pf.DEBUG.INFO)
    pf.debug("Arguments left after constructing the QApplication: %s" % '\n'.join(pf.app.arguments()),pf.DEBUG.INFO)
    #pf.options.debug = 0
    # As far as I have been testing this, the args passed to the Qt application are
    # NOT acknowledged and neither are they removed!!


    pf.debug("Setting application attributes",pf.DEBUG.INFO)
    pf.app.setOrganizationName("pyformex.org")
    pf.app.setOrganizationDomain("pyformex.org")
    pf.app.setApplicationName("pyFormex")
    pf.app.setApplicationVersion(pf.__version__)
    ## pf.settings = QtCore.QSettings("pyformex.org", "pyFormex")
    ## pf.settings.setValue("testje","testvalue")

    # Quit application if last window closed
    pf.app.lastWindowClosed.connect(pf.app.quit)

    # Check if we have DRI
    pf.debug("Setting OpenGL format",pf.DEBUG.OPENGL)
    dri = hasDRI()

    # Check for existing pyFormex processes
    pf.debug("Checking for running pyFormex",pf.DEBUG.INFO)
    if pf.X11:
        windowname,running = findOldProcesses()
    else:
        windowname,running = "UNKOWN",[]
    pf.debug("%s,%s" % (windowname,running),pf.DEBUG.INFO)


    while len(running) > 0:
        if len(running) >= 16:
            print("Too many open pyFormex windows --- bailing out")
            return -1

        pids = [ i[2] for i in running if i[2] is not None ]
        warning = """..

pyFormex is already running on this screen
------------------------------------------
A main pyFormex window already exists on your screen.

If you really intended to start another instance of pyFormex, you
can just continue now.

The window might however be a leftover from a previously crashed pyFormex
session, in which case you might not even see the window anymore, nor be able
to shut down that running process. In that case, you would better bail out now
and try to fix the problem by killing the related process(es).

If you think you have already killed those processes, you may check it by
rerunning the tests.
"""
        actions = ['Really Continue','Rerun the tests','Bail out and fix the problem']
        if pids:
            warning += """

I have identified the process(es) by their PID as::

%s

If you trust me enough, you can also have me kill this processes for you.
""" % pids
            actions[2:2] = ['Kill the running processes']

        if dri:
            answer = draw.ask(warning,actions)
        else:
            warning += """
I have detected that the Direct Rendering Infrastructure
is not activated on your system. Continuing with a second
instance of pyFormex may crash your XWindow system.
You should seriously consider to bail out now!!!
"""
            answer = draw.warning(warning,actions)


        if answer == 'Really Continue':
            break # OK, Go ahead

        elif answer == 'Rerun the tests':
            windowname,running = findOldProcesses() # try again

        elif answer == 'Kill the running processes':
            killProcesses(pids)
            windowname,running = findOldProcesses() # try again

        else:
            return -1 # I'm out of here!


    # Load the splash image
    pf.debug("Loading the splash image",pf.DEBUG.GUI)
    splash = None
    if os.path.exists(pf.cfg['gui/splash']):
        pf.debug('Loading splash %s' % pf.cfg['gui/splash'],pf.DEBUG.GUI)
        splashimage = QtGui.QPixmap(pf.cfg['gui/splash'])
        splash = QtGui.QSplashScreen(splashimage)
        splash.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint|QtCore.Qt.SplashScreen)
        splash.setFont(QtGui.QFont("Helvetica",20))
        splash.showMessage(pf.Version(),QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop,QtCore.Qt.red)
        splash.show()

    # create GUI, show it, run it

    pf.debug("Creating the GUI",pf.DEBUG.GUI)
    desktop = pf.app.desktop()
    pf.maxsize = Size(desktop.availableGeometry())
    size = pf.cfg.get('gui/size',(800,600))
    pos = pf.cfg.get('gui/pos',(0,0))
    bdsize = pf.cfg.get('gui/bdsize',(800,600))
    size = MinSize(size,pf.maxsize)

    # Create the GUI
    pf.GUI = Gui(windowname,
                 pf.cfg.get('gui/size',(800,600)),
                 pf.cfg.get('gui/pos',(0,0)),
                 pf.cfg.get('gui/bdsize',(800,600)),
                 )


    # set the appearance
    pf.debug("Setting Appearence",pf.DEBUG.GUI)
    pf.GUI.setAppearence()


    # setup the message board
    pf.board = pf.GUI.board
    pf.board.write("""%s   (C) Benedict Verhegghe

pyFormex comes with ABSOLUTELY NO WARRANTY. This is free software, and you are welcome to redistribute it under the conditions of the GNU General Public License, version 3 or later. See Help->License or the file COPYING for details.
""" % pf.fullVersion())

    pf.board.printBanner()
    pf.board.marker()

    # Set interaction functions


    def show_warning(message,category,filename,lineno,file=None,line=None):
        """Replace the default warnings.showwarning

        We display the warnings using our interactive warning widget.
        This feature can be turned off by setting
        cfg['warnings/popup'] = False
        """
        full_message = warnings.formatwarning(message,category,filename,lineno,line)
        pf.message(full_message)
        res,check = draw.showMessage(full_message,level='warning',check="Do not show this warning anymore in future sessions")
        if check[0]:
            utils.filterWarning(str(message))
            utils.saveWarningFilter(str(message))

    if pf.cfg['warnings/popup']:
        warnings.showwarning = show_warning


    pf.message = draw.message
    pf.warning = draw.warning
    pf.error = draw.error


    # setup the canvas
    pf.debug("Setting the canvas",pf.DEBUG.GUI)
    pf.GUI.processEvents()
    pf.GUI.viewports.changeLayout(1)
    pf.GUI.viewports.setCurrent(0)
    #pf.canvas = pf.GUI.viewports.current
    pf.canvas.setRenderMode(pf.cfg['draw/rendermode'])

    #
    # PYSIDE: raises (intercepted) exception on startup
    #
    draw.reset()

    # setup the status bar
    pf.debug("Setup status bar",pf.DEBUG.GUI)
    pf.GUI.addInputBox()
    pf.GUI.toggleInputBox(False)
    pf.GUI.addCoordsTracker()
    pf.GUI.toggleCoordsTracker(pf.cfg.get('gui/coordsbox',False))
    pf.debug("Using window name %s" % pf.GUI.windowTitle(),pf.DEBUG.GUI)

    # Script menu
    pf.GUI.scriptmenu = appMenu.createAppMenu(mode='script',parent=pf.GUI.menu,before='help')

    # App menu
    pf.GUI.appmenu = appMenu.createAppMenu(parent=pf.GUI.menu,before='help')


    # BV: removed, because they are in the script/app menus,
    # and the file menu is alredy very loaded

    ## # Link History Menus also in the File menu
    ## parent = pf.GUI.menu.item('file')
    ## before = parent.item('---1')
    ## if pf.GUI.apphistory:
    ##     parent.insert_menu(pf.GUI.apphistory,before)

    ## if pf.GUI.scripthistory:
    ##     parent.insert_menu(pf.GUI.scripthistory,before)

    # Create databases
    createDatabases()

    # Plugin menus
    import plugins
    filemenu = pf.GUI.menu.item('file')
    pf.gui.plugin_menu = plugins.create_plugin_menu(filemenu,before='---1')
    # Load configured plugins, ignore if not found
    plugins.loadConfiguredPlugins()

    # show current application/file
    appname = pf.cfg['curfile']
    pf.GUI.setcurfile(appname)

    # Last minute menu modifications can go here

    # cleanup
    pf.GUI.setBusy(False)         # HERE
    pf.GUI.addStatusBarButtons()

    if splash is not None:
        # remove the splash window
        splash.finish(pf.GUI)

    pf.GUI.setBusy(False)        # OR HERE

    pf.debug("Showing the GUI",pf.DEBUG.GUI)
    pf.GUI.show()

    # redirect standard output to board
    # TODO: this should disappear when we have buffered stdout
    # and moved this up into GUI init
    pf.GUI.board.redirect(pf.cfg['gui/redirect'])


    pf.GUI.update()

    if pf.cfg['gui/fortune']:
        sta,out = utils.runCommand(pf.cfg['fortune'])
        if sta == 0:
            draw.showInfo(out)

    #pf.app.setQuitOnLastWindowClosed(False)
    pf.app_started = True
    pf.GUI.processEvents()

    # load last project
    #
    #  TODO
    if pf.cfg['openlastproj']:
        fn = pf.cfg['curproj']
        if fn:
            try:
                proj = fileMenu.readProjectFile(fn)
                fileMenu.setProject(proj)
            except:
                # Avoid crashes from a faulty project file
                # TODO: should we push this up to fileMenu.readProjectFile ?
                #
                pf.message("Could not load the current project %s" % fn)
    #
    return 0


def createDatabases():
    """Create unified database objects for all menus."""
    from plugins import objects
    from geometry import Geometry
    from formex import Formex
    from mesh import Mesh
    from plugins.trisurface import TriSurface
    from plugins.curve import PolyLine,BezierSpline
    from plugins.nurbs import NurbsCurve
    pf.GUI.database = objects.Objects()
    pf.GUI.drawable = objects.DrawableObjects()
    pf.GUI.selection = {
        'geometry' : objects.DrawableObjects(clas=Geometry),
        'formex' : objects.DrawableObjects(clas=Formex),
        'mesh' : objects.DrawableObjects(clas=Mesh),
        'surface' : objects.DrawableObjects(clas=TriSurface),
        'polyline' : objects.DrawableObjects(clas=PolyLine),
        'nurbs' : objects.DrawableObjects(clas=NurbsCurve),
        'curve' : objects.DrawableObjects(clas=BezierSpline),
        }

def runGUI():
    """Go into interactive mode"""

    egg = pf.cfg.get('gui/easter_egg',None)
    pf.debug('EGG: %s' % str(egg),pf.DEBUG.INFO)
    if egg:
        pf.debug('EGG')
        if type(egg) is str:
            pye = egg.endswith('pye')
            egg = open(egg).read()
        else:
            pye = True
            egg = ''.join(egg)
        draw.playScript(egg,pye=True)

    if os.path.isdir(pf.cfg['workdir']):
        # Make the workdir the current dir
        os.chdir(pf.cfg['workdir'])
        pf.debug("Setting workdir to %s" % pf.cfg['workdir'],pf.DEBUG.INFO)
    else:
        # Save the current dir as workdir
        prefMenu.updateSettings({'workdir':os.getcwd(),'_save_':True})

    pf.interactive = True
    pf.debug("Start main loop",pf.DEBUG.INFO)

    #utils.procInfo('runGUI')
    #from multiprocessing import Process
    #p = Process(target=pf.app.exec_)
    #p.start()
    #res = p.join()
    res = pf.app.exec_()
    pf.debug("Exit main loop with value %s" % res,pf.DEBUG.INFO)
    return res


def classify_examples():
    m = pf.GUI.menu.item('Examples')


#### End
