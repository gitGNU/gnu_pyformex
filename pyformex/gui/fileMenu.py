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
"""Functions from the File menu."""

import os,shutil
import pyformex as pf
import widgets
import utils
import project
import draw
from script import processArgs,play
import image
import plugins

from gettext import gettext as _
from prefMenu import updateSettings


##################### handle project files ##########################


def openProject(fn=None,exist=False,access='wr',addGlobals=None,makeDefault=True):
    """Open a (new or old) Project file.

    The user is asked for a Project file name and the access modalities.
    Depending on the results of the dialog:

    - either an new project is create or an old is opened,
    - the old data may be discarded, added to the current exported symbols,
      or replace them
    - the opened Project may become the current Project, or its data are
      just imported in the current Project.


    The default will let the user create new project files as well as open
    existing ones.
    Use create=False or the convenience function openProject to only accept
    existing project files.

    If a compression level (1..9) is given, the contents will be compressed,
    resulting in much smaller project files at the cost of  

    Only one pyFormex project can be open at any time. The open project
    owns all the global data created and exported by any script.

    If makeDefault is True, an already open project will be closed and
    the opened project becomes the current project.
    If makeDefault is False, the project data are imported into pf.PF
    and the current project does not change. This means that if a project was
    open, the imported data will be added to it.
    
    If addGlobals is None, the user is asked whether the current globals
    should be added to the project. Set True or False to force or reject
    the adding without asking.
    """
    cur = fn if fn else '.'
    if makeDefault and pf.PF.filename is not None:
        options = ['Cancel','Close without saving','Save and Close']
        ans = draw.ask("What shall I do with your current project?",options)
        if ans == 'Cancel':
            return
        if ans == options[2]:
            pf.PF.save()
        cur = pf.PF.filename
    
    typ = utils.fileDescription(['pyf','all'])
    res = widgets.ProjectSelection(cur,typ,exist=exist).getResult()
    if res is None:
        # user canceled
        return

    fn = res.fn
    if not fn.endswith('.pyf'):
        fn += '.pyf'
    access = res.acc
    ## legacy = res.leg
    ## ignoresig = res.sig
    compression = res.cpr
    #print(fn,legacy,compression)

    ## if create and os.path.exists(fn):
    ##     res = draw.ask("The project file '%s' already exists\nShall I delete the contents or add to it?" % fn,['Delete','Add','Cancel'])
    ##     if res == 'Cancel':
    ##         return
    ##     if res == 'Add':
    ##         create = False
    pf.message("Opening project %s" % fn)
    
    if pf.PF:
        ## pf.message("Exported symbols: %s" % pf.PF.keys())
        ## if addGlobals is None:
        ##     res = draw.ask("pyFormex already contains exported symbols.\nShall I delete them or add them to your project?",['Delete','Add','Cancel'])
        ##     if res == 'Cancel':
        ##         # ESCAPE FROM CREATING THE PROJECT
        ##         return

        ##     addGlobals = res == 'Add'

        if addGlobals is None:
            pf.message("Currently exported symbols: %s" % pf.PF.keys())
            res = draw.ask("pyFormex already contains exported symbols.\nShall I delete them or add them to your project?",['Cancel','Delete','Add'])
            if res == 'Cancel':
                # ESCAPE FROM CREATING THE PROJECT
                return

            addGlobals = res == 'Add'

    # OK, we have all data, now create/open the project
        
    updateSettings({'workdir':os.path.dirname(fn)},save=True)
    signature = pf.Version[:pf.Version.rfind('-')]
    ## if ignoresig:
    ##     sig = ''

    # Loading the project may take a long while; attent user
    pf.GUI.setBusy()
    try:
        proj = project.Project(fn,access=access,signature=signature,compression=compression)
    except:
        proj = None
        raise
    finally:
        pf.GUI.setBusy(False)
        
    pf.message("Project contents: %s" % proj.keys())

    if hasattr(proj,'_autoscript_'):
        _ignore = "Ignore it!"
        _show = "Show it"
        _edit = "Load it in the editor"
        _exec = "Execute it"
        res = draw.ask("There is an autoscript stored inside the project.\nIf you received this project file from an untrusted source, you should probably not execute it.",[_ignore,_show,_edit,_exec])
        if res == _show:
            res = draw.showText(proj._autoscript_)#,actions=[_ignore,_edit,_show])
            return
        if res == _exec:
            draw.playScript(proj._autoscript_)
        elif res == _edit:
            fn = "_autoscript_.py"
            draw.checkWorkdir()
            f = open(fn,'w')
            f.write(proj._autoscript_)
            f.close()
            openScript(fn)
            editScript(fn)

    if hasattr(proj,'autofile') and draw.ack("The project has an autofile attribute: %s\nShall I execute this script?" % proj.autofile):
        processArgs([proj.autofile])

    if makeDefault:
        if pf.PF and addGlobals:
            proj.update(pf.PF)
        pf.PF = proj
        pf.GUI.setcurproj(fn)

    else:
        # Just import the data into current project
        pf.PF.update(proj)

    pf.message("Exported symbols: %s" % pf.PF.keys())


