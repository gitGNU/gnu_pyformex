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

"""A class for holding results from Finite Element simulations.

"""
from __future__ import absolute_import, division, print_function


import pyformex as pf
from pyformex.arraytools import *
from pyformex.script import export
from pyformex.odict import OrderedDict

import re

class FeResult(object):
    """Finite Element Results Database.

    This class can hold a collection of results from a Finite Element
    simulation. While the class was designed for the post-processing
    of Abaqus (tm) results, it can be used more generally to store
    results from any program performing simulations over a mesh.

    pyFormex comes with an included program `postabq` that scans an
    Abaqus .fil output file and translates it into a pyFormex script.
    Use it as follows::

      postabq job.fil > job.py

    Then execute the created script `job.py` from inside pyFormex. This
    will create an FeResult instance with all the recognized results.

    The structure of the FeResult class very closely follows that
    of the Abaqus results database. There are some attributes
    with general info and with the geometry (mesh) of the domain.
    The simulation results are divided in 'steps' and inside each step
    in 'increments'. Increments are usually connected to incremental time
    and so are often the steps, though it is up to the user to interprete
    the time. Steps could just as well be different unrelated simulations
    performed over the same geometry.

    In each step/increment result block, individual values can be accessed
    by result codes. The naming mostly follows the result codes in Abaqus,
    but components of vector/tensor values are number starting from 0, as
    in Python and pyFormex.

    Result codes:

    - `U`: displacement vector
    - `U0`, `U1`, `U2` : x, y, resp. z-component of displacement
    - `S`: stress tensor
    - `S0` .. `S5`: components of the (symmetric) stress tensor:
       0..2 : x, y, z normal stress
       3..5 : xy, yz, zx shear stress
    """

    _name_ = '__FePost__'
    re_Skey = re.compile("S[0-5]")
    re_Ukey = re.compile("U[0-2]")

    def __init__(self,name=_name_,datasize={'U':3,'S':6,'COORD':3}):
        self.name = name
        self.datasize = datasize.copy()
        self.about = {'creator': pf.Version(),
                      'created': pf.StartTime,
                      }
        self.modeldone = False
        self.labels = {}
        self.nelems = 0
        self.nnodes = 0
        self.dofs = None
        self.displ = None
        self.nodid = None
        self.nodes = None
        self.elems = None
        self.nset = None
        self.nsetkey = None
        self.eset = None
        self.res = None
        self.hdr = None
        self.nodnr = 0
        self.elnr = 0

    def dataSize(self, key, data):
        if key in self.datasize:
            return self.datasize[key]
        else:
            return len(data)

    def Abqver(self, version):
        self.about.update({'abqver':version})

    def Date(self, date, time):
        self.about.update({'abqdate':date,'abqtime':time})

    def Size(self, nelems, nnodes, length):
        self.nelems = nelems
        self.nnodes = nnodes
        self.length = length
        self.nodid = -ones((nnodes,), dtype=int32)
        self.nodes = zeros((nnodes, 3), dtype=float32)
        self.elems = {}
        self.nset = {}
        self.eset = {}

    def Dofs(self, data):
        self.dofs = array(data)
        self.displ = self.dofs[self.dofs[:6] > 0]
        if self.displ.max() > 3:
            self.datasize['U'] = 6

    def Heading(self, head):
        self.about.update({'heading':head})

    def Node(self,nr,coords,normal=None):
        self.nodid[self.nodnr] = nr
        nn = len(coords)
        self.nodes[self.nodnr][:nn] = coords
        self.nodnr += 1

    def Element(self, nr, typ, conn):
        if typ not in self.elems:
            self.elems[typ] = []
        self.elems[typ].append(conn)

    def Nodeset(self, key, data):
        self.nsetkey = key
        self.nset[key] = asarray(data)

    def NodesetAdd(self, data):
        self.nset[self.nsetkey] = union1d(self.nset[self.nsetkey], asarray(data))

    def Elemset(self, key, data):
        self.esetkey = key
        self.eset[key] = asarray(data)

    def ElemsetAdd(self, data):
        self.eset[self.esetkey] = union1d(self.eset[self.esetkey], asarray(data))

    def Finalize(self):
        self.nid = inverseUniqueIndex(self.nodid)
        for k in self.elems.iterkeys():
            v = asarray(self.elems[k])
            self.elems[k] = asarray(self.nid[v])
        self.modeldone = True
        # we use lists, to keep the cases in order
        self.res = OrderedDict()
        self.step = None
        self.inc = None

    def Increment(self,step,inc,**kargs):
        """Add a new step/increment to the database.

        This method can be used to add a new increment to an existing step,
        or to add a new step and set the initial increment, or to just select
        an existing step/inc combination.
        If the step/inc combination is new, a new empty result record is created.
        The result record of the specified step/inc becomes the current result.
        """
        if not self.modeldone:
            self.Finalize()
        if step != self.step:
            if step not in self.res.keys():
                self.res[step] = OrderedDict()
            self.step = step
            self.inc = None
        res = self.res[self.step]
        if inc != self.inc:
            if inc not in res.keys():
                res[inc] = {}
            self.inc = inc
        self.R = self.res[self.step][self.inc]

    def EndIncrement(self):
        if not self.modeldone:
            self.Finalize()
        self.step = self.inc = -1

    def Label(self, tag, value):
        self.labels[tag] = value

    def NodeOutput(self, key, nodid, data):
        if key not in self.R:
            self.R[key] = zeros((self.nnodes, self.dataSize(key, data)), dtype=float32)
        if key == 'U':
            self.R[key][nodid-1][self.displ-1] = data
        elif key == 'S':
            n1 = self.hdr['ndi']
            n2 = self.hdr['nshr']
            ind = arange(len(data))
            ind[n1:] += (3-n1)
            #print(ind)
            self.R[key][nodid-1][ind] = data
        else:
            self.R[key][nodid-1][:len(data)] = data

    def ElemHeader(self,**kargs):
        self.hdr = dict(**kargs)

    def ElemOutput(self, key, data):
        if self.hdr['loc'] == 'na':
            self.NodeOutput(key, self.hdr['i'], data)

    def Export(self):
        """Align on the last increment and export results"""
        try:
            self.step = self.res.keys()[-1]
            self.inc = self.res[self.step].keys()[-1]
            self.R = self.res[self.step][self.inc]
        except:
            self.step = None
            self.inc = None
            self.R = None
        export({self.name:self, self._name_:self})
        print("Read %d nodes, %d elements" % (self.nnodes, self.nelems))
        if self.res is None:
            print("No results")
        else:
            print("Steps: %s" % self.res.keys())

    def do_nothing(*arg,**kargs):
        """A do nothing function to stand in for as yet undefined functions."""
        pass

    TotalEnergies = do_nothing
    OutputRequest = do_nothing
    Coordinates = do_nothing
    Displacements = do_nothing
    Unknown = do_nothing

    def setStepInc(self,step,inc=1):
        """Set the database pointer to a given step,inc pair.

        This sets the step and inc attributes to the given values, and puts
        the corresponding results in the R attribute. If the step.inc pair does
        not exist, an empty results dict is set.
        """
        try:
            self.step = step
            self.inc = inc
            self.R = self.res[self.step][self.inc]
        except:
            self.R = {}


    def getSteps(self):
        """Return all the step keys."""
        return self.res.keys()

    def getIncs(self, step):
        """Return all the incs for given step."""
        if step in self.res:
            return self.res[step].keys()

    def nextStep(self):
        """Skips to the start of the next step."""
        if self.step < self.getSteps()[-1]:
            self.setStepInc(self.step+1)

    def nextInc(self):
        """Skips to the next increment.

        The next increment is either the next increment of the current step,
        or the first increment of the next step.
        """
        if self.inc < self.getIncs(self.step)[-1]:
            self.setStepInc(self.step, self.inc+1)
        else:
            self.nextStep()

    def prevStep(self):
        """Skips to the start of the previous step."""
        if self.step > 1:
            self.setStepInc(self.step-1)

    def prevInc(self):
        """Skips to the previous increment.

        The previous increment is either the previous increment of the current
        step, or the last increment of the previous step.
        """
        if self.inc > 1:
            self.setStepInc(self.step, self.inc-1)
        else:
            if self.step > 1:
                step = self.step-1
                inc = self.getIncs(step)[-1]
            self.setStepInc(step, inc)


    def getres(self,key,domain='nodes'):
        """Return the results of the current step/inc for given key.

        The key may include a component to return only a single column
        of a multicolumn value.
        """
        components = '012'
        if self.re_Skey.match(key):
            if self.datasize['S']==3:
                components = '013'
            else:
                components = '012345'
        elif self.re_Ukey.match(key):
            if self.datasize['U']==2:
                components = '01'
            else:
                components = '012'
        comp = components.find(key[-1])
        if comp >= 0:
            key = key[:-1]
        if key in self.R:
            val = self.R[key]
            if comp in range(val.shape[1]):
                return val[:, comp]
            else:
                return val
        else:
            return None


    def printSteps(self):
        """Print the steps/increments/resultcodes for which we have results."""
        if self.res is not None:
            for i, step in self.res.items():
                for j, inc in step.items():
                    for k, v in inc.items():
                        if isinstance(v, ndarray):
                            data = "%s %s" % (v.dtype.kind, str(v.shape))
                        else:
                            data = str(v)
                        print("Step %s, Inc %s, Res %s (%s)" % (i, j, k, data))


#End
