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
"""Saving OpenGL renderings to image files.

This module defines some functions that can be used to save the
OpenGL rendering and the pyFormex GUI to image files. There are even
provisions for automatic saving to a series of files and creating
a movie from these images.
"""
from __future__ import print_function


import pyformex as pf

from OpenGL import GL
from pyformex.gui import QtCore, QtGui, QtOpenGL
from pyformex import utils
from pyformex.gui.qtutils import relPos
import os


# The image formats recognized by pyFormex
image_formats_qt = []
image_formats_qtr = []
image_formats_gl2ps = []
image_formats_fromeps = []

def imageFormats(type='w'):
    if type == 'r':
        return image_formats_qtr
    else:
        return image_formats_qt + image_formats_gl2ps + image_formats_fromeps


# global parameters for multisave mode
multisave = None

# imported module
gl2ps = None

def initialize():
    """Initialize the image module."""
    global image_formats_qt, image_formats_qtr, image_formats_gl2ps, image_formats_fromeps, gl2ps, _producer, _gl2ps_types

    # Find interesting supporting software
    utils.hasExternal('imagemagick')
    # Set some globals
    pf.debug("Loading Image Formats", pf.DEBUG.IMAGE)
    image_formats_qt = [str(f) for f in QtGui.QImageWriter.supportedImageFormats()]
    image_formats_qtr = [str(f) for f in QtGui.QImageReader.supportedImageFormats()]
    ## if pf.cfg.get('imagesfromeps',False):
    ##     pf.image_formats_qt = []

    if utils.hasModule('gl2ps'):

        import gl2ps

        _producer = pf.Version() + ' (%s)' % pf.cfg.get('help/website', '')
        _gl2ps_types = {
            'ps': gl2ps.GL2PS_PS,
            'eps': gl2ps.GL2PS_EPS,
            'tex': gl2ps.GL2PS_TEX,
            'pdf': gl2ps.GL2PS_PDF,
            }
        if utils.checkVersion('gl2ps', '1.03') >= 0:
            _gl2ps_types.update({
                'svg': gl2ps.GL2PS_SVG,
                'pgf': gl2ps.GL2PS_PGF,
                })
        image_formats_gl2ps = _gl2ps_types.keys()
        image_formats_fromeps = [ 'ppm', 'png', 'jpeg', 'rast', 'tiff',
                                     'xwd', 'y4m' ]
    pf.debug("""
Qt image types for saving: %s
Qt image types for input: %s
gl2ps image types: %s
image types converted from EPS: %s""" % (image_formats_qt, image_formats_qtr, image_formats_gl2ps, image_formats_fromeps), pf.DEBUG.IMAGE|pf.DEBUG.INFO)


def imageFormats():
    """Return a list of the valid image formats.

    image formats are lower case strings as 'png', 'gif', 'ppm', 'eps', etc.
    The available image formats are derived from the installed software.
    """
    return image_formats_qt + \
           image_formats_gl2ps + \
           image_formats_fromeps


def checkImageFormat(fmt,verbose=True):
    """Checks image format; if verbose, warn if it is not.

    Returns the image format, or None if it is not OK.
    """
    pf.debug("Format requested: %s" % fmt, pf.DEBUG.IMAGE)
    pf.debug("Formats available: %s" % imageFormats(), pf.DEBUG.IMAGE)
    if fmt in imageFormats():
        if fmt == 'tex' and verbose:
            pf.warning("This will only write a LaTeX fragment to include the 'eps' image\nYou have to create the .eps image file separately.\n")
        return fmt
    else:
        if verbose:
            from pyformex.gui import draw
            draw.error("Sorry, can not save in %s format!\n"
                       "I suggest you use 'png' format ;)"%fmt)
        return None


def imageFormatFromExt(ext):
    """Determine the image format from an extension.

    The extension may or may not have an initial dot and may be in upper or
    lower case. The format is equal to the extension characters in lower case.
    If the supplied extension is empty, the default format 'png' is returned.
    """
    if len(ext) > 0:
        if ext[0] == '.':
            ext = ext[1:]
        fmt = ext.lower()
    else:
        fmt = 'png'
    return fmt


##### LOW LEVEL FUNCTIONS ##########