## def createProject():
##     """Open an new project.

##     Ask the user to select an existing project file, and then open it.
##     """
##     openProject(exist=False,access='w')


## def openExistingProject():
##     """Open an existing project.

##     Ask the user to select an existing project file, and then open it.
##     """
##     openProject(exist=True,access='rw')


def importProject():
    """Import an existing project.

    Ask the user to select an existing project file, and then import
    its data into the current project.
    """
    openProject(exist=True,access='r',addGlobals=False,makeDefault=False)
    

def setAutoScript():
    """Set the current script as autoScript in the project"""
    if pf.cfg['curfile'] and pf.GUI.canPlay:
        pf.PF._autoscript_ = open(pf.cfg['curfile']).read()
 

def setAutoFile():
    """Set the current script as autoScriptFile in the project"""
    if pf.cfg['curfile'] and pf.GUI.canPlay:
        pf.PF.autofile = pf.cfg['curfile']


def removeAutoScript():
    delattr(pf.PF,'_autoscript_')


def removeAutoFile():
    delattr(pf.PF,'autofile')


def saveProject():
    if pf.PF:
        pf.message("Project contents: %s" % pf.PF.keys())
        pf.GUI.setBusy()
        pf.PF.save()
        pf.GUI.setBusy(False)


def saveAsProject():
    if pf.PF:
        closeProjectWithoutSaving()
        openProject(pf.PF.filename,addGlobals=True)
        saveProject()


def closeProjectWithoutSaving():
    """Close the current project without saving it."""
    closeProject(False)
    

def closeProject(save=True):
    """Close the current project, saving it by default."""
    if pf.PF.filename is not None:
        pf.message("Closing project %s" % pf.PF.filename)
        if save:
            saveProject()
            if pf.PF:
                pf.message("Exported symbols: %s" % pf.PF.keys())
                if draw.ask("What shall I do with the exported symbols?",["Delete","Keep"]) == "Delete":
                    proj.clear()

    pf.PF.filename = None
    pf.GUI.setcurproj('None')
    

def askCloseProject():
    if pf.PF and pf.PF.filename is not None:
        choices = ['Exit without saving','SaveAs and Exit','Save and Exit']
        if pf.PF.access == 'r':
            choices = choices[:2]
        res = draw.ask("You have an unsaved open project: %s\nWhat do you want me to do?"%pf.PF.filename,choices,default=2)
        res = choices.index(res)
        if res == 1:
            saveAsProject()
        elif res == 2:
            saveProject()


##################### handle script files ##########################

def openScript(fn=None,exist=True,create=False):
    """Open a pyFormex script and set it as the current script.

    If no filename is specified, a file selection dialog is started to select
    an existing script, or allow to create a new file if exist is False.

    If the file exists and is a pyFormex script, it is set ready to execute.

    If create is True, a default pyFormex script template will be written
    to the file, overwriting the contents if the file existed. Then, the
    script is loaded into the editor.

    We encourage the use of createScript() to create new scripts and leave
    openScript() to open existing scripts.
    """
    if fn is None:
        cur = pf.cfg['curfile']
        if cur is None:
            cur = pf.cfg['workdir']
        if cur is None:
            cur  = '.'
        typ = utils.fileDescription('pyformex')
        fn = widgets.FileSelection(cur,typ,exist=exist).getFilename()
    if fn:
        if create:
            if not exist and os.path.exists(fn) and not draw.ack("The file %s already exists.\n Are you sure you want to overwrite it?" % fn):
                return None
            template = pf.cfg['scripttemplate']
            if (os.path.exists(template)):
                shutil.copyfile(template,fn)
        updateSettings({'workdir':os.path.dirname(fn)},save=True)
        pf.GUI.setcurfile(fn)
        pf.GUI.history.add(fn)
        if create:
            editScript(fn)
    return fn

      
