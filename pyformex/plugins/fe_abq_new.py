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
"""Exporting finite element models in Abaqus\ |trade| input file format.

This module provides functions and classes to export finite element models
from pyFormex in the Abaqus\ |trade| input format (.inp).
The exporter handles the mesh geometry as well as model, node and element
properties gathered in a :class:`PropertyDB` database (see module
:mod:`properties`).

While this module provides only a small part of the Abaqus input file format,
it suffices for most standard jobs. While we continue to expand the interface,
depending on our own necessities or when asked by third parties, we do not
intend to make this into a full implementation of the Abaqus input
specification. If you urgently need some missing function, there is always
the possibility to edit the resulting text file or to import it into the
Abaqus environment for further processing.

The module provides two levels of functionality: on the lowest level, there
are functions that just generate a part of an Abaqus input file, conforming
to the Abaqus\ |trade| Keywords manual.

Then there are higher level functions that read data from the property module
and write them to the Abaqus input file and some data classes to organize all
the data involved with the finite element model.
"""
from __future__ import print_function
from pyformex import zip

from pyformex.plugins.properties import *
from pyformex.plugins.fe import *
from pyformex.mydict import Dict, CDict
import pyformex as pf
from datetime import datetime
import os, sys
from pyformex import utils
from pyformex.arraytools import isInt, fmtData1d, isqrt

##################################################
## Some Abaqus .inp format output routines
##################################################

def abqInputNames(job):
    """Returns corresponding Abq jobname and input filename.

    job can be either a jobname or input file name, with or without
    directory part, with or without extension (.inp)

    The Abq jobname is the basename without the extension.
    The abq filename is the abspath of the job with extension '.inp'
    """
    jobname = os.path.basename(job)
    if jobname.endswith('.inp'):
        jobname = jobname[:-4]
    filename = os.path.abspath(job)
    if not filename.endswith('.inp'):
        filename += '.inp'
    return jobname, filename


def nsetName(p):
    """Determine the name for writing a node set property."""
    if p.name is None:
        return 'Nall'
    else:
        return p.name


def esetName(p):
    """Determine the name for writing an element set property."""
    if p.name is None:
        return 'Eall'
    else:
        return p.name


###########################################################
##   Output Formatting Following Abaqus Keywords Manual  ##
###########################################################

#
#  !! This is only a very partial implementation
#     of the Abaqus keyword specs.
#

## The following output functions return the formatted output
## and should be written to file by the caller.
###############################################

def fmtData2d(data,linesep='\n'):
    """Format 2D data.

    `data`: list.

    Each item of data is formatted using fmtData1D and the resulting
    strings are joined with linesep.

    Examples:

      >>> print(fmtData2d([('set0',1,5.0),('set1',2,10.0)]))
      set0, 1, 5.0
      set1, 2, 10.0

    """
    return linesep.join([fmtData1d(d) for d in data])


def fmtData(data,linesep='\n'):
    """Format the data section

    If data is a list of tuples, or data is a 2D array, each item/row of
    data will be formatted on a separate line.
    Any other data will be formatted as a 1D sequence with 8 items per
    line.
    Lines are separated with linesep.

    Examples:

    >>> print(fmtData([1,2,3,4.0,'last']))
    1, 2, 3, 4.0, last
    >>> print(fmtData([(1,2),(3,4.0,'last')]))
    1, 2
    3, 4.0, last

    """
    if (isinstance(data,list) and isinstance(data[0],tuple)) or (isinstance(data,ndarray) and data.ndim==2) :
        return fmtData2d(data,linesep=linesep)
    else:
        return fmtData1d(data,linesep=linesep)


def fmtKeyword(keyword,options='',data=None,extra='',*args,**kargs):
    """Format any keyword block in INP file.

    - `keyword`: string, keyword command, possibly including options
    - `options`: string or Options. The argument is first converted to str.
      If the result starts with a comma, it is added as is to the command line;
      otherwise it is added with interposition of ', '.
    - `data`: numerical data: will be formatted with maximum 8 values per line,
      or a list of tuples: each tuple will be formatted on a line
    - `extra`: string: will be added as is below the command and data

    All other arguments will be formatted with fmtOptions on the command line,
    between `keyword` and `options`.

    Examples:

    """
    out = '*'
    out += ', '.join([ str(v).upper() for v in (keyword,) + args ])
    if kargs:
        out += fmtOptions(**kargs)
    if options:
        options = str(options)
        if options[:1] != ',':
            out += ', '
        out += options
    out += '\n'

    if data is not None:
        out += fmtData(data)
        out += '\n'

    if extra:
        out += extra
        out += '\n'

    return out


def fmtOption(key,value):
    """Format a single option.

    """
    key = key.replace('_',' ').upper()
    value = "=%s" % value if value else ''
    return ", %s%s" % (key,value)


def fmtOptions(**kargs):
    """Format the options of an Abaqus command line.

    Each key,value pair in the argument list is formated into s string
    'KEY=value', or just 'KEY' if the value is an empty string.
    The key is always converted to upper case, and any underscore in the
    key is replaced with a space.
    The resulting strings are joined with ', ' between them.

    Returns a comma-separated string of 'keyword' or 'keyword=value' fields.
    The string has a leading but no trailing comma.

    Note that if you specified two arguments whose keyword only differs
    by case, both will appear in the output with the same keyword.
    Also note that the order in which the options appear is unspecified.

    Examples:
      >>> print(fmtOptions(var_a = 123., var_B = '123.', Var_C = ''))
      , VAR C, VAR B=123., VAR A=123.0

    """
    return ''.join([ fmtOption(k,v) for k,v in kargs.items() ])


class Command(object):
    """A class to format a keyword block in an INP file.

    Parameters (all are optional, except for `cmd`):
    - `cmd`: string, starting with an Abaqus keyword. The `cmd` string may
      include already formatted options. It will be converted to upper case
      and put as is after the initial '*' character.
    - `options`: string. String to be added to the command line after any
      other `args` and `kargs` keyword options have been formatted (even those
      added later with the :func:`add` method). If the string does not
      start with a comma, a ', ' will be interposed.
    - `data`: list-like or list of tuple. Specifies the data to be put below
      the command line. A list of tuples will be formatted with one tuple
      per line. Any other data type will be transformed to a flat sequence
      and be formatted with maximum 8 values per line. Each individual item
      is converted to str type, so the data sequence may contain numerical
      (float or int) as well as string data.
    - `extra`: string: will be added as is below the command and data. This
      may be a multiline string and can be used to add complete preformatted
      sections to the output.
    - `args`: any other non-keyword arguments are added as options to the
      command line, after conversion to string and upper case.
    - `kargs`: any other keyword arguments are added to the command line as
      options of the form 'KEY=value'. The keys are converted to upper case,
      the values not.

    After initial construction, the :func:`add` method can be used to add
    more parts to the command.

    Remark: there is no check whether a certain option contains multiple
      occurrences of the same option.

    Examples:

      >>> cmd1 = Command('Key','material=plastic',options='material=steel',data=[1,2,3,4.0,'last'],extra='*AnotherKey, opt=optionalSet1,\\n 1, 4.7')
      >>> cmd1.add(material='wood')
      >>> print(cmd1)
      *KEY, MATERIAL=PLASTIC, MATERIAL=wood, material=steel
      1, 2, 3, 4.0, last
      *AnotherKey, opt=optionalSet1,
       1, 4.7
      <BLANKLINE>

    """
    def __init__(self,cmd,*args,**kargs):
        """Initialize the Command"""
        self.cmd = '*' + str(cmd).upper()
        self.data = None
        self.options = ''
        self.extra = ''
        self.add(*args,**kargs)


    def add(self,*args,**kargs):
        """Add more parts to the Command.

        This method takes all the parameters as the initializer,
        except for `cmd`. Specifying `data` will overwrite any
        previously defined data for the command. All other parameters
        will be added to the already existing.
        """

        if 'data' in kargs:
            self.data = kargs['data']
            del kargs['data']

        if 'options' in kargs:
            options = kargs['options']
            del kargs['options']
            if isinstance(options,str):
                if len(options) > 0 and options[0] != ',':
                    self.options += ', '
                self.options += options

        if 'extra' in kargs:
            extra = kargs['extra']
            del kargs['extra']
            if isinstance(extra,str):
                self.extra += extra

        if args:
            self.cmd += ', '
            self.cmd += ', '.join([ str(v).upper() for v in args ])
        if kargs:
            self.cmd += fmtOptions(**kargs)



    @property
    def out(self):
        """The formatted command as a string"""
        return self.__str__()


    def __str__(self):
        """Format the full command block"""
        out = self.cmd

        if self.options:
            out += self.options

        out += '\n'

        if self.data is not None:
            out += fmtData(self.data)
            out += '\n'

        if self.extra:
            out += self.extra
            out += '\n'

        return out


def fmtHeading(text=''):
    """Format the heading of the Abaqus input file."""
    out = """**  Abaqus input file created by %s (%s)
**
*HEADING
%s
""" % (pf.Version(), pf.Url, text)
    return out


def fmtSectionHeading(text=''):
    """Format a section heading of the Abaqus input file."""
    return """**
**  %s
**
""" %text


def fmtPart(name='Part-1'):
    """Start a new Part."""
    out = """**  Abaqus input file created by %s (%s)
**
*PART
""" % (name)
    return out

#########################################################
#
#  MATERIALS
#
#########################################################
materialswritten=[]

