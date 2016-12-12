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

"""Handling pyFormex Geometry Files

This module defines a class to work with files in the native
pyFormex Geometry File Format.
"""
from __future__ import absolute_import, division, print_function

import pyformex as pf
from pyformex import utils
from pyformex import filewrite
from pyformex.odict import OrderedDict
from pyformex import arraytools as at
from pyformex.formex import Formex
from pyformex.mesh import Mesh
# We need to import the Mesh subclasses that can be read !
from pyformex.trisurface import TriSurface

from distutils.version import StrictVersion as Version
import numpy as np
import os

class GeometryFile(object):
    """A class to handle files in the pyFormex Geometry File format.

    The pyFormex Geometry File (PGF) format allows the persistent storage
    of most of the geometrical objects available in pyFormex using a format
    that is independent of the pyFormex version. It guarantees a possible read
    back in future versions. The format is simple and public, and hence
    also allows read back from other software.

    See http://pyformex.org/doc/file_format for a full description
    of the file format(s). Older file formats are supported for reading.

    Other than just geometry, the pyFormex Geometry File format can also
    store some attributes of the objects, like names and colors.
    Future versions will also allow to store field variables.

    The GeometryFile class uses the utils.File class to access the files,
    and thus provides for transparent compression and decompression of the
    files. When making use of the compression, the PGF files will remain small
    even for complex models.

    A PGF file starts with a specific header identifying the format and
    version. When opening a file for reading, the PGF header is read
    automatically, and the file is thus positioned ready for reading
    the objects. When opening a file for writing (not appending!), the
    header is automatically written, and the file is ready for writing objects.

    In append mode however, nothing is currently done with the header.
    This means that it is possible to append to a file using a format
    different from that used to create the file initially. This is not a
    good practice, as it may hinder the proper read back of the data.
    Therefore, append mode should only be used when you are sure that
    your current pyFormex uses the same format as the already stored file.
    As a reminder, warning is written when opening the file in append mode.

    The `filename`, `mode`, `compr`, `level` and `delete_temp` arguments are
    passed to the utils.File class. See :class:`utils.File` for more
    details.

    Parameters:

    - `filename`: string: the name of the file to open.
      If the file name ends with '.gz' or '.bz2', transparent (de)compression
      will be used, as provided by the :class:`utils.File` class.
    - `mode`: one of 'r', 'w' or 'a': specifies that the file should be
      opened in read, write or append mode. If omitted, an
      existing file will be opened in read mode and a non-existing in write
      mode. Opening an existing file in 'w' mode will overwrite the file,
      while opening it in 'a' mode will allow to append to the file.
    - `compr`: string, one of 'gz' or 'bz2': identifies the compression
      algorithm to be used: gzip or bzip2. If the file name is ending with
      '.gz' or '.bz2', `compr` is set automatically from the extension.
    - `level`: an integer from 1..9: gzip/bzip2 compression level.
      Higher values result in smaller files, but require longer compression
      times. The default of 5 gives already a fairly good compression ratio.
    - `delete_temp`: bool: if True (default), the temporary files needed to
      do the (de)compression are deleted when the GeometryFile is closed.
    - `sep`: string: separator string to be used when writing numpy arrays
      to the file. An empty string will make the arrays being written in
      binary format. Any other string will force text mode, and the `sep`
      string is used as a separator between subsequent array elements.
      See also :func:`numpy.tofile`.
    - `ifmt` and `ffmt` are present for historical and development reasons,
      but currently inactive.
    - `version`: if specified, write according to old version standard.
      Available: '1.9', '2.0'(default)
    """

    _version_ = '2.0'

    def __init__(self,filename,mode=None,compr=None,level=5,delete_temp=True,
                 sep=' ',ifmt=' ',ffmt=' ',version=None):
        """Create the GeometryFile object."""
        if version is None:
            version = GeometryFile._version_
        if not version in [ '1.9', '2.0' ]:
            raise ValueError("Can not write GeometryFile of version %s" % version)
        self.version = version

        if mode is None:
            if os.path.exists(filename):
                mode = 'r'
            else:
                mode = 'w'

        self.file = utils.File(filename,mode,compr,level,delete_temp)
        self._autoname = None

        if self.writing:
            self.sep = sep
            self.fmt = {'i':ifmt,'f':ffmt}

        self.open()


    @property
    def writing(self):
        return self.file.mode[0:1] in 'wa'


    @property
    def autoname(self):
        if self._autoname is None:
            self._autoname = utils.NameSequence(utils.projectName(self.file.name)+'-0')
        return self._autoname


    def open(self):
        self.fil = self.file.open()
        if self.writing:
            self.writeHeader()
        else:
            self.readHeader()


    def reopen(self,mode='r'):
        """Reopen the file, possibly changing the mode.

        The default mode for the reopen is 'r'
        """
        self.fil = self.file.reopen(mode)
        if self.writing:
            self.writeHeader()
        else:
            self.readHeader()


    def close(self):
        """Close the file.

        """
        self.file.close()


    def checkWritable(self):
        if not self.writing:
            raise RuntimeError("File is not opened for writing")
        if not self.header_done:
            self.writeHeader()


    def writeHeader(self):
        """Write the header of a pyFormex geometry file.

        The header identifies the file as a pyFormex geometry file
        and sets the following global values:

        - `version`: the version of the geometry file format
        - `sep`: the default separator to be used when not specified in
          the data block
        """
        self.fil.write("# pyFormex Geometry File (http://pyformex.org) version='%s'; sep='%s'\n" % (self.version, self.sep))
        self.header_done = True


    def writeData(self,data,sep,fmt=None):
        """Write an array of data to a pyFormex geometry file.

        If fmt is None, the data are written using numpy.tofile, with
        the specified separator. If sep is an empty string, the data block
        is written in binary mode, leading to smaller files.
        If fmt is specified, each
        """
        if not self.writing:
            raise RuntimeError("File is not opened for writing")
        #kind = data.dtype.kind
        #if fmt is None:
        #    fmt = self.fmt[kind]
        filewrite.writeData(self.fil, data, sep, end='\n')


    def write(self,geom,name=None,sep=None):
        """Write a collection of Geometry objects to the Geometry File.

        Parameters:

        - `geom`: an object of one the supported Geometry data types
          or a list or dict of such objects, or a WebGL objdict.
          Currently exported geometry objects are
          :class:`Coords`, :class:`Formex`, :class:`Mesh`,
          :class:`PolyLine`, :class:`BezierSpline`.

        Returns the number of objects written.
        """
        self.checkWritable()
        nobj = 0
        if isinstance(geom, dict):
            for name in geom:
                nobj += self.writeGeometry(geom[name], name)
        elif isinstance(geom, list):
            for obj in geom:
                ## if hasattr(obj, 'obj'):
                ##     # This must be a WebGL object dict
                ##     nobj += self.writeDict(obj)
                ## else:
                nobj += self.writeGeometry(obj,sep=sep)
        else:
            nobj += self.writeGeometry(geom,name,sep)

        return nobj


    def writeGeometry(self,geom,name=None,sep=None):
        """Write a single Geometry object to the Geometry File.

        Writes a single Geometry object to the Geometry File, using the
        specified name and separator.

        Parameters:

        - `geom`: a supported Geometry type object.
          Currently supported Geometry objects are
          :class:`Coords`,
          :class:`Formex`,
          :class:`Mesh`,
          :class:`PolyLine`,
          :class:`BezierSpline`.
          Other types are skipped, and a message is written, but processing
          continues.
        - `name`: string: the name of the object to be stored in the file.
          If not specified, and the object has an `attrib` dict containing
          a name, that value is used. Else an object name is generated
          from the file name.
          On readback, the object names are used as keys to store the objects
          in a dict.
        - `sep`: string: defines the separator to be used for writing this
          object. If not specified, the value given in the constructor will
          be used. This argument allows to override it on a per object base.

        Returns 1 if the object has been written, 0 otherwise.
        """
        self.checkWritable()

        try:
            writefunc = getattr(self, 'write'+geom.__class__.__name__)
        except:
            pf.warning("Can not (yet) write objects of type %s to geometry file: skipping" % type(geom))
            return 1

        if name is None:
            name = geom.attrib.name
        if name is None:
            name = next(self.autoname)

        try:
            writefunc(geom, name, sep)
        except:
            pf.warning("Error while writing objects of type %s to geometry file: skipping" % type(geom))
            raise

        if geom.attrib and Version(self.version) >= Version('2.0'):
            try:
                if geom.attrib:
                    self.fil.write("# attrib = %s\n" % geom.attrib)
            except:
                pf.warning("Error while writing objects of type %s to geometry file: skipping" % type(geom))
                raise


        return 0


    def writeMesh(self,F,name=None,sep=None,objtype='Mesh'):
        """Write a Mesh to a pyFormex geometry file.

        This writes a header line with these attributes and arguments:
        objtype, ncoords, nelems, nplex, props(True/False),
        eltype, normals(True/False), color, sep, name.
        This is followed by the array data for: coords, elems, prop,
        normals, color

        The objtype can/should be overridden for subclasses.
        """
        if objtype is None:
            objtype = 'Mesh'
        if sep is None:
            sep = self.sep
        hasprop = F.prop is not None
        hasnorm = hasattr(F, 'normals') and isinstance(F.normals, np.ndarray) and F.normals.shape == (F.nelems(), F.nplex(), 3)
        color = None
        colormap = None
        Fc = F.attrib['color']
        if Fc is not None:
            if isinstance(Fc,(str,unicode)):
                color = Fc
            else:
                try:
                    Fc = at.checkArray(Fc,kind='f')
                    colormap = None
                    colorshape = Fc.shape
                except:
                    Fc = at.checkArray(Fc,kind='i')
                    colormap = 'default'
                    colorshape = Fc.shape + (3,)
                if colorshape == (3,):
                    color = tuple(Fc)
                elif colorshape == (F.nelems(), 3):
                    color = 'element'
                elif colorshape == (F.nelems(), F.nplex(), 3):
                    color = 'vertex'
                else:
                    raise ValueError("Incorrect color shape: %s" % str(colorshape))

        head = "# objtype='%s'; ncoords=%s; nelems=%s; nplex=%s; props=%s; normals=%s; color=%r; sep='%s'" % (objtype, F.npoints(), F.nelems(), F.nplex(), hasprop, hasnorm, color, sep)
        if name:
            head += "; name='%s'" % name
        if F.elName():
            head += "; eltype='%s'" % F.elName()
        if colormap:
            head += "; colormap='%s'" % colormap

        self.fil.write(head+'\n')

        # Apply a fix to avoid a fewgl bug
        #
        # pyFormex webgl exporter exports in pgf format.
        # Unfortunately, due to a bug in fewgl pgf reader, geometries
        # having a first value in the coords block that starts with a
        # bit pattern corresponding with a '#' byte, (dec 35), can not
        # be read back. The solution is to force the first bit (the least
        # significant bit of the mantisse) to zero. This will make sure
        # the bit pattern does not match dec 35 ('#'), and have a
        # neglectable influence on the value. (Still the solution below
        # resets the original value).
        if pf.cfg['webgl/avoid_fewgl_read_pgf_bug']:
            save_first = F.coords[0,0]
            F.coords.view(np.int32)[0, 0] &= -2  # Force least significant bit of the first byte to zero
        self.writeData(F.coords, sep)
        if pf.cfg['webgl/avoid_fewgl_read_pgf_bug']:
            F.coords[0,0] = save_first

        if not objtype == 'Formex':
            self.writeData(F.elems, sep)
        if hasprop:
            self.writeData(F.prop, sep)
        if hasnorm:
            self.writeData(F.normals, sep)
        if color == 'element' or color == 'vertex':
            self.writeData(Fc, sep)
        for field in F.fields:
            fld = F.fields[field]
            head = "# field='%s'; fldtype='%s'; shape=%r; sep='%s'" % (fld.fldname, fld.fldtype,fld.data.shape, sep)
            self.fil.write(head+'\n')
            self.writeData(fld.data, sep)


    def writeFormex(self,F,name=None,sep=None):
        """Write a Formex to the geometry file.

        This is equivalent to writeMesh(F,name,sep,objtype='Formex')
        """
        self.writeMesh(F, name=name, sep=sep, objtype='Formex')


    def writeTriSurface(self,F,name=None,sep=None):
        """Write a TriSurface to a pyFormex geometry file.

        This is equivalent to writeMesh(F,name,sep,objtype='TriSurface')
        """
        self.writeMesh(F, name=name, sep=sep, objtype='TriSurface')


    def writeCurve(self,F,name=None,sep=None,objtype=None,extra=None):
        """Write a Curve to a pyFormex geometry file.

        This function writes any curve type to the geometry file.
        The `objtype` is automatically detected but can be overridden.

        The following attributes and arguments are written in the header:
        ncoords, closed, name, sep.
        The following attributes are written as arrays: coords
        """
        if sep is None:
            sep = self.sep
        head = "# objtype='%s'; ncoords=%s; closed=%s; sep='%s'" % (F.__class__.__name__, F.coords.shape[0], F.closed, sep)
        if name:
            head += "; name='%s'" % name
        if extra:
            head += extra
        self.fil.write(head+'\n')
        self.writeData(F.coords, sep)


    def writePolyLine(self,F,name=None,sep=None):
        """Write a PolyLine to a pyFormex geometry file.

        This is equivalent to writeCurve(F,name,sep,objtype='PolyLine')
        """
        self.writeCurve(F, name=name, sep=sep, objtype='PolyLine')


    def writeBezierSpline(self,F,name=None,sep=None):
        """Write a BezierSpline to a pyFormex geometry file.

        This is equivalent to writeCurve(F,name,sep,objtype='BezierSpline')
        """
        self.writeCurve(F, name=name, sep=sep, objtype='BezierSpline', extra="; degree=%s" % F.degree)


    def writeNurbsCurve(self,F,name=None,sep=None,extra=None):
        """Write a NurbsCurve to a pyFormex geometry file.

        This function writes a NurbsCurve instance to the geometry file.

        The following attributes and arguments are written in the header:
        ncoords, nknots, closed, name, sep.
        The following attributes are written as arrays: coords, knots
        """
        if sep is None:
            sep = self.sep
        head = "# objtype='%s'; ncoords=%s; nknots=%s; closed=%s; sep='%s'" % (F.__class__.__name__, F.coords.shape[0], F.knots.shape[0], F.closed, sep)
        if name:
            head += "; name='%s'" % name
        if extra:
            head += extra
        self.fil.write(head+'\n')
        self.writeData(F.coords, sep)
        self.writeData(F.knots, sep)


    def writeNurbsSurface(self,F,name=None,sep=None,extra=None):
        """Write a NurbsSurface to a pyFormex geometry file.

        This function writes a NurbsSurface instance to the geometry file.

        The following attributes and arguments are written in the header:
        ncoords, nknotsu, nknotsv, closedu, closedv, name, sep.
        The following attributes are written as arrays: coords, knotsu, knotsv
        """
        if sep is None:
            sep = self.sep
        head = "# objtype='%s'; ncoords=%s; nuknots=%s; nvknots=%s; uclosed=%s; vclosed=%s; sep='%s'" % (F.__class__.__name__, F.coords.shape[0], F.uknots.shape[0], F.uknots.shape[0], F.closed[0], F.closed[1], sep)
        if name:
            head += "; name='%s'" % name
        if extra:
            head += extra
        self.fil.write(head+'\n')
        self.writeData(F.coords, sep)
        self.writeData(F.uknots, sep)
        self.writeData(F.vknots, sep)


