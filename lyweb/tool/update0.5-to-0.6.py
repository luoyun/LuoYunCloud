#!/usr/bin/env python

import os,sys

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, '../lib'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, '../'))

import gettext
# TODO: i18n
import __builtin__
__builtin__.__dict__['_'] = lambda s: s

import settings

for m in settings.app:
    try:
        exec "from %s.models import *" % m
    except ImportError:
        pass
    except Exception, e:
        print 'from %s import table failed: %s' % (m, e)

from lyorm import dbsession as db

from app.appliance.models import Appliance

def tmp():
    logo_dir = os.path.join(PROJECT_ROOT, '../static/appliance/')
    t_dir = os.path.join(PROJECT_ROOT, 't')
    for fname in os.listdir(t_dir):
        ID = fname.strip('0').split('.')[0]
        a_logodir = os.path.join(logo_dir, '%s' % ID)
        if os.path.exists(a_logodir):
            a_logopath = os.path.join(a_logodir, 'r.png')

            if os.path.exists(a_logopath):
                os.unlink(a_logopath)

            os.link(os.path.join(t_dir, fname), a_logopath)
            print 'creat link: %s' % a_logopath
        else:
            print 'NOT EXIST: ', a_logodir
        
    
def update_appliance_logo():

    appliances = db.query(Appliance)

    for A in appliances:
        old_logo = os.path.join(A.logodir, 'alogo.png')
        if os.path.exists(old_logo):
            os.rename(old_logo, A._p_logo_raw)
            print A._p_logo_raw
#        else: # for test
#            if os.path.exists(A._p_logo):
#                os.rename(A._p_logo, old_logo)
        if os.path.exists(A._p_logo_raw):
            A.rebuild_logo()
        else:
            print 'NOT FOUND : ', A._p_logo_raw


if __name__ == '__main__':

    #tmp()
    update_appliance_logo()
