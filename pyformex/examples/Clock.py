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

"""Clock

"""
from __future__ import absolute_import, division, print_function


_status = 'checked'
_level = 'advanced'
_topics = []
_techniques = ['timer']

from pyformex.gui.draw import *
from pyformex import simple
from datetime import datetime
from pyformex.gui import QtCore

class AnalogClock(object):
    """An analog clock built from Formices"""

    def __init__(self,lw=2,mm=0.75,hm=0.85,mh=0.7,hh=0.6, sh=0.9):
        """Create an analog clock."""
        self.linewidth = lw
        self.circle = simple.circle()
        radius = Formex('l:2')
        self.mainmark = radius.divide([mm, 1.0])
        self.hourmark = radius.divide([hm, 1.0])
        self.mainhand = radius.divide([0.0, mh])
        self.hourhand = radius.divide([0.0, hh])
        if sh > 0.0:
            self.secshand = radius.divide([0.0, sh])
        else:
            self.secshand = None
        self.hands = []
        self.timer = None


    def draw(self):
        """Draw the clock (without hands)"""
        draw(self.circle, color='black', linewidth=self.linewidth)
        draw(self.mainmark.rosette(4, 90), color='black', linewidth=self.linewidth)
        draw(self.hourmark.rot(30).rosette(2, 30).rosette(4, 90),
             color='black', linewidth=0.5*self.linewidth)


    def drawTime(self,hrs,min,sec=None):
        """Draw the clock's hands showing the specified time.

        If no seconds are specified, no seconds hand is drawn.
        """
        hrot = - hrs*30. - min*0.5
        mrot = - min*6.
        undraw(self.hands)
        MH = draw(self.mainhand.rot(mrot), bbox=None, color='red', linewidth=self.linewidth)
        HH = draw(self.hourhand.rot(hrot), bbox=None, color='red', linewidth=self.linewidth)
        self.hands = [MH, HH]
        if self.secshand and sec:
            srot = - sec*6.
            SH = draw(self.secshand.rot(srot), bbox=None, color='orange', linewidth=0.5*self.linewidth)
            self.hands.append(SH)


    def drawNow(self):
        """Draw the hands showing the current time."""
        now = datetime.now()
        self.drawTime(now.hour, now.minute, now.second)
        breakpt("The clock has been stopped!")


    def run(self,granularity=1,runtime=100):
        """Run the clock for runtime seconds, updating every granularity."""
        if granularity > 0.0:
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(self.drawNow)
            self.timer.start(1000*granularity)
        if runtime > 0.0:
            self.timeout = QtCore.QTimer()
            self.timeout.timeout.connect(self.stop)
            self.timeout.setSingleShot(True)
            self.timeout.start(1000*runtime)


    def stop(self):
        """Stop a running clock."""
        print("STOP")
        if self.timer:
            self.timer.stop()


def run():
    reset()
    C = AnalogClock()
    C.draw()
    setDrawOptions({'bbox':None})
    res = askItems([_I('runtime', 15, text='Run time (seconds)')])
    if res and res['runtime'] > 0:
        C.drawNow()
        C.run()
        sleep(res['runtime'])
        C.stop()
        print(pf.scriptlock)

if __name__ == '__draw__':
    run()
# End
