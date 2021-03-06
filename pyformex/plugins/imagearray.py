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
"""Convert bitmap images into numpy arrays.

This module contains functions to convert bitmap images into numpy
arrays and vice versa.

This code was based on ideas found on the PyQwt mailing list.
"""
from __future__ import absolute_import, division, print_function


import pyformex as pf
from pyformex import arraytools as at
from pyformex.gui import QtGui
QImage = QtGui.QImage
QColor = QtGui.QColor

import numpy as np
from pyformex import utils


def resizeImage(image,w=0,h=0):
    """Load and optionally resize an image.

    Parameters:

    - `image`: a QImage, or any data that can be converted to a QImage,
      e.g. the name of a raster image file.
    - `w`, `h`: requested size in pixels of the image.
      A value <= 0 will be replaced with the corresponding actual size of
      the image.

    Returns a QImage with the requested size.
    """
    if not isinstance(image, QImage):
        image = QImage(image)

    W, H = image.width(), image.height()
    if w <= 0:
        w = W
    if h <= 0:
        h = H
    if w != W or h != H:
        image = image.scaled(w, h)

    return image


def qimage2numpy(image,resize=(0, 0),order='RGBA',flip=True,indexed=None,expand=None):
    """Transform an image to a Numpy array.

    Parameters:

    - `image`: a QImage or any data that can be converted to a QImage,
      e.g. the name of an image file, in any of the formats supported by Qt.
      The image can be a full color image or an indexed type. Only 32bit
      and 8bit images are currently supported.
    - `resize`: a tuple of two integers (width,height). Positive value will
      force the image to be resized to this value.
    - `order`: string with a permutation of the characters 'RGBA', defining
      the order in which the colors are returned. Default is RGBA, so that
      result[...,0] gives the red component. Note however that QImage stores
      in ARGB order. You may also specify a subset of the 'RGBA' characters,
      in which case you will only get some of the color components. An often
      used value is 'RGB' to get the colors without the alpha value.
    - `flip`: boolean: if True, the image scanlines are flipped upside down.
      This is practical because image files are usually stored in top down
      order, while OpenGL uses an upwards positive direction, requiring a
      flip to show the image upright.
    - `indexed`: True, False or None.

      - If True, the result will be an indexed image where each pixel color
        is an index into a color table. Non-indexed image data will be
        converted.

      - If False, the result will be a full color array specifying the color
        of each pixel. Indexed images will be converted.

      - If None (default), no conversion is done and the resulting data are
        dependent on the image format. In all cases both a color and a
        colortable will be returned, but the latter will be None for
        non-indexed images.

    - `expand`: deprecated, retained for compatibility

    Returns:

    - if `indexed` is False: an int8 array with shape (height,width,4), holding
      the 4 components of the color of each pixel. Order of the components
      is as specified by the `order` argument. Indexed image formats will
      be expanded to a full color array.

    - if `indexed` is True: a tuple (colors,colortable) where colors is an
      (height,width) shaped int array of indices into the colortable,
      which is an int8 array with shape (ncolors,4).

    - if `indexed` is None (default), a tuple (colors,colortable) is returned,
      the type of which depend on the original image format:

      - for indexed formats, colors is an int (height,width) array of indices
        into the colortable, which is an int8 array with shape (ncolors,4).

      - for non-indexed formats, colors is a full (height,width,4) array
        and colortable is None.
    """
    if expand is not None:
        utils.warn("depr_qimage2numpy_arg")
        indexed = not expand


    image = resizeImage(image,*resize)

    if indexed:
        image = image.convertToFormat(QImage.Format_Indexed8)

    h, w = image.height(), image.width()

    if image.format() in (QImage.Format_ARGB32_Premultiplied,
                          QImage.Format_ARGB32,
                          QImage.Format_RGB32):
        buf = image.bits()
        if not pf.options.pyside:
            buf = buf.asstring(image.numBytes())
        ar = np.frombuffer(buf, dtype='ubyte', count=image.numBytes()).reshape(h, w, 4)
        idx = [ 'BGRA'.index(c) for c in order ]
        ar = ar[..., idx]
        ct = None

    elif image.format() == QImage.Format_Indexed8:
        ct = np.array(image.colorTable(), dtype=np.uint32)
        #print("IMAGE FORMAT is INDEXED with %s colors" % ct.shape[0])
        ct = ct.view(np.uint8).reshape(-1, 4)
        idx = [ 'BGRA'.index(c) for c in order ]
        ct = ct[..., idx]
        buf = image.bits()
        if not pf.options.pyside:
            buf = buf.asstring(image.numBytes())
        ar = np.frombuffer(buf, dtype=np.uint8)
        if ar.size % h == 0:
            ar = ar.reshape(h, -1)
            if ar.shape[1] > w:
                # The QImage buffer always has a size corresponding
                # with a width that is a multiple of 8. Here we strip
                # off the padding pixels of the QImage buffer to the
                # reported width.
                ar = ar[:,:w]

        if ar.size != w*h:
            # This should no longer happen, since we have now adjusted
            # the numpy buffer width to the correct image width.
            pf.warning("Size of image data (%s) does not match the reported dimensions: %s x %s = %s" % (ar.size, w, h, w*h))

    else:
        raise ValueError("qimage2numpy only supports 32bit and 8bit images")

    # Put upright as expected
    if flip:
        ar = np.flipud(ar)

    # Convert indexed to nonindexed if requested
    if indexed is False and ct is not None:
            ar = ct[ar]
            ct = None

    # Return only full colors if requested
    if indexed is False:
        return ar
    else:
        return ar, ct


