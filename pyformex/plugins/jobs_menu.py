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
"""Jobs Menu

"""
from __future__ import print_function

import pyformex as pf
from pyformex import utils
from pyformex.gui import menu

from numpy import *
from pyformex.formex import *
from pyformex.gui.draw import *
from pyformex.opengl.colors import *

import os


def about():
    showInfo("""Jobs.py

This is pyFormex plugin allowing the user to
- submit computational jobs to a cluster,
- check available job results on a remote host,
- copy job results to the local workstation,
- execute a command on the remote host.

While primarily intended for use with the BuMPer cluster at
IBiTech-bioMMeda, we have made this plugin available to the
general public, as an example of how to integrate external
commands and hosts into a pyFormex menu.

In order for these commands to work, you need to have `ssh`
access to the host system.
""")


def configure():
    from pyformex.gui.prefMenu import updateSettings

    dia = None

    def close():
        dia.close()

    def accept(save=False):
        dia.acceptData()
        res = dia.results
        res['_save_'] = save
        if res['_addhost_']:
            hosts = pf.cfg['jobs/hosts']
            if res['_addhost_'] not in hosts:
                hosts.append(res['_addhost_'])
            res['jobs/hosts'] = sorted(hosts)
            res['jobs/host'] = res['_addhost_']
        pf.debug(res)
        updateSettings(res)

    def acceptAndSave():
        accept(save=True)

    def autoSettings(keylist):
        return [_I(k, pf.cfg[k]) for k in keylist]

    jobs_settings = [
        _I('jobs/host', pf.cfg.get('jobs/host', 'localhost'), text="Host", tooltip="The host machine where your job input/output files are located.", choices=pf.cfg.get('jobs/hosts', ['localhost'])), #,buttons=[('Add Host',addHost)]),
        _I('jobs/inputdir', pf.cfg.get('jobs/inputdir', 'bumper/requests'), text="Input directory"),
        _I('jobs/outputdir', pf.cfg.get('jobs/outputdir', 'bumper/results'), text="Output directory"),
        _I('_addhost_', '', text="New host", tooltip="To set a host name that is not yet in the list of hosts, you can simply fill it in here."),
        ]

    dia = widgets.InputDialog(
        caption='pyFormex Settings',
        store=pf.cfg,
        items=jobs_settings,
        actions=[
            ('Close', close),
            ('Accept and Save', acceptAndSave),
            ('Accept', accept),
        ])
    dia.show()


def getRemoteDirs(host, userdir):
    """Get a list of all subdirs in userdir on host.

    The host should be a machine where the user has ssh access.
    The userdir is relative to the user's home dir.
    """
    cmd = "ssh %s 'cd %s;ls -F|egrep \".*/\"'" % (host, userdir)
    P = utils.command(cmd, shell=True)
    if P.sta:
        dirs = []
    else:
        dirs = [ j.strip('/') for j in P.out.split('\n') ]
    return dirs


## def getRemoteFiles(host,userdir):
##     """Get a list of all files in userdir on host.

##     The host should be a machine where the user has ssh access.
##     The userdir is relative to the user's home dir.
##     """
##     cmd = "ssh %s 'cd %s;ls -F'" % (host,userdir)
##     P = utils.command(cmd,shell=True)
##     if P.sta:
##         P.out = ''
##     dirs = P.out.split('\n')
##     dirs = [ j.strip('/') for j in dirs ]
##     return dirs


def transferFiles(host, userdir, files, targetdir):
    """Copy files from userdir on host to targetdir.

    files is a list of file names.
    """
    files = [ '%s:%s/%s' % (host, userdir.rstrip('/'), f) for f in files ]
    cmd = "scp %s %s" % (' '.join(files), targetdir)
    P = utils.command(cmd)
    return P.sta


def rsyncFiles(srcdir, tgtdir, include=['*'], exclude=[], exclude_first=False, rsh='ssh -q', chmod='ug+rwX,o-rwx', opts='-rv'):
    """Transfer files remotely using rsync

    Parameters:

    - `srcdir`: string: path from where to copy files. The path may be relative
      or absolute, and it can containing a leading 'host:' part to specify a
      remote directory (if `tgtdir` does not contain one).
    - `tgtdir`: string: path where to copy files to. The path may be relative
      or absolute, and it can containing a leading 'host:' part to specify a
      If tgtdir does not exist, it is created (thought the parent should exist).
      remote directory (if `srcdir` does not contain one).
    - `include`: list of strings: files to include in the copying process.
    - `exclude`: list of strings: files to exclude from the copying process.
    - `rsh`: string: the remote shell command to be used.
    - `chmod`: string: the permissions settings on the target system.
    - `opts`: string: the

    The includes are applied before the excludes. The first match will decide
    the outcome. The default is to recursively copy all files from `srcdir` to
    `tgtdir`. Other typical uses:

    - Copy some files from srcdir to tgtdir::

        rsyncFiles(src,tgt,include=['*.png','*.jpg'],exclude=['*'])

    - Copy all but some files from srcdir to tgtdir::

        rsyncFiles(src,tgt,exclude=['*.png','*.jpg'],exclude_first=True)

    Returns the Process used to execute the command. If the -v option
    is included in `opts`, then the Process.out atribute will contain
    the list of files transfered.

    Remarks:

    - You need to have no-password ssh access to the remote systems
    - You need to have rsync installed on source and target systems.

    """
    include = ' '.join(["--include '%s'" % i for i in include])
    exclude = ' '.join(["--exclude '%s'" % i for i in exclude])
    if exclude_first:
        include,exclude = exclude,include
    cmd = "rsync -e '%s' --chmod=%s %s %s %s/ %s %s" % (rsh, chmod, include, exclude, srcdir, tgtdir, opts)
    P = utils.command(cmd,shell=True)
    return P


