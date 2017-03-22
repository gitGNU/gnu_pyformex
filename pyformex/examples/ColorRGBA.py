##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see http://www.gnu.org/licenses/.
##
"""ColorRGBA

This example demonstrates the use of RGBA color model in drawing
operations.

"""
from __future__ import absolute_import, division, print_function


_status = 'checked'
_level = 'normal'
_topics = ['drawing']
_techniques = ['color', 'rgba', 'transparency']

from pyformex.gui.draw import *

def run():
    reset()
    clear()
    transparent(False)
    flat()
    nx,ny = 1,1
    F = Formex('4:0123').replic2(nx,ny).centered()
    G = F.scale(0.8)
    F1 = F.trl(0,1.2)
    G1 = G.trl(0,1.2)
    F.attrib(color = [[(1.,0,0),(0,1,0),(0,0,1),(1,0,1)]])
    F1.attrib(color = [[(1,0,0,0.0),(0,1,0,1),(0,0,1,1),(1,0,1,0)]])
    FA = draw(F)
    FB = draw(F1)
    draw(G)
    draw(G1)
    print("Colors of the left square:")
    print(FA.color)
    print("Colors of the right square:")
    print(FB.color)
    if pf.options.shader == 'alpha':
         showInfo("""..

These two colored squares were drawn with RGBA color mode using the alpha
shader. The RGB components are the same for both squares. The squares hide
a smaller black square.

For the left square only RGB components were given, without A value:
the default 0.5 is then used for all points.
For the right square the value of A was set to 0.0 at the left corners
and to 1.0 at the right corners, making the transparency
range from full to minimal over the square.

To see the effect, transparency needs to be switched on. I will do that
when you push the OK button.
""")
         transparent(True)
    else:
         showInfo("""..

The effect of the RGBA color mode can currently only be visualized
when using the alpha shader. Start pyFormex with the command::

  pyformex --shader=alpha

""")



if __name__ == '__draw__':
    run()

# End