def numpy2qimage(array):
        """Convert a 2D or 3D integer numpy array into a QImage

        Parameters:

        - `array`: 2D or 3D int array. If the input array is 2D, the array
          is converted into a gray image. If the input array is 3D, the last
          axis should have length 3 or 4 and represents the color channels in
          order RGB or RGBA.

        This is equivalent with calling :func:`gray2qimage` for a 2D array
        and rgb2qimage for a 3D array.

        """
        if np.ndim(array) == 2:
                return gray2qimage(array)
        elif np.ndim(array) == 3:
                return rgb2qimage(array)
        raise ValueError("can only convert 2D or 3D arrays")


def gray2qimage(gray):
        """Convert the 2D numpy array `gray` into a 8-bit QImage with a gray
        colormap.  The first dimension represents the vertical image axis."""
        if len(gray.shape) != 2:
                raise ValueError("gray2QImage can only convert 2D arrays")

        gray = np.require(gray, np.uint8, 'C')

        h, w = gray.shape

        result = QImage(gray.data, w, h, QImage.Format_Indexed8)
        result.ndarray = gray
        for i in range(256):
                result.setColor(i, QColor(i, i, i).rgb())
        return result


def rgb2qimage(rgb):
        """Convert the 3D numpy array into a 32-bit QImage.

        Parameters:

        - `rgb` : (height,width,nchannels) integer array specifying the
          pixels of an image. There can be 3 (RGB) or 4 (RGBA) channels.

        Returns a QImage with size (height,width) in the format
        RGB32 (3channel) or ARGB32 (4channel).
        """
        if len(rgb.shape) != 3:
                raise ValueError("rgb2QImage expects the first (or last) dimension to contain exactly three (R,G,B) channels")
        if rgb.shape[2] != 3:
                raise ValueError("rgb2QImage can only convert 3D arrays")

        h, w, channels = rgb.shape

        # Qt expects 32bit BGRA data for color images:
        bgra = np.empty((h, w, 4), np.uint8, 'C')
        bgra[..., 0] = rgb[..., 2]
        bgra[..., 1] = rgb[..., 1]
        bgra[..., 2] = rgb[..., 0]

        if channels == 4:
            bgra[..., 3] = rgb[..., 3]
            fmt = QImage.Format_ARGB32
        else:
            fmt = QImage.Format_RGB32

        result = QImage(bgra.data, w, h, fmt)
        result.ndarray = bgra
        return result


def qimage2glcolor(image,resize=(0, 0)):
    """Convert a bitmap image to corresponding OpenGL colors.

    Parameters:

    - `image`: a QImage or any data that can be converted to a QImage,
      e.g. the name of an image file, in any of the formats supported by Qt.
      The image can be a full color image or an indexed type. Only 32bit
      and 8bit images are currently supported.
    - `resize`: a tuple of two integers (width,height). Positive value will
      force the image to be resized to this value.

    Returns a (w,h,3) shaped array of float values in the range 0.0 to 1.0,
    containing the OpenGL colors corresponding to the image RGB colors.
    By default the image is flipped upside-down because the vertical
    OpenGL axis points upwards, while bitmap images are stored downwards.
    """
    c = qimage2numpy(image, resize=resize, order='RGB', flip=True, indexed=False)
    c = c.reshape(-1, 3)
    c = c / 255.
    return c, None


def removeAlpha(qim):
    """Remove the alpha channel from a QImage.

    Directly saving a QImage grabbed from the OpenGL buffers always
    results in an image with transparency.
    See https://savannah.nongnu.org/bugs/?36995 .

    This function will remove the alpha channel from the QImage, so
    that it can be saved with opaque objects.

    Note: we did not find a way to do this directly on the QImage,
    so we go through a conversion to a numpy array and back.
    """
    ar, cm = qimage2numpy(qim, flip=False)
    return rgb2qimage(ar[..., :3])


####################################################################
# Import images using PIL