###########################################################################
        ### READING ###


    def read(self,count=-1,warn_version=True):
        """Read objects from a pyFormex Geometry File.

        This function reads objects from a Geometry File until the file
        ends, or until `count` objects have been read.
        The File should have been opened for reading.

        A count may be specified to limit the number of objects read.

        Returns a dict with the objects read. The keys of the dict are the
        object names found in the file. If the file does not contain
        object names, they will be autogenerated from the file name.

        Note that PGF files of version 1.0 are no longer supported.
        The use of formats 1.1 to 1.5 is deprecated, and users are
        urged to upgrade these files to a newer format. Support for
        these formats may be removed in future.
        """
        if self.writing:
            print("File is opened for writing, not reading.")
            return {}

        self.results = OrderedDict()
        self.geometry = None # used to make sure fields follow geom block

        if Version(self.version) < Version('1.6'):
            if warn_version:
                pf.warning("This is an old PGF format (%s). We recommend you to convert it to a newer format. The geometry import menu contains an item to upgrade a PGF file to the latest format (%s)." % (self.version,GeometryFile._version_))
            return self.readLegacy(count)


        while True:
            s = self.fil.readline()

            if len(s) == 0:   # end of file
                break

            if s.startswith('#'):

                # Remove the leading '#' and space
                s = s[1:].strip()

                if s.startswith('objtype'):
                    if count > 0 and len(self.results) >= count:
                        break
                    self.readGeometry(**self.decode(s))

                elif s.startswith('field'):
                    self.readField(**self.decode(s))

                elif s.startswith('attrib'):
                    try: # GDS 291116
                        self.readAttrib(**self.decode(s))
                    except:# GDS 291116
                        pf.warning('FIXED by GIANLUCA, to read COLORs from PGF')
                        pass# GDS 291116

                elif s.startswith('pyFormex Geometry File'):
                    # we have a new header line
                    self.readHeader(s)

            # Unrecognized lines are silently ignored, whether starting
            # with a '#' or not.
            # We recommend to start all comments lines with a '#' though.

        self.file.close()

        return self.results


    def decode(self,s):
        """Decode the announcement line.

        Returns a dict with the interpreted values of the line.
        """
        kargs = {}
        try:
            exec(s,kargs)
        except:
            raise RuntimeError("This does not look like a regular pyFormex geometry file. I got stuck on the following line:\n==> %s" % s)
        return kargs


    def readHeader(self,s=None):
        """Read the header of a pyFormex geometry file.

        Without argument, reads a line from the file and interpretes it as
        a header line. This is normally used to read the first line of the
        file. A string `s` may be specified to interprete further lines as
        a header line.
        """
        if s is None:
            s = self.fil.readline()

        pos = s.rfind(')')
        s = s[pos+1:].strip()
        kargs = self.decode(s)
        self.version = kargs['version']
        self.sep = kargs['sep']
        self.header_done = True


    def doHeader(self,version='1.1',sep='',**kargs):
        """Read the header of a pyFormex geometry file.

        Sets detected default values
        """

        self.version = version
        self.sep = sep
        self.header_done = True


    def readGeometry(self,objtype='Formex',name=None,nelems=None,ncoords=None,nplex=None,props=None,eltype=None,normals=None,color=None,colormap=None,closed=None,degree=None,nknots=None,sep=None,**kargs):
        """Read a geometry record of a pyFormex geometry file.

        If an object was succesfully read, it is set in self.geometry
        """
        pf.debug("Reading object of type %s" % objtype, pf.DEBUG.INFO)
        self.geometry = None

        if objtype == 'Formex':
            obj = self.readFormex(nelems, nplex, props, eltype, sep)
        elif objtype in ['Mesh', 'TriSurface']:
            obj = self.readMesh(ncoords, nelems, nplex, props, eltype, normals, sep, objtype)
        elif objtype == 'PolyLine':
            obj = self.readPolyLine(ncoords, closed, sep)
        elif objtype == 'BezierSpline':
            obj = self.readBezierSpline(ncoords, closed, degree, sep)
        elif objtype == 'NurbsCurve':
            obj = self.readNurbsCurve(ncoords, nknots, closed, sep)
        elif objtype in globals() and hasattr(globals()[objtype], 'read_geom'):
            obj = globals()[objtype].read_geom(self,**kargs)
        else:
            print("Can not (yet) read objects of type %s from geometry file: skipping" % objtype)

        if obj is not None:
            if color is not None:
                if isinstance(color,str):
                    # Check for special values:
                    if color == 'element':
                        colorshape = (nelems,)
                    elif color == 'vertex':
                        colorshape = (nelems,nplex,)
                    elif color == '':
                        # Fix for pre 1.9 versions using color='' for no color
                        color = colorshape = None
                    else:
                        # string should be a color name
                        colorshape = None

                    if colorshape:
                        if colormap == 'default':
                            colortype = at.Int
                        else:
                            colortype = at.Float
                            colorshape += ( 3,)

                        try:
                            # Read the color array
                            color = at.readArray(self.fil, colortype, colorshape, sep=sep)
                        except Exception as e:
                            print("Invalid color array on PGF file: skipped. Traceback: %s" % e)
                            color = None

                else:
                    # A single color encoded in the attribute
                    if colormap == 'default':
                        colortype = 'i'
                    else:
                        colortype = 'f'
                    colorshape = (3,)
                    try:
                        color = at.checkArray(color, colorshape, colortype)
                    except Exception as e:
                        print("Invalid color attribute on PGF file: skipped. Traceback: %s" % e)
                        color = None

            obj.attrib.color = color

            # store the geometry object, and remember as last
            if name is None:
                name = next(self.autoname)
            self.results[name] = self.geometry = obj


    def readField(self,field=None,fldtype=None,shape=None,sep=None,**kargs):
        """Read a Field defined on the last read geometry.

        """
        data = at.readArray(self.fil, at.Float, shape, sep=sep)
        self.geometry.addField(fldtype,data,field)


    def readAttrib(self,attrib=None,**kargs):
        """Read an Attributes dict defined on the last read geometry.

        """