def fmtMaterial(mat):
    """Write a material section.

    `mat` is the property dict of the material. The following keys are
    recognized and output accordingly. The keys labeled (opt) are optional.

    - name: if specified, and a material with this name has already been
      written, this function does nothing.

    - elasticity: one of 'LINEAR', 'HYPERELASTIC', 'ANISOTROPIC HYPERELASTIC',
      'USER' or another string specifying a valid material command.
      Default is 'LINEAR'.
      Defines the elastic behavior class of the material. The required and
      recognized keys depend on this parameter (see below).

    - constants : list of floats or None.
      The material constants to be used in the model.
      For 'LINEAR' elasticity, these may alternatively be specified by other
      keywords (see below).

    - options (opt): string: will be added to the material command as is.

    - extra (opt): (multiline) string: will be added to the material data as is.

    - plastic (opt): arraylike, float, shape (N,2). Definition of the
      material plasticity law. Each row contains a tuple of a yield stress
      value and the corresponding equivalent plastic strain.

    - damping (opt): tuple (alpha,beta). Adds damping into the material.
      See Abaqus manual for the meaning of alpha and beta. Either of them
      can be a float or None.

    - field (opt): boolean. If True, a keyword "USER DEFINED FIELD" is added.

    Recognized keys depending on model:

    'LINEAR': allows the specification of the material constants using the
    following keys:

    - young_modulus: float
    - shear_modulus (opt): float
    - poisson_ratio (opt): float: if not specified, it is calculated from
      the above two values.

    'HYPERELASTIC': has a required key 'model':

    - model: one of 'OGDEN', 'POLYNOMIAL' or 'REDUCED POLYNOMIAL'
    - order (opt): order of the model. If omitted, it is calculated from the
      number of constants specified.
    - testdata:

    'ANISOTROPIC HYPERELASTIC': has a required key 'model':

    - model: one of 'FUNG-ANISOTROPIC', 'FUNG-ORTHOTROPIC', 'HOLZAPFEL' or
      'USER'.
    - depvar (opt): see below ('USER')
    - localdir (opt): int: number of local directions.

    'USER':
    - depvar (opt): list. The first item in the list is the number of solution
      dependent variables. Further items are optional and are to specify
      output names for (some of) solution dependent state variables. Each
      item is a tuple of a variable number and the corresponding variable
      name. See the examples below.

    Example:

    >>> steel = {
    ...      'name': 'steel',
    ...      'young_modulus': 207000,
    ...      'poisson_ratio': 0.3,
    ...      'density': 7.85e-9,
    ...      'plastic': [(200.,0.), (900.,0.5)],
    ...      }
    >>> from pyformex.attributes import Attributes
    >>> print(fmtMaterial(Attributes(steel)))
    *MATERIAL, NAME=steel
    *ELASTIC
    207000.0, 0.3
    *DENSITY
    7.85e-09
    *PLASTIC
    200.0, 0.0
    900.0, 0.5
    <BLANKLINE>

    >>> intima = {
    ...      'name': 'intima',
    ...      'density': 0.1,
    ...      'elasticity':'hyperelastic',
    ...      'model':'reduced polynomial',
    ...      'constants': [6.79E-03, 5.40E-01, -1.11, 10.65, -7.27, 1.63, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    ...      }
    >>> print(fmtMaterial(Attributes(intima)))
    *MATERIAL, NAME=intima
    *HYPERELASTIC, REDUCED POLYNOMIAL, N=6
    0.00679, 0.54, -1.11, 10.65, -7.27, 1.63, 0.0, 0.0
    0.0, 0.0, 0.0, 0.0
    *DENSITY
    0.1
    <BLANKLINE>

    >>> nitinol = {
    ...     'name': 'ABQ_SUPER_ELASTIC_N3D',
    ...     'elasticity': 'user',
    ...     'density': 6.5e-9,
    ...     'depvar' : [24, (1,'VAR1'), (3,'DAMAGE')],
    ...     'constants' : [10000., 0.3, 5000, 0.3, 0.03, 6.5, 200., 300.,
    ...                    0.0, 6.5, 260., 100.,0., 0.03,  ]
    ...     }
    >>> print(fmtMaterial(Attributes(nitinol)))
    *MATERIAL, NAME=ABQ_SUPER_ELASTIC_N3D
    *DEPVAR
    24
    1, VAR1
    3, DAMAGE
    *USER MATERIAL, CONSTANTS=14
    10000.0, 0.3, 5000, 0.3, 0.03, 6.5, 200.0, 300.0
    0.0, 6.5, 260.0, 100.0, 0.0, 0.03
    *DENSITY
    6.5e-09
    <BLANKLINE>


    """
    out = Command('MATERIAL',name=mat.name).out
    materialswritten.append(mat.name)

    if mat.field is not None:
        out += Command('USER DEFINED FIELD').out

    if mat.depvar is not None:
        data = [ (mat.depvar[0],)] + mat.depvar[1:]
        out += Command('DEPVAR',data=data).out

    # Default elasticity type
    if mat.elasticity is None:
        elasticity = 'linear'
    else:
        elasticity =  mat.elasticity.lower()
    constants = mat.constants

    if elasticity == 'linear':
        cmd = Command('ELASTIC')

        if constants is None:
            if mat.poisson_ratio is None and mat.shear_modulus is not None:
                mat.poisson_ratio = 0.5 * mat.young_modulus / mat.shear_modulus - 1.0
            constants = [float(mat.young_modulus), float(mat.poisson_ratio)]

    elif elasticity == 'hyperelastic':
        model = mat.model.lower()
        order = mat.order
        if order is not None:
            nconst = len(constants)
            if model == 'ogden':
                order = nconst // 3
                mconst = 3*order

            elif model == 'polynomial':
                order = (isqrt(25+8*nconst)-5) // 2
                mconst = ((order+1)*(order+2)) // 2 + order - 1

            elif model  == 'reduced polynomial':
                order = nconst // 2
                mconst = 2*order

            else:
                mconst = nconst
                pf.warning('Sorry, number of constants for material %s is not checked' % model)

            if mconst != nconst:
                raise ValueError("Wrong number of material constants (%s) for order (%s) of %s model" % (nconst,mconst,model))

        cmd = Command('HYPERELASTIC',mat.model)
        if order is not None:
            cmd.add(N=order)

    elif elasticity == 'anisotropic hyperelastic':
        cmd = Command('ANISOTROPIC HYPERELASTIC',mat.model)
        if mat.localdir is not None:
            cmd.add(LOCAL_DIRECTIONS=mat.localdir)

    elif elasticity == 'user':
        cmd = Command('USER MATERIAL',CONSTANTS=len(constants))

    elif elasticity is not None:
        cmd = Command(elasticity)

    if mat.options is not None:
        cmd.add(mat.options)

    if constants is not None:
        cmd.add(data=constants)

    out += cmd.out

    if mat.density is not None:
        out += Command('DENSITY',data=[float(mat.density)]).out

    if mat.plastic is not None:
        mat.plastic = asarray(mat.plastic)
        if mat.plastic.ndim != 2:
            raise ValueError("Plastic data should be 2-dim array")
        out += Command('PLASTIC',data=mat.plastic).out

    if mat.damping is not None:
        alpha,beta = mat.damping
        cmd = Command('DAMPING')
        if alpha:
            cmd.add(ALPHA=alpha)
        if beta:
            cmd.add(BETA=beta)
        out += cmd.out

    if mat.extra is not None:
        out += mat.extra
        out += '\n'

    return out



# TODO : - THESE NEED TO BE UNIFIED
#        - VERY BAD DOCSTRING !!!!

def fmtConnectorBehavior(prop):
    ## """_Write a connector behavior.
    ## Implemented: Elasticity,  Stop

    ## Optional parameter:
    ## - `extrapolation`: extrapolation method for all subcomponents of the behavior.
    ##                    'CONSTANT' (default) or 'LINEAR'

    ## Example:

    ## Elasticity
    ## elasticity = dict(component=[1,2,3,4,5,6], value=[1,1,1,1,1,1])
    ## P.Prop(name='connbehavior1', ConnectorBehavior='', Elasticity=elasticity, extrapolation='LINEAR')

    ## Optional parameter for Elasticity dictionary:
    ## - `nonlinear`: use nonlinear elasticity data. Can be False (default) or True.

    ## Stop:
    ## stop = dict(component=[1,2,3,4,5,6],lowerlimit=[1,1,1,1,1,1], upperlimit=[2, 2, 2, 2,2,2])
    ## P.Prop(name='connbehavior3',ConnectorBehavior='',Stop=stop)
    ## """
    out = ''
    for p in prop:
        out += '*CONNECTOR BEHAVIOR, NAME=%s' % p.name
        if p.extrapolation:
            out += ', EXTRAPOLATION=%s\n' % p.extrapolation
        else:
            out += '\n'
        if p.Elasticity:
            out += fmtConnectorElasticity(p.Elasticity)
        if p.Stop:
            out += fmtConnectorStop(p.Stop)
    return out


def fmtConnectorElasticity(elas):
    """Format connector elasticity behavior."""
    out = ''
    for j in range(len(elas['component'])):
        out += '*CONNECTOR ELASTICITY, COMPONENT=%s' % elas['component'][j]
        try:
            if elas['nonlinear']:
                out += ', NONLINEAR\n'
            else:
                out += '\n'
        except:
            out += '\n'
        out += '%s ,\n' % elas['value'][j]
    return out


def fmtConnectorStop(stop):
    """Format connector stop behavior."""
    out = ''
    for j in range(len(stop['component'])):
        out += '*CONNECTOR STOP, COMPONENT=%s\n' % stop['component'][j]
        out += '%s , %s\n'% (stop['lowerlimit'][j], stop['upperlimit'][j])
    return out



#########################################
#
#  ELEMENT LIBRARY
#
#########################################
#
# For each key in the library, there should be a corresponding
#   fmtKeySection function
#
element_library = dict(
    mass = ['MASS'],
    inertia = ['ROTARYI'],
    spring = ['SPRINGA', ],
    dashpot = ['DASHPOTA', ],
    connector = ['CONN3D2', 'CONN2D2'],
    frame = ['FRAME3D', 'FRAME2D'],
    truss = [
        'T2D2', 'T2D2H', 'T2D3', 'T2D3H',
        'T3D2', 'T3D2H', 'T3D3', 'T3D3H'],
    beam = [
        'B21', 'B21H', 'B22', 'B22H', 'B23', 'B23H',
        'B31', 'B31H', 'B32', 'B32H', 'B33', 'B33H'],
    membrane = [
        'M3D3',
        'M3D4', 'M3D4R',
        'M3D6', 'M3D8',
        'M3D8R',
        'M3D9', 'M3D9R'],
    solid2d = [
        # plane stress
        'CPS3',
        'CPS4', 'CPS4I', 'CPS4R',
        'CPS6', 'CPS6M',
        'CPS8', 'CPS8R', 'CPS8M'] + [
        # plane strain
        'CPE3', 'CPE3H',
        'CPE4', 'CPE4H', 'CPE4I', 'CPE4IH', 'CPE4R', 'CPE4RH',
        'CPE6', 'CPE6H', 'CPE6M', 'CPE6MH',
        'CPE8', 'CPE8H', 'CPE8R', 'CPE8RH'] + [
        # generalized_plane_strain
        'CPEG3', 'CPEG3H',
        'CPEG4', 'CPEG4H', 'CPEG4I', 'CPEG4IH', 'CPEG4R', 'CPEG4RH',
        'CPEG6', 'CPEG6H', 'CPEG6M', 'CPEG6MH',
        'CPEG8', 'CPEG8H', 'CPEG8R', 'CPEG8RH'],
    shell = [
        'S3', 'S3R', 'S3RS',
        'S4', 'S4R', 'S4RS', 'S4RSW', 'S4R5',
        'S8R', 'S8R5',
        'S9R5',
        'STRI3',
        'STRI65',
        'SC8R'],
    surface = [
        'SFM3D3',
        'SFM3D4', 'SFM3D4R',
        'SFM3D6',
        'SFM3D8', 'SFM3D8R'],
    solid3d = [
        'C3D4', 'C3D4H',
        'C3D6', 'C3D6H',
        'C3D8', 'C3D8I', 'C3D8H', 'C3D8R', 'C3D8RH', 'C3D10',
        'C3D10H', 'C3D10M', 'C3D10MH',
        'C3D15', 'C3D15H',
        'C3D20', 'C3D20H', 'C3D20R', 'C3D20RH',],
    rigid = [
        'R2D2', 'RB2D2', 'RB3D2', 'RAX2', 'R3D3', 'R3D4',
        ],
    )


