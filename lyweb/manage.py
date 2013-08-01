#!/usr/bin/env python
# coding: utf-8

import settings
import os,sys,logging

logging.basicConfig()
lylog = logging.getLogger("Manage")
lylog.setLevel(logging.DEBUG)

import random, time, pickle, base64
from hashlib import md5, sha512, sha1

from app.auth.utils import enc_login_passwd

# TODO: i18n is too ugly yet
import gettext
gettext.install( 'app', settings.I18N_PATH, unicode=False )


from app.auth.models import User
from app.account.models import UserProfile


def update_user(db):

    # User
    for username, password in settings.default_user:
        u = db.query(User).filter_by(username=username).first()
        if u:
            print '[W] user exist: %s' % username
        else:
            enc_password = enc_login_passwd( password )
            u = User(username = username, password = enc_password)
            db.add(u)

    db.commit()

    # Profile
    for user in db.query(User).order_by(User.id):
        if user.profile: continue
        profile = UserProfile(user)
        db.add(profile)
        print '[D] add profile for %s' % user.username

    db.commit()
            

def update_language(db):

    from yweb.locale import LANGUAGES
    from app.language.models import Language

    # languages
    for L in LANGUAGES:
        lang = db.query(Language).filter_by(codename = L['codename']).first()
        if lang: continue
        lang = Language( name = L['name'],
                         name_en = L['name_en'],
                         codename = L['codename'] )
        db.add(lang)


def update_storage(db):

    from app.storage.models import StoragePool
    for name, description, total in settings.default_storage_config:
        p = StoragePool( name = name,
                         description = description,
                         total = total )
        db.add(p)

def default_value(db):

    update_language(db)

    # Permission
    from app.auth.models import Permission
    for codename, name in settings.default_permission:
        p = db.query(Permission).filter_by(codename = codename).first()
        if p:
            print '[W] permission codename exist: %s' % codename
        else:
            p = Permission(codename = codename, name = name)
            db.add(p)

    # Group
    from app.auth.models import Group
    for name in settings.default_group:
        g = db.query(Group).filter_by(name=name).first()
        if g:
            print '[W] group exist: %s' % name
        else:
            # Group created defaultly is locked.
            g = Group(name = name, islocked = True)
            db.add(g)

    update_user(db)

    # User Group
    for groupname, username in settings.default_user_group:
        u = db.query(User).filter_by(username=username).first()
        g = db.query(Group).filter_by(name=groupname).first()
        if u and (g not in u.groups):
            u.groups.append(g)

    # Group Permission
    for groupname, codename in settings.default_group_permission:
        g = db.query(Group).filter_by(name=groupname).first()
        p = db.query(Permission).filter_by(codename=codename).first()
        if p not in g.permissions:
            g.permissions.append(p)


    # Appliance Catalog
    from app.appliance.models import ApplianceCatalog
    for name, summary in settings.default_appliance_catalog:
        c = db.query(ApplianceCatalog).filter_by(name=name).first()
        if c:
            print '[W] appliance catalog exist: %s' % name
        else:
            c = ApplianceCatalog(name=name, summary=summary)
            db.add(c)
            db.commit()


    update_site_config(db)
    update_storage(db)

    db.commit()


def update_site_config(db):

    from app.site.models import SiteConfig
    for key, value in settings.default_site_config:
        it = db.query(SiteConfig).filter_by(key=key).first()
        if it:
            print '[W] SiteConfig: key exist: %s' % key
        else:
            it = SiteConfig(key=key, value=value)
            db.add( it )
            db.commit()


def syncdb():


    for m in settings.app:
#        print 'm = ', m
        try:
            exec "from %s.models import *" % m
        except ImportError, e:
            print 'import error: %s' % e

    from yweb.orm import ORMBase, dbengine, db
    ORMBase.metadata.create_all(dbengine)

    default_value(db)


def i18n():

    import subprocess
    #settings.PROJECT_ROOT
    #settings.I18N_PATH
    for language in os.listdir(settings.I18N_PATH):
        language_path = os.path.join(settings.I18N_PATH, language)
        if os.path.isdir(language_path):
            po_path = os.path.join(language_path, 'LC_MESSAGES')
            for po in os.listdir(po_path):
                name, suffix = po.split('.')
                if suffix == 'po':
                    po_file = os.path.join(po_path, po)
                    mo_file = os.path.join(po_path, "%s.mo" % name)
                    cmd = 'msgfmt %s -o %s' % (po_file, mo_file)
                    try:
                        r = subprocess.call(cmd.split())
                    except Exception, e:
                        lylog.error('exec msgfmt error, maybe gettext was not install : %s' % e)
                    if r == 0:
                        lylog.debug('build %s success' % mo_file)
                    else:
                        lylog.error('build %s failed' % mo_file)


if __name__ == '__main__':
    import sys

    if len(sys.argv) == 2:
        if sys.argv[1] == '--i18n':
            i18n()
            sys.exit(0)

    syncdb()
    i18n()
