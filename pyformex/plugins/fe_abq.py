# $Id$

import pyformex as pf

# This trick is for Sphinx
try:
    oldabq = pf.options.oldabq
except:
    oldabq = False

if oldabq:
    from fe_abq_old import *

else:
    from fe_abq_new import *