def save_canvas(canvas,fn,fmt='png',quality=-1,size=None,alpha=False):
    """Save the rendering on canvas as an image file.

    canvas specifies the qtcanvas rendering window.
    fn is the name of the file
    fmt is the image file format
    """
    # make sure we have the current content displayed (on top)
    canvas.makeCurrent()
    canvas.raise_()
    canvas.display()
    pf.app.processEvents()

    if fmt in image_formats_qt:
        pf.debug("Image format can be saved by Qt", pf.DEBUG.IMAGE)
        if size is None:
            #
            # Use direct grabbing from current buffer
            #
            GL.glFlush()
            pf.debug("Saving image from opengl buffer with size %sx%s" % canvas.getSize(), pf.DEBUG.IMAGE)
            qim = canvas.grabFrameBuffer(withAlpha=alpha)
        else:
            wc, hc = canvas.getSize()
            try:
                w, h = size
            except:
                w, h = wc, hc
            pf.debug("Saving image from virtual buffer with size %sx%s" % (w, h), pf.DEBUG.IMAGE)
            qim = canvas.image(w,h,remove_alpha=not alpha)

        pf.debug("Image has alpha channel: %s" % qim.hasAlphaChannel())
        print("SAVING %s in format %s with quality %s" % (fn, fmt, quality))
        if qim.save(fn, fmt, quality):
            sta = 0
        else:
            sta = 1

    elif fmt in image_formats_gl2ps:
        pf.debug("Image format can be saved by gl2ps", pf.DEBUG.IMAGE)
        sta = save_PS(canvas, fn, fmt)

    elif fmt in image_formats_fromeps:
        pf.debug("Image format can be converted from eps", pf.DEBUG.IMAGE)
        fneps = os.path.splitext(fn)[0] + '.eps'
        delete = not os.path.exists(fneps)
        save_PS(canvas, fneps, 'eps')
        if os.path.exists(fneps):
            cmd = 'pstopnm -portrait -stdout %s' % fneps
            if fmt != 'ppm':
                cmd += '| pnmto%s > %s' % (fmt, fn)
            utils.command(cmd, shell=True)
            if delete:
                os.remove(fneps)

    return sta

initialize()

if gl2ps:

    def save_PS(canvas,filename,filetype=None,title='',producer='',viewport=None):
        """ Export OpenGL rendering to PostScript/PDF/TeX format.

        Exporting OpenGL renderings to PostScript is based on the PS2GL
        library by Christophe Geuzaine (http://geuz.org/gl2ps/), linked
        to Python by Toby Whites's wrapper
        (http://www.esc.cam.ac.uk/~twhi03/software/python-gl2ps-1.1.2.tar.gz)

        This function is only defined if the gl2ps module is found.

        The filetype should be one of 'ps', 'eps', 'pdf' or 'tex'.
        If not specified, the type is derived from the file extension.
        In case of the 'tex' filetype, two files are written: one with
        the .tex extension, and one with .eps extension.
        """
        fp = open(filename, "wb")
        if filetype:
            filetype = _gl2ps_types[filetype]
        else:
            s = filename.lower()
            for ext in _gl2ps_types.keys():
                if s.endswith('.'+ext):
                    filetype = _gl2ps_types[ext]
                    break
            if not filetype:
                filetype = gl2ps.GL2PS_EPS
        if not title:
            title = filename
        if not viewport:
            viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
        bufsize = 0
        state = gl2ps.GL2PS_OVERFLOW
        opts = gl2ps.GL2PS_SILENT | gl2ps.GL2PS_SIMPLE_LINE_OFFSET | gl2ps.GL2PS_USE_CURRENT_VIEWPORT
        ##| gl2ps.GL2PS_NO_BLENDING | gl2ps.GL2PS_OCCLUSION_CULL | gl2ps.GL2PS_BEST_ROOT
        ##color = GL[[0.,0.,0.,0.]]
        #print("VIEWPORT %s" % str(viewport))
        #print(fp)
        viewport=None
        while state == gl2ps.GL2PS_OVERFLOW:
            bufsize += 1024*1024
            gl2ps.gl2psBeginPage(title, _producer, viewport, filetype,
                                 gl2ps.GL2PS_BSP_SORT, opts, GL.GL_RGBA,
                                 0, None, 0, 0, 0, bufsize, fp, '')
            canvas.display()
            GL.glFinish()
            state = gl2ps.gl2psEndPage()
        fp.close()
        return 0


def save_window(filename,format,quality=-1,windowname=None,crop=None):
    """Save a window as an image file.

    This function needs a filename AND format.
    If a window is specified, the named window is saved.
    Else, the main pyFormex window is saved.

    If crop is given, the specified rectangle is cropped.
    If crop='canvas', windowname is set to main pyFormex window
    and crop to canvas rectangle.

    In all cases, the GUI and current canvas are raised.
    """
    pf.GUI.raise_()
    pf.GUI.repaint()
    pf.GUI.toolbar.repaint()
    pf.GUI.update()
    pf.canvas.makeCurrent()
    pf.canvas.raise_()
    pf.canvas.update()
    pf.app.processEvents()

    if crop == 'canvas':
        windowname = pf.GUI.windowTitle()
        x,y = relPos(pf.canvas)
        crop = (x,y,pf.canvas.width(),pf.canvas.height())

    if windowname is None:
        windowname = pf.GUI.windowTitle()

    return save_window_rect(filename, format, quality, windowname, crop)