#        s = ''
#        for line in self.fil:
#            if line.startswith('# end_attrib'):
#                break
#            s += line
#        #print(s)
#        attr = json.loads(s)
#        #print(type(attr))
        self.geometry.attrib(**attrib)


    def readFormex(self, nelems, nplex, props, eltype, sep):
        """Read a Formex from a pyFormex geometry file.

        The coordinate array for nelems*nplex points is read from the file.
        If present, the property numbers for nelems elements are read.
        From the coords and props a Formex is created and returned.
        """
        ndim = 3
        f = at.readArray(self.fil, at.Float, (nelems, nplex, ndim), sep=sep)
        if props:
            p = at.readArray(self.fil, at.Int, (nelems,), sep=sep)
        else:
            p = None
        return Formex(f, p, eltype)


    def readMesh(self,ncoords,nelems,nplex,props,eltype,normals,sep,objtype='Mesh'):
        """Read a Mesh from a pyFormex geometry file.

        The following arrays are read from the file:
        - a coordinate array with `ncoords` points,
        - a connectivity array with `nelems` elements of plexitude `nplex`,
        - if present, a property number array for `nelems` elements.

        Returns the Mesh constructed from these data, or a subclass if
        an objtype is specified.
        """

        ndim = 3
        x = at.readArray(self.fil, at.Float, (ncoords, ndim), sep=sep)
        e = at.readArray(self.fil, at.Int, (nelems, nplex), sep=sep)
        if props:
            p = at.readArray(self.fil, at.Int, (nelems,), sep=sep)
        else:
            p = None
        M = Mesh(x, e, p, eltype)
        if objtype != 'Mesh':
            try:
                clas = locals()[objtype]
            except:
                clas = globals()[objtype]
            M = clas(M)
        if normals:
            n = at.readArray(self.fil, at.Float, (nelems, nplex, ndim), sep=sep)
            M.normals = n
        return M


    def readPolyLine(self, ncoords, closed, sep):
        """Read a Curve from a pyFormex geometry file.

        The coordinate array for ncoords points is read from the file
        and a Curve of type `objtype` is returned.
        """
        from pyformex.plugins.curve import PolyLine
        ndim = 3
        coords = at.readArray(self.fil, at.Float, (ncoords, ndim), sep=sep)
        return PolyLine(control=coords, closed=closed)


    def readBezierSpline(self, ncoords, closed, degree, sep):
        """Read a BezierSpline from a pyFormex geometry file.

        The coordinate array for ncoords points is read from the file
        and a BezierSpline of the given degree is returned.
        """
        from pyformex.plugins.curve import BezierSpline
        ndim = 3
        coords = at.readArray(self.fil, at.Float, (ncoords, ndim), sep=sep)
        return BezierSpline(control=coords, closed=closed, degree=degree)


    def readNurbsCurve(self, ncoords, nknots, closed, sep):
        """Read a NurbsCurve from a pyFormex geometry file.

        The coordinate array for ncoords control points and the nknots
        knot values are read from the file.
        A NurbsCurve of degree p = nknots - ncoords - 1 is returned.
        """
        from pyformex.plugins.nurbs import NurbsCurve
        ndim = 4
        coords = at.readArray(self.fil, at.Float, (ncoords, ndim), sep=sep)
        knots = at.readArray(self.fil, at.Float, (nknots,), sep=sep)
        return NurbsCurve(control=coords, knots=knots, closed=closed)


    def readNurbsSurface(self, ncoords, nuknots, nvknots, uclosed, vclosed, sep):
        """Read a NurbsSurface from a pyFormex geometry file.

        The coordinate array for ncoords control points and the nuknots and
        nvknots values of uknots and vknots are read from the file.
        A NurbsSurface of degree ``pu = nuknots - ncoords - 1``  and
        ``pv = nvknots - ncoords - 1`` is returned.
        """
        from pyformex.plugins.nurbs import NurbsSurface
        ndim = 4
        coords = at.readArray(self.fil, at.Float, (ncoords, ndim), sep=sep)
        uknots = at.readArray(self.fil, at.Float, (nuknots,), sep=sep)
        vknots = at.readArray(self.fil, at.Float, (nvknots,), sep=sep)
        return NurbsSurface(control=coords, knots=(uknots, vknots), closed=(uclosed, vclosed))


