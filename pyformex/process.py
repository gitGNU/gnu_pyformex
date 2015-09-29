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
"""A class for executing external commands.

This is a wrapper around the standard Python :class:`subprocess.Popen` class
"""
from __future__ import print_function

import time
import subprocess
import threading
import shlex
import os

class Process(subprocess.Popen):
    """A subprocess for running an external command.

    This is a subclass of Python's :class:`subprocess.Popen` class, providing
    some extra functionality:

    - It stores the specified command

    - If a string is passed as command and shell is False, the string is
      automatically tokenized into an args list.

    - stdout and stderr default to subprocess.PIPE instead of None.

    - stdin, stdout and stderr can be file names. They will be replaced
      with the opened files (in mode 'r' for stdin, 'w' for the others).

    - After the command has terminated, the Process instance has three
      attributes sta, out and err, providing the return code, standard
      output and standard error of the command.

    - If 'shell=True' is specified, and no executable is specified, it sets
      executable to the value of the environment variable 'SHELL'.

    Parameters:

    - `cmd`: string or args list. If a string, it is the command as it should
      entered in a shell. If an args list, args[0] is the executable to run
      and the remainder are the arguments to be passed.
    - `timeout`: float. If > 0.0, the subprocess will be terminated
      or killed after this number of seconds have passed.
    - `wait`: bool. If True (default), the caller waits for the Process
      to terminate. Setting this value to False will allow the caller to
      continue, but it will not be able to retrieve the standard output
      and standard error of the process.

    Any other parameters are passed to the :class:`subprocess.Popen`
    initialization. See the Python documentation for details.
    Some interesting ones:

    - `shell`: bool. Default False. If True, the command will be run in a
      new shell. This may cause problems with killing the command and also
      poses a security risk.
    - `executable`: string. The full path name of the program to be executed.
      This can be used to specify the real executable if the program specified
      in `cmd` is not in your PATH, or, with `shell == True`, if you want
      to use another shell than the default. Note that Process uses a default
      shell equal to the SHELL variable, while Python uses `/bin/sh` by default.
    - `stdout`, `stderr`: Standard output and error output. See Python docs
      for subprocess.Popen. Here, they default to PIPE, allowing the caller
      to grab the output of the command. Set them to an open file object to
      redirect output to that file.

    """

    gracetime = 2

    def __init__(self,cmd,timeout,wait,**kargs):

        self.cmd = cmd

        shell = bool(kargs.get('shell', False))
        if isinstance(cmd, str) and shell is False:
            # Tokenize the command line
            cmd = shlex.split(cmd)

        if shell and 'executable' not in kargs:
            kargs['executable'] = os.environ['SHELL']

        for f in [ 'stdin', 'stdout', 'stderr' ]:
            if f not in kargs or kargs[f] is None:
                kargs[f] = subprocess.PIPE
            elif f in kargs and isinstance(kargs[f], str):
                if f.endswith('in'):
                    mode = 'r'
                else:
                    mode = 'w'
                kargs[f] = open(kargs[f], mode)
        self.kargs = kargs

        try:
            self.failed = False
            subprocess.Popen.__init__(self,cmd,**kargs)
        except:
            self.failed = True
            # Set a return code to mark the process finished
            self.returncode = 127
            # This is also the bash shell exit code on nonexistent executable

        self.out = self.err = None
        self.timeout = self.timedout = False
        # Should we provide non-run mode??
        self.run(timeout,wait)


    @property
    def sta(self):
        return self.returncode


    def run(self,timeout=None,wait=True):
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
        self.timeout = timeout
        self.timedout = False
        if timeout and float(timeout) > 0.0:
            # Start a timer to terminate the subprocess
            t = threading.Timer(timeout, Process.terminate_on_timeout, [self])
            t.start()
        else:
            t = None

        if wait:
            # Wait for the process to finish and retrieve its stdout/stdin
            out, err = self.communicate()
            if out is not None:
                out = out.decode(encoding='UTF-8')
            if err is not None:
                err = err.decode(encoding='UTF-8')
            self.out, self.err = out,err
            #pf.debug("Command output %s %s" % (type(out),type(err)),pf.DEBUG.UNICODE)

        if t:
            # Cancel the timer if one was started
            t.cancel()


    def terminate_on_timeout(self):
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


### End