def submitJob(srcdir,tgtdir,include=[],delete_old=True):
    """Submit a cluster job in srcdir to the tgtdir.

    This will copy the specified include files from srcdir to the tgtdir,
    making sure that a file '*.request' is only copied after all other files
    have been copied.
    If no includes are given, all files in the srcdir are copied.

    For example, to submit a simple abaqus job from a folder with
    multiple job files, you can do::

      submitJob('myjobdir','bumpfs1:bumper/requests/jobname',include=['*.inp'])

    To submit a job having its own input folder equal to the job name, do::

      submitJob('myjobdir/jobname','bumpfs1:bumper/requests/jobname')

    """
    if delete_old:
        P = rsyncFiles(srcdir,tgtdir,include=[],exclude=['*'],exclude_first=True,opts=' -rv --delete --delete-excluded')
        if P.sta:
            pf.warning("Could not delete old files from request folder!")

    if include:
        P = rsyncFiles(srcdir,tgtdir,include=include,exclude=['*'])
    else:
        P = rsyncFiles(srcdir,tgtdir,exclude=['*.request'],include=include,exclude_first=True)
    if P.sta:
        print(P.out)
    else:
        P = rsyncFiles(srcdir,tgtdir,include=['*.request'],exclude=['*'])
    if P.sta:
        pf.warning("Some error occurred during file transfer!")


def remoteCommand(host=None,command=None):
    """Execute a remote command.

    host: the hostname where the command is executed
    command: the command line
    """
    if host is None or command is None:
        res = askItems(
            [ _I('host', choices=['bumpfs', 'bumpfs2', '--other--']),
              _I('other', '', text='Other host name'),
              _I('command', 'hostname'),
              ],
            enablers = [('host', '--other--', 'other')],
            )

    if res:
        host = res['host']
        if host == '--other--':
            host = res['other']
        command = res['command']

    if host and command:
        P = utils.command(['ssh', host, command])
        print(P.out)
        return P.sta


def runLocalProcessor(filename='',processor='abaqus'):
    """Run a black box job locally.

    The black box job is a command run on an input file.
    If a filename is specified and is not an absolute path name,
    it is relative to the current directory.
    """
    if not filename:
        filename = askFilename(pf.cfg['workdir'], filter="Abaqus input files (*.inp)", exist=True)
    cpus = '4'
    if filename:
        jobname = os.path.basename(filename)[:-4]
        dirname = os.path.dirname(filename)
        if dirname == '':
            dirname = '.'
        cmd = pf.cfg['jobs/cmd_%s' % processor]
        cmd = cmd.replace('$F', jobname)
        cmd = cmd.replace('$C', cpus)
        cmd = "cd %s;%s" % (dirname, cmd)
        P = utils.command(cmd, shell=True)
        print(P.out)


def runLocalAbaqus(filename=''):
    runLocalProcessor(filename, processor='abaqus')

def runLocalCalculix(filename=''):
    runLocalProcessor(filename, processor='calculix')


def submitToCluster(filename=None):
    """Submit an Abaqus job to the cluster."""
    if not filename:
        filename = askFilename(pf.cfg['workdir'], filter="Abaqus input files (*.inp)", exist=True)
    if filename:
        jobname = os.path.basename(filename)[:-4]
        dirname = os.path.dirname(filename)
        add_all = jobname == dirname
        res = askItems([
            _I('jobname', jobname, text='Cluster job name/directory'),
            _I('add_all', add_all, text='Include all the files in the input directory',tooltip='If unchecked, only the jobname.inp and jobname.request files comprise the job'),
            _I('ncpus', 4, text='Number of cpus', min=1, max=1024),
            _I('abqver', 'default', text='Abaqus Version', choices=pf.cfg['jobs/abqver']),
            _I('postabq', False, text='Run postabq on the results?'),
            ])
        if res:
            reqtxt = 'cpus=%s\n' % res['ncpus']
            reqtxt += 'abqver=%s\n' % res['abqver']
            if res['postabq']:
                reqtxt += 'postproc=postabq\n'
            host = pf.cfg.get('jobs/host', 'bumpfs')
            reqdir = pf.cfg.get('jobs/inputdir', 'bumper/requests')

            filereq = utils.changeExt(filename,'.request')
            with open(filereq,'w') as fil:
                fil.write(reqtxt)

            srcdir = os.path.dirname(filename)
            tgtdir = "%s:%s/%s" % (host, reqdir,jobname)
            if res['add_all']:
                include = []
            else:
                include = ['*.inp']
            submitJob(srcdir,tgtdir,include=include)