def elementClass(eltype):
    """Find the general element class for Abaqus eltype"""
    for k,v in element_library.items():
        if eltype.upper() in v:
            return k
    return ''


#########################################################
#
#  SECTIONS
#
#########################################################


def fmtSolidSection(section ,setname):
    """Format a solid section for the named element set.

    Parameters:

    - `section`: dict: section properties
    - `setname`: string: element set name for which these section properties
      are to be applied.

    Recognized keys in the section dict:

    - orientation
    - thickness

    Examples:

      >>> sec1 = dict(matname='steel',thickness=0.12)
      >>> from pyformex.attributes import Attributes
      >>> print(fmtSolidSection(Attributes(sec1),'section1'))
      *SOLID SECTION, ELSET=section1, MATERIAL=steel
      0.12
      <BLANKLINE>

    """
    cmd = Command('SOLID SECTION',ELSET=setname,MATERIAL=section.matname,options=section.options,extra=section.extra)

    if section.orientation is not None:
        cmd.add(ORIENTATION=section.orientation.name)
    if section.thickness is not None:
        cmd.add(data=[ float(section.thickness) ])

    return cmd.out


fmtSolid2dSection = fmtSolid3dSection = fmtSolidSection


def fmtShellSection(section, setname):
    """Format a SHELL SECTION keyword.

    Parameters: see `func:fmtSolidSection`.

    Recognized keys in the section dict:

    - thickness
    - offset (opt): for contact surface SPOS or 0.5, SNEG or -0.5
    - transverseshearstiffness (opt):
    - poisson (opt): ?? CLASH WITH MATERIAL ??
    - thicknessmodulus (opt):
    """
    cmd = Command('SHELL SECTION',ELSET=setname,MATERIAL=section.matname,options=section.options,extra=section.extra)

    if section.offset is not None:
        cmd.add(offset=section.offset)
    if section.thicknessmodulus is not None:
        cmd.add(thickness_modulus=float(section.thicknessmodulus))
    if section.poisson is not None:
        cmd.add(poisson=float(section.poisson))
    if section.thickness is not None:
        cmd.add(data=[ float(section.thickness) ])

    out = cmd.out

    if section.transverseshearstiffness is not None:
        out += Command('TRANSVERSE SHEAR STIFFNESS',data=[section.transverseshearstiffness]).out

    return out


def fmtMembraneSection(section, setname):
    """Format a MEMBRANE SECTION keyword.

    Parameters: see `func:fmtSolidSection`.

    Recognized keys in the section dict:

    - thickness: float

    """
    cmd = Command('MEMBRANE SECTION',ELSET=setname,MATERIAL=section.matname,data = [ float(section.thickness) ],options=section.options,extra=section.extra)
    return cmd.out


def fmtSurfaceSection(section, setname):
    """Format a SURFACE SECTION keyword.

    Parameters: see `func:fmtSolidSection`.

    Recognized keys in the section dict:

    - density (opt): float

    """
    cmd = Command('SURFACE SECTION',ELSET=setname)
    if section.density:
        cmd.add(density=float(section.density))
    return cmd.out


def fmtBeamSection(section, setname):
    """Format a beam section for the named element set.

    Note that there are two Beam section keywords:
    - BEAM SECTION
    - BEAM GENERAL SECTION: this is formatted by a separate function,
      currently selected if no material name is specified

    Parameters: see `func:fmtSolidSection`.

    The following holds for the BEAM SECTION:

    Recognized keys:

    - sectiontype: 'ARBITRARY', 'BOX', 'CIRC', 'HEX', 'I', 'L', 'PIPE',
      'RECT', 'TRAPEZOID' or 'ELBOW'
    - material:
    - data: list of tuples: data corresponding with the sectiontype.
      See Abaqus manual.
    - transverseshearstiffness (opt):

    """
    if section.matname is None:
        return fmtGeneralBeamSection(section, setname)

    cmd = Command('BEAM SECTION',ELSET=setname,MATERIAL=section.matname,SECTION=section.sectiontype,data=section.data,options=section.options,extra=section.extra)

    if section.poisson is not None:
        cmd.add(POISSON=section.poisson)

    out = cmd.out

    if section.transverseshearstiffness is not None:
        out += Command('TRANSVERSE SHEAR STIFFNESS',data=[section.transverseshearstiffness]).out

    return out


def fmtGeneralBeamSection(section, setname):
    """Format a general beam section for the named element set.

    This specifies a beam section when numerical integration over the section
    is not required and the material constants are specified directly.
    See also `func:fmtBeamSection`.

    Parameters: see `func:fmtSolidSection`.

    Recognized keys:

    - all sectiontypes:

      - sectiontype (opt): 'GENERAL' (default), 'CIRC' or 'RECT'
      - data (opt): list of tuples: section data (see Abaqus Manual).
        For some sections, the data may be specified by other arguments
        instead (see below).
      - density (opt): density of the material (required in Abaqus/Explicit)
      - transverseshearstiffness (opt):

    Data specifying keys (only used if 'data' is not specified):

    - sectiontype GENERAL:

      - cross_section
      - moment_inertia_11
      - moment_inertia_12
      - moment_inertia_22
      - torsional_constant

    - sectiontype CIRC:

      - radius

    - sectiontype RECT:

      - width, height

    - sectiontype GENERAL, CIRC or RECT:
      - orientation (opt): a vector with the direction cosines of the 1 axis
      - young_modulus
      - shear_modulus or poisson_ratio

    """
    sectiontype = section.sectiontype.upper()
    if section.data is None:
        if sectiontype == 'CIRC':
            data = ( section.radius, )
        elif sectiontype == 'RECT':
            data = ( section.width, section.height)
        elif sectiontype == 'GENERAL':
            data = ( section.cross_section, section.moment_inertia_11, section.moment_inertia_12, section.moment_inertia_22, section.torsional_constant )
        else:
            raise ValueError("For sectiontype '%s', a data field should be specified.")
        data = [data]

        if section.orientation is not None:
            data.append(section.orientation)
        else:
            data.append( (' ',) )

        if section.shear_modulus is None and section.poisson_ratio is not None:
            section.shear_modulus = section.young_modulus / 2. / (1.+float(section.poisson_ratio))
        data.append( (section.young_modulus, section.shear_modulus) )

    else:
        # User should specify all data
        data = section.data

    cmd = Command('BEAM GENERAL SECTION',ELSET=setname,SECTION=sectiontype,data=data,options=section.options,extra=section.extra)

    if section.density:
        cmd.add(density=section.density)

    out = cmd.out

    if section.transverseshearstiffness is not None:
        out += Command('TRANSVERSE SHEAR STIFFNESS',data=[section.transverseshearstiffness]).out

    return out


def fmtFrameSection(section,setname):
    """Format a frame section for the named element set.

    Parameters: see `func:fmtSolidSection`.

    Recognized keys:

    - all sectiontypes:

      - sectiontype (opt): 'GENERAL' (default), 'CIRC' or 'RECT'
      - young_modulus
      - shear_modulus
      - density (opt): density of the material
      - yield_stress (opt): yield stress of the material
      - orientation (opt): a vector with the direction cosines of the 1 axis

    - sectiontype GENERAL:

      - cross_section
      - moment_inertia_11
      - moment_inertia_12
      - moment_inertia_22
      - torsional_constant

    - sectiontype CIRC:

      - radius

    - sectiontype RECT:

      - width
      - height

    """
    sectiontype = section.sectiontype.upper()
    if section.data is None:
        if sectiontype == 'GENERAL':
            data = ( section.cross_section, section.moment_inertia_11, section.moment_inertia_12, section.moment_inertia_22, section.torsional_constant )
        else:
            raise ValueError("For sectiontype '%s', a data field should be specified.")
        data = [data]

        if section.orientation is not None:
            data.append(section.orientation)
        else:
            data.append( (' ',) )

        if section.shear_modulus is None and section.poisson_ratio is not None:
            section.shear_modulus = section.young_modulus / 2. / (1.+float(section.poisson_ratio))
        data.append( (section.young_modulus, section.shear_modulus) )

    else:
        # User should specify all data
        data = section.data

    cmd = Command('FRAME SECTION',ELSET=setname,SECTION=sectiontype,data=data,options=section.options,extra=section.extra)

    if section.density:
        cmd.add(density=float(section.density))
    if section.yield_stress:
        cmd.add('plastic defaults',yield_stress=float(section.yield_stress))

    return cmd.out


def fmtTrussSection(section,setname):
    """Format a truss section for the named element set.

    Parameters: see `func:fmtSolidSection`.

    Recognized keys:

    - all sectiontypes:

      - sectiontype (opt): 'GENERAL' (default), 'CIRC' or 'RECT'
      - material

    - sectiontype GENERAL:

      - cross_section

    - sectiontype CIRC:

      - radius

    - sectiontype RECT:

      - width
      - height

    """
    sectiontype = section.sectiontype.upper()
    if sectiontype == 'CIRC':
        cross_section = float(section.radius)**2*pi
    elif sectiontype == 'RECT':
        cross_section = float(section.width)*float(section.height)
    else:
        cross_section = float(section.cross_section)

    cmd = Command('SOLID SECTION',ELSET=setname,MATERIAL=section.matname,data=[cross_section],options=section.options,extra=section.extra)
    return cmd.out


def fmtConnectorSection(section, setname):
    """Format a connector section.

    Parameters: see `func:fmtSolidSection`.

    Recognized keys:

    - sectiontype: 'JOIN', 'HINGE', ...
    - behavior (opt): connector behavior name
    - orientation (opt): connector orientation
    - elimination (opt): 'NO' (default), 'YES'

    """
    cmd = Command('CONNECTOR SECTION',ELSET=setname,data=[section.sectiontype],options=section.options,extra=section.extra)

    if section.behavior is not None:
        cmd.add(behavior=section.behavior)

    if section.elimination is not None:
        cmd.add(elimination=section.elimination)

    return cmd.out


def fmtSpringOrDashpot(eltype, section, setname):
    """Format a section of type spring or dashpot.

    Parameters (see also `func:fmtSolidSection`):

    - `eltype`: 'SPRING' or 'DASHPOT'

    Recognized keys:

    - stiffness: float: spring or dashpot stiffness. For SPRING type, this
      is the force per relative displacement; for DASHPOT type, the force
      per relative velocity.

    """
    cmd = Command(eltype,elset=setname,data=['\n%s' % float(section.stiffness)],options=section.options,extra=section.extra)
    return cmd.out


def fmtSpringSection(section, setname):
    """Shorthand for `fmtSpringOrDashpot("SPRING", section, setname)`"""
    return fmtSpringOrDashpot("SPRING", section, setname)


