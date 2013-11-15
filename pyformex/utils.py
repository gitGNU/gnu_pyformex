# $Id$
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
"""A collection of miscellaneous utility functions.

"""
from __future__ import print_function

import pyformex as pf

import os
import re
import sys
import tempfile
import time
import subprocess
import threading
import shlex

from mydict import formatDict

# Software detection has been moved to software.py
# We currently import everything from software here, for compatibility
# TODO: This should be removed later on.
from software import *

# Some regular expressions
digits = re.compile(r'(\d+)')

######### WARNINGS ##############

_warn_category = { 'U': UserWarning, 'D':DeprecationWarning }

def saveWarningFilter(message,module='',category=UserWarning):
    cat = inverseDict(_warn_category).get(category,'U')
    oldfilters = pf.prefcfg['warnings/filters']
    newfilters = oldfilters + [(str(message),'',cat)]
    pf.prefcfg.update({'filters':newfilters},name='warnings')
    pf.debug("Future warning filters: %s" % pf.prefcfg['warnings/filters'],pf.DEBUG.WARNING)


def filterWarning(message,module='',cat='U',action='ignore'):
    import warnings
    pf.debug("Filter Warning '%s' from module '%s' cat '%s'" % (message,module,cat),pf.DEBUG.WARNING)
    category = _warn_category.get(cat,Warning)
    warnings.filterwarnings(action,message,category,module)


def warn(message,level=UserWarning,stacklevel=3):
    import warnings
    warnings.warn(message,level,stacklevel)


def deprec(message,stacklevel=4):
    warn(message,level=DeprecationWarning,stacklevel=stacklevel)


def deprecation(message):
    def decorator(func):
        def wrapper(*_args,**_kargs):
            deprec(message)
            # For some reason these messages are not auto-appended to
            # the filters for the currently running program
            # Therefore we do it here explicitely
            filterWarning(str(message))
            return func(*_args,**_kargs)
        return wrapper
    return decorator


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
    dirname,basename = os.path.split(filename)
    basename,ext = os.path.splitext(basename)
    if accept_ext and ext not in accept_ext or \
       reject_ext and ext in reject_ext:
        basename,ext = basename+ext,''
    return dirname,basename,ext


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
    return os.path.join(dirname,basename) + ext


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
    dirname,basename,oldext = splitFilename(filename,accept_ext,reject_ext)
    return buildFilename(dirname,basename,ext)


def projectName(fn):
    """Derive a project name from a file name.
`
    The project name is the basename of the file without the extension.
    It is equivalent with splitFilename(fn)[1]
    """
    return os.path.splitext(os.path.basename(fn))[0]


def tildeExpand(fn):
    """Perform tilde expansion on a filename.

    Bash, the most used command shell in Linux, expands a '~' in arguments
    to the users home direction.
    This function can be used to do the same for strings that did not receive
    the bash tilde expansion, such as strings in the configuration file.
    """
    return fn.replace('~',os.environ['HOME'])


##########################################################################
## File types ##
################

def all_image_extensions():
    """Return a list with all known image extensions."""
    imgfmt = []


file_description = {
    'all': 'All files (*)',
    'ccx': 'CalCuliX files (*.dat *.inp)',
    'dxf': 'AutoCAD .dxf files (*.dxf)',
    'dxfall': 'AutoCAD .dxf or converted(*.dxf *.dxftext)',
    'dxftext': 'Converted AutoCAD files (*.dxftext)',
    'flavia' : 'flavia results (*.flavia.msh *.flavia.res)',
    'gts': 'GTS files (*.gts)',
    'html': 'Web pages (*.html)',
    'icon': 'Icons (*.xpm)',
    'img': 'Images (*.png *.jpg *.eps *.gif *.bmp)',
    'inp': 'Abaqus or CalCuliX input files (*.inp)',
    'neu': 'Gambit Neutral files (*.neu)',
    'off': 'OFF files (*.off)',
    'pgf': 'pyFormex geometry files (*.pgf)',
    'png': 'PNG images (*.png)',
    'postproc': 'Postproc scripts (*_post.py *.post)',
    'pyformex': 'pyFormex scripts (*.py *.pye)',
    'pyf': 'pyFormex projects (*.pyf)',
    'smesh': 'Tetgen surface mesh files (*.smesh)',
    'stl': 'STL files (*.stl)',
    'stlb': 'Binary STL files (*.stl)',  # Use only for output
    'surface': 'Surface model (*.off *.gts *.stl *.off.gz *.gts.gz *.stl.gz *.neu *.smesh *.vtp *.vtk)',
    'tetgen': 'Tetgen file (*.poly *.smesh *.ele *.face *.edge *.node *.neigh)',
    'vtp': 'vtkPolyData file (*.vtp)',
}


