#!/usr/bin/env python
# coding: utf-8

import settings
import os,sys,logging

logging.basicConfig()
lylog = logging.getLogger("Manage")
lylog.setLevel(logging.DEBUG)

import random, time, pickle, base64
from hashlib import md5, sha512, sha1

from app.account.utils import encrypt_password, check_password

# TODO: i18n is too ugly yet
import gettext
gettext.install( 'app', settings.I18N_PATH, unicode=False )



def default_value(dbsession):

    from app.account.models import Group
    if dbsession.query(Group).count() > 0:
        print '[W] db is init already, do not init now.'
        return

    # Permission
    from app.account.models import Permission
    for codename, name in settings.default_permission:
        p = dbsession.query(Permission).filter_by(codename = codename).first()
        if p:
            print '[W] permission codename exist: %s' % codename
        else:
            p = Permission(codename = codename, name = name)
            dbsession.add(p)

    # Group
    from app.account.models import Group
    for name in settings.default_group:
        g = dbsession.query(Group).filter_by(name=name).first()
        if g:
            print '[W] group exist: %s' % name
        else:
            # Group created defaultly is locked.
            g = Group(name = name, islocked = True)
            dbsession.add(g)

    # User
    from app.account.models import User
    for username, password in settings.default_user:
        u = dbsession.query(User).filter_by(username=username).first()
        if u:
            print '[W] user exist: %s' % username
        else:
            salt = md5(str(random.random())).hexdigest()[:12]
            hsh = encrypt_password(salt, password)
            enc_password = "%s$%s" % (salt, hsh)
            u = User(username = username, password = enc_password)
            dbsession.add(u)
            dbsession.commit()

        if not u.profile:
            from app.account.models import UserProfile
            profile = UserProfile(u, email = '%s@localhost' % u.username)
            dbsession.add(profile)


    # User Group
    for groupname, username in settings.default_user_group:
        u = dbsession.query(User).filter_by(username=username).first()
        g = dbsession.query(Group).filter_by(name=groupname).first()
        if u and (g not in u.groups):
            u.groups.append(g)

    # User Permission
    for username, codename in settings.default_user_permission:
        u = dbsession.query(User).filter_by(username=username).first()
        p = dbsession.query(Permission).filter_by(codename=codename).first()
        if p not in u.permissions:
            u.permissions.append(p)

    # Group Permission
    for groupname, codename in settings.default_group_permission:
        g = dbsession.query(Group).filter_by(name=groupname).first()
        p = dbsession.query(Permission).filter_by(codename=codename).first()
        if p not in g.permissions:
            g.permissions.append(p)


    # Appliance Catalog
    from app.appliance.models import ApplianceCatalog
    for name, summary in settings.default_appliance_catalog:
        c = dbsession.query(ApplianceCatalog).filter_by(name=name).first()
        if c:
            print '[W] appliance catalog exist: %s' % name
        else:
            c = ApplianceCatalog(name=name, summary=summary)
            dbsession.add(c)
            dbsession.commit()


    # Wiki Catalog
    from app.wiki.models import WikiCatalog
    for name, summary in settings.default_wiki_catalog:
        c = dbsession.query(WikiCatalog).filter_by(name=name).first()
        if c:
            print '[W] wiki catalog exist: %s' % name
        else:
            c = WikiCatalog(name=name, summary=summary)
            dbsession.add(c)
            dbsession.commit()
        


    dbsession.commit()



def syncdb():


    for m in settings.app:
        try:
            exec "from %s.models import *" % m
        except ImportError:
            pass

    from lyorm import ORMBase, dbengine, dbsession
    ORMBase.metadata.create_all(dbengine)

    default_value(dbsession)


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