def save_window_rect(filename,format,quality=-1,window='root',crop=None):
    """Save a rectangular part of the screen to a an image file.

    crop: (x,y,w,h)
    """
    options = ''
    if crop:
        x,y,w,h = crop
        options += ' -crop "%sx%s+%s+%s"' % (w, h, x, y)
    cmd = 'import -window "%s" %s %s:%s' % (window, options, format, filename)
    # We need to use shell=True because window name might contain spaces
    # thus we need to add quotes, but these are not stripped off when
    # splitting the command line.
    # TODO: utils should probably be changed to strip quotes after splitting
    P = utils.command(cmd,shell=True)
    if P.sta:   # He, isn't this standard with utils.command?
        print(P.sta)
        print(P.err)
        print(P.out)
    return P.sta


#### USER FUNCTIONS ################

def save(filename=None,window=False,multi=False,hotkey=True,autosave=False,border=False,grab=False,format=None,quality=-1,size=None,verbose=False,alpha=True,rootcrop=None):
    """Saves an image to file or Starts/stops multisave mode.

    With a filename and multi==False (default), the current viewport rendering
    is saved to the named file.

    With a filename and multi==True, multisave mode is started.
    Without a filename, multisave mode is turned off.
    Two subsequent calls starting multisave mode without an intermediate call
    to turn it off, do not cause an error. The first multisave mode will
    implicitely be ended before starting the second.

    In multisave mode, each call to saveNext() will save an image to the
    next generated file name.
    Filenames are generated by incrementing a numeric part of the name.
    If the supplied filename (after removing the extension) has a trailing
    numeric part, subsequent images will be numbered continuing from this
    number. Otherwise a numeric part '-000' will be added to the filename.

    If window is True, the full pyFormex window is saved.
    If window and border are True, the window decorations will be included.
    If window is False, only the current canvas viewport is saved.

    If grab is True, the external 'import' program is used to grab the
    window from the screen buffers. This is required by the border and
    window options.

    If hotkey is True, a new image will be saved by hitting the 'S' key.
    If autosave is True, a new image will be saved on each execution of
    the 'draw' function.
    If neither hotkey nor autosave are True, images can only be saved by
    executing the saveNext() function from a script.

    If no format is specified, it is derived from the filename extension.
    fmt should be one of the valid formats as returned by imageFormats()

    If verbose=True, error/warnings are activated. This is usually done when
    this function is called from the GUI.

    """
    #print "SAVE: quality=%s" % quality
    global multisave

    if rootcrop is not None:
        pf.warning("image.save does no longer support the 'rootcrop' option")

    # Leave multisave mode if no filename or starting new multisave mode
    if multisave and (filename is None or multi):
        print("Leave multisave mode")
        if multisave[6]:
            pf.GUI.signals.SAVE.disconnect(saveNext)
        multisave = None

    if filename is None:
        return

    #chdir(filename)
    name, ext = os.path.splitext(filename)
    # Get/Check format
    if not format: # is None:
        format = checkImageFormat(imageFormatFromExt(ext))
    if not format:
        return

    if multi: # Start multisave mode
        names = utils.NameSequence(name, ext)
        if os.path.exists(names.peek()):
            next = names.next()
        print("Start multisave mode to files: %s (%s)" % (names.name, format))
        if hotkey:
             pf.GUI.signals.SAVE.connect(saveNext)
             if verbose:
                 pf.warning("Each time you hit the '%s' key,\nthe image will be saved to the next number." % pf.cfg['keys/save'])
        multisave = (names, format, quality, size, window, border, hotkey, autosave, grab)
        print("MULTISAVE %s "% str(multisave))
        return multisave is None

    else:
        # Save the image
        if grab:
            # Grab from X server buffers (needs external)
            #
            # TODO: configure command to grab screen rectangle
            #
            if window:
                if border:
                    windowname = 'root'
                    crop = pf.GUI.frameGeometry().getRect()
                else:
                    windowname = None
                    crop = None
            else:
                windowname = None
                crop = 'canvas'

            sta = save_window(filename, format, quality, windowname=windowname, crop=crop)
        else:
            # Get from OpenGL rendering
            if size == pf.canvas.getSize():
                # TODO:
                # We could grab from the OpenGL buffers here!!
                size = None
            # Render in an off-screen buffer and grab from there
            #
            # TODO: the offscreen buffer should be properly initialized
            # according to the current canvas
            #
            sta = save_canvas(pf.canvas, filename, format, quality, size, alpha)

        if sta:
            pf.debug("Error while saving image %s" % filename, pf.DEBUG.IMAGE)
        else:
            print("Image file %s written" % filename)
        return


