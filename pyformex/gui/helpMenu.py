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
# -*- coding: utf-8 -*-
##
##  This file is part of pyFormex 0.9.1  (Tue Oct 15 21:05:25 CEST 2013)
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  http://savannah.nongnu.org/projects/pyformex/
##  Copyright 2004-2013 (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
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
"""Display help

"""
from __future__ import print_function


import pyformex as pf

import os, sys
from pyformex.gui import draw
from pyformex import utils
import random
from pyformex.gui import viewport
from gettext import gettext as _


def help(page=None):
    """Display a html help page.

    If no page is specified, the help manual is displayed.

    If page is a string starting with 'http:', the page is displayed with
    the command set in pf.cfg['browser'], else with the command in
    pf.cfg['viewer']
    """
    if not page:
        page = pf.cfg['help/manual']
    if page.startswith('http:') or page.startswith('file:'):
        browser = pf.cfg['browser']
    else:
        browser = pf.cfg['viewer']
    print([browser, page])
    utils.system([browser, page],wait=False)


def catchAndDisplay(expression):
    """Catch stdout from a Python expression and display it in a window."""
    save = sys.stdout
    try:
        f = utils.tempFile(delete=True)
        sys.stdout = f
        eval(expression)
        f.seek(0)
        draw.showText(f.read())
        f.close()
    finally:
        sys.stdout = save


## def qappargs():
##     """Display informeation on the Qt application arguments."""
##     qtversion = utils.hasModule('pyqt4')
##     qtversion = '.'.join(qtversion.split('.')[:2])
##     link = "http://doc.trolltech.com/%s/qapplication.html#QApplication" % qtversion
##     help(link)

def opengl():
    """Display the OpenGL format description."""
    if pf.options.opengl2:
        from pyformex.opengl import canvas
        s = utils.formatDict(canvas.glVersion()) + '\n'
    else:
        s = ''

    s += viewport.OpenGLFormat(pf.canvas.format())
    draw.showText(s)

def detected():
    """Display the detected software components."""
    draw.showText(utils.reportSoftware(header="Detected Software"))

def about():
    """Display short information about pyFormex."""
    version = pf.Version()
    draw.showInfo("""..

%s
%s

A tool for generating, manipulating and transforming 3D geometrical models by sequences of mathematical operations.

%s

Distributed under the GNU GPL version 3 or later
""" % (version, '='*len(version), pf.Copyright))

# List of developers/contributors (current and past)
_developers = [
    'Matthieu De Beule',
    'Nic Debusschere',
    'Gianluca De Santis',
    'Bart Desloovere',
    'Wouter Devriendt',
    'Francesco Iannaccone',
    'Peter Mortier',
    'Tim Neels',
    'Tomas Praet',
    'Tran Phuong Toan',
    'Sofie Van Cauter',
    'Benedict Verhegghe',
    'Zhou Wenxuan',
    ]
random.shuffle(_developers)

def developers():
    """Display the list of developers."""
    random.shuffle(_developers)
    draw.showInfo("""
The following people have
contributed to pyFormex.
They are listed in random order.

%s

If you feel that your name was left
out in error, please write to
benedict.verhegghe@ugent.be.
""" % '\n'.join(_developers))


_cookies = [
    "Smoking may be hazardous to your health.",
    "Windows is a virus.",
    "Coincidence does not exist. Perfection does.",
    "It's all in the code.",
    "Python is the universal glue.",
    "Intellectual property is a mental illness.",
    "Programmers are tools for converting caffeine into code.",
    "There are 10 types of people in the world: those who understand binary, and those who don't.",
    "Linux: the choice of a GNU generation",
    "Everything should be made as simple as possible, but not simpler. (A. Einstein)",
    "Perfection [in design] is achieved, not when there is nothing more to add, but when there is nothing left to take away. (Antoine de Saint-Exupéry)",
    "Programming today is a race between software engineers striving to build bigger and better idiot-proof programs, and the universe trying to build bigger and better idiots. So far, the universe is winning. (Rick Cook)",
    "In theory, theory and practice are the same. In practice, they're not. (Yoggi Berra)",
    "Most good programmers do programming not because they expect to get paid or get adulation by the public, but because it is fun to program. (Linus Torvalds)",
    "Always code as if the guy who ends up maintaining your code will be a violent psychopath who knows where you live. (Martin Golding)",
    "If Microsoft had developed Internet, we could not ever see the source code of web pages. HTML might be a compiled language then.",
    "What one programmer can do in one month, two programmers can do in two months.",
    "Windows 9x: n. 32 bit extensions and a graphical shell for a 16 bit patch to an 8 bit operating system originally coded for a 4 bit microprocessor, written by a 2 bit company that can't stand 1 bit of competition. (Cygwin FAQ)",
    "You know, when you have a program that does something really cool, and you wrote it from scratch, and it took a significant part of your life, you grow fond of it. When it's finished, it feels like some kind of amorphous sculpture that you've created. It has an abstract shape in your head that's completely independent of its actual purpose. Elegant, simple, beautiful.\nThen, only a year later, after making dozens of pragmatic alterations to suit the people who use it, not only has your Venus-de-Milo lost both arms, she also has a giraffe's head sticking out of her chest and a cherubic penis that squirts colored water into a plastic bucket. The romance has become so painful that each day you struggle with an overwhelming urge to smash the fucking thing to pieces with a hammer. (Nick Foster)",
    "One of my most productive days was throwing away 1000 lines of code. (Ken Thompson)",
    ]
random.shuffle(_cookies)

def roll(l):
    l.append(l.pop(0))

