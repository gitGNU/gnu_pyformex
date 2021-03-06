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
#
"""Setup script for pyFormex

To install pyFormex: python setup.py install --prefix=/usr/local
To uninstall pyFormex: pyformex --remove
"""
from __future__ import print_function

#from distutils.command.install import install as _install
#from distutils.command.install_data import install_data as _install_data
#from distutils.command.install_scripts import install_scripts as _install_scripts
#from distutils.command.build_ext import build_ext as _build_ext
from distutils.command.build_py import build_py as _build_py
from distutils.command.sdist import sdist as _sdist
from distutils.core import setup, Extension
from distutils import filelist
from distutils.util import get_platform

import os,sys
from glob import glob

# Detect platform
pypy = hasattr(sys, 'pypy_version_info')
jython = sys.platform.startswith('java')
py3k = False
if sys.version_info < (2, 7):
    raise Exception("pyFormex requires Python 2.7 or higher.")
elif sys.version_info >= (3, 0):
    py3k = True


# define the things to include
import manifest

# pyFormex release
__RELEASE__ = '1.0.4-a3'

# The acceleration libraries
LIB_MODULES = [ 'misc_', 'nurbs_' ]

ext_modules = [Extension('pyformex/lib/%s'%m,
                         sources = ['pyformex/lib/%s.c'%m],
                         # optional=True,
                         ) for m in LIB_MODULES ]


class BuildFailed(Exception):

    def __init__(self):
        self.cause = sys.exc_info()[1] # work around py 2/3 different syntax

def status_msgs(*msgs):
    """Print status messages"""
    print('*' * 75)
    for msg in msgs:
        print(msg)
    print('*' * 75)


class build_py(_build_py):
    description = "Custom build_py preserving file mode in bin subdirectory. Also provides the install_type user option."

    ## user_options = [ ('install-type=', None, "Set the installation type. Default R. Should be set to D when creating distribution specific packages.") ]

    ## def initialize_options(self):
    ##     _build_py.initialize_options(self)
    ##     self.install_type = 'R'

    def build_package_data (self):
        """Copy data files into build directory

        The default Python distutils do not preserve the file mode
        when copying the Python package.
        This version will preserve the file mode for files in the
        packages `bin` subdirectory. Thus executable scripts there
        will remain executable.
        """
        lastdir = None
        for package, src_dir, build_dir, filenames in self.data_files:
            #print(package, src_dir, build_dir, filenames)
            for filename in filenames:
                target = os.path.join(build_dir, filename)
                self.mkpath(os.path.dirname(target))
                self.copy_file(
                    os.path.join(src_dir, filename), target,
                    preserve_mode = (
                        filename.startswith('bin/') # or
#                        filename.startswith('extra/')
                        )
                    )
        print("Package data built!")
        #print(self.build_temp)


    # Override to remove the non-maching compat module
    def find_package_modules(self, package, package_dir):
        self.check_package(package, package_dir)
        module_files = glob(os.path.join(package_dir, "*.py"))
        modules = []
        setup_script = os.path.abspath(self.distribution.script_name)

        # Remove the nonmatchin compat module
        if (sys.hexversion) < 0x03000000:
            remove = 'compat_3k.py'
        else:
            remove = 'compat_2k.py'
        module_files = [m for m in module_files if not m.endswith(remove)]
        # End removal

        for f in module_files:
            abs_f = os.path.abspath(f)
            if abs_f != setup_script:
                module = os.path.splitext(os.path.basename(f))[0]
                modules.append((package, module, f))
            else:
                self.debug_print("excluding %s" % setup_script)
        return modules



class sdist(_sdist):

    def get_file_list(self):
        """Create list of files to include in the source distribution

        Create the list of files to include in the source distribution,
        and put it in 'self.filelist'.  This might involve
        reading the manifest template (and writing the manifest), or just
        reading the manifest, or just using the default file set -- it all
        depends on the user's options.
        """
        self.filelist = filelist.FileList()
        self.filelist.files = manifest.DIST_FILES
        self.filelist.sort()
        self.filelist.remove_duplicates()
        self.write_manifest()



def run_setup(with_cext):
    kargs = {}
    if with_cext:
            kargs['ext_modules'] = ext_modules

    # PKG_DATA, relative from pyformex path

    INCLUDE = []

    import numpy
    INCLUDE.append(numpy.get_include()),

    with open('Description') as file:
        long_description = file.read()

    PKG_DATA = [
        'pyformexrc',
        'icons/README',
        'icons/*.xpm',
        'icons/pyformex*.png',
        'icons/64x64/*',
        'examples/apps.cat',
        'bin/*',
        'data/*',
        'glsl/*',
        'extra/Makefile',
        'extra/*/*',
        ]

    PKG_DATA += [ i[9:] for i in manifest.DOC_FILES ]
    setup(cmdclass={
        'build_py': build_py,
        'sdist':sdist
        },
          name='pyformex',
          version=__RELEASE__,
          description='program to create 3D geometry from Python scripts',
          long_description=long_description,
          author='Benedict Verhegghe',
          author_email='benedict.verhegghe@feops.com',
          url='http://pyformex.org',
          download_url='http://download.savannah.gnu.org/releases/pyformex/pyformex-%s.tar.gz' % __RELEASE__,
          license='GNU General Public License (GPL)',
          packages=[
              'pyformex',
              'pyformex.gui',
              'pyformex.lib',
              'pyformex.opengl',
              'pyformex.plugins',
              'pyformex.examples',
              'pyformex.fe',
              'pyformex.freetype',
              'pyformex.freetype.ft_enums',
              ],
          package_data={ 'pyformex': PKG_DATA },
          scripts=['pyformex/pyformex'],
          data_files=manifest.OTHER_DATA,
          classifiers=[
              'Development Status :: 4 - Beta',
              'Environment :: Console',
              'Environment :: X11 Applications :: Qt',
              'Intended Audience :: End Users/Desktop',
              'Intended Audience :: Science/Research',
              'Intended Audience :: Education',
              'License :: OSI Approved :: GNU General Public License (GPL)',
              'Operating System :: POSIX :: Linux',
              'Operating System :: POSIX',
              'Operating System :: OS Independent',
              'Programming Language :: Python',
              'Programming Language :: C',
              'Topic :: Multimedia :: Graphics :: 3D Modeling',
              'Topic :: Multimedia :: Graphics :: 3D Rendering',
              'Topic :: Scientific/Engineering :: Mathematics',
              'Topic :: Scientific/Engineering :: Visualization',
              'Topic :: Scientific/Engineering :: Physics',
              ],
#          requires=['numpy','OpenGL','PyQt4 | PySide'],
          include_dirs=INCLUDE,
          **kargs
          )


# Detect the --no-accel option
try:
    i = sys.argv.index('--no-accel')
    del(sys.argv[i])
    accel = False
except ValueError:
    accel = True



if pypy or jython:
    accel = False
    status_msgs(
        "WARNING: C extensions are not supported on this Python platform,"
        "I will continue without the acceleration libraries."
    )

# Try with compilation
if accel:
    try:
        run_setup(accel)
        sys.exit()
    except BuildFailed:
        exc = sys.exc_info()[1] # work around py 2/3 different syntax
        status_msgs(
            exc.cause,
            "WARNING: The acceleration library could not be compiled, "
            "I will retry without them.")

# Run without compilation
run_setup(False)

status_msgs("WARNING: Building without the acceleration library")

if py3k:
    status_msgs("WARNING: This is an experimental Python3 version of pyFormex.\npyFormex is currently not yet fully functional with Python3.\nThis build is for development purposes only. DO NOT USE!")

# End