# Keep the old name for compatibility
saveImage = save


def saveNext():
    """In multisave mode, saves the next image.

    This is a quiet function that does nothing if multisave was not activated.
    It can thus safely be called on regular places in scripts where one would
    like to have a saved image and then either activate the multisave mode
    or not.
    """
    if multisave:
        names, format, quality, size, window, border, hotkey, autosave, grab = multisave
        name = names.next()
        save(name, window, False, hotkey, autosave, border, grab, format, quality, size, False)


def changeBackgroundColorXPM(fn, color):
    """Changes the background color of an .xpm image.

    This changes the background color of an .xpm image to the given value.
    fn is the filename of an .xpm image.
    color is a string with the new background color, e.g. in web format
    ('#FFF' or '#FFFFFF' is white). A special value 'None' may be used
    to set a transparent background.
    The current background color is selected from the lower left pixel.
    """
    t = open(fn).readlines()
    c = ''
    for l in t[::-1]:
        if l.startswith('"'):
            c = l[1]
            print("Found '%s' as background character" % c)
            break
    if not c:
        print("Can not change background color of '%s' " % fn)
        return
    for i, l in enumerate(t):
        if l.startswith('"%s c ' % c):
            t[i] = '"%s c None",\n' % c
            break
    f = open(fn, 'w')
    f.writelines(t)
    f.close()


def saveIcon(fn,size=32,transparent=True):
    """Save the current rendering as an icon."""

    if not fn.endswith('.xpm'):
        fn += '.xpm'
    save_canvas(pf.canvas, fn, fmt='xpm', size=(size, size))
    print("Saved icon to file %s in %s" % (fn, os.getcwd()))
    if transparent:
        changeBackgroundColorXPM(fn, 'None')


def autoSaveOn():
    """Returns True if autosave multisave mode is currently on.

    Use this function instead of directly accessing the autosave variable.
    """
    return multisave and multisave[-2]


def createMovie(files,encoder='convert',outfn='output',**kargs):
    """Create a movie from a saved sequence of images.

    Parameters:

    - `files`: a list of filenames, or a string with one or more filenames
      separated by whitespace. The filenames can also contain wildcards
      interpreted by the shell.
    - `encoder`: string: the external program to be used to create the movie.
      This will also define the type of output file, and the extra parameters
      that can be passed. The external program has to be installed on the
      computer. The default is `convert`, which will create animated gif.
      Other possible values are 'mencoder' and 'ffmeg', creating meg4
      encode movies from jpeg input files.
    - `outfn`: string: output file name (not including the extension).
      Default is output.

    Other parameters may be passed and may be needed, depending on the
    converter program used. Thus, for the default 'convert' program,
    each extra keyword parameter will be translated to an option
    '-keyword value' for the command.

    Example::

      createMovie('images*.png',delay=1,colors=256)

    will create an animated gif 'output.gif'.
    """
    print("Encoding %s" % files)
    if isinstance(files, list):
        files = ' '.join(files)

    if encoder == 'convert':
        outfile = outfn+'.gif'
        cmd= "convert "+" ".join(["-%s %s"%k for k in kargs.items()])+" %s %s"%(files, outfile)
    elif encoder == 'mencoder':
        outfile = outfn + '.avi'
        cmd = "mencoder \"mf://%s\" -o %s -mf fps=%s -ovc lavc -lavcopts vcodec=msmpeg4v2:vbitrate=%s" % (files, outfile, kargs['fps'], kargs['vbirate'])
    else:
        outfile = outfn+'.mp4'
        cmd = "ffmpeg -qscale 1 -r 1 -i %s output.mp4" % files
    pf.debug(cmd, pf.DEBUG.IMAGE)
    P = utils.command(cmd)
    print("Created file %s" % os.path.abspath(outfile))
    return P.sta


def saveMovie(filename,format,windowname=None):
    """Create a movie from the pyFormex window."""
    if windowname is None:
        windowname = pf.GUI.windowTitle()
    pf.GUI.raise_()
    pf.GUI.repaint()
    pf.GUI.toolbar.repaint()
    pf.GUI.update()
    pf.canvas.makeCurrent()
    pf.canvas.raise_()
    pf.canvas.update()
    pf.app.processEvents()
    windowid = windowname
    cmd = "xvidcap --fps 5 --window %s --file %s" % (windowid, filename)
    pf.debug(cmd, pf.DEBUG.IMAGE)
    P = utils.command(cmd)
    return P.sta


initialize()


### End