###########################################################################
        ### OLD READ FUNCTIONS ###

    def readLegacy(self,count=-1):
        """Read the objects from a pyFormex Geometry File format <= 1.7.

        This function reads all the objects of a Geometry File.
        The File should have been opened for reading, and the header
        should have been read previously.

        A count may be specified to limit the number of objects read.

        Returns a dict with the objects read. The keys of the dict are the
        object names found in the file. If the file does not contain
        object names, they will be autogenerated from the file name.
        """
        if not self.header_done:
            self.readHeader()
        eltype = None # for compatibility with pre 1.1 .formex files
        #ndim = 3
        while True:
            objtype = 'Formex' # the default obj type
            obj = None
            nelems = None
            nplex = None
            ncoords = None
            sep = self.sep
            name = None
            normals = None
            color = None
            props = None
            closed = None
            nparts = None
            nknots = None
            s = self.fil.readline()

            if len(s) == 0:   # end of file
                break

            if not s.startswith('#'):  # not a header: skip
                continue


            ###
            ###  THIS WILL USE UNDEFINED VALUES FROM A PREVIOUS OBJECT
            ###  THIS SHOULD THEREFORE BE CHANGED !!!!
            ###
            try:
                exec(s[1:].strip())
                #pf.debug("READ COLOR: %s" % str(color),pf.DEBUG.INFO)
            except:
                nelems = ncoords = None

            if nelems is None and ncoords is None:
                # For historical reasons, this is a certain way to test
                # that no geom data block is following
                pf.debug("SKIPPING %s" % s, pf.DEBUG.LEGACY)
                continue  # not a legal header: skip

            pf.debug("Reading object of type %s" % objtype, pf.DEBUG.INFO)

            # OK, we have a legal header, try to read data
            if objtype == 'Formex':
                obj = self.readFormex(nelems, nplex, props, eltype, sep)
            elif objtype in ['Mesh', 'TriSurface']:
                obj = self.readMesh(ncoords, nelems, nplex, props, eltype, normals, sep, objtype)
            elif objtype == 'PolyLine':
                obj = self.readPolyLine(ncoords, closed, sep)
            elif objtype == 'BezierSpline':
                if 'nparts' in s:
                    # This looks like a version 1.3 BezierSpline
                    obj = self.oldReadBezierSpline(ncoords, nparts, closed, sep)
                else:
                    if not 'degree' in s:
                        # compatibility with 1.4  BezierSpline records
                        degree = 3
                    obj = self.readBezierSpline(ncoords, closed, degree, sep)
            elif objtype == 'NurbsCurve':
                obj = self.readNurbsCurve(ncoords, nknots, closed, sep)
            elif objtype in globals() and hasattr(globals()[objtype], 'read_geom'):
                obj = globals()[objtype].read_geom(self)
            else:
                print("Can not (yet) read objects of type %s from geometry file: skipping" % objtype)
                continue # skip to next header


            if obj is not None:
                try:
                    color = at.checkArray(color, (3,), 'f')
                    obj.color = color
                except:
                    pass

                if name is None:
                    name = next(self.autoname)
                self.results[name] = obj

            if count > 0 and len(self.results) >= count:
                break

        self.file.close()

        return self.results


    def oldReadBezierSpline(self, ncoords, nparts, closed, sep):
        """Read a BezierSpline from a pyFormex geometry file version 1.3.

        The coordinate array for ncoords points and control point array
        for (nparts,2) control points are read from the file.
        A BezierSpline is constructed and returned.
        """
        from pyformex.plugins.curve import BezierSpline
        ndim = 3
        coords = at.readArray(self.fil, at.Float, (ncoords, ndim), sep=sep)
        control = at.readArray(self.fil, at.Float, (nparts, 2, ndim), sep=sep)
        return BezierSpline(coords, control=control, closed=closed)


    def rewrite(self):
        """Convert the geometry file to the latest format.

        The conversion is done by reading all objects from the geometry file
        and writing them back. Parts that could not be succesfully read will
        be skipped.
        """
        self.reopen('r')
        obj = self.read(warn_version=False)
        self.version = GeometryFile._version_
        if obj is not None:
            self.reopen('w')
            self.write(obj)
        self.close()

# End