def fileDescription(ftype):
    """Return a description of the specified file type.

    The description of known types are listed in a dict file_description.
    If the type is unknown, the returned string has the form
    ``TYPE files (*.type)``
    """
    if type(ftype) is list:
        return map(fileDescription,ftype)
    ftype = ftype.lower()
    return file_description.get(ftype,"%s files (*.%s)" % (ftype.upper(),ftype))


def fileType(ftype):
    """Normalize a filetype string.

    The string is converted to lower case and a leading dot is removed.
    This makes it fit for use with a filename extension.

    Example:

    >>> fileType('pdf')
    'pdf'
    >>> fileType('.pdf')
    'pdf'
    >>> fileType('PDF')
    'pdf'
    >>> fileType('.PDF')
    'pdf'

    """
    ftype = ftype.lower()
    if len(ftype) > 0 and ftype[0] == '.':
        ftype = ftype[1:]
    return ftype


def fileTypeFromExt(fname):
    """Derive the file type from the file name.

    The derived file type is the file extension part in lower case and
    without the leading dot.

    Example:

    >>> fileTypeFromExt('pyformex.pdf')
    'pdf'
    >>> fileTypeFromExt('pyformex')
    ''
    >>> fileTypeFromExt('pyformex.pgf')
    'pgf'
    >>> fileTypeFromExt('pyformex.pgf.gz')
    'pgf.gz'
    >>> fileTypeFromExt('pyformex.gz')
    'gz'
    """
    name,ext = os.path.splitext(fname)
    ext = fileType(ext)
    if ext == 'gz':
        ext1 = fileTypeFromExt(name)
        if ext1:
            ext = '.'.join([ext1,ext])
    return ext


def fileSize(fn):
    """Return the size in bytes of the file fn"""
    return os.path.getsize(fn)


def findIcon(name):
    """Return the file name for an icon with given name.

    If no icon file is found, returns the question mark icon.
    """
    fname = buildFilename(pf.cfg['icondir'],name,pf.cfg['gui/icontype'])
    if not os.path.exists(fname):
        fname = buildFilename(pf.cfg['icondir'],'question',pf.cfg['gui/icontype'])

    return fname


##########################################################################
## File lists ##
################

def prefixFiles(prefix,files):
    """Prepend a prefix to a list of filenames."""
    return [ os.path.join(prefix,f) for f in files ]


def matchMany(regexps,target):
    """Return multiple regular expression matches of the same target string."""
    return [re.match(r,target) for r in regexps]


def matchCount(regexps,target):
    """Return the number of matches of target to  regexps."""
    return len(filter(None,matchMany(regexps,target)))


def matchAny(regexps,target):
    """Check whether target matches any of the regular expressions."""
    return matchCount(regexps,target) > 0


def matchNone(regexps,target):
    """Check whether targes matches none of the regular expressions."""
    return matchCount(regexps,target) == 0


