#!/usr/bin/env python
import os, sys
THIRD_LIB = os.path.dirname(os.path.realpath(__file__))+"/lib"
if sys.path.count(THIRD_LIB) == 0:
    sys.path.insert(0,THIRD_LIB)

from django.core.management import execute_manager
import imp
try:
    imp.find_module('lsettings') # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'lsettings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n" % __file__)
    sys.exit(1)

import lsettings

if __name__ == "__main__":
    execute_manager(lsettings)