if utils.checkModule('pil'):

    from PIL import Image

    def imagefile2string(filename):
        im = Image.open(filename)
        nx, ny = im.size[0], im.size[1]
        try:
            data = im.tostring("raw", "RGBA", 0, -1)
        except SystemError:
            data = im.tostring("raw", "RGBX", 0, -1)
        return nx, ny, data



# Import images using dicom
_dicom_spacing = None
_dicom_origin = None
_dicom_intercept = 0
_dicom_slope = 1

#
# The use of python-dicom is deprecated! Use python-gdcm instead
#

# if utils.checkModule('dicom'):

#     def loadImage_dicom(filename):
#         """Load a DICOM image into a numpy array.

#         This function uses the python-dicom module to load a DICOM image
#         into a numpy array. See also :func:`loadImage_gdcm` for an
#         equivalent using python-gdcm.

#         Parameters:

#         - `file`: the name of a DICOM image file

#         Returns a 2D array with the pixel data of all the image. The first
#           axis is the `y` value, the last the `x`.

#         As a side effect, this function sets the global variable `_dicom_spacing`
#         to a (3,) array with the pixel/slice spacing factors, in order (x,y,z).
#         """
#         import dicom
#         global _dicom_spacing
#         _dicom_spacing = None
#         try:
#             dcm = dicom.read_file(filename)
#             #print("%s %s %s %s" % (filename[-10:],dcm.PixelSpacing[0],dcm.PixelSpacing[1],dcm.SliceThickness))
#         except:
#             print("While reading file '%s'" % filename)
#             raise
#         pix = dcm.pixel_array
#         _dicom_spacing = np.array(dcm.PixelSpacing + [dcm.SliceThickness])
#         return pix

#     readDicom = loadImage_dicom


