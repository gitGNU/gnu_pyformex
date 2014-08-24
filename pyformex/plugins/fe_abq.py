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


def fmtCmd(cmd='*'):
    """Format a command."""
    return '*'+cmd+'\n'


def fmtOptions(options):
    """Format the options of an Abaqus command line.

    - `options`: a dict with ABAQUS command keywords and values. If the keyword
      does not take any value, the value in the dict should be an empty string.

    Returns a comma-separated string of 'keyword' or 'keyword=value' fields.
    The string includes an initial comma.
    """
    s = ''
    for k in options:
        s += ", %s" % k.upper()
        if options[k] != '':
            s += "=%s" % options[k]
    return s


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

    - constants: arraylike, float. The material constants to be used in the
      model. In the case of 'LINEAR', it is optional and the constant may be
      specified by other keys (see below).

    - options (opt): string: will be added to the material command as is.

    - extra (opt): (multiline) string: will be added to the material data as is.

    - plastic (opt): arraylike, float, shape (N,2). Definition of the
      material plasticity law. Each row contains a tuple of a yield stress
      value and the corresponding equivalent plastic strain.

    - damping (opt): tuple (alpha,beta). Adds damping into the material.
      See Abaqus manual for the meaning of alpha and beta. Either of them
      can be a float or None.

    - field (opt): boolean. If True, a keyword "USER DEFINED FIELD" is added.

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

    'ANISOTROPIC HYPERELASTIC': has a required key 'model':

    - model: one of 'FUNG-ANISOTROPIC', 'FUNG-ORTHOTROPIC', 'HOLZAPFEL' or
      'USER'.
    - depvar (opt): see below ('USER')
    - localdir (opt): int: number of local directions.

    'USER':
    - depvar (opt): list of tuples specifying the solution-dependent state
      variables. Each item in the list is a tuple of a variable number and
      the variable name, e.g. `[[ 1,' var1'],[ 2,' var2']]`.

    Examples::

        steel = {
            'name': 'steel',
            'young_modulus': 207000e-6,
            'poisson_ratio': 0.3,
            'density': 7.85e-9,
            }

        intimaMat = {
            'name': 'intima',
            'density': 0.1,
            'elasticity':'hyperelastic',
            'type':'reduced polynomial',
            'constants': [6.79E-03, 5.40E-01, -1.11, 10.65, -7.27, 1.63, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            }

    """

    if mat.name is None or mat.name in materialswritten:
        return ""

    out ="*MATERIAL, NAME=%s\n" % mat.name
    materialswritten.append(mat.name)

    if mat.field:
        out+='*USER DEFINED FIELD\n'

    if mat.depvar is not None:
        out += "*DEPVAR\n%s\n" % len(mat.depvar) # Is this correct ??
        out += fmtData1d(mat.depvar,npl=2)

    # Default elasticity type
    if mat.elasticity is None:
        elasticity = 'linear'
    else:
        elasticity =  mat.elasticity.lower()
    constants = mat.constants

    if elasticity == 'linear':
        out += '*ELASTIC'

        if constants is None:
            if mat.poisson_ratio is None and mat.shear_modulus is not None:
                mat.poisson_ratio = 0.5 * mat.young_modulus / mat.shear_modulus - 1.0
            constants = (float(mat.young_modulus), float(mat.poisson_ratio))

    elif elasticity == 'hyperelastic':
        out += "*HYPERELASTIC, %s" % mat.model

        model = mat.model.lower()
        order = mat.order
        if not order:
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

            if mconst != nconst:
                raise ValueError("Wrong number of material constants (%s) for order (%s) of %s model" % (nconst,mconst,model))

        out += ", N=%i\n" %order

    elif elasticity == 'anisotropic hyperelastic':
        out += "*ANISOTROPIC HYPERELASTIC, %s" % mat.model
        if mat.localdir is not None:
            out += ', LOCAL DIRECTIONS=%i'%mat.localdir

    elif elasticity == 'user':
        out += "*USER MATERIAL, CONSTANTS=%s\n" % len(mat.constants)

    elif elasticity is not None:
        out += "%s\n" % elasticity.upper()

    # complete the command
    if mat.options is not None:
        out += mat.options
    out += '\n'
    out += fmtData1d(constants)
    out += '\n'

    if mat.density is not None:
        out += "*DENSITY\n%s\n" % float(mat.density)

    if mat.plastic is not None:
        out += "*PLASTIC\n"
        mat.plastic = asarray(mat.plastic)
        if mat.plastic.ndim != 2:
            raise ValueError("Plastic data should be 2-dim array")
        out += fmtData1d(mat.plastic) + '\n'

    if mat.damping is not None:
        alpha,beta = mat.damping
        out += "*DAMPING"
        if alpha:
            out +=", ALPHA = %s" % alpha
        if beta:
            out +=", BETA = %s" % beta
        out += '\n'

    if mat.extra is not None:
        out += mat.extra
        out += '\n'

    return out


def fmtTransform(setname, csys):
    """Write transform command for the given set.

    - `setname` is the name of a node set
    - `csys` is a CoordSystem.
    """
    out = "*TRANSFORM, NSET=%s, TYPE=%s\n" % (setname, csys.sys)
    out += fmtData1d(csys.data.reshape(-1))
    out += '\n'
    return out


def fmtFrameSection(el, setname):
    """Write a frame section for the named element set.

    Recognized data fields in the property record:

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

    - all sectiontypes:

      - young_modulus
      - shear_modulus

    - optional:

      - density: density of the material
      - yield_stress: yield stress of the material
      - orientation: a vector specifying the direction cosines of the 1 axis
    """
    out = ""
    extra = ''
    if el.density:
        extra += ', DENSITY=%s' % float(el.density)
    if el.yield_stress:
            extra += ', PLASTIC DEFAULTS, YIELD STRESS=%s' % float(el.yield_stress)
    if el.shear_modulus is None and el.poisson_ratio is not None:
        el.shear_modulus = el.young_modulus / 2. / (1.+float(el.poisson_ratio))

    sectiontype = el.sectiontype.upper()
    out += "*FRAME SECTION, ELSET=%s, SECTION=%s%s\n" % (setname, sectiontype, extra)
    if sectiontype == 'GENERAL':
        out += "%s, %s, %s, %s, %s \n" % (float(el.cross_section), float(el.moment_inertia_11), float(el.moment_inertia_12), float(el.moment_inertia_22), float(el.torsional_constant))
    elif sectiontype == 'CIRC':
        out += "%s \n" % float(el.radius)
    elif sectiontype == 'RECT':
        out += "%s, %s\n" % (float(el.width), float(el.height))

    if el.orientation != None:
        out += fmtData1d(el.orientation)
    out += '\n'

    out += fmtData1d([float(el.young_modulus), float(el.shear_modulus)])
    out += '\n'

    return out


def fmtGeneralBeamSection(el, setname):
    """Write a general beam section for the named element set.

    This specifies a beam section when numerical integration over the section
    is not required. See also `func:fmtBeamSection`.

    Recognized data fields in the property record:

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

    - all sectiontypes:

      - young_modulus
      - shear_modulus or poisson_ration

    - optional:

      - density: density of the material (required in Abaqus/Explicit)
    """
    out = ""
    extra = ''
    if el.density:
        extra += ', DENSITY=%s' % float(el.density)

    if el.shear_modulus is None and el.poisson_ratio is not None:
        el.shear_modulus = el.young_modulus / 2. / (1.+float(el.poisson_ratio))

    sectiontype = el.sectiontype.upper()
    out += "*BEAM GENERAL SECTION, ELSET=%s, SECTION=%s%s\n" % (setname, sectiontype, extra)
    if sectiontype == 'GENERAL':
        out += "%s, %s, %s, %s, %s \n" % (float(el.cross_section), float(el.moment_inertia_11), float(el.moment_inertia_12), float(el.moment_inertia_22), float(el.torsional_constant))
    elif sectiontype == 'CIRC':
        out += "%s \n" % float(el.radius)
    elif sectiontype == 'RECT':
        out += "%s, %s\n" % (float(el.width), float(el.height))

    if el.orientation != None:
        out += fmtData1d(el.orientation)

    if el.orientation != None:
        out += fmtData1d(el.orientation)
    out += '\n'

    out += "%s, %s \n" % (float(el.young_modulus), float(el.shear_modulus))

    return out


def fmtBeamSection(el, setname):
    """Write a beam section for the named element set.

    This specifies a beam section when numerical integration over the section
    is required. See also `func:fmtGeneralBeamSection`.

    Recognized data fields in the property record:

    - all sectiontypes: material

    - sectiontype GENERAL:

      - cross_section
      - moment_inertia_11
      - moment_inertia_12
      - moment_inertia_22
      - torsional_constant

    - sectiontype CIRC:

      - radius
      - intpoints1 (opt): number of integration points in the first direction
      - intpoints2 (opt): number of integration points in the second direction

    - sectiontype RECT:

      - width, height
      - intpoints1 (opt): number of integration points in the first direction
      - intpoints2 (opt): number of integration points in the second direction

    """
    out = ""

    sectiontype = el.sectiontype.upper()
    out += "*BEAM SECTION, ELSET=%s, MATERIAL=%s, SECTION=%s" % (setname, el.material.name, sectiontype)
    if el.poisson != None:
        out += ", POISSON=%s"% (float(el.poisson))
    out += "\n"
    if sectiontype == 'GENERAL':
        out += "%s, %s, %s, %s, %s \n" % (float(el.cross_section), float(el.moment_inertia_11), float(el.moment_inertia_12), float(el.moment_inertia_22), float(el.torsional_constant))
    elif sectiontype == 'CIRC':
        out += "%s \n" % float(el.radius)
    elif sectiontype == 'RECT':
        out += "%s, %s\n" % (float(el.width), float(el.height))

    if el.orientation != None:
        out += fmtData1d(el.orientation)
    out += '\n'

    if el.intpoints1 != None:
        out += "%s" % el.intpoints1
        if el.intpoints2 != None:
            out += ", %s" % el.intpoints2
        out += "\n"

    if el.transverseshearstiffness != None:
        out += "*TRANSVERSE SHEAR STIFFNESS\n"
        out += fmtData1d(el.transverseshearstiffness)
        out += '\n'

    return out


def fmtConnectorSection(el, setname):
    """Write a connector section.

    Required:

    - `sectiontype`: JOIN, HINGE, ...

    Optional data:

    - `behavior` : connector behavior name
    - `orient`  : connector orientation
    - `elimination` : 'NO' (default), 'YES'
    """
    out = ""
    if el.sectiontype.upper() != 'GENERAL':
        out += '*CONNECTOR SECTION, ELSET=%s' % setname
        if el.behavior:
            out += ', BEHAVIOR=%s' % el.behavior
        if el.elimination:
            out += ', ELIMINATION=%s' % el.elimination
        out += '\n%s\n' % el.sectiontype.upper()
        if el.orient:
            out += '%s\n' % el.orient

    return out


def fmtConnectorBehavior(prop):
    """ Write a connector behavior.
    Implemented: Elasticity,  Stop

    Optional parameter:
    - `extrapolation`: extrapolation method for all subcomponents of the behavior.
                       'CONSTANT' (default) or 'LINEAR'

    Examples:
    ---------

    Elasticity
    ''''''''''
    elasticity = dict(component=[1,2,3,4,5,6], value=[1,1,1,1,1,1])
    P.Prop(name='connbehavior1', ConnectorBehavior='', Elasticity=elasticity, extrapolation='LINEAR')

    Optional parameter for Elasticity dictionary:
    - `nonlinear`: use nonlinear elasticity data. Can be False (default) or True.

    Stop:
    '''''
    stop = dict(component=[1,2,3,4,5,6],lowerlimit=[1,1,1,1,1,1], upperlimit=[2, 2, 2, 2,2,2])
    P.Prop(name='connbehavior3',ConnectorBehavior='',Stop=stop)
    """
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
        out += '%s , %s\n'% (p.Stop['lowerlimit'][j], stop['upperlimit'][j])
    return out


def fmtSpring(el, setname):
    """Write a spring of type spring.

    Optional data:

    - `springstiffness` : spring stiffness (force (S11) per relative displacement (E11))
    """
    out = ""
    #if el.sectiontype.upper() != 'GENERAL':
    out += '*SPRING, ELSET=%s\n' % setname
    if el.springstiffness:
        out += '\n%s\n' % float(el.springstiffness)

    return out


def fmtDashpot(el, setname):
    """Write a dashpot.

    Optional data:

    - `dashpotcoefficient` : dashpot coefficient (force (S11) per relative velocity (ER11, only produced in Standard))
    """
    out = ""
    #if el.sectiontype.upper() != 'GENERAL':
    out += '*DASHPOT, ELSET=%s\n' % setname
    if el.dashpotcoefficient:
        out += '\n%s\n' % float(el.dashpotcoefficient)

    return out


def fmtAnySection(el,setname,matname):
    """Format any SECTION keyword.

    The name should be derived from the ELTYPE_elems list
    to automatically set the section type

    Required:

    - setname
    - matname

    Optional:
    - options:
    - controls:
    - orientation:
    - sectiondata:
    -extra:

    """
    out = ''
    try:
        section_elems=globals()[el.sectiontype.lower()+'_elems']
    except:
        raise ValueError("element section '%s' not yet implemented" % el.sectiontype.lower())

    out += '*%s SECTION, ELSET=%s'%( el.sectiontype.upper(),setname)

    if matname is not None:
        out += ', MATERIAL=%s'%(matname)

    if el.density:
        out += ', DENSITY=%s'%(el.density)

    if el.options is not None:
        out += fmtOptions(el.options)

    if el.controls is not None:
            out += ", CONTROLS=%s" %(el.controls.name)

    if el.orientation is not None:
        out += ", ORIENTATION=%s" %(el.orientation.name)

    out += '\n'

    if el.sectiondata is not None:
        out += fmtData(el.sectiondata)
        out += '\n'

    if el.controls is not None:
        controls=CDict(el.controls)
        out += "*SECTION CONTROLS, NAME=%s" %el.controls.name
        out += fmtOptions(utils.removeDict(el.controls,['name','data']))
        out += '\n'
        if controls.data is not None:
           out += fmtData(controls.data)
        out += '\n'

    if el.extra is not None:
        extra = CDict(extra)
        out += fmtExtra(extra)
        out += '\n'
    return out


def fmtSolidSection(el, setname, matname):
    """Format the SOLID SECTION keyword.

    Required:

    - setname
    - matname

    Optional:

    - orientation
    - thickness
    - controls

    `controls` is a dict with name, options and data keys. Options is
    a string which is added as is to the command. Data are added below
    the command. All other items besides name, options and data are formatted
    as extra command options.

    Example::

     mycontrol = Dict({'name':'StentControl', 'options':'HOURGLASS=enhanced','data':[1., 1., 1.]})
     mysection = ElemSection(section=stentSec, material=steel,controls=mycontrol)
     P.elemProp(set='STENT',name='Name',eltype='C3D8R',section=mysection)
    """
    out = "*SOLID SECTION, ELSET=%s, MATERIAL=%s" % (setname, matname)
    if el.orientation is not None:
        out += ", ORIENTATION=%s" % el.orientation.name
    if el.controls is not None:
        out += ", CONTROLS=%s" % el.controls.name
    out += '\n'

    if el.thickness is not None:
        out += '%s\n'%float(el.thickness)

    if el.controls is not None:
        out += "*SECTION CONTROLS, NAME=%s" % el.controls.name
        if el.controls.options is not None:
            out += ", "+str(el.controls.options)
        out += fmtOptions(utils.removeDict(el.controls, ['name', 'options', 'data']))
        out += '\n'

        if el.controls.data is not None:
           out += fmtData1d(el.controls.data)
           out += '\n'

    return out


def fmtShellSection(el, setname, matname):
    """Format the shell SHELL SECTION keyword.

    Required:

    - setname
    - matname

    Optional:

    - transverseshearstiffness
    - offset (for contact surface SPOS or 0.5, SNEG or -0.5)
    """
    out = ''
    #
    # BV: ARE THESE TESTS RELEVANT?
    #
    if el.sectiontype.upper() == 'SHELL':
        if matname is not None:
            out += "*SHELL SECTION, ELSET=%s, MATERIAL=%s"%(setname, matname)
            if el.offset is not None:
                out += ", OFFSET=%s"%el.offset
            if el.thicknessmodulus is not None:
                out += ", THICKNESS MODULUS=%f" % el.thicknessmodulus
            if el.poisson is not None:
                out += ", POISSON=%f" % el.poisson
            if el.options is not None:
                out += el.options
            out += "\n"
            out += " %s \n" % float(el.thickness)
    if el.transverseshearstiffness is not None:
        out += "*TRANSVERSE SHEAR STIFFNESS\n"
        out += fmtData1d(el.transverseshearstiffness)
        out += '\n'
    return out


def fmtSurface(prop):
    """Format the surface definitions.

    Required:

    - set: the elements/nodes in the surface, either numbers or a set name.
    - name: the surface name
    - surftype: 'ELEMENT' or 'NODE'
    - label: face or edge identifier (only required for surftype = 'ELEMENT')

    This label can be a string, or a list of strings. This allows to use
    different identifiers for the different elements in the surface. Thus::

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
        out += "*SURFACE, NAME=%s, TYPE=%s\n" % (p.name, p.surftype)
        for i, e in enumerate(p.set):
            if e.dtype.kind != 'S':
                e += 1
            if p.label is None:
                out += "%s\n" % e
            elif isinstance(p.label, str):
                out += "%s, %s\n" % (e, p.label)
            else:
                out += "%s, %s\n" % (e, p.label[i])
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

    -name

    Optional:

    - cross_section (for node based interaction)
    - friction : friction coeff or 'rough'
    - surface behavior: no separation
    - surface behavior: pressureoverclosure
    """
    out = ''
    for p in prop:
        out += "*Surface Interaction, name=%s\n" % (p.name)
        if p.cross_section is not None:
            out += "%s\n" % p.cross_section
        if p.friction is not None:
            if p.friction == 'rough':
                out += "*FRICTION, ROUGH\n"
            else:
                out += "*FRICTION\n%s\n" % float(p.friction)
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


def fmtGeneralContact(prop):
    """Format the general contact.

    Only implemented on model level

    Required:

    - interaction: interaction properties: name or Dict

    Optional:

    - Exclusions (exl)
    - Extra (extra). Example ::

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

    -name
    -adjust (yes or no)
    -slave
    -master

    Optional:

    -type (surf2surf, node2surf)
    -positiontolerance
    -no rotation
    -tiednset (it cannot be used in combination with positiontolerance)

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

    -type
    -nodes
    -data

    Example::

      P.Prop(initialcondition='', nodes ='Nall', type = 'TEMPERATURE', data = 37.)
    """

    for p in prop:
        out ="*Initial Conditions, type = %s\n" % p.type
        out +="%s,%.2f\n" % (p.nodes, p.data)
    return out


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


def fmtEquation(prop):
    """Format multi-point constraint using an equation

    Required:

    - equation

    Equation should be a list, which contains the different terms of the equation.
    Each term is again a list with three values:

    - First value: node number
    - Second value: degree of freedom
    - Third value: coefficient

    Example::

      P.nodeProp(equation=[[209,1,1],[32,1,-1]])

    This forces the displacement in Y-direction of nodes 209 and 32 to
    be equal.
    """

    out = ''
    nofs = 1
    for p in prop:
        out += "*EQUATION\n"
        out += "%s\n" % asarray(p.equation).shape[0]
        for i in p.equation:
            dof = i[1]+1
            out += "%s, %s, %s\n" % (i[0]+nofs, dof, i[2])
    return out




def fmtMass(prop):
    """Format mass

    Required:

    - mass : mass magnitude
    - set : name of the element set on which mass is applied
    """
    out = ''
    for p in prop:
        out +='*MASS, ELSET={0}\n'.format(p.name)
        out +='{0}\n'.format(p.mass)
    return out


def fmtInertia(prop):
    """Format rotary inertia

    Required:

    - inertia : inertia tensor i11, i22, i33, i12, i13, i23
    - set : name of the element set on which inertia is applied
    """
    out = ''
    for p in prop:
        out +='*ROTARY INERTIA, ELSET={0}\n'.format(p.name)
        out += fmtData1d(p.inertia,  6)
        out += '\n'
    return out


## The following output sections with possibly large data
## are written directly to file.
##########################################################

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

pointmass_elems = ['MASS']
spring_elems = ['SPRINGA', ]
dashpot_elems = ['DASHPOTA', ]
connector_elems = ['CONN3D2', 'CONN2D2']
frame_elems = ['FRAME3D', 'FRAME2D']
truss_elems = [
    'T2D2', 'T2D2H', 'T2D3', 'T2D3H',
    'T3D2', 'T3D2H', 'T3D3', 'T3D3H']
beam_elems = [
    'B21', 'B21H', 'B22', 'B22H', 'B23', 'B23H',
    'B31', 'B31H', 'B32', 'B32H', 'B33', 'B33H']
membrane_elems = [
    'M3D3',
    'M3D4', 'M3D4R',
    'M3D6', 'M3D8',
    'M3D8R',
    'M3D9', 'M3D9R']
plane_stress_elems = [
    'CPS3',
    'CPS4', 'CPS4I', 'CPS4R',
    'CPS6', 'CPS6M',
    'CPS8', 'CPS8R', 'CPS8M']
plane_strain_elems = [
    'CPE3', 'CPE3H',
    'CPE4', 'CPE4H', 'CPE4I', 'CPE4IH', 'CPE4R', 'CPE4RH',
    'CPE6', 'CPE6H', 'CPE6M', 'CPE6MH',
    'CPE8', 'CPE8H', 'CPE8R', 'CPE8RH']
generalized_plane_strain_elems = [
    'CPEG3', 'CPEG3H',
    'CPEG4', 'CPEG4H', 'CPEG4I', 'CPEG4IH', 'CPEG4R', 'CPEG4RH',
    'CPEG6', 'CPEG6H', 'CPEG6M', 'CPEG6MH',
    'CPEG8', 'CPEG8H', 'CPEG8R', 'CPEG8RH']
solid2d_elems = plane_stress_elems + \
                plane_strain_elems + \
                generalized_plane_strain_elems
shell_elems = [
    'S3', 'S3R', 'S3RS',
    'S4', 'S4R', 'S4RS', 'S4RSW', 'S4R5',
    'S8R', 'S8R5',
    'S9R5',
    'STRI3',
    'STRI65',
    'SC8R']
surface_elems = [
    'SFM3D3',
    'SFM3D4', 'SFM3D4R',
    'SFM3D6',
    'SFM3D8', 'SFM3D8R']
solid3d_elems = [
    'C3D4', 'C3D4H',
    'C3D6', 'C3D6H',
    'C3D8', 'C3D8I', 'C3D8H', 'C3D8R', 'C3D8RH', 'C3D10',
    'C3D10H', 'C3D10M', 'C3D10MH',
    'C3D15', 'C3D15H',
    'C3D20', 'C3D20H', 'C3D20R', 'C3D20RH',]
rigid_elems = [
    'R2D2', 'RB2D2', 'RB3D2', 'RAX2', 'R3D3', 'R3D4',
    ]

def writeSection(fil, prop):
    """Write an element section.

    prop is a an element property record with a section and eltype attribute
    """
    print("WRITE SECTION %s" % prop)
    out = ""
    setname = esetName(prop)
    el = prop.section
    eltype = prop.eltype.upper()
    mat = el.material
    if mat is not None:
        print(" Writing material %s" % mat.name)
        fil.write(fmtMaterial(mat))

    if eltype in connector_elems:
        fil.write(fmtConnectorSection(el, setname))

    elif eltype in spring_elems:
        fil.write(fmtSpring(el, setname))

    elif eltype in dashpot_elems:
        fil.write(fmtDashpot(el, setname))

    elif eltype in frame_elems:
        fil.write(fmtFrameSection(el, setname))

    elif eltype in truss_elems:
        if el.sectiontype.upper() == 'GENERAL':
            fil.write("""*SOLID SECTION, ELSET=%s, MATERIAL=%s
%s
""" %(setname, el.material.name, float(el.cross_section)))
        elif el.sectiontype.upper() == 'CIRC':
            fil.write("""*SOLID SECTION, ELSET=%s, MATERIAL=%s
%s
""" %(setname, el.material.name, float(el.radius)**2*pi))

    ############
    ##BEAM elements
    ##########################
    elif eltype in beam_elems:
        if el.integrate:
            fil.write(fmtBeamSection(el, setname))
        else:
            fil.write(fmtGeneralBeamSection(el, setname))

    ############
    ## SHELL elements
    ##########################
    elif eltype in shell_elems:
        fil.write(fmtShellSection(el, setname, mat.name))

    ############
    ## SURFACE elements
    ##########################
    elif eltype in surface_elems:
        if el.sectiontype.upper() == 'SURFACE':
            if el.density:
                fil.write("""*SURFACE SECTION, ELSET=%s, DENSITY=%s \n""" % (setname, el.density))
            else:
                fil.write("""*SURFACE SECTION, ELSET=%s \n""" % setname)

    ############
    ## MEMBRANE elements
    ##########################
    elif eltype in membrane_elems:
        if el.sectiontype.upper() == 'MEMBRANE':
            if mat is not None:
                fil.write("""*MEMBRANE SECTION, ELSET=%s, MATERIAL=%s
%s \n""" % (setname, mat.name, float(el.thickness)))


    ############
    ## 3DSOLID elements
    ##########################
    elif eltype in solid3d_elems:
        if el.sectiontype.upper() == 'SOLID':
            if mat is not None:
                fil.write(fmtSolidSection(el, setname, mat.name))

    ############
    ## 2D SOLID elements
    ##########################
    elif eltype in solid2d_elems:
        if el.sectiontype.upper() == 'SOLID':
            if mat is not None:
                fil.write(fmtSolidSection(el, setname, mat.name))

    ############
    ## RIGID elements
    ##########################
    elif eltype in rigid_elems:
        if el.sectiontype.upper() == 'RIGID':
            # refnode can be setname or number
            # do not test for int type, because it might be np.intx
            if not isinstance(el.refnode, str):
                el.refnode += 1
            out = "*RIGID BODY, ELSET=%s, REFNODE=%s" % (setname, el.refnode)
            if el.density is not None:
                out += ", DENSITY=%s" % el.density
            if el.thickness is not None:
                out += "\n%s" % el.thickness
            out += '\n'
            fil.write(out)

    ############
    ## POINT MASS elements
    ##########################
    elif eltype in pointmass_elems:
        if el.sectiontype.upper() == 'MASS':
            if el.mass:
                fil.write("*MASS, ELSET=%s\n%s\n" % (setname, el.mass))

    ############
    ## UNSUPPORTED elements
    ##########################
    else:
        pf.warning('Sorry, element type %s is not yet supported' % eltype)


#
# TODO: should we remove option of specifying nonzero bound values?
#
def writeBoundaries(fil, prop):
    """Write nodal boundary conditions.

    prop is a list of node property records having the 'bound' key.

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
      The user can set op='NEW' to remove the previous conditions.
      This will also remove initial conditions.

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
    for p in prop:
        setname = nsetName(p)
        fil.write("*BOUNDARY")
        if p.op is None:
            fil.write(", OP=MOD")
        else:
            fil.write(", OP=%s" % p.op)
        if p.ampl is not None:
            fil.write(", AMPLITUDE=%s" % p.ampl)
        if p.options is not None:
            fil.write(p.options)
        fil.write("\n")

        if isinstance(p.bound, str):
            fil.write("%s, %s\n" % (setname, p.bound))
        elif isInt(p.bound[0]):
            for b in range(6):
                if p.bound[b]==1:
                    fil.write("%s, %s\n" % (setname, b+1))
        elif isinstance(p.bound[0], tuple):
            for b in p.bound:
                dof = b[0]+1
                fil.write("%s, %s, %s, %s\n" % (setname, dof, dof, b[1]))

#
# TODO: explaine what 'resetting' a condition means.
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

    - op (opt): 'NEW' (default) or 'MOD'. By default, the boundary conditions
      are applied as new values in the current step.
      The user can set op='MOD' to add the specified conditions to the already
      existing ones.

    - ampl (opt): string: specifies the name of an amplitude that is to be
      multiplied with the values to have the time history of the variable.

    - options (opt): string that is added to the command line.

    """
    for p in prop:
        setname = nsetName(p)
        fil.write("*BOUNDARY, TYPE=%s" % btype.upper())
        if p.op is None:
            fil.write(", OP=NEW")
        else:
            fil.write(", OP=%s" % p.op)
        if p.ampl is not None:
            fil.write(", AMPLITUDE=%s" % p.ampl)
        if p.options is not None:
            fil.write(p.options)
        fil.write("\n")
        data = p[btype[:5]]
        if data:
            for v in data:
                dof = v[0]+1
                fil.write("%s, %s, %s, %s\n" % (setname, dof, dof, v[1]))


def writeCloads(fil, prop):
    """Write cloads.

    prop is a list of node property records that should be scanned for
    displ attributes to write.

    By default, the loads are applied as new values in the current step.
    The user can set op='MOD' to add the loads to already existing ones.
    """
    for p in prop:
        setname = nsetName(p)
        fil.write("*CLOAD")
        if p.op is None:
            fil.write(", OP=NEW")
        if p.op is not None:
            fil.write(", OP=%s" % p.op)
        if p.ampl is not None:
            fil.write(", AMPLITUDE=%s" % p.ampl)
        fil.write("\n")
        for v in p.cload:
            dof = v[0]+1
            fil.write("%s, %s, %s\n" % (setname, dof, v[1]))


def writeCommaList(fil,*args):
    """Write a list of values comma-separated to fil"""
    fil.write(', '.join([str(i) for i in args]))


def writeDloads(fil, prop):
    """Write Dloads.

    prop is a list of elem property records having an attribute dload.

    By default, the loads are applied as new values in the current step.
    The user can set op='MOD' to add the loads to already existing ones.
    """
    for p in prop:
        setname = esetName(p)
        fil.write("*DLOAD")
        if p.op is None:
            fil.write(", OP=NEW")
        if p.op is not None:
            fil.write(", OP=%s" % p.op)
        if p.ampl is not None:
            fil.write(", AMPLITUDE=%s" % p.ampl)
        fil.write("\n")
        data = [setname, p.dload.label, p.dload.value]
        if p.dload.dir is not None:
            data += p.dload.dir
        writeCommaList(fil,*data)
        fil.write('\n')


def writeDsloads(fil, prop):
    """Write Dsloads.

    prop is a list property records having an attribute dsload

    By default, the loads are applied as new values in the current step.
    The user can set op='MOD' to add the loads to already existing ones.
    """
    for p in prop:
        fil.write("*DSLOAD")
        if p.op is None:
            fil.write(", OP=NEW")
        if p.op is not None:
            fil.write(", OP=%s" % p.op)
        if p.ampl is not None:
            fil.write(", AMPLITUDE=%s" % p.ampl)
        fil.write("\n")
        fil.write("%s, %s, %s\n" % (p.dsload.surface, p.dsload.label, p.dsload.value))

#######################################################
# General model data
#

def writeAmplitude(fil, prop):
    for p in prop:
        fil.write("*AMPLITUDE, NAME=%s, DEFINITION=%s, TIME=%s\n" % (p.name, p.amplitude.type, p.amplitude.atime))
        for i, v in enumerate(p.amplitude.data):
            fil.write("%s, %s," % tuple(v))
            if i % 4 == 3:
                fil.write("\n")
        if i % 4 != 3:
            fil.write("\n")


### Output requests ###################################
# Output: goes to the .odb file (for postprocessing with Abaqus/CAE)
# Result: goes to the .fil file (for postprocessing with other means)
#######################################################


def writeNodeOutput(fil,kind,keys,set='Nall'):
    """ Write a request for nodal result output to the .odb file.

    - `keys`: a list of NODE output identifiers
    - `set`: a single item or a list of items, where each item is either
      a property number or a node set name for which the results should
      be written
    """
    output = 'OUTPUT'
    if isinstance(set, str) or isInt(set):
        set = [ set ]
    for i in set:
        if isInt(i):
            setname = Nset(str(i))
        else:
            setname = i
        s = "*NODE %s, NSET=%s" % (output, setname)
        fil.write("%s\n" % s)
        for key in keys:
            fil.write("%s\n" % key)


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


def writeElemOutput(fil,kind,keys,set='Eall'):
    """ Write a request for element output to the .odb file.

    - `keys`: a list of ELEMENT output identifiers
    - `set`: a single item or a list of items, where each item is either
      a property number or an element set name for which the results should
      be written
    """
    output = 'OUTPUT'

    if isinstance(set, str) or isInt(set):
        set = [ set ]
    for i in set:
        if isInt(i):
            setname = Eset(str(i))
        else:
            setname = i
        s = "*ELEMENT %s, ELSET=%s" % (output, setname)
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



#~ Fi this function works like the previous one(if extra is a str)
# but now extra can be also a list of Dict .This is more convenient  if more addictional lines
# need to be written at the step level for type history.
def writeModelProps(fil, prop):
    """_ BAD STRUCTURE Write model props for this step

    extra : str
             : list of Dict. each Dict is a new line.Only 2 keys are dedicated

                REQUIRED
                    -keyword =  abaqus keyword name

                OPTIONAL
                    -data = list or array of numerical data for any additional data line

                    All other keys have name equal to the ABAQUS keywords and value equal to parameter setting
                    if an ABAQUS keyword does not have a value to be the Dict value must be an empty string

                EXAMPLE
                P.Prop(tag='step1',extra='*CONTACT CONTROLS , AUTOMATIC TOLERANCES\n')
                P.Prop(tag='step1',extra=[Dict({'keyword':'CONTACT CONTROLS','AUTOMATIC TOLERANCES':''})])
    """
    for p in prop:
        if p.extra:
            if isinstance(p.extra, str):
                fil.write(p.extra)
            elif isinstance(p.extra, list):
                cmd = ''
                for l in p.extra:
                    l = CDict(l) # to avoid keyerrors if l.data is not a key
                    cmd += '*%s'%l['keyword']
                    cmd += fmtOptions(utils.removeDict(l, ['keyword', 'data']))
                    cmd += '\n'
                    if l.data is not None:
                        cmd += fmtData1d(l.data) + '\n'
                fil.write(cmd.upper())


##################################################
## Some classes to store all the required information
##################################################


#
# This is TOO complex. We should restrict the way users can specify things.
#
class Interaction(Dict):
    """A Dict for setting surface interactions

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
            cmd += ',NAME = %s' % self.name
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
            writeBoundaries(fil, prop)

        for btype in [ 'displacement', 'velocity', 'acceleration' ]:
            shorttype = btype[:5]
            prop = propDB.getProp('n', tag=self.tags, attr=[shorttype])
            if prop:
                print("  Writing step prescribed %s" % btype)
                writeDisplacements(fil, prop, btype)

        prop = propDB.getProp('n', tag=self.tags, attr=['cload'])
        if prop:
            print("  Writing step cloads")
            writeCloads(fil, prop)

        prop = propDB.getProp('e', tag=self.tags, attr=['dload'])
        if prop:
            print("  Writing step dloads")
            writeDloads(fil, prop)

        prop = propDB.getProp('', tag=self.tags, attr=['dsload'])
        if prop:
            print("  Writing step dsloads")
            writeDsloads(fil, prop)

        prop = propDB.getProp('', tag=self.tags)
        if prop:
            print("  Writing step model props")
            writeModelProps(fil, prop)

        print("  Writing output")
        for i in out + self.out:
            if i.kind is None:
                fil.write(i.fmt())
            if i.kind == 'N':
                writeNodeOutput(fil,**i)
            elif i.kind == 'E':
                writeElemOutput(fil,**i)

        if res and self.analysis == 'EXPLICIT':
            writeFileOutput(fil, resfreq, timemarks)
        for i in res + self.res:
            if i.kind == 'N':
                writeNodeResult(fil,**i)
            elif i.kind == 'E':
                writeElemResult(fil,**i)
        fil.write("*END STEP\n")


class Output(Dict):
    """A request for output to .odb and history.

    Parameters:

    - `type`: 'FIELD' or 'HISTORY'
    - `kind`: None, 'NODE', or 'ELEMENT' (first character suffices)
    - `extra`: an extra string to be added to the command line. This
      allows to add Abaqus options not handled by this constructor.
      The string will be appended to the command line preceded by a comma.

    For kind=='':

    - `variable`: 'ALL', 'PRESELECT' or ''

    For kind=='NODE' or 'ELEMENT':

    - `keys`: a list of output identifiers (compatible with kind type)
    - `set`: a single item or a list of items, where each item is either
      a property number or a node/element set name for which the results
      should be written. If no set is specified, the default is 'Nall'
      for kind=='NODE' and 'Eall' for kind='ELEMENT'
    """

    def __init__(self,kind=None,keys=None,set=None,type='FIELD',variable='PRESELECT',extra='',**options):
        """ Create a new output request."""
        if 'history' in options:
            pf.warning("The `history` argument in an output request is deprecated.\nPlease use `type='history'` instead.")
        if 'numberinterval' in options:
            pf.warning("The `numberinterval` argument in an output request is deprecated.\nPlease use the `extra` argument instead.")

        if kind:
            kind = kind[0].upper()
        if set is None:
            set = "%sall" % kind
        Dict.__init__(self, {'kind':kind})
        if kind is None:
            self.update({'type':type,'variable':variable,'extra':extra})
        else:
            self.update({'keys':keys,'set':set})


    def fmt(self):
        """Format an output request.

        Return a string with the formatted output command.
        """
        out = ['*OUTPUT', self.type.upper()]
        if self.variable:
            out.append('VARIABLE=%s' % self.variable.upper())
        if self.extra:
            out.append(self.extra)
        return ', '.join(out)+'\n'


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

        nnod = self.model.nnodes()
        print("Writing %s nodes" % nnod)
        writeNodes(fil, self.model.coords)

        print("Writing node sets")
        fil.write(fmtSectionHeading("NODE SETS"))
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
            fil.write(fmtTransform(p.name, p.csys))

        print("Writing element sets")
        fil.write(fmtSectionHeading("ELEMENT SETS"))
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
                    grpname = Eset('grp', i, setname)
                    subsetname = Eset(p.nr, 'grp', i, setname)
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
            writeBoundaries(fil, prop)

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
    If an eltype is specified, it will oerride the value stored in the mesh.
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
