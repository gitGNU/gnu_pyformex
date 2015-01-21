..     -*- rst -*-

About p2to3
-----------
This README is intended for development purposes
on the Python3 version of pyFormex.

Conversion is done byt the 2to3 fixers:
see http://docs.python.org/2/library/2to3.html#fixers


List of applied fixes
---------------------

A - in the first column means that the fixer has been applied, ? means that
it still needs to be done, an = that there is no need to fix it, as we have
implemented another solution::

    - apply
    - basestring
    - buffer
    = callable: no need: we have added callable to Python 3.1
    ? dict
    - except
    - exec:
    = execfile: dealt with in compat_?k.py
    - exitfunc
    - filter
    - funcattrs
    = future: We need to keep future for python2 version
    - getcwdu
    - has_key
    - idioms
    - import: all imports converted to absolute imports
    = imports: some inports of changed modules handled un compat modules
    - imports2
    - input
    - intern
    - isinstance
    - itertools
    - itertools_imports
    - long
    = map: converted everything to []. Should add future import????
    - metaclass
    - methodattrs
    - ne
    = next: NameSequence next can stay for now, varray has been changed
    - nonzero
    - numliterals
    - paren
    - print
    - raise
    = raw_input : dealt with in compat_?k.py
    - reduce
    - renames
    - repr
    - set_literal
    - standarderror
    - sys_exc
    - throw
    - tuple_params
    - types
    - unicode
    - urllib
    - ws_comma
    - xrange
    - xreadlines
    - zip


How to do it
------------

To see a list of possible fixes::

  2to3 -l


To convert the code for s specific fixer::

  2to3 -f fixer pyformex

To write back the converted files::

  2to3 -f fixer -w pyformex

To avoid creating backup files::

  2to3 -f fixer -w -n pyformex

It is a good practice to first run the above commands without -w option, check the output to see what would be changed, and when ok to run with -n and -w options. If not all changes are ok, you can run the command with the files that should be changed.


Future code should avoid the use of filter, map, reduce


Dependencies for pyformex-p3
----------------------------
python3-pyside
libshiboken-py3-1.2


.. End