def fmtDashpotSection(section, setname):
    """Shorthand for `fmtSpringOrDashpot("SPRING", section, setname)`"""
    return fmtSpringOrDashpot("DASHPOT", section, setname)


def fmtMassSection(section,setname):
    """Format a section of type mass.

    Parameters: see `func:fmtSolidSection`

    Recognized keys:

    - mass: float: mass magnitude

    """
    cmd = Command('MASS',elset=setname,data=[float(section.mass)],options=section.options,extra=section.extra)
    return cmd.out


def fmtInertiaSection(section,setname):
    """Format a section of type inertia.

    Parameters: see `func:fmtSolidSection`

    Recognized keys:

    - inertia: list of six floats: [I11, I22, I33, I12, I13, I23]

    """
    cmd = Command('ROTARY INERTIA',elset=setname,data=map(float,section.inertia),options=section.options,extra=section.extra)
    return cmd.out


def fmtRigidSection(section,setname):
    """Format rigid body sectiontype.

    Parameters: see `func:fmtSolidSection`

    Recognized keys:

    - refnode: string (set name) or integer (node number)
    - density (opt): float:
    - density (opt): float:

    """
    refnode = section.refnode
    if isInt(refnode):
        refnode += + 1  # increment for Abaqus base 1 node numbering

    cmd = Command('RIGID BODY',elset=setname,refnode=section.refnode,options=section.options,extra=section.extra)
    if section.density is not None:
        cmd.add(density=section.density)
    if section.thickness is not None:
        cmd.add(data=[float(section.thickness)])
    return cmd.out


#########################################################
#
#  OTHER
#
#########################################################


def fmtTransform(csys,setname):
    """Format a coordinate transfor for the given set.

    - `setname` is the name of a node set
    - `csys` is a CoordSystem.
    """
    cmd = Command('TRANSFORM',nset=setname,type=csys.sys,data=csys.data)
    return cmd.out


def fmtOrientation(prop):
    """Format the orientation.

    Optional:

    - definition
    - system: coordinate system
    - a: a first point
    - b: a second point
    """
    out = ''
    for p in prop:
        out += "*ORIENTATION, NAME=%s" % (p.name)
        if p.definition is not None:
            out += ", definition=%s" % p.definition
        if p.system is not None:
            out += ", SYSTEM=%s" % p.system
        out += "\n"
        if p.a is not None:
            data = tuple(p.a)
            if p.b is not None:
                data += tuple(p.b)
            out += fmtData1d(data) + '\n'
        else:
            raise ValueError("Orientation needs at least point a")
    return out


# TODO : update list of abaqus surface types

def fmtSurface(prop):
    """Format the surface definitions.

    Parameters:

    - `prop`: a property record containing the key `surftype`.

    Recognized keys:

    - set: string, list of strings or list of integers.
        - string : name of an existing set.
        - list of integers: list of elements/nodes of the surface.
        - list of strings: list of existing set names.

    - name: string. The surface name.

    - surftype: string. Can assume values 'ELEMENT' or 'NODE' or other abaqus
        surface types.

    - label (opt): string, or a list of strings storing the abaqus face or edge identifier
        It is only required for surftype == 'ELEMENT'.

    - options (opt): string that is added as is to the command line.

    Example:

      # This allow specifying a surface from an existing set of surface elements
      P.Prop(set='quad_set'  ,name='quad_surface',surftype='element',label='SPOS')

      # This allow specifying a surface from already existing sets of brick elements
      # using different label identifiers per each set

      P.Prop(set=['hex_set1, 'hex_set2']  ,name='quad_surface',surftype='element',label=['S1','S2'])

       #This allows to use different identifiers for the different elements in the surface
       Prop(name='mysurf',set=[0,1,2,6],surftype='element',label=['S1','S2','S1','S3')

       will get exported to Abaqus as::

       *SURFACE, NAME=mysurf, TYPE=element
        1, S1
        2, S2,
        3, S1
        7, S3
    """
    out = ''
    for p in prop:
        cmd = "SURFACE, NAME=%s, TYPE=%s" % (p.name, p.surftype)
        out += fmtKeyword(cmd,options=p.options)
        if isinstance(p.set,str):
            p.set = asarray([p.set]) # handles single string for set name
        for i, e in enumerate(p.set):
            if e.dtype.kind != 'S':
                e += 1
            if 'label' not in p:
                out += "%s\n" % e
            elif isinstance(p.label, str):
                out += "%s, %s\n" % (e, p.label)
            elif isinstance(p.label, list):
                out += "%s, %s\n" % (e, p.label[i])
            else:
                raise ValueError("Data type %s not allowed for key 'label' " % (type(p.label)))
    return out


def fmtAnalyticalSurface(prop):
    """Format the analytical surface rigid body.

    Required:

    - nodeset: refnode.
    - name: the surface name
    - surftype: 'ELEMENT' or 'NODE'
    - label: face or edge identifier (only required for surftype = 'NODE')

    Example::

      P.Prop(name='AnalySurf', nodeset = 'REFNOD', analyticalsurface='')

    """
    out = ''
    for p in prop:
        out += "*RIGID BODY, ANALYTICAL SURFACE = %s, REFNOD=%s\n" % (p.name, p.nodeset)
    return out


def fmtSurfaceInteraction(prop):
    """Format the interactions.

    Required:

    - name

    Optional:

    - cross_section (for node based interaction)
    - friction : friction coeff or 'rough'
    - surface behavior: no separation
    - surface behavior: pressureoverclosure
    """
    out = ''
    for p in prop:
        out += "*Surface Interaction, name=%s\n" % (p.name)
        if hasattr(p, 'cross_section') and p.cross_section is not None:
            out += "%s\n" % p.cross_section
        if p.friction is not None:
            if p.friction['data'][0] == 'rough':
                out += "*FRICTION, ROUGH\n"
            else:
                out += "*FRICTION\n%s\n" % float(p.friction['data'][0])
        if p.surfacebehavior:
            out += "*Surface Behavior"
            print("writing Surface Behavior")
            if p.noseparation == True:
                out += ", no separation"
            if p.pressureoverclosure:
                if p.pressureoverclosure[0] == 'soft':
                    out += ", pressure-overclosure=%s\n" % p.pressureoverclosure[1]
                    out += "%s" % fmtData1d(p.pressureoverclosure[2:]) + '\n'
                elif p.pressureoverclosure[0] == 'hard':
                    out += ", penalty=%s\n" % p.pressureoverclosure[1]
                    out += "%s" % fmtData1d(p.pressureoverclosure[2:]) + '\n'
            else:
                out += "\n"
    return out


def fmtContact(prop):
    """Format a contact property record.

    Parameters:

    - `prop`: a Property record having a key 'contact'

    Recognized keys:

    - contact: string, one of 'GENERAL' or 'PAIR'
    - interaction: string, the name of a surface interaction

    For 'GENERAL' contact:

    - include: tuple or list of tuples (surf1,surf2). surf1 and surf2 are
      the names of defined surfaces or an empty string. If surf1 is empty,
      a surface containing all exterior surfaces defined in the model is used.
      If surf2 is empty, it is equal to surf1 a case of self-contact results.
      If both are empty, self contact between all surfaces is modeled.

    - exclude (opt): tuple or list of tuples (surf1,surf2). Specifies names of
      surfaces on which no contact is to be modeled.

    For 'PAIR' contact:

    - include: tuple or list of tuples (slave,master).
      slave and master are the names of defined surfaces.
      Each tuple can optionally contain one or two more values, with the
      orientation of the tangential slip directions for the slave, resp.
      master surface. They are strings with the name of defined orientations.

    Examples:
      >>> PDB = PropertyDB()
      >>> p1 = PDB.Prop(contact='pair',include=('s1','m1'),interaction='i1')
      >>> print(fmtContact(p1))
      *CONTACT PAIR, INTERACTION=I1
      s1, m1
      <BLANKLINE>

      >>> p2 = PDB.Prop(contact='pair',include=[('s1','m1'),('s2','m2')],interaction='i1')
      >>> print(fmtContact(p2))
      *CONTACT PAIR, INTERACTION=I1
      s1, m1
      s2, m2
      <BLANKLINE>

      >>> g1 = PDB.Prop(contact='general',include=('s1','m1'),interaction='i1')
      >>> print(fmtContact(g1))
      *CONTACT
      *CONTACT INCLUSIONS
      s1, m1
      *CONTACT PROPERTY ASSIGNMENT
      s1, m1, i1
      <BLANKLINE>

      >>> g2 = PDB.Prop(contact='general',include=[('s1','m1'),('s2','m2')],interaction='i1')
      >>> print(fmtContact(g2))
      *CONTACT
      *CONTACT INCLUSIONS
      s1, m1
      s2, m2
      *CONTACT PROPERTY ASSIGNMENT
      s1, m1, i1
      s2, m2, i1
      <BLANKLINE>

    """
    contact = prop.contact.upper()

    if contact=='GENERAL':

        out = fmtKeyword('CONTACT',prop.options)
        out += fmtKeyword('CONTACT INCLUSIONS',data=prop.include)
        if 'exclude' in prop:
            out += fmtKeyword('CONTACT EXCLUSIONS',data=prop.exclude)
        data = prop.include
        if not isinstance(data,list):
            data = [ data ]
        data = [ d + (prop.interaction,) for d in data ]
        out += fmtKeyword('CONTACT PROPERTY ASSIGNMENT',data=data)

    elif contact=='PAIR':

        options = fmtOptions(interaction=prop.interaction)
        out = fmtKeyword('CONTACT PAIR'+options,options=prop.options,data=prop.include)

    else:
        raise ValueError('Invalid value for contact parameter')

    if 'extra' in prop:
        out += extra

    return out


# TODO: BAD DOCSTRING

def fmtGeneralContact(prop):
    """_Format the general contact.

    Only implemented on model level

    Required:

    - interaction: interaction properties: name or Dict

    Optional:

    - Exclusions (exl)
    - Extra (extra).

    Example::

        extra = "*CONTACT CONTROLS ASSIGNMENT, TYPE=SCALE PENALTY\\n, , 1.e3\\n"

    Example::

      P.Prop(generalinteraction=Interaction(name ='contactprop1'),exl =[
      ['surf11', 'surf12'],['surf21',surf22]])

    """
    out = ''
    for p in prop:
        if isinstance(p.generalinteraction, str):
            intername = p.generalinteraction
        else:
            intername = p.generalinteraction.name
            out += fmtSurfaceInteraction([p.generalinteraction])
        out += "*Contact\n"
        out += "*Contact Inclusions, ALL EXTERIOR\n"
        if p.exl:
            out += "*Contact Exclusions\n"
            for ex in p.exl:
                out += "%s, %s\n" % (ex[0], ex[1])
        out += "*Contact property assignment\n"
        out += ", , %s\n" % intername
        if p.extra:
            out += p.extra
    return out