if utils.checkModule('gdcm'):


    def loadImage_gdcm(filename):
        """Load a DICOM image into a numpy array.

        This function uses the python-gdcm module to load a DICOM image
        into a numpy array. See also :func:`loadImage_dicom` for an
        equivalent using python-dicom.

        Parameters:

        - `file`: the name of a DICOM image file

        Returns a 2D array with the pixel data of the image. The first
          axis is the `y` value, the last the `x`.

        As a side effect, this function sets the global variables
        `_dicom_spacing` and `_dicom_origin` to a to a (3,) array with
        the pixel/slice spacing factors, resp. the origin, in order (x,y,z).
        It also sets the _dicom_slope, _dicom_intercept global variables.
        """
        import gdcm

        def get_gdcm_to_numpy_typemap():
            """Returns the GDCM Pixel Format to numpy array type mapping."""
            _gdcm_np = {gdcm.PixelFormat.UINT8  :np.int8,
                        gdcm.PixelFormat.INT8   :np.uint8,
                        #gdcm.PixelFormat.UINT12 :np.uint12,
                        #gdcm.PixelFormat.INT12  :np.int12,
                        gdcm.PixelFormat.UINT16 :np.uint16,
                        gdcm.PixelFormat.INT16  :np.int16,
                        gdcm.PixelFormat.UINT32 :np.uint32,
                        gdcm.PixelFormat.INT32  :np.int32,
                        #gdcm.PixelFormat.FLOAT16:np.float16,
                        gdcm.PixelFormat.FLOAT32:np.float32,
                        gdcm.PixelFormat.FLOAT64:np.float64 }
            return _gdcm_np


        def get_numpy_array_type(gdcm_pixel_format):
            """Returns a numpy array typecode given a GDCM Pixel Format."""
            return get_gdcm_to_numpy_typemap()[gdcm_pixel_format]


        def gdcm_to_numpy(image):
            """Convert a GDCM image to a numpy array.

            """
            fmt = image.GetPixelFormat()

            if fmt.GetScalarType() not in get_gdcm_to_numpy_typemap().keys():
                raise ValueError("Unsupported Pixel Format\n%s"%fmt)

            shape = (image.GetDimension(0), image.GetDimension(1))
            if image.GetNumberOfDimensions() == 3:
              shape = shape + (image.GetDimension(2),)
            if fmt.GetSamplesPerPixel() != 1:
                raise ValueError("Can not read images with multiple samples per pixel.")

            dtype = get_numpy_array_type(fmt.GetScalarType())
            gdcm_array = image.GetBuffer()
            data = np.frombuffer(gdcm_array, dtype=dtype).reshape(shape)
            spacing = np.array(image.GetSpacing())
            origin = np.array(image.GetOrigin())
            intercept = image.GetIntercept()
            slope = image.GetSlope()
            return data, spacing, origin, slope, intercept


        global _dicom_spacing, _dicom_origin, _dicom_slope, _dicom_intercept
        rdr = gdcm.ImageReader()
        rdr.SetFileName(filename)

        if not rdr.Read():
            raise ValueError("Could not read image file '%s'" % filename)
        pix, _dicom_spacing, _dicom_origin, _dicom_slope, _dicom_intercept = gdcm_to_numpy(rdr.GetImage())
        return pix

    readDicom = loadImage_gdcm


    class DicomStack(object):
        """A stack of DICOM images.

        The DicomStack class stores a collection of DICOM images
        and provides conversion to ndarray.

        The DicomStack is initialized by a list of file names.
        All input files are scanned for DICOM image data and
        non-DICOM files are skipped.
        From the DICOM files, the pixel and slice spacing are read,
        as well as the origin.
        The DICOM files are sorted in order of ascending origin_z value.

        While reading the DICOM files, the following attributes are set:

        - `files`: a list of the valid DICOM files, in order of ascending
          z-value.
        - `pixel_spacing`: a dict with an (x,y) pixel spacing tuple as key
          and a list of indices of the matching images as value.
        - `slice_thickness`: a list of the slice thicknesses of the
          images, in the same order as `files`.
        - `xy_origin`: a dict with an (x,y) position the pixel (0,0) as key
          and a list of indices of the matching images as value.
        - `z_origin`: a list of the z positions of the images,
          in the same order as `files`.
        - `rejected`: list of rejected files.

        """
        class Object(object):
            """_A dummy object to allow attributes"""
            pass


        def __init__(self,files,zsort=True,reverse=False):
            """Initialize the DicomStack."""
            ok = []
            rejected = []
            for fn in files:
                obj = DicomStack.Object()
                try:
                    obj.fn = fn
                    obj.image = loadImage_gdcm(fn)
                    obj.spacing = _dicom_spacing
                    obj.origin = _dicom_origin
                    obj.intercept = _dicom_intercept
                    obj.slope = _dicom_slope
                    ok.append(obj)
                except:
                    rejected.append(obj)
                    raise

            if zsort:
                ok.sort(key=lambda obj:obj.origin[2], reverse=reverse)

            self.ok, self.rejected = ok,rejected


        def nfiles(self):
            """Return the number of accepted files."""
            return len(self.ok)


        def files(self):
            """Return the list of accepted filenames"""
            return [ obj.fn for obj in self.ok ]


        def rejected(self):
            """Return the list of rejected filenames"""
            return [ obj.fn for obj in self.rejected ]


        def spacing(self):
            """Return the pixel spacing and slice thickness.

            Return the pixel spacing (x,y) and the slice thickness (z)
            in the accepted images.

            Returns: a float array of shape (nfiles,3).
            """
            return np.array([ obj.spacing for obj in self.ok ])


        def origin(self):
            """Return the origin of all accepted images.

            Return the world position of the pixel (0,0) in all accepted images.

            Returns: a float array of shape (nfiles,3).
            """
            return np.array([ obj.origin for obj in self.ok ])


        def zvalue(self):
            """Return the zvalue of all accepted images.

            The zvalue is the z value of the origin of the image.

            Returns: a float array of shape (nfiles).
            """
            return np.array([ obj.origin[2] for obj in self.ok ])


        def image(self,i):
            """Return the image at index i"""
            return self.ok[i].image


        def pixar(self,raw=False):
            """Return the DicomStack as an array

            Returns all images in a single array. This is only succesful
            if all accepted images have the same size.
            """
            if raw:
                data = np.dstack([ obj.image for obj in self.ok ])
            else:
                data = np.dstack([ obj.image*obj.slope+obj.intercept for obj in self.ok ])
            return data


def dicom2numpy(files):
    """Read a set of DICOM image files.

    Parameters:

    - `files`: a list of file names of dicom images of the same size,
      or a directory containing such images. In the latter case, all the
      DICOM images in the directory will be read.

    Returns a tuple of:

    - `pixar`: a 3D array with the pixel data of all the images. The first
      axis is the `z` value, the last the `x`.
    - `scale`: a (3,) array with the scaling factors, in order (x,y,z).
    """
    if isinstance(files, str):
        files = utils.listTree(files, listdirs=False, includefiles="*.dcm")
    # read and stack the images
    print("Using %s to read DICOM files" % readDicom.__name__)

    pixar = np.dstack([ readDicom(f) for f in files ])
    scale = _dicom_spacing
    return pixar, scale


def saveGreyImage(a, f, flip=True):
    """Save a 2D int array as a grey image.

    Parameters:

    - `a`: int array (nx,ny) with values in the range 0..255. These are
      the grey values of the pixels.
    - `f`: filename
    - `flip`: by default, the vertical axis is flipped, so that images are
      stored starting at the top. If your data already have the vertical axis
      downwards, use flip=False.

    """
    a = at.checkArray(a,ndim=2,kind='u',allow='i').astype(np.uint8)
    c = np.flipud(a)
    c = np.dstack([c, c, c])
    im = numpy2qimage(c)
    im.save(f)


# End