def matchAll(regexps,target):
    """Check whether targets matches all of the regular expressions."""
    return matchCount(regexps,target) == len(regexps)


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
            remove = [ d for d in dirs if matchAny(excludedirs,d) ]
            for d in remove:
                dirs.remove(d)
        if includedirs:
            remove = [ d for d in dirs if not matchAny(includedirs,d) ]
            for d in remove:
                dirs.remove(d)
        if listdirs and topdown:
            filelist.append(root)
        if excludefiles:
            files = [ f for f in files if matchNone(excludefiles,f) ]
        if includefiles:
            files = [ f for f in files if matchAny(includefiles,f) ]
        filelist.extend(prefixFiles(root,files))
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
    files = listTree(path,listdirs=False,sorted=True,includedirs=['gui','plugins','apps','examples','lib','opengl'],includefiles=['.*\.py$'],symlinks=symlinks)
    if extended:
        searchdirs = [ i[1] for i in pf.cfg['appdirs'] + pf.cfg['scriptdirs'] ]
        for path in set(searchdirs):
            if os.path.exists(path):
                files += listTree(path,listdirs=False,sorted=True,includefiles=['.*\.py$'],symlinks=symlinks)
    return files


def grepSource(pattern,options='',relative=True,quiet=False):
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
    files = sourceFiles(relative=relative,extended=extended,symlinks=False)
    cmd = "grep %s '%s' %s" % (options,pattern,' '.join(files))
    sta,out = runCommand(cmd,verbose=not quiet)
    return out


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
    locale.setlocale(locale.LC_ALL,localestring)
    locale.setlocale(locale.LC_NUMERIC, 'C')
    locale.setlocale(locale.LC_COLLATE, 'C')

##########################################################################
## Text conversion  tools ##
############################

def strNorm(s):
    """Normalize a string.

    Text normalization removes all '&' characters and converts it to lower case.
    """
    return str(s).replace('&','').lower()

###################### ReST conversion ###################