def fmtContactPair(prop):
    """Format the contact pair.

    Required:

    - master: master surface
    - slave: slave surface
    - interaction: interaction properties : name or Dict

    Example::

      P.Prop(name='contact0',interaction=Interaction(name ='contactprop',
      surfacebehavior=True, pressureoverclosure=['hard','linear',0.0, 0.0, 0.001]),
      master ='quadtubeINTSURF1',  slave='hexstentEXTSURF', contacttype='NODE TO SURFACE')

    """
    out = ''
    for p in prop:
        if isinstance(p.interaction, str):
            intername = p.interaction
        else:
            intername = p.interaction.name
            out += fmtSurfaceInteraction([p.interaction])

        out += "*Contact Pair, interaction=%s" % intername
        if p.contacttype is not None:
            out += ", type=%s\n" % p.contacttype
        else:
            out+="\n"
        out += "%s, %s\n" % (p.slave, p.master)
    return out


def fmtConstraint(prop):
    """Format Tie constraint

    Required:

    - name
    - adjust (yes or no)
    - slave
    - master

    Optional:

    - type (surf2surf, node2surf)
    - positiontolerance
    - no rotation
    - tiednset (it cannot be used in combination with positiontolerance)

    Example::

      P.Prop(constraint='1', name = 'constr1', adjust = 'no',
      master = 'hexstentbarSURF', slave = 'hexstentEXTSURF',type='NODE TO SURFACE')

    """
    out =''
    for p in prop:
        out +="*Tie, name=%s, adjust=%s" % (p.name, p.adjust)
        if p.type is not None:
            out+=",type = %s" % p.type
        if p.positiontolerance is not None:
            out+=", position tolerance = %s" % (float(p.positiontolerance))
        if p.norotation == True:
            out+=", NO ROTATION"
        if p.tiednset is not None:
            out+=",TIED NSET = %s" % p.tiednset
        out +="\n"
        out +="%s, %s\n" % (p.slave, p.master)
    return out


def fmtInitialConditions(prop):
    """Format initial conditions

    Required:

    - type
    - nodes
    - data

    Example::

      P.Prop(initialcondition='', nodes ='Nall', type = 'TEMPERATURE', data = 37.)
    """

    for p in prop:
        out ="*Initial Conditions, type = %s\n" % p.type
        out +="%s,%.2f\n" % (p.nodes, p.data)
    return out


def fmtEquation(prop):
    """Format multi-point constraint using an equation

    Required:

    - equation: list of tuples (node,dof,coeff), where

      - node: is a node number or node set name
      - dof: is the number of the degree of freedom (0 based)
      - coeff: is the coefficient for this variable in the equation

    Example::

      >>> P = PropertyDB()
      >>> eq1 = P.Prop(equation=[(9,1,1.),(32,2,-1.)])
      >>> eq2 = P.Prop(equation=[('seta',0,1)])

      The first equation forces the Z-displacement of node 32 to be equal
      to the Y-displacement of node 9. The second forces the sum of the
      X-displacement of all nodes in node set 'seta' to be equal to zero.

      >>> print(fmtEquation(eq1)+fmtEquation(eq2))
      *EQUATION
      2
      10, 2, 1.0
      33, 3, -1.0
      *EQUATION
      1
      seta, 1, 1
      <BLANKLINE>

    """
    nofs = 1
    data = [ (len(prop.equation),) ]
    for i in prop.equation:
        if isInt(i[0]):
            node = i[0] + nofs
        else:
            node = i[0]
        dof = i[1] + 1
        data.append( (node,dof,i[2]) )
    cmd = Command('EQUATION',data=data)
    return cmd.out


def fmtInertia(prop):
    """Format rotary inertia

    Required:

    - inertia : inertia tensor i11, i22, i33, i12, i13, i23
    - set : name of the element set on which inertia is applied
    """
    cmd = Command('ROTARY INERTIA',elset=prop.name,data=prop.inertia)
    return cmd.out


def fmtBoundary(prop):
    """Format nodal boundary conditions.

    prop is a node property record having the 'bound' key.

    Recognized keys:

    - bound : either of:
      - a string, representing a standard set of boundary conditions
      - a list of 6 integer values (0 or 1) corresponding with the 6
        degrees of freedom UX,UY,UZ,RX,RY,RZ. The dofs corresponding
        to the 1's will be restrained (given a value 0.0).
      - a list of tuples (dofid, value) : this allows for nonzero
        boundary values to be specified. NOTE: this can also be
        achieved by a 'displ' keyword (see writeDisplacements) and
        that is the prefered way of specifying nonzero boundary conditions.

    - op (opt): 'MOD' (default) or 'NEW'. By default, the boundary conditions
      are applied as a modification of the existing boundary conditions, i.e.
      initial conditions and conditions from previous steps remain in effect.
      The user can set op='NEW' to remove the previous conditions. This will
      remove ALL conditions of the same type.

    - ampl (opt): string: specifies the name of an amplitude that is to be
      multiplied with the values to have the time history of the variable.
      Only relevant if bound specifies nonzero values. Its use is
      discouraged (see above).

    - options (opt): string that is added as is to the command line.

    Examples::

      # The following are quivalent
      P.nodeProp(tag='init',set='setA',name='pinned_nodes',bound='pinned')
      P.nodeProp(tag='init',set='setA',name='pinned_nodes',bound=[1,1,1,0,0,0])

      # this is possible, but discouraged
      P.nodeProp(tag='init',set='setB',name='forced_displ',bound=[(1,3.0)])
      # it is better to use:
      P.nodeProp(tag='step0',set='setB',name='forced_displ',displ=[(1,3.0)])

    """
    setname = nsetName(prop)
    if isinstance(prop.bound, str):
        data = [setname, prop.bound]
    elif isInt(prop.bound[0]):
        data = []
        for b in range(6):
            if prop.bound[b]==1:
                data.append((setname, b+1))
    else:
        data = []
        for b in prop.bound:
            dof = b[0]+1
            data.append((setname, dof, dof, b[1]))
    cmd = Command('BOUNDARY',data=data,options=prop.options,extra=prop.extra)
    if prop.op is not None:
        cmd.add(op=prop.op)
    if prop.ampl is not None:
        cmd.add(amplitude=prop.ampl)

    return cmd.out

#########################################################
#
#  OUTPUT FUNCTIONS
#
#########################################################


## The section data are limited in size and are
## first formatted and then written
################################################

def writeSection(fil, prop):
    """Write an element section.

    prop is an element property record with a section and eltype attribute
    """
    utils.warn('warn_fe_abq_write_section')
    print("WRITE SECTION %s" % prop)
    out = ""
    setname = esetName(prop)
    section = prop.section
    eltype = prop.eltype.upper()

    mat = section.material
    if mat is not None:
        # Provide default matname ???
        #if mat.name is None:

        if mat.name not in materialswritten:
            print(" Writing material %s" % mat.name)
            fil.write(fmtMaterial(mat))

        section.matname = mat.name

    elclass = elementClass(eltype)
    formatter = globals().get("fmt"+elclass.capitalize()+'Section',"fmtAnySection")
    if not callable(formatter):
        pf.warning('Sorry, element type %s is not yet supported' % eltype)
        return

    fil.write(formatter(section,setname))

## The following output sections with possibly
## large data sets are written directly to file
################################################

def writeNodes(fil,nodes,name='Nall',nofs=1):
    """Write nodal coordinates.

    The nodes are added to the named node set.
    If a name different from 'Nall' is specified, the nodes will also
    be added to a set named 'Nall'.
    The nofs specifies an offset for the node numbers.
    The default is 1, because Abaqus numbering starts at 1.
    """
    fil.write('*NODE, NSET=%s\n' % name)
    for i, n in enumerate(nodes):
        fil.write("%d, %14.6e, %14.6e, %14.6e\n" % ((i+nofs,)+tuple(n)))
    if name != 'Nall':
        fil.write('*NSET, NSET=Nall\n%s\n' % name)


#
# Translation of element connectivity from pyFormex to Abaqus
#
# TODO: Shouldn't the key be the Abaqus element name??
#
AbqConnectivity = {
    'tet10': (0,1,2,3,4,7,5,6,9,8)
    }


def writeElems(fil,elems,type,name='Eall',eid=None,eofs=1,nofs=1):
    """Write element group of given type.

    elems is the list with the element node numbers.
    The elements are added to the named element set.
    If a name different from 'Eall' is specified, the elements will also
    be added to a set named 'Eall'.
    The eofs and nofs specify offsets for element and node numbers.
    The default is 1, because Abaqus numbering starts at 1.
    If eid is specified, it contains the element numbers increased with eofs.
    """
    fil.write('*ELEMENT, TYPE=%s, ELSET=%s\n' % (type.upper(), name))
    nn = elems.shape[1]
    fmt = '%d' + nn*', %d' + '\n'
    if eid is None:
        eid = arange(elems.shape[0])
    else:
        eid = asarray(eid)
    for i, e in zip(eid+eofs, elems+nofs):
        fil.write(fmt % ((i,)+tuple(e)))
    writeSet(fil, 'ELSET', 'Eall', [name])


def writeSet(fil,type,name,set,ofs=1):
    """Write a named set of nodes or elements (type=NSET|ELSET)

    `set` : an ndarray. `set` can be a list of node/element numbers,
    in which case the `ofs` value will be added to them,
    or a list of names the name of another already defined set.
    """
    fil.write("*%s,%s=%s\n" % (type, type, name))
    set = asarray(set)
    fl = False
    if set.dtype.kind == 'S':
        # we have set names
        for i in set:
            fil.write('%s\n' % i)
    else:
        for i,j in enumerate(set+ofs):
            fil.write("%d," % j)
            if not fl:
                fl = True
            if (i+1)%16==0:
                fil.write("\n")
                fl = False
    if fl:
        fil.write("\n")



def writeDistribution(fil,prop):
    """Write a distribution table.

    Parameters:

    - `prop`: a Property record having with the key `distribution`.

    Recognized keys:

    - distribution: string. Name of the distribution.

    - location:string. can assume values 'ELEMENT','NODE' or 'NONE'

    - table: arraylike. The array needs to be passed as should be written in the
        abaqus data line. Every row is a new line and it is in the form [element_or_node_number,data1,data2, ...].
        NB For the first line used in Abaqus as default, the element_or_node_number should be an empty string.

    - format: list of strings. Every string is  an abaqus `word` to be used in the distribution table.
        See Abaqus documentation for allowed `words`.

    - options (opt): string that is added as is to the command line.

    The name  of the distribution table (required) is derived from the name of the distribution.

    """

    nameTable = prop.name+'_TABLE' # automatically create a distribution table name
    cmd = 'DISTRIBUTION TABLE, NAME=%s\n' %nameTable
    fil.write(fmtKeyword(cmd,data=prop.format))

    cmd = 'DISTRIBUTION, NAME=%s, LOCATION=%s, TABLE=%s\n'%(prop.distribution,prop.location,nameTable)
    fil.write(fmtKeyword(cmd,prop.options,data=prop.table))

