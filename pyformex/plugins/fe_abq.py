import pyformex as pf

if pf.options and pf.options.oldabq:
    from fe_abq_old import *

else:
    from fe_abq_new import *

