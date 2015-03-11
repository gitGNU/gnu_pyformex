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
#
"""Framework for multi-processing in pyFormex

This module contains some functions to perform multiprocessing inside
pyFormex in a unified way.

"""
from __future__ import print_function


import pyformex as pf
from pyformex.arraytools import splitar

from multiprocessing import Pool, cpu_count, Process, Queue
import numpy as np


## def splitArgs(args,mask=None,nproc=-1,close=False):
##     """Split a number of data blocks over multiple processors.

##     Parameters:

##     - `args`: a list or tuple of data blocks. All array items in the list
##       should have the same first dimension.
##     - `nproc`: number of processors intended. If negative (default),
##       it is set equal to the number of processors detected.
##     - `close`: bool. If True, the elements where the arrays are
##       split are included in both blocks delimited by the element.

##     Returns a list of `nproc` lists. Each sublist contains the same
##     number of items as the input list and in the same order, whereby
##     the arrays are replaced by a slice of the array along the first
##     axes, and the non-array items are replicated as is.

##     This function uses :meth:`arraytools.splitar` for the splitting
##     of the arrays.

##     Example:

##     >>> for i in splitData([np.eye(5),'=>',np.arange(5)],3):
##     ...     print("%s %s %s" % tuple(i))
##     [[ 1.  0.  0.  0.  0.]
##      [ 0.  1.  0.  0.  0.]] => [0 1]
##     [[ 0.  0.  1.  0.  0.]] => [2]
##     [[ 0.  0.  0.  1.  0.]
##      [ 0.  0.  0.  0.  1.]] => [3 4]

##     """
##     if nproc < 0:
##         nproc = cpu_count()
##     split = [ splitar(d,nproc,close) if isinstance(d,np.ndarray) else [ d ] * nproc for d in data ]
##     return zip(*split)


def splitArgs(args,mask=None,nproc=-1,close=False):
    """Split data blocks over multiple processors.

    Parameters:

    - `args`: a list or tuple of data blocks. All items in the list
      that need to be split should be arrays with the same first dimension.
    - `mask`: list of bool, with same length as `args`. It flags which
      items in the `args` list are to be split. If not specified,
      all array type items will be split.
    - `nproc`: number of processors intended. If negative (default),
      it is set equal to the number of processors detected.
    - `close`: bool. If True, the elements where the arrays are
      split are included in both blocks delimited by the element.

    Returns a sequence of `nproc` tuples. Each tuple contains the same
    number of items as the input `args` and in the same order, whereby
    the (nonmasked) arrays are replaced by a slice of the array along
    its first axis, and the masked and non-array items are replicated
    as is.

    This function uses :meth:`arraytools.splitar` for the splitting
    of the arrays.

    Example:

    >>> for i in splitArgs([np.eye(5),'=>',np.arange(5)],nproc=3):
    ...     print("%s %s %s" % i)
    [[ 1.  0.  0.  0.  0.]
     [ 0.  1.  0.  0.  0.]] => [0 1]
    [[ 0.  0.  1.  0.  0.]] => [2]
    [[ 0.  0.  0.  1.  0.]
     [ 0.  0.  0.  0.  1.]] => [3 4]
    >>> for i in splitArgs([np.eye(5),'=>',np.arange(5)],mask=[1,0,0],nproc=3):
    ...     print("%s %s %s" % i)
    [[ 1.  0.  0.  0.  0.]
     [ 0.  1.  0.  0.  0.]] => [0 1 2 3 4]
    [[ 0.  0.  1.  0.  0.]] => [0 1 2 3 4]
    [[ 0.  0.  0.  1.  0.]
     [ 0.  0.  0.  0.  1.]] => [0 1 2 3 4]

    """
    if nproc < 0:
        nproc = cpu_count()
    if mask is None:
        mask = [ isinstance(a,np.ndarray) for a in args ]
    split = [ splitar(a,nproc,close) if m else [ a ] * nproc for a,m in zip(args,mask) ]
    return zip(*split)


def dofunc(arg):
    """Helper function for the multitask function.

    It expects a tuple with (function,args) as single argument.
    """
    func, args = arg
    return func(*args)


def multitask(tasks,nproc=-1):
    """Perform tasks in parallel.

    Runs a number of tasks in parallel over a number of subprocesses.

    Parameters:

    - `tasks` : a list of (function,args) tuples, where function is a
      callable and args is a tuple with the arguments to be passed to the
      function.
    - ` nproc`: the number of subprocesses to be started. This may be
      different from the number of tasks to run: processes finishing a
      task will pick up a next one. There is no benefit in starting more
      processes than the number of tasks or the number of processing units
      available. The default will set `nproc` to the minimum of these two
      values.
    """
    if nproc < 0:
        nproc = min(len(tasks), cpu_count())

    pf.debug("Multiprocessing using %s processors" % nproc, pf.DEBUG.MULTI)
#    if pf.scriptMode == 'script':
    if __name__ == '__draw__':
        if pf.warning("""..

Multiprocessing in 'script' mode
================================

You are trying to use multiprocessing while running in 'script' mode.
Multiprocessing in 'script' mode may cause pyFormex to hang indefinitely.
We strongly advice you to cancel the operation now and to run your
application in 'app' mode. Multiprocessing runs fine in 'app' mode.
""", actions=['Cancel', 'I know the risks and insist on continuing']) == 'Cancel':
            return

    pool = Pool(nproc)
    res = pool.map(dofunc, tasks)
    pool.close()
    return res


### Following is an alternative using Queues

def worker(input, output):
    """Helper function for the multitask function.

    This is the function executed by any of the processes started
    by the multitask function. It takes tuples (function,args) from
    the input queue, computes the results of the call function(args),
    and pushes these results on the output queue.

    Parameters:

    - `input`: Queue holding the tasks to be performed
    - `output`: Queue where the results are to be delivered
    """
    for func, args in iter(input.get, 'STOP'):
        result = func(*args)
        output.put(result)


def multitask2(tasks,nproc=-1):
    """Perform tasks in parallel.

    Runs a number of tasks in parallel over a number of subprocesses.

    Parameters:

    - `tasks` : a list of (function,args) tuples, where function is a
      callable and args is a tuple with the arguments to be passed to the
      function.
    - ` nproc`: the number of subprocesses to be started. This may be
      different from the number of tasks to run: processes finishing a
      task will pick up a next one. There is no benefit in starting more
      processes than the number of tasks or the number of processing units
      available. The default will set `nproc` to the minimum of these two
      values.
    """
    if nproc < 0:
        nproc = min(len(tasks), cpu_count())

    # Create queues
    task_queue = Queue()
    done_queue = Queue()

    # Submit tasks
    for task in tasks:
        task_queue.put(task)

    # Start worker processes
    for i in range(nproc):
        Process(target=worker, args=(task_queue, done_queue)).start()

    # Get results
    res = [ done_queue.get() for i in range(len(tasks)) ]

    # Tell child processes to stop
    for i in range(nproc):
        task_queue.put('STOP')

    # Return result
    return res


# End