def createScript(fn=None):
    return openScript(fn,exist=False,create=True)

    
def editScript(fn=None):
    """Load the current file in the editor.

    This only works if the editor was set in the configuration.
    The author uses 'emacsclient' to load the files in a running copy
    of Emacs.
    If a filename is specified, that file is loaded instead.
    """
    if pf.cfg['editor']:
        if fn is None:
            fn = pf.cfg['curfile']
        pid = utils.spawn('%s %s' % (pf.cfg['editor'],fn))
    else:
        draw.warning('No known editor was found or configured')

##################### other functions ##########################

    
def saveImage(multi=False):
    """Save an image to file.

    This will show the Save Image dialog, with the multisave mode checked if
    multi = True. Then, depending on the user's selection, it will either:
     - save the current Canvas/Window to file
     - start the multisave/autosave mode
     - do nothing
    """
    pat = map(utils.fileDescription, ['img','icon','all'])  
    dia = widgets.SaveImageDialog(pf.cfg['workdir'],pat,multi=multi)
    opt = dia.getResult()
    if opt:
        if opt.fm == 'From Extension':
            opt.fm = None
        if opt.qu < 0:
            opt.qu = -1
        updateSettings({'workdir':os.path.dirname(opt.fn)},save=True)
        image.save(filename=opt.fn,
                   format=opt.fm,
                   quality=opt.qu,
                   size=opt.sz,
                   window=opt.wi,
                   multi=opt.mu,
                   hotkey=opt.hk,
                   autosave=opt.au,
                   border=opt.bo,
                   rootcrop=opt.rc
                   )
def saveIcon():
    """Save an image as icon.

    This will show the Save Image dialog, with the multisave mode off and
    asking for an icon file name. Then save the current rendering to that file.
    """
    ## We should create a specialized input dialog, asking also for the size 
    fn = draw.askNewFilename(filter=utils.fileDescription('icon'))
    if fn:
        image.saveIcon(fn,size=32)

    
def startMultiSave():
    """Start/change multisave mode."""
    saveImage(True)


def stopMultiSave():
    """Stop multisave mode."""
    image.save()

from imageViewer import ImageViewer
viewer = None
def showImage():
    """Display an image file."""
    global viewer
    fn = draw.askFilename(filter=utils.fileDescription('img'))
    if fn:
        viewer = ImageViewer(pf.app,fn)
        viewer.show()


MenuData = [
    (_('&Open project'),openProject),
    ## (_('&Start new project'),createProject),
    ## (_('&Open existing project'),openExistingProject),
    (_('&Import a project'),importProject),
    (_('&Set current script as AutoScript'),setAutoScript),
    (_('&Remove the AutoScript'),removeAutoScript),
    (_('&Set current script as AutoFile'),setAutoFile),
    (_('&Remove the AutoFile'),removeAutoFile),
    (_('&Save project'),saveProject),
    (_('&Save project As'),saveAsProject),
    (_('&Close project without saving'),closeProjectWithoutSaving),
    (_('&Save and Close project'),closeProject),
    ('---',None),
    (_('&Create new script'),createScript),
    (_('&Open existing script'),openScript),
    (_('&Play script'),play),
    (_('&Edit script'),editScript),
    (_('&Change workdir'),draw.askDirname),
    (_('---1'),None),
    (_('&Save Image'),saveImage),
    (_('Start &MultiSave'),startMultiSave),
    (_('Save &Next Image'),image.saveNext),
    (_('Create &Movie'),image.createMovie),
    (_('&Stop MultiSave'),stopMultiSave),
    (_('&Save as Icon'),saveIcon),
    (_('&Show Image'),showImage),
    (_('---2'),None),
    (_('E&xit'),draw.closeGui),
]

#onExit(closeProject)

# End