def killClusterJob(jobname=None):
    """Kill a job to the cluster."""
    res = askItems([('jobname', '')])
    if res:
        jobname = res['jobname']
        host = pf.cfg.get('jobs/host', 'mecaflix')
        reqdir = pf.cfg.get('jobs/inputdir', 'bumper/requests')
        cmd = "touch %s/%s.kill" % (reqdir, jobname)
        print(host)
        print(cmd)
        P = utils.command(['ssh', host, "%s" % cmd])
        print(P.out)


the_host = None
the_userdir = None
the_jobnames = None
the_jobname = None


def checkResultsOnServer(host=None,userdir=None):
    """Get a list of job results from the cluster.

    Specify userdir='bumper/running' to get a list of running jobs.
    """
    global the_host, the_userdir, the_jobnames
    if host is None or userdir is None:
        res = askItems(
            [ _I('host', None, 'select', choices=['bumpfs', 'bumpfs2', 'other']),
              _I('other', '', text='Other host name'),
              _I('status', None, 'select', choices=['results', 'running', 'custom']),
              _I('userdir', 'bumper/results/', text='Custom user directory'),
            ], enablers=[
                ('status', 'custom', 'userdir')
                ]
            )
        if not res:
            return
        host = res['host']
        if host == 'other':
            host = res['other']
        status = res['status']
        if status in ['results', 'running']:
            userdir = 'bumper/%s/' % status
        else:
            userdir = res['userdir']

    jobnames = getRemoteDirs(host, userdir)
    if jobnames:
        the_host = host
        the_userdir = userdir
        the_jobnames = jobnames
    else:
        the_host = None
        the_userdir = None
        the_jobnames = None
    print(the_jobnames)


def changeTargetDir(field):
    from pyformex.gui import draw
    return draw.askDirname(field.value())


def getResultsFromServer(jobname=None,targetdir=None,ext=['.fil']):
    """Get results back from cluster."""
    global the_jobname
    print("getRESULTS")
    if targetdir is None:
        targetdir = pf.cfg['workdir']
    if jobname is None:
        if the_jobnames is None:
            jobname_input = [
                ('host', pf.cfg['jobs/host']),
                ('userdir', 'bumper/results'),
                ('jobname', ''),
                ]
        else:
            jobname_input = [
                _I('jobname', the_jobname, choices=the_jobnames)
                ]

        print(jobname_input)
        res = askItems(jobname_input + [
            _I('target dir', targetdir, itemtype='button', func=changeTargetDir),
            _I('create subdir', False, tooltip="Create subdir (with same name as remote) in target dir"),
            ('_post.py', True),
            ('.fil', False),
            ('.odb', False),
            _I('other', [], tooltip="A list of '.ext' strings"),
            ])
        if res:
            host = res.get('host', the_host)
            userdir = res.get('userdir', the_userdir)
            jobname = res['jobname']
            targetdir = res['target dir']
            if res['create subdir']:
                targetdir = os.path.join(targetdir, jobname)
                mkdir(targetdir)
            ext = [ e for e in ['.fil', '_post.py', '.odb'] if res[e] ]
            res += [ e for e in res['other'] if e.startswith('.') ]
    if jobname and ext:
        files = [ '%s%s' % (jobname, e) for e in ext ]
        userdir = "%s/%s" % (userdir, jobname)
        pf.GUI.setBusy(True)
        if transferFiles(host, userdir, files, targetdir) == 0:
            the_jobname = jobname
            print("Files succesfully transfered")
        pf.GUI.setBusy(False)



####################################################################
######### MENU #############

_menu = 'Jobs'

def create_menu():
    """Create the Jobs menu."""
    MenuData = [
        ("&About", about),
        ("&Configure Job Plugin", configure),
        ("&Run local Abaqus job", runLocalAbaqus),
        ("&Run local Calculix job", runLocalCalculix),
        ("&Submit Abaqus Job", submitToCluster),
        ("&Kill Cluster Job", killClusterJob),
        ("&List available results on server", checkResultsOnServer),
        ("&Get results from server", getResultsFromServer),
        ("&Execute remote command", remoteCommand),
        ("---", None),
        ("&Reload Menu", reload_menu),
        ("&Close Menu", close_menu),
        ]
    return menu.Menu(_menu, items=MenuData, parent=pf.GUI.menu, before='help')


def show_menu():
    """Show the menu."""
    if not pf.GUI.menu.item(_menu):
        create_menu()


def close_menu():
    """Close the menu."""
    pf.GUI.menu.removeItem(_menu)


def reload_menu():
    """Reload the menu."""
    close_menu()
    show_menu()


####################################################################
######### What to do when the script is executed ###################

if __name__ == '__draw__':

    reload_menu()

# End

