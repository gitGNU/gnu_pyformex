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
"""Animals

Show models of animals retrieved over the web.
"""
from __future__ import absolute_import, division, print_function


_status = 'checked'
_level = 'advanced'
_topics = ['geometry']
_techniques = ['vtk', 'web']

from pyformex import utils
utils.requireModule('vtk')
from pyformex.gui.draw import *
from pyformex.plugins.web import show3d

animals = {
    'dd4e920d': 'Elephant',
    'b0d8aa3a': 'Gorilla',
    '9dce6c01': 'Flock',
    '60d7244e': 'Seahorse',
    '63227524': 'Snake',
    'd24a0708': 'Dog',
    '3a6640cd': 'Fish',
    '21576988': 'Cow',
    'b7ea04dd': 'Cat',
    '8c63653f': 'Dinosaur',
    'cc794c75': 'Fish',
    '04ddea43': 'Camel',
    '75d11d7b': 'Dog',
    '5ca9a760': 'Turtle',
    '917049e4': 'Leopard',
    '6f77cd41': 'Rhino',
    'a6f95afa': 'Cage',
    '65d019e7': 'Cell',
    '0316721c': 'Chicken',
    'fb467425': 'Cage',
    '13748c9a': 'Butterfly',
    'c0cd1fcc': 'Seahorse',
    '8bd611bf': 'Snake',
    '943ffd34': 'Bird',
}


def run():
    resetAll()
    smooth()
    res = ask("""..

Animals
-------

This example requires that you have

- python-vtk installed on your machine
- a network connection to the internet

If not, you would better cancel now.
""",choices = ['Cancel','OK'])

    if res == 'OK':
        ranimals = utils.inverseDict(animals)

        res = askItems([_I('animal',choices=list(ranimals.keys()))])
        if res:
            show3d(ranimals[res['animal']])


if __name__ == '__draw__':
    run()

# End
