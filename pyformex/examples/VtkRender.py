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
"""renderVTK

Create an interactive vtk window. Shows the correct sequence
of commands to remove any floating widget
"""
from __future__ import absolute_import, division, print_function


_status = 'flaky'
_level = 'advanced'
_topics = ['vtk','rendering']
_techniques =  ['vtk','rendering']

from pyformex.gui.draw import *


###
#
#  This gives a flaky user experience
#

def renderVTK(object,color=[0.,0.,0.],bkg=[1.,1.,1.]):
    """Display an objet in an interactive vtk render window.

    Parameters:

      - `object`: any object convertable to vtkPolyData
      - `color`: arraylike float (3,) storing RGB color values.
    """
    from vtk import vtkActor,vtkPolyDataMapper,vtkRenderer,vtkRenderWindow,vtkRenderWindowInteractor
    from pyformex.plugins.vtk_itf import convert2VPD,SetInput,Update
    from pyformex.arraytools import checkArray

    vpd = convert2VPD(object)
    color=checkArray(color,shape=(3,),kind='f')
    # creating the actors mapper
    mapper = vtkPolyDataMapper()
    mapper = SetInput(mapper,vpd)
    mapper = Update(mapper)

    # creating the actor
    actor = vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(color)
    actor.Modified()

    # creating the renderer
    ren = vtkRenderer()
    ren.SetBackground(bkg)
    ren.AddActor(actor)
    ren.ResetCamera()
    ren.GetActiveCamera().SetParallelProjection(1)

    #creating the render window
    renWin = vtkRenderWindow()
    renWin.SetOffScreenRendering(0)
    renWin.AddRenderer(ren)

    #creating the interactor
    iren = vtkRenderWindowInteractor()
    iren.SetRenderWindow(renWin)
    iren.Initialize()
    renWin.Render()  # this update the object in the renderer
    iren.Start()

    # closing the window
    renWin.Finalize()
    iren.TerminateApp()
    del renWin, iren

def run():
    S = TriSurface.read(getcfg('datadir')+'/horse.off')
    pause(msg="Use the Play button to proceed, close the VTK window to finish.")
    renderVTK(S,color=[0.1,0.4,0.2],bkg=[0,0,0])

if __name__ == '__draw__':
    run()

# End
