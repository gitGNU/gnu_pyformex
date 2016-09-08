#!/usr/bin/python
from __future__ import print_function
failed=[]
with open('pyformex.imports','r') as fil:
    for line in fil:
        m = line.strip()
        print(m,end=': ')
        try:
            __import__(m)
            print("ok")
        except:
            print("FAILED")
            failed.append(m)

    print("\nThe following modules could not be imported:")
    print(", ".join(failed))

# End