#
# TODO: should we remove option of specifying nonzero bound values?
#


def writeDisplacements(fil,prop,btype):
    """Write prescribed displacements, velocities or accelerations

    Parameters:

    - `prop` is a list of node property records containing one (or more)
      of the keys 'displ', 'veloc' 'accel'.
    - `btype` is the boundary type: one of 'displacement', 'velocity' or
      'acceleration'

    Recognized property keys:

    - displ, veloc, accel: each is optional and is a list of tuples
      (dofid, value), for respectively the displacement, velocity or
      acceleration. A special value 'reset' may also be specified to
      reset  the prescribed condition for these variables.

    - op (opt): 'MOD' (default) or 'NEW'. By default, the boundary conditions
      are applied as a modification of the existing boundary conditions, i.e.
      initial conditions and conditions from previous steps remain in effect.
      The user can set op='NEW' to remove the previous conditions. This will
      remove ALL conditions of the same type.

    - ampl (opt): string: specifies the name of an amplitude that is to be
      multiplied with the values to have the time history of the variable.

    - options (opt): string that is added to the command line.

    """
    for p in prop:
        setname = nsetName(p)
        cmd = "BOUNDARY, TYPE=%s" % btype.upper()
        if p.op is not None:
            cmd += ", OP=%s" % p.op
        if p.ampl is not None:
            cmd += ", AMPLITUDE=%s" % p.ampl
        fil.write(fmtKeyword(cmd,options=p.options))

        data = p[btype[:5]]
        if data:
            for v in data:
                dof = v[0]+1
                fil.write("%s, %s, %s, %s\n" % (setname, dof, dof, v[1]))

        if p.extra:
            fil.write(p.extra)


def fmtLoad(key,prop):
    """Format a load input block.

    Parameters:

    - `key`: load type, one of: 'cload', 'dload' or 'dsload'
    - `prop`: a node property record containing the specified key.

    Recognized keys:
    - op (opt): string: 'MOD' or 'NEW'. See `func:writeDisplacements`.
    - ampl (opt): string: amplitude name. See `func:writeDisplacements`.
    - options (opt): string: see `func:fmtKeyWord`
    - extra (opt): string: see `func:fmtKeyWord`

    For load type 'cload':

    - set: node set on which to apply the load
    - cload: list of tuples (dofid, magnitude)

    For load type 'dload':

    - set: element set on which to apply the load
    - dload: ElemLoad or data

    For load type 'dsload':

    - surface: string: name of surface on which to apply the load
    - dsload: ElemLoad or data

    """
    cmd = key.upper()

    if cmd == 'CLOAD':
        setname = nsetName(prop)
        data = [ (setname, v[0]+1, v[1]) for v in prop.cload ]

    elif cmd == 'DLOAD':
        setname = esetName(prop)
        if isinstance(prop.dload,ElemLoad):
            data = [setname, prop.dload.label, prop.dload.value]
        else:
            data = prop.dload

    elif cmd == 'DSLOAD':
        if isinstance(prop.dload,ElemLoad):
            data = [setname, prop.dsload.label, prop.dsload.value]
        else:
            data = prop.dsload

    if 'op' in prop:
        cmd += ", OP=%s" % prop.op
    if 'ampl' in prop:
        cmd += ", AMPLITUDE=%s" % prop.ampl

    return fmtKeyword(cmd,prop.options,data,prop.extra)


#######################################################
# General model data
#


#
# TODO:
#   This is TOO complex. We should restrict the way users can specify things.
#   Also, docstring does not compile in sphinx
#

class Interaction(Dict):
    """_A Dict for setting surface interactions

    Required:

    - `name`: str name of the surface interaction

    Optional: (congrats to anyone understanding this)

    - `friction`: Dict , float, or arraylike. If Dict needs to store all
      friction options as 'abaqus_option_name': 'value'.
      An empty string can be set for parameters with no value.
      If float or arraylike a default friction keyword Dict
      is created with nop other *friction options.
    - `surfacebehavior`: Dict storing all *SURFACE BEHAVIOUR options as
      'abaqus_option_name': 'value'.
      An empty string can be set for parameters with no value.
      If float or arraylike a default friction keyword Dict
      is created with nop other *friction options.
    - `surfaceinteraction`: Dict storing all *SURFACE INTERACTIONS options
      as 'abaqus_option_name': 'value'.
      An empty string can be set for parameters with no value.
      If float or arraylike a default friction keyword Dict
      is created with nop other *friction options.
    - `extra`: Dict or list of Dict of any additional abaqus keyword lines
      to be passed via fmtExtra.
      See fmtExtra for more details.

    """
    def __init__(self, name, friction=None, surfacebehavior=None, surfaceinteraction=None, extra=None):
        utils.warn('warn_Interaction_changed')

        self.name = name

        self.friction=None
        if friction is not None:
            if isinstance(friction,dict):
                self.friction=friction
            else:
                if isinstance(friction,(int,float)):
                    friction=asarray([friction],float)
                self.friction=Dict()
                self.friction.data=friction

        self.surfacebehavior = surfacebehavior
        self.surfaceinteraction=surfaceinteraction
        self.extra = extra

def writeAmplitude(fil, prop):
    """Write Amplitude.

    Parameters:

    -`prop`: list of property records having an attribute `amplitude`.

    Recognized keys:

    - name: string. The name of the amplitude.

    - amplitude: class Amplitude (see plugins.property).

    - options (opt): string that is added as is to the command line.


    Examples:

    P=PropertyDB()
    t=[0,1]
    a=[0,0.5]
    amp = Amplitude(data=column_stack([t,a]))
    P.Prop(amplitude=amp,name='ampl1',options='definition=TABULAR,smooth=0.1')

    """

    for p in prop:
        cmd = "AMPLITUDE, NAME=%s" % (p.name)
        fil.write(fmtKeyword(cmd,p.options,asarray(p.amplitude.data).ravel()))

### Output requests ###################################
# Output: goes to the .odb file (for postprocessing with Abaqus/CAE)
# Result: goes to the .fil file (for postprocessing with other means)
#######################################################


def writeNodeResult(fil,kind,keys,set='Nall',output='FILE',freq=1,
                    globalaxes=False,lastmode=None,
                    summary=False,total=False):
    """ Write a request for nodal result output to the .fil or .dat file.

    - `keys`: a list of NODE output identifiers
    - `set`: a single item or a list of items, where each item is either
      a property number or a node set name for which the results should
      be written
    - `output` is either ``FILE`` (for .fil output) or ``PRINT`` (for .dat
      output)(Abaqus/Standard only)
    - `freq` is the output frequency in increments (0 = no output)

    Extra arguments:

    - `globalaxes`: If 'YES', the requested output is returned in the global
      axes. Default is to use the local axes wherever defined.

    Extra arguments for output=``PRINT``:

    - `summary`: if True, a summary with minimum and maximum is written
    - `total`: if True, sums the values for each key

    'Remark that the `kind` argument is not used, but is included so that we can
    easily call it with a `Results` dict as arguments.'
    """
    if isinstance(set, str) or isInt(set):
        set = [ set ]
    for i in set:
        if isInt(i):
            setname = Nset(str(i))
        else:
            setname = i
        s = "*NODE %s, NSET=%s" % (output, setname)
        if freq != 1:
            s += ", FREQUENCY=%s" % freq
        if globalaxes:
            s += ", GLOBAL=YES"
        if lastmode is not None:
            s += ", LAST MODE=%s" % lastmode
        if output=='PRINT':
            if summary:
                s += ", SUMMARY=YES"
            if total:
                s += ", TOTAL=YES"
        fil.write("%s\n" % s)
        for key in keys:
            fil.write("%s\n" % key)


def writeElemResult(fil,kind,keys,set='Eall',output='FILE',freq=1,
                    pos=None,
                    summary=False,total=False):
    """ Write a request for element result output to the .fil or .dat file.

    - `keys`: a list of ELEMENT output identifiers
    - `set`: a single item or a list of items, where each item is either
      a property number or an element set name for which the results should
      be written
    - `output` is either ``FILE`` (for .fil output) or ``PRINT`` (for .dat
      output)(Abaqus/Standard only)
    - `freq` is the output frequency in increments (0 = no output)

    Extra arguments:

    - `pos`: Position of the points in the elements at which the results are
      written. Should be one of:

      - 'INTEGRATION POINTS' (default)
      - 'CENTROIDAL'
      - 'NODES'
      - 'AVERAGED AT NODES'

      Non-default values are only available for ABAQUS/Standard.

    Extra arguments for output='PRINT':

    - `summary`: if True, a summary with minimum and maximum is written
    - `total`: if True, sums the values for each key

    Remark: the ``kind`` argument is not used, but is included so that we can
    easily call it with a Results dict as arguments
    """
    if isinstance(set, str) or isInt(set):
        set = [ set ]
    for i in set:
        if isInt(i):
            setname = Eset(str(i))
        else:
            setname = i
        s = "*EL %s, ELSET=%s" % (output, setname)
        if freq != 1:
            s += ", FREQUENCY=%s" % freq
        if pos:
            s += ", POSITION=%s" % pos
        if output=='PRINT':
            if summary:
                s += ", SUMMARY=YES"
            if total:
                s += ", TOTAL=YES"
        fil.write("%s\n" % s)
        for key in keys:
            fil.write("%s\n" % key)


def writeFileOutput(fil,resfreq=1,timemarks=False):
    """Write the FILE OUTPUT command for Abaqus/Explicit"""
    fil.write("*FILE OUTPUT, NUMBER INTERVAL=%s" % resfreq)
    if timemarks:
        fil.write(", TIME MARKS=YES")
    fil.write("\n")



##################################################
## Some classes to store all the required information
##################################################