#try:
# be quiet, because the import is done early
if checkModule('docutils',quiet=True):
    from docutils.core import publish_string
    def rst2html(text,writer='html'):
        return publish_string(text,writer_name=writer)
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
    """
    i = s.find('\n')
    if i < 0:
        i = len(s)
    return s[:i] + '\n' + char*i + s[i:]


###################### file conversion ###################

def dos2unix(infile,outfile=None):
    if outfile is None:
        cmd = "sed -i 's|\\r||' %s" % infile
    else:
        cmd = "sed -i 's|\\r||' %s > %s" % (infile,outfile)
    return runCommand(cmd)

def unix2dos(infile,outfile=None):
    if outfile is None:
        cmd = "sed -i 's|$|\\r|' %s" % infile
    else:
        cmd = "sed -i 's|$|\\r|' %s > %s" % (infile,outfile)
    return runCommand(cmd)


def gzip(filename,gzipped=None,remove=True,level=5):
    """Compress a file in gzip format.

    Parameters:

    - `filename`: input file name
    - `gzipped`: output file name. If not specified, it will be set to
      the input file name + '.gz'. An existing output file will be
      overwritten.
    - `remove`: if True (default), the input file is removed after
      succesful compression
    - `level`: an integer from 1..9: gzip compression level. Higher values
      result in smaller files, but require longer compression times. The
      default of 5 gives already a fairly good compression ratio.

    Returns the name of the compressed file.
    """
    import gzip
    if gzipped is None:
        gzipped = filename+'.gz'
    fil = open(filename,'rb')
    gz = gzip.open(gzipped,'wb',compresslevel=level)
    gz.write(fil.read())
    fil.close()
    gz.close()
    if remove:
        removeFile(filename)
    return gzipped


def gunzip(filename,unzipped=None,remove=True):
    """Uncompress a file in gzip format.

    Parameters:

    - `filename`: compressed input file name (usually ending in '.gz')
    - `unzipped`: output file name. If not specified and `filename` ends with
      '.gz', it will be set to the `filename` with the '.gz' removed.
      If an empty string is specified or it is not specified and the filename
      does not end in '.gz', the name of a temporary file is generated. Since
      you will normally want to read something from the decompressed file, this
      temporary file is not deleted after closing. It is up to the user to
      delete it (using the returned file name) when he is ready with it.
    - `remove`: if True (default), the input file is removed after
      succesful decompression. You probably want to set this to False when
      decompressing to a temporary file.

    Returns the name of the decompressed file.
    """
    import gzip
    gz = gzip.open(filename,'rb')
    if unzipped is None and filename.endswith('.gz'):
        unzipped = filename[:-3]
    if unzipped:
        fil = open(unzipped,'wb')
    else:
        fil = tempFile(prefix='gunzip-',delete=False)
        unzipped = fil.name
    fil.write(gz.read())
    gz.close()
    fil.close()
    if remove:
        removeFile(filename)
    return unzipped


# These two functions are undocumented for a reason. Believe me! BV
def splitme(s):
    return s[::2],s[1::2]
def mergeme(s1,s2):
    return ''.join([a+b for a,b in zip(s1,s2)])


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
    res = eval(s,glob)
    stop = time.time()
    pf.message("Timed evaluation: %s seconds" % (stop-start))
    return res


def countLines(fn):
    """Return the number of lines in a text file."""
    sta,out = runCommand("wc %s" % fn)
    if sta == 0:
        return int(out.split()[0])
    else:
        return 0


##########################################################################
## Running external commands ##
###############################


# DEPRECATED, KEPT FOR EMERGENCIES
# currently activated by --commands option
@deprecation("system1 is deprecated: use system instead")
def system1(cmd):
    """Execute an external command."""
    import commands
    return commands.getstatusoutput(cmd)


class Process(subprocess.Popen):
    """A subprocess for running an external command.

    This is a subclass of Python's :class`subprocess.Popen` class, providing
    some extra functionality:

    - If a string is passed as command and shell is False, the string is
      automatically tokenized into an args list.

    - stdout and stderr default to subprocess.PIPE instead of None.

    - After the command has terminated, the Process instance has three
      attributes sta, out and err, providing the return code, standard
      output and standard error of the command.

    Parameters:

    - `cmd`: string or args list. If a string, it is the command as it should
      entered in a shell. If an args list, args[0] is the executable to run
      and the remainder are the arguments to be passed.
    - `shell`: bool. Default False. If True, the command will be run in a
      new shell. This may cause problems with killing the command and also
      poses a security risk.
    - `stdout`,`stderr`: Standard output and error output. See Python docs
      for subprocess.Popen. Here, they default to PIPE, allowing the caller
      to grab the output of the command. Set them to an open file object to
      redirect output to that file.
    - Any other parameters accepted by :class`subprocess.Popen` can also be
      specified.

    """

    gracetime = 2

    def __init__(self,cmd,shell=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE,**kargs):

        shell = bool(shell)
        if type(cmd) is str and shell is False:
            # Tokenize the command line
            cmd = shlex.split(cmd)

        try:
            self.failed = False
            subprocess.Popen.__init__(self,cmd,shell=shell,stdout=stdout,stderr=stderr,**kargs)
        except:
            self.failed = True
            # Set a return code to mark the process finished
            self.returncode = 127
            # This is also the bash shell exit code on nonexistent executable

        self.out = self.err = None
        self.timeout = False


    @property
    def sta(self):
        return self.returncode


    def run(self,timeout=None):
        """Run a Process, optionally with timeout.

        Parameters:

        - `timeout`: float. If > 0.0, the subprocess will be terminated
          or killed after this number of seconds have passed.

        On return, the following attributes of the Process are set:

        - `sta`: alias for the Popen.returncode (0 for normal exit, -15
          for terminated, -9 for killed).
        - `out`,`err`: the stdout and stderr as returned by the
          Popen.communicate method.
        - `timedout`: True if a timeout was specified and the process timed
          out, otherwise False.
        """
        self.timedout = False
        if timeout > 0.0:
            # Start a timer to terminate the subprocess
            t = threading.Timer(timeout,Process.timeout,[self])
            t.start()
        else:
            t = None

        # Start the process and wait for it to finish
        self.out,self.err = self.communicate()

        if t:
            # Cancel the timer if one was started
            t.cancel()


    def timeout(self):
        """Terminate or kill a Process, and set the timeout flag

        This method is primarily intended to be called by the timeout
        mechanism. It sets the timedout attribute of the Process to True,
        and then calls its terminate_or_kill method.
        """
        self.timedout = True
        self.terminate_or_kill()


    def terminate_or_kill(self):
        """Terminate or kill a Process

        This is like Popen.terminate, but adds a check to see if the
        process really terminated, and if not kills it.

        Sets the returncode of the process to -15(terminate) or -9(kill).

        This does not do anything if the process was already stopped.
        """
        if self.poll() is None:
            # Process is still running: terminate it
            self.terminate()
            # Wait a bit before checking
            time.sleep(0.1)
            if self.poll() is None:
                # Give the process some more time to terminate
                time.sleep(Process.gracetime)
                if self.poll() is None:
                    # Kill the unwilling process
                    self.kill()


def system(cmd,timeout=None,verbose=False,raise_error=False,**kargs):
    """Execute an external command.

    Parameters:

    - `cmd`: a string with the command to be executed
    - `timeout`: float. If specified and > 0.0, the command will time out
      and be terminated or killed after the specified number of seconds.
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

    Returns the Process used to run the command. This gives access to all
    its info, like the exit code, stdout and stderr, and whether the command
    timed out or not. See :class:`Process` for more info.
    """
    pf.debug("Command: %s" % cmd,pf.DEBUG.INFO)
    if verbose:
        print("Running command: %s" % cmd)
    P = Process(cmd,**kargs)
    P.run(timeout)
    if verbose:
        if P.timedout:
            print("Command terminated due to timeout (%ss)" % timeout)

        elif P.failed:
            print("The subprocess failed to start, probably because the executable does not exist or is not in your current PATH.")
            if raise_error:
                raise RuntimeError, "Error while executing command:\n  %s" % cmd

        elif P.sta != 0:
            print(P.out)
            print("Command exited with an error (exitcode %s)" % P.sta)
            print(P.err)
            if raise_error:
                raise RuntimeError, "Error while executing command:\n  %s" % cmd
    return P


def command(cmd,timeout=None,verbose=True,raise_error=True,**kargs):
    """Run an external command in a user friendly way.

    This is equivalent with the utils.system function but with
    verbose=True and raise_error=True by default.
    """
    return system(cmd,timeout,verbose,raise_error,**kargs)


def runCommand(cmd,timeout=None,shell=True,**kargs):
    """Run an external command in a user friendly way.

    This is like with the utils.command, but with shell=True by default,
    and the return value is a tuple (P.sta,P.out) instead of the Process P.
    """
    P = command(cmd,timeout,shell=shell,**kargs)
    return P.sta,P.out.rstrip('\n')


def killProcesses(pids,signal=15):
    """Send the specified signal to the processes in list

    - `pids`: a list of process ids.
    - `signal`: the signal to send to the processes. The default (15) will
      try to terminate the process. See 'man kill' for more values.
    """
    for pid in pids:
        try:
            os.kill(pid,signal)
        except:
            pf.debug("Error in killing of process '%s'" % pid,pf.DEBUG.INFO)


def userName():
    """Find the name of the user."""
    try:
        return os.environ['LOGNAME']
    except:
        return 'NOBODY'


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
    fil = open(scriptfile,'r')
    s = fil.read()
    i = s.find('"""')
    if i >= 0:
        j = s.find('"""',i+1)
        if j >= i+3:
            return s[i+3:j]
    return ''