def cookie():
    draw.showInfo(_cookies[0], ["OK"])
    roll(_cookies)


def showURL(link):
    """Show a html document in the browser.

    `link` is an URL of a html document. If it does not start with
    `http://`, the latter will be prepended.
    The resulting URL is passed to the user's default or configured browser.
    """
    if not link.startswith('http://') and not link.startswith('file://'):
        link = 'http://'+link
    help(link)


def showFileOrURL(link):
    """Show a html document or a text file.

    `link` is either a file name or an URL of a html document.
    If `link` starts with `http://` or `file://`, it is interpreted as
    an URL and the corresponding document is shown in the user's browser.
    Else, `link` is interpreted as a filename and if the file exists, it
    is shown in a pyFormex text window.
    """
    if link.startswith('http://') or link.startswith('file://'):
        showURL(link)
    else:
        draw.showFile(link, mono=not link.endswith('.rst'))


def searchText():
    """Search text in pyFormex source files.

    Asks a pattern from the user and searches for it through all
    the pyFormex source files.
    """
    from pyformex.gui.draw import _I
    res = draw.askItems([
        _I('pattern', '', text='String to grep'),
        _I('options', '', text='Options', tooltip="Some cool options: -a (extended search), -i (ignore case), -f (literal string), -e (extended regexp)"),
        ])

    if res:
        out = utils.grepSource(relative=False,**res)
        draw.showText(out, mono=True, modal=False)


def searchIndex():
    """Search text in pyFormex refman index.

    Asks a pattern from the user and searches for it the index of the
    local pyFormex documentation. Displays the results in the browser.
    """
    from pyformex.gui.draw import _I
    res = draw.askItems([
        _I('text', '', text='String to search'),
        ])

    if res:
        print("file://%s/doc/html/search.html?q=%s&check_keywords=yes&area=default" % (pf.cfg['pyformexdir'], res['text']))
        showURL("file://%s/doc/html/search.html?q=%s&check_keywords=yes&area=default" % (pf.cfg['pyformexdir'], res['text']))


def createMenuData():
    """Returns the help menu data"""
    DocsMenuData = [(k, help, {'data':v}) for k, v in pf.cfg['help/docs']]
    Docs2MenuData = [(k, draw.showFile, {'data':v}) for k, v in pf.cfg['help/docs2']]
    LinksMenuData = [(k, showURL, {'data':v}) for k, v in pf.cfg['help/links']]

    try:
        MenuData = [
            DocsMenuData[0],
            ('---', None),
            ] + DocsMenuData[1:] + [
            (_('&Search in index'), searchIndex),
            (_('&Search in source'), searchText),
            (_('&Current Application'), draw.showDoc),
            ('---', None),
            ] + Docs2MenuData + [
            (_('&Detected Software'), detected),
            (_('&OpenGL Format'), opengl),
            (_('&Fortune Cookie'), cookie),
            (_('&Favourite Links'), LinksMenuData),
            (_('&People'), developers),
            (_('&About'), about),
            ]
    except:
        MenuData = []

    if pf.installtype in 'SG':
        pyformexdir = pf.cfg['pyformexdir']
        devtodo = os.path.join(pyformexdir, "..", "TODO")
        devhowto = os.path.join(pyformexdir, "..", "HOWTO-dev.rst")
        devapp = os.path.join(pyformexdir, "..", "scripts-apps.rst")
        devextra = os.path.join(pyformexdir, "..", "install-extra.rst")
        devopengl = os.path.join(pyformexdir, "..", "OPENGL-dev.rst")
        #print pf.refcfg.help['developer']
        developer = [
            ('Developer HOWTO', devhowto),
            ('New OPENGL engine', devopengl),
            ('Scripts versus Apps', devapp),
            ('pyFormex TODO list', devtodo),
            ('Installation of extra software', devextra),
            ('Numpy documentation guidelines', 'http://github.com/numpy/numpy/blob/master/doc/HOWTO_DOCUMENT.rst.txt'),
            ('re-structured text (reST)', 'http://docutils.sourceforge.net/rst.html')
            ]


        DevLinksMenuData = [(k, showFileOrURL, {'data':v}) for k, v in developer]
        MenuData += [
            ('---', None),
            (_('&Developer Guidelines'), DevLinksMenuData),
            ]

        def install_external(pkgdir, prgname):
            extdir = os.path.join(pf.cfg['pyformexdir'], 'extra', pkgdir)
            P = utils.system("cd %s; make && gksu make install" % extdir, shell=True)
            if P.sta:
                info = P.out
            else:
                if utils.hasExternal(prgname, force=True):
                    info = "Succesfully installed %s" % pkgdir
                else:
                    info ="You should now restart pyFormex!"
            draw.showInfo(info)
            return P.sta

        def install_dxfparser():
            install_external('dxfparser', 'pyformex-dxfparser')

        def install_postabq():
            install_external('postabq', 'pyformex-postabq')

        def install_gts():
            install_external('gts', 'gtsinside')


        MenuData.append((_('&Install Externals'), [
            (_('dxfparser'), install_dxfparser, {'tooltip':"Install dxfparser: requires libdxflib-dev!"}),
            (_('postabq'), install_postabq),
            (_('gts'), install_gts),
            ]))


        # DEV: Leave the following commented code as an example

        ## #
        ## # Test of the exit function
        ## #

        ## def testExit():
        ##     import guimain
        ##     ret = guimain.exitDialog()
        ##     print "ExitDialog returned: %s" % ret

        ## MenuData.append((_('&Test Functions'),[
        ##     (_('test exit'),testExit),
        ##     ]))


    return MenuData


# End