class Output(Dict):
    """A request for output to .odb.

    Parameters:

    - `type`: 'FIELD' (default), 'HISTORY' or ''.
    - `kind`: string: one of '', 'N', 'NODE', 'E', 'ELEMENT', 'ENERGY',
      'CONTACT'.
      'N' and 'E' are abbreviations for 'NODE', 'ELEMENT', respectively.
    - `vars`: 'ALL', 'PRESELECT' or, if `kind` != None, a list of output
      identifiers compatible with the specified `kind`.
    - `set`: a single set name or a list of node/element set names.
      This can not be specified for kind==''.
      If no set is specified, the default is 'Nall' for kind=='NODE' and
      'Eall' for kind=='ELEMENT'
    - `typeset`: string: it is equal to the corresponding abaqus
      parameter to identify the kind of set. If not specified, the default
      is the default is 'NSET' for kind=='NODE' , 'CONTACT' and
      'ELSET' for kind=='ELEMENT' , 'ENERGY'
    - `options`: (opt) options string to be added to the keyword line.
    - `extra`: (opt)  extra string to be added below the keyword line
      and optional data.

    Examples::

      >>> out1 = Output(type='field')
      >>> print(out1.fmt())
      *OUTPUT, FIELD, VARIABLE=PRESELECT
      <BLANKLINE>

      >>> out0 = Output(vars=None)
      >>> out2 = Output(type='field', kind='e', vars=['S','SP'])
      >>> print(out0.fmt()+out2.fmt())
      *OUTPUT, FIELD
      *ELEMENT OUTPUT, ELSET=Eall
      S, SP
      <BLANKLINE>

      >>> out3 = Output(type='field', kind='e', vars=['S','SP'], set=['set1','set2'])
      >>> print(out0.fmt()+out3.fmt())
      *OUTPUT, FIELD
      *ELEMENT OUTPUT, ELSET=set1
      S, SP
      *ELEMENT OUTPUT, ELSET=set2
      S, SP
      <BLANKLINE>

      >>> out4 = Output(type='',diagnostic='yes')
      >>> print(out4.fmt())
      *OUTPUT, DIAGNOSTIC=yes
      <BLANKLINE>

    """

    def __init__(self,kind='',vars='PRESELECT',set=None,typeset=None,type='FIELD',options='',extra='',variable=None,keys=None,*args,**kargs):
        """ Create a new output request."""
        if keys is not None or variable is not None:
            utils.warn('warn_Output_changed')
            if keys is not None:
                vars = keys
            if variable is not None:
                vars = variable

        Dict.__init__(self,{'kind':'','otype':type.upper(),'vars':vars,'options':options,'extra':extra,'args':args,'kargs':kargs})
        if kind:
            kind = kind.upper()
            if kind == 'N':
                kind = 'NODE'
            elif kind == 'E':
                kind = 'ELEMENT'

            if set is None:
                if kind in ['NODE']:
                    set = "Nall"
                    typeset = 'nset'
                if kind in ['ELEMENT','ENERGY']:
                    set = "Eall"
                    typeset = 'elset'
            elif set is not None and typeset is None:
                if kind in ['NODE']:
                    typeset = 'NSET'
                if kind in ['ELEMENT','ENERGY']:
                    typeset = 'ELSET'

            if not isinstance(set, list):
                set = [ set ]
            self.update({'kind':kind,'set':set,'typeset':typeset})


    def fmt(self):
        """Format an output request.

        Return a string with the formatted output command.
        """
        if self.kind == '':
            cmd = Command('OUTPUT',*self.args,options=self.options,extra=self.extra,**self.kargs)
            if self.otype:
                cmd.add(self.otype)
                if isinstance(self.vars,str):
                    cmd.add(variable=self.vars)
            out = str(cmd)


        elif self.kind in ['NODE','ELEMENT','CONTACT','ENERGY']:
            out = ''
            for setname in self.set:
                cmd = Command('%s OUTPUT' % self.kind,options=self.options,extra=self.extra)
                if self.kind in ['NODE', 'CONTACT','ELEMENT', 'ENERGY']:
                    if setname is not None:
                        cmd.add(options='%s=%s'%(self.typeset.upper(),setname))
                if isinstance(self.vars,str):
                    cmd.add(variable=self.vars)
                else:
                    cmd.add(data = self.vars)
                out += str(cmd)

        return out


#
# TODO : this should be restructured like Output, and include a fmt() method
#
class Result(Dict):
    """A request for output of results on nodes or elements.

    Parameters:

    - `kind`: 'NODE' or 'ELEMENT' (first character suffices)
    - `keys`: a list of output identifiers (compatible with kind type)
    - `set`: a single item or a list of items, where each item is either
      a property number or a node/element set name for which the results
      should be written. If no set is specified, the default is 'Nall'
      for kind=='NODE' and 'Eall' for kind='ELEMENT'
    - `output` is either ``FILE`` (for .fil output) or ``PRINT`` (for .dat
      output)(Abaqus/Standard only)
    - `freq` is the output frequency in increments (0 = no output)

    Extra keyword arguments are available: see the `writeNodeResults` and
    `writeElemResults` methods for details.

    """

    # The following values can be changed to set the output frequency
    # for Abaqus/Explicit
    nintervals = 1
    timemarks = False

    def __init__(self,kind,keys,set=None,output='FILE',freq=1,time=False,
                 **kargs):
        """Create new result request."""
        kind = kind[0].upper()
        if set is None:
            set = "%sall" % kind
        Dict.__init__(self, {'keys':keys,'kind':kind,'set':set,'output':output,
                            'freq':freq})
        self.update(dict(**kargs))


class Step(Dict):
    """_VERY badly structured docstring

    The basic logical unit in the simulation history.

    In Abaqus, a step is the smallest logical entity in the simulation
    history. It is typically a time step in a dynamic simulation, but it
    can also describe different loading states in a (quasi-)static simulation.

    Our Step class holds all the data describing the global step parameters.
    It combines the Abaqus 'STEP', 'STATIC', 'DYNAMIC' and 'BUCKLE' keyword
    commands (and even some more global parameter setting commands).

    Parameters:

    - `analysis`: the analysis type, one of: 'STATIC', 'DYNAMIC', 'EXPLICIT',
      'PERTURBATION', 'BUCKLE', 'RIKS'
    - `time`: either

      - a single float value specifying the step time,
      - a list  of 2 values (special cases with analysis=EXPLICIT)
      - a list  of 4 values: time inc, step time, min. time inc, max. time inc (all the other cases)
      - for LANCZOS: a list of 5 values
      - for RIKS: a list of 8 values

      In most cases, only the step time should be specified.

    - `nlgeom`: True or False (default). If True, the analysis will be
      geometrically non-linear. For Analysis type 'RIKS', `nlgeom` is set
      True, for 'BUCKLE' it is set False, 'PERTURBATION' ignores `nlgeom`.
    - `tags`: a list of property tags to include in this step.
      If specified, only the property records having one of the listed values
      as their `tag` attribute will be included in this step.
    - `out` and `res`: specific output/result records for this step. They
      come in addition to the global ones.

    - stepOption is a  Dict of optional parameters to be added at a step level at the FIRST line. it is placed after the *STEP keyword i.e
        *STEP, NLGEOM=YES,INC=10000,UNSYMM = YES
        It has keys name equal to the ABAQUS keywords and value equal to parameter setting
        if an ABAQUS keyword does not have a value to be the Dict value must be an empty string (see example below)

    - subheading is a string printed as an additionanal subheading (not important normally)

    - analysisOption is a  Dict of optional parameters to be added at a step level at the SECOND line. it is placed after the analysis keyword i.e
        *STATIC, STABILIZE=0.0002,CONTINUE=NO
        with keys name equal to the ABAQUS keywords and value equal to parameter setting
        if an ABAQUS keyword does not have a value to be the Dict value must be an empty string (see example below)

    -extra : str  for any extra keyword to be added at a step level after the time line
              : list of Dict for any extra keyword to be added at a step level after the time line. Each Dict is a separate line (see example below)

                Only 2 keys are dedicated:

                REQUIRED
                    -keyword =  abaqus keyword name

                OPTIONAL
                    -data = list or array of numerical data for any additional data line

                All the other keys are optional and must have name equal to the ABAQUS keywords and value equal to parameter setting
                if an ABAQUS keyword does not have a value to be the Dict value must be an empty string (see example below)


    Examples on stepOption ,  analysisOption, extra

    stepOption standard analysis, not needed for explicit
        Dict({'UNSYMM':'YES'/'NO','CONVERT SDI':'YES'/'NO','AMPLITUDE':'STEP'/'RAMP','INC':100})

    analysisOption:
        static, riks
            Dict({'STABILIZE':0.0002,'CONTINUE':'NO'/'YES','ALLSDTOL':0.05,'DIRECT':'NO STOP','FACTOR':1.,'INCR':0.1 (for riks)})
        dynamic (implicit)
            Dict({'APPLICATION':'QUASI-STATIC'/'MODERATE DISSIPATION'/'TRANSIENT FIDELITY'})
        dynamic explicit
            Dict({'DIRECT USER CONTROL':'' / 'ELEMENT BY ELEMENT':'' / 'FIXED TIME INCREMENTATION':'',\
            'IMPROVED DT METHOD'='NO'/'YES','SCALE FACTOR':1.})
        buckle
            Dict({'EIGENSOLVER':'SUBSPACE'})

    extra:
        extra='*BULK VISCOSITY\n0.12, 0.06\n'

        extra=[Dict({'keyword':'BULK VISCOSITY','data':[0.12, 0.06]})]


    """

    analysis_types = [ 'STATIC', 'DYNAMIC', 'EXPLICIT', \
                       'PERTURBATION', 'BUCKLE', 'RIKS', 'ANNEAL' ]

    def __init__(self,analysis='STATIC',time=[0., 0., 0., 0.],nlgeom=False,
                 heading=None,tags=None,name=None,out=[],res=[],
                 options=None,analysisOptions=None,extra=None):
        """Create a new analysis step."""

        self.analysis = analysis.upper()

        self.name = name
        if not self.analysis in Step.analysis_types:
            raise ValueError('analysis should be one of %s' % analysis_types)
        if isinstance(time, float):
            time = [ 0., time, 0., 0. ]
        self.time = time

        if analysis == 'RIKS':
            nlgeom = True
        elif analysis in ['BUCKLE', 'PERTURBATION']:
            nlgeom = False
        if nlgeom == 'NO':
            nlgeom = False
        self.nlgeom = nlgeom

        self.tags = tags
        self.out = out
        self.res = res
        self.options = options
        self.analysisOptions = analysisOptions
        self.heading = heading
        self.extra = extra


    def write(self,fil,propDB,out=[],res=[],resfreq=1,timemarks=False):
        """Write a simulation step.

        propDB is the properties database to use.

        Except for the step data itself, this will also write the passed
        output and result requests.
        out is a list of Output-instances.
        res is a list of Result-instances.
        resfreq and timemarks are global values only used by Explicit
        """
        cmd = '*STEP'
        if self.name:
            cmd += ', NAME=%s' % self.name
        if self.analysis == 'PERTURBATION':
            cmd += ', PERTURBATION'

        if self.nlgeom:
            cmd += ', NLGEOM=%s' % self.nlgeom

        if self.options is not None:
            cmd += self.options
        cmd += '\n'
        fil.write(cmd)

        if self.heading is not None:
            fil.write(self.heading+'\n')

        if self.analysis =='STATIC':
            fil.write("*STATIC")
        elif self.analysis == 'EXPLICIT':
            fil.write("*DYNAMIC, EXPLICIT")
        elif self.analysis == 'DYNAMIC':
            fil.write("*DYNAMIC")
        elif self.analysis == 'BUCKLE':
            fil.write("*BUCKLE")
        elif self.analysis == 'PERTURBATION':
            fil.write("*STATIC")
        elif self.analysis == 'RIKS':
            fil.write("*STATIC, RIKS")
        elif self.analysis == 'ANNEAL':
            fil.write("*ANNEAL")

        if self.analysisOptions is not None:
            fil.write(self.analysisOptions)
        fil.write('\n')

        fil.write(fmtData1d(self.time))
        fil.write('\n')

        if self.extra is not None:
            fil.write(self.extra)
            fil.write('\n')

        prop = propDB.getProp('n', tag=self.tags, attr=['bound'])
        if prop:
            print("  Writing step boundary conditions")
            for p in prop:
                fil.write(fmtBoundary(p))

        for btype in [ 'displacement', 'velocity', 'acceleration' ]:
            shorttype = btype[:5]
            prop = propDB.getProp('n', tag=self.tags, attr=[shorttype])
            if prop:
                print("  Writing step prescribed %s" % btype)
                writeDisplacements(fil, prop, btype)

        for kind,attr in [ ('n','cload'), ('e','dload'), ('','dsload') ]:
            prop = propDB.getProp(kind, tag=self.tags, attr=[attr])
            if prop:
                print("  Writing step data: %s" % attr.upper())
                for p in prop:
                    fil.write(fmtLoad(attr,p))

        prop = propDB.getProp(tag=self.tags,attr=['keyword'])
        if prop:
            print("Writing general keywords")
            for p in prop:
                fil.write(fmtKeyword(**p))

        print("  Writing output")
        for i in out + self.out:
            fil.write(i.fmt())

        if res and self.analysis == 'EXPLICIT':
            writeFileOutput(fil, resfreq, timemarks)

        for i in res + self.res:
            if i.kind == 'N':
                writeNodeResult(fil,**i)
            elif i.kind == 'E':
                writeElemResult(fil,**i)
        fil.write("*END STEP\n")