tempFile = tempfile.NamedTemporaryFile
tempDir = tempfile.mkdtemp


def numsplit(s):
    """Split a string in numerical and non-numerical parts.

    Returns a series of substrings of s. The odd items do not contain
    any digits. Joined together, the substrings restore the original.
    The even items only contain digits.
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
    return digits.split(s)


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
        s = digits.split(s)+['0']
        return zip(s[0::2], map(int, s[1::2]))
    return sorted(l,key=human)


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
        return ''.join(g[:i]),g[i],''.join(g[i+1:])
    else:
        return s,'',''


# BV: We could turn this into a factory
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
    >>> [ N.next() for i in range(3) ]
    ['abc.98', 'abc.99', 'abc.100']
    >>> N = NameSequence('abc-8x.png')
    >>> [ N.next() for i in range(3) ]
    ['abc-8x.png', 'abc-9x.png', 'abc-10x.png']
    >>> NameSequence('abc','.png').next()
    'abc-000.png'
    >>> N = NameSequence('/home/user/abc23','5.png')
    >>> [ N.next() for i in range(2) ]
    ['/home/user/abc235.png', '/home/user/abc245.png']
    """

    def __init__(self,name,ext=''):
        """Create a new NameSequence from name,ext."""
        prefix,number,suffix = splitDigits(name)
        if len(number) > 0:
            self.nr = int(number)
            format = "%%0%dd" % len(number)
        else:
            self.nr = 0
            format = "-%03d"
        self.name = prefix+format+suffix+ext

    def next(self):
        """Return the next name in the sequence"""
        fn = self.name % self.nr
        self.nr += 1
        return fn

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
        j = self.name.find('d',i)
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
    return dict([ (prefix+k,v) for k,v in d.items() ])


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
        return dict([ (k.replace(prefix,'',1),v) for k,v in d.items() if k.startswith(prefix)])
    else:
        return dict([ (k,v) for k,v in d.items() if k.startswith(prefix)])


