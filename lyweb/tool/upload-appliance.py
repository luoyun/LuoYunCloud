#!/usr/bin/env python

import os, sys, logging
from hashlib import md5

logging.basicConfig(level=logging.DEBUG)

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, '../lib'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, '../'))

import settings

import gettext
# TODO: i18n
import __builtin__
__builtin__.__dict__['_'] = lambda s: s

for m in settings.app:
    try:
        exec "from %s.models import *" % m
    except ImportError:
        pass
    except Exception, e:
        logging.error('from %s import table failed: %s' % (m, e))


from yweb.orm import db

from app.appliance.models import Appliance
from app.auth.models import User

from ytool.ini import ConfigINI

cf = ConfigINI(settings.sitecfg, catalog='base')
appdir = cf.get('appliance_top_dir', '/opt/LuoYun/data/appliance/')

def _save_upfile(fpath, fhash):

    global appdir

    if not os.path.exists(fpath):
        return _('%s not exist !') % fpath

    if not os.path.exists(appdir):
        try:
            os.mkdir(appdir)
        except OSError, emsg:
            return _('mkdir error: %s') % emsg

    # file exists ?
    dpath = os.path.join(appdir, 'appliance_%s' % fhash)
    if os.path.exists(dpath):
        return _('%s already exists !') % dpath

    try:
        if ( os.stat(fpath).st_dev != os.stat(appdir).st_dev ):
            # not in same partition, use copy
            import shutil
            shutil.copy(fpath, dpath)
        else:
            # in same partition, use hard link
            os.link(fpath, dpath)
            #os.unlink(fpath)

    except Exception, e:
        return _('copy failed: %s') % e

    # no news is good news !



def _md5sum(fpath):

    f = open(fpath, 'r')
    m = md5()
    while True:
        d = f.read( 1024*1024 )
        if not d:
            break
        m.update(d)

    return m.hexdigest()

def _isadmin(user):
    for g in user.groups:
        for p in g.permissions:
            if p.codename == 'admin':
                return True
    return False


def upload_appliance(fpath):

    fname = os.path.basename(fpath)
    fsize = os.stat(fpath).st_size
    fhash = _md5sum(fpath)

    old = db.query(Appliance).filter_by(checksum = fhash).count()
    if old:
        logging.warning(_('%s already exists in LuoYunCloud DB.') % fpath)
        return

    users = [ db.query(User).get(1),
              db.query(User).filter_by(username='admin').first(),
              None ]
    for user in users:
        if user and _isadmin(user):
            break

    catalog = db.query(ApplianceCatalog).order_by(ApplianceCatalog.id).first()

    if user:

        r = _save_upfile(fpath, fhash)
        if r:
            dpath = os.path.join(appdir, 'appliance_%s' % fhash)
            if os.path.exists(dpath):
                logging.warning(_('%s already exists !') % dpath)
            else:
                logging.error(r)
                return
        else:
            logging.debug(_('Save appliance %s success.') % fpath)

        new = Appliance( name = fname.replace('.', ' '), user = user,
                         filesize = fsize, checksum = fhash )
        new.isprivate = False
        new.isuseable = True
        new.islocked = False
        new.catalog_id = catalog.id
        db.add(new)
        db.commit()
        logging.debug(_('Insert appliance to DB success, owner is %s') % user.username)
    else:
        logging.error(_('Have not found admin user, please check DB !'))


def usage():
    print '''
upload-appliance.py : upload appliance manually.

Usage: python /opt/LuoYun/web/tool/upload-appliance.py APPLIANCE_FILE

'''

def main():

    upload_appliance(sys.argv[1])


if __name__ == '__main__':

    if len(sys.argv) != 2:
        usage()
    else:
        main()