############################################################ AbqData


class AbqData(object):
    """Contains all data required to write the Abaqus input file.

    - `model` : a :class:`Model` instance.
    - `prop`  : the `Property` database.
    - `nprop` : the node property numbers to be used for by-prop properties.
    - `eprop` : the element property numbers to be used for by-prop properties.
    - `steps` : a list of `Step` instances.
    - `res` : a list of `Result` instances to be applied on all steps.
    - `out` : a list of `Output` instances to be applied on all steps.
    - `initial` : a tag or alist of the initial data, such as boundary
      conditions. The default is to apply ALL boundary conditions initially.
      Specify a (possibly non-existing) tag to override the default.
    """

    def __init__(self,model,prop,nprop=None,eprop=None,steps=[],res=[],out=[],initial=None):
        """Create new AbqData."""
        if not isinstance(model, Model) or not isinstance(prop, PropertyDB):
            raise ValueError("Invalid arguments: expected Model and PropertyDB, got %s and %s" % (type(model), type(prop)))

        self.model = model
        self.prop = prop
        self.nprop = nprop
        self.eprop = eprop
        self.initial = initial
        self.steps = steps
        self.res = res
        self.out = out


    def write(self,jobname=None,group_by_eset=True,group_by_group=False,header='',create_part=False):
        """Write an Abaqus input file.

        - `jobname` : the name of the inputfile, with or without '.inp'
          extension. If None is specified, the output is written to sys.stdout
          An extra header text may be specified.
        - `create_part` : if True, the model will be created as an Abaqus Part,
          followed by an assembly of that part.
        """
        global materialswritten
        materialswritten = []
        # Create the Abaqus input file
        if jobname is None:
            jobname, filename = 'Test', None
            fil = sys.stdout
        else:
            jobname, filename = abqInputNames(jobname)
            fil = open(filename, 'w')
            print("Writing to file %s" % (filename))

        fil.write(fmtHeading("""Model: %s     Date: %s      Created by pyFormex
Script: %s
%s
""" % (jobname, datetime.now(), pf.scriptName, header)))

        if create_part:
            fil.write("*PART, name=Part-0\n")

        fil.write(fmtSectionHeading("NODES"))
        nnod = self.model.nnodes()
        print("Writing %s nodes" % nnod)
        writeNodes(fil, self.model.coords)

        print("Writing node sets")
        for p in self.prop.getProp('n', attr=['set']):
            print("NODE SET", p)
            if p.set is not None:
                # set is directly specified
                set = p.set
            elif p.prop is not None:
                # set is specified by nprop nrs
                if self.nprop is None:
                    print(p)
                    raise ValueError("nodeProp has a 'prop' field but no 'nprop' was specified")
                set = where(self.nprop == p.prop)[0]
            else:
                # default is all nodes
                set = arange(self.model.nnodes())

            setname = nsetName(p)
            writeSet(fil, 'NSET', setname, set)

        print("Writing coordinate transforms")
        for p in self.prop.getProp('n', attr=['csys']):
            fil.write(fmtTransform(p.csys, p.name))

        print("Writing elements and element sets")
        fil.write(fmtSectionHeading("ELEMENTS"))
        telems = self.model.celems[-1]
        nelems = 0
        for p in self.prop.getProp('e'):
            if p.set is not None:
                # element set is directly specified
                set = p.set
            elif p.prop is not None:
                # element set is specified by eprop nrs
                if self.eprop is None:
                    print(p)
                    raise ValueError("elemProp has a 'prop' field but no 'eprop' was specified")
                set = where(self.eprop == p.prop)[0]
            else:
                # default is all elements
                set = arange(telems)

            if 'eltype' in p:
                pf.debug('Elements of type %s: %s' % (p.eltype, set), pf.DEBUG.ABQ)

                setname = esetName(p)
                gl, gr = self.model.splitElems(set)
                elems = self.model.getElems(gr)
                for i, elnrs, els in zip(range(len(gl)), gl, elems):
                    grpname = Eset('grp', i)
                    subsetname = Eset(p.nr, 'grp', i, setname)
                    print("GROUP NAME %s" % grpname)
                    print("SUBSET NAME %s" % subsetname)
                    nels = len(els)
                    # Translate element connectivity to Abaqus order
                    if els.eltype in AbqConnectivity:
                        els = els[:,AbqConnectivity[els.eltype]]
                    if nels > 0:
                        print("Writing %s elements from group %s" % (nels, i))
                        writeElems(fil, els, p.eltype, name=subsetname, eid=elnrs)
                        nelems += nels
                        if group_by_eset:
                            writeSet(fil, 'ELSET', setname, [subsetname])
                        if group_by_group:
                            print("write grpset %s: %s" % (grpname, subsetname))
                            writeSet(fil, 'ELSET', grpname, [subsetname])
            else:
                writeSet(fil, 'ELSET', p.name, p.set)

        print("Total number of elements: %s" % telems)
        if nelems != telems:
            print("!! Number of elements written: %s !!" % nelems)

        ## # Now process the sets without eltype
        ## for p in self.prop.getProp('e',noattr=['eltype']):
        ##     setname = esetName(p)
        ##     writeSet(fil,'ELSET',setname,p.set)

        print("Writing distribution tables")
        for p in self.prop.getProp('', attr=['distribution']):
            writeDistribution(fil, p)

        print("Writing element sections")
        fil.write(fmtSectionHeading("SECTIONS"))
        for p in self.prop.getProp('e', attr=['section', 'eltype']):
            writeSection(fil, p)

        if create_part:
            fil.write("*END PART\n")
            fil.write("*ASSEMBLY, name=Assembly\n")
            fil.write("*INSTANCE, name=Part-0-0, part=Part-0\n")
            fil.write("*END INSTANCE\n")
            fil.write("*END ASSEMBLY\n")

        print('Materials written:\n  ')
        print('\n  '.join(materialswritten)+'\n')

        print("Writing global model properties")

        prop = self.prop.getProp(attr=['keyword'])
        if prop:
            print("Writing general keywords")
            for p in prop:
                fil.write(fmtKeyword(**p))

        prop = self.prop.getProp('', attr=['mass'])
        if prop:
            print("Writing masses")
            fil.write(fmtMass(prop))

        prop = self.prop.getProp('', attr=['inertia'])
        if prop:
            print("Writing rotary inertia")
            fil.write(fmtInertia(prop))

        prop = self.prop.getProp('', attr=['amplitude'])
        if prop:
            print("Writing amplitudes")
            writeAmplitude(fil,prop)

        prop = self.prop.getProp('', attr=['orientation'])
        if prop:
            print("Writing orientations")
            fil.write(fmtOrientation(prop))

        prop = self.prop.getProp('', attr=['ConnectorBehavior'])
        if prop:
            print("Writing Connector Behavior")
            fil.write(fmtConnectorBehavior(prop))

        prop = self.prop.getProp('n', attr=['equation'])
        if prop:
            print("Writing constraint equations")
            fil.write(fmtEquation(prop))

        prop = self.prop.getProp('', attr=['surftype'])
        if prop:
            print("Writing surfaces")
            fil.write(fmtSurface(prop))

        prop = self.prop.getProp('', attr=['analyticalsurface'])
        if prop:
            print("Writing analytical surfaces")
            fil.write(fmtAnalyticalSurface(prop))

        prop = self.prop.getProp('', attr=['interaction'])
        if prop:
            print("Writing contact pairs")
            fil.write(fmtContactPair(prop))

        prop = self.prop.getProp('', attr=['generalinteraction'])
        if prop:
                print("Writing general contact")
                fil.write(fmtGeneralContact(prop))

        prop = self.prop.getProp('', attr=['constraint'])
        if prop:
                print("Writing constraints")
                fil.write(fmtConstraint(prop))

        prop = self.prop.getProp('', attr=['initialcondition'])
        if prop:
                print("Writing initial conditions")
                fil.write(fmtInitialConditions(prop))

        prop = self.prop.getProp('n', tag=self.initial, attr=['bound'])
        if prop:
            print("Writing initial boundary conditions")
            fil.write(fmtSectionHeading("BOUNDARY CONDITIONS"))
            for p in prop:
                fil.write(fmtBoundary(p))

        print("Writing steps")
        for step in self.steps:
            fil.write(fmtSectionHeading("STEP %s" % (step.name if step.name else '')))
            step.write(fil, self.prop, out=self.out, res=self.res, resfreq=Result.nintervals, timemarks=Result.timemarks)

        if filename is not None:
            fil.close()
        print("Wrote Abaqus input file %s" % filename)



##################################################
## Some convenience functions
##################################################

def exportMesh(filename,mesh,eltype=None,header=''):
    """Export a finite element mesh in Abaqus .inp format.

    This is a convenience function to quickly export a mesh to Abaqus
    without having to go through the whole setup of a complete
    finite element model.
    This just writes the nodes and elements specified in the mesh to
    the file with the specified name. The resulting file  can then be
    imported in Abaqus/CAE or manual be edited to create a full model.
    If an eltype is specified, it will override the value stored in the mesh.
    This should be used to set a correct Abaqus element type matchin the mesh.
    """
    fil = open(filename, 'w')
    fil.write(fmtHeading(header))
    if eltype is None:
        eltype = mesh.eltype
    writeNodes(fil, mesh.coords)
    writeElems(fil, mesh.elems, eltype, nofs=1)
    fil.close()
    print("Abaqus file %s written." % filename)


# End