def selectDict(d,keys):
    """Return a dict with the items whose key is in keys.

    - `d`: a dict where all the keys are strings.
    - `keys`: a set of key values, can be a list or another dict.

    The return value is a dict with all the items from d whose key
    is in keys.
    See :func:`removeDict` for the complementary operation.

    Example:

    >>> d = dict([(c,c*c) for c in range(6)])
    >>> selectDict(d,[4,0,1])
    {0: 0, 1: 1, 4: 16}
    """
    return dict([ (k,d[k]) for k in set(d)&set(keys) ])


def removeDict(d,keys):
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
    return dict([ (k,d[k]) for k in set(d)-set(keys) ])


def refreshDict(d,src):
    """Refresh a dict with values from another dict.

    The values in the dict d are update with those in src.
    Unlike the dict.update method, this will only update existing keys
    but not add new keys.
    """
    d.update(selectDict(src,d))


def inverseDict(d):
    return dict([(v,k) for k,v in d.items()])


def selectDictValues(d,values):
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
""" % (', '.join(self.added()),', '.join(self.removed()),', '.join(self.changed()),', '.join(self.unchanged()))



def sortedKeys(d):
    """Returns the sorted keys of a dict.

    It is required that the keys of the dict be sortable, e.g. all strings
    or integers.
    """
    k = d.keys()
    k.sort()
    return k


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
    xmin,x0,xmax = xval
    ymin,y0,ymax = yval
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


def listFontFiles():
    """List all fonts known to the system.

    Returns a list of path names to all the font files found on the system.
    """
    cmd = "fc-list : file | sed 's|.*file=||;s|:||'"
    sta,out = runCommand(cmd)
    if sta:
        warning("fc-list could not find your font files.\nMaybe you do not have fontconfig installed?")
    else:
        return [ f.strip() for f in out.split('\n') ]


###########################################################################


def procInfo(title):
    print(title)
    print('module name: %s' %  __name__)
    print('parent process: %s' % os.getppid())
    print('process id: %s' % os.getpid())


def interrogate(item):
    """Print useful information about item."""
    import odict
    info = odict.ODict()
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
    for line in P.out.split('\n'):
        try:
            k,v = line.split(':')
            k = k.strip()
            v = v.replace('kB','').strip()
            res[k] = int(v)
        except:
            break
    res['MemUsed'] = res['MemTotal'] - res['MemFree'] - res['Buffers'] - res['Cached']
    if keys:
        res = selectDict(res,keys)
    return res


def memory_diff(mem0,mem1,tag=None):
    m0 = mem0['MemUsed']/1024.
    m1 = mem1['MemUsed']/1024.
    m2 = m1 - m0
    m3 = mem1['MemFree']/1024.
    print("%10.1f MB before; %10.1f MB after; %10.1f MB used; %10.1f MB free; %s" % (m0,m1,m2,m3,tag))


_mem_state = None
def memory_track(tag=None,since=None):
    global _mem_state
    if since is None:
        since = _mem_state
    new_mem_state = memory_report()
    if tag and _mem_state is not None:
        memory_diff(since,new_mem_state,tag)
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
    from collections import deque
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
                s += sum(map(sizeof, handler(o)))
                break
        return s

    return sizeof(o)


### End
