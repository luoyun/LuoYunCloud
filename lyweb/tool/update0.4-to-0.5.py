#!/usr/bin/env python

import os,sys

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(PROJECT_ROOT, '../lib'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, '../'))

import settings

for m in settings.app:
    try:
        exec "from %s.models import *" % m
    except ImportError:
        pass
    except Exception, e:
        print 'from %s import table failed: %s' % (m, e)

from lyorm import dbsession as db

from app.system.models import IPPool



from sqlalchemy import Column, Integer, String, \
    Sequence, DateTime, Table, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship, backref

class IpAssign(ORMBase):

    __tablename__ = 'ip_assign'

    id = Column( Integer, Sequence('ip_assign_id_seq'), primary_key=True )

    ip = Column( String(32) )

    user_id = Column( ForeignKey('auth_user.id') )
    user = relationship("User", backref=backref('static_ips',order_by=id) )

    instance_id = Column( ForeignKey('instance.id') )
    instance = relationship("Instance", backref=backref('static_ips', order_by=id))

    created = Column( DateTime, default=datetime.now )
    updated = Column( DateTime, default=datetime.now )


    def __init__(self, ip, user, instance=None):
        self.ip = ip
        self.user_id = user.id
        if instance:
            self.instance_id = instance.id



ERROR, OK = [], []
EXIST_ERROR, EXIST_OK = [], []
for x in db.query(IpAssign).all():
    if x.instance_id:
        newip = db.query(IPPool).filter_by( ip=x.ip ).first()
        if newip:
            if newip.instance_id:
                if newip.instance_id != x.instance_id:
                    EXIST_ERROR.append( (x.ip, newip.instance_id) )
                else:
                    EXIST_OK.append( (x.ip, newip.instance_id) )
            else:
                OK.append( (x.ip, x.instance_id) )
        else:
            ERROR.append( (x.ip, x.instance_id) )



if ERROR:
    print 'The following ip->instance binding failed:'
    for x, y in ERROR:
        print '  %s -> %s' % (x, y)
    print 'Reconfigure the networkpool to fix this problem.'

if EXIST_ERROR:
    print 'The following ip->instance binding exist:'
    for x, y in EXIST_ERROR:
        print '  %s -> %s' % (x, y)

    print 'Manual import important network config and delete those record from DB.'

if EXIST_OK:
    print 'The following ip->instance binding is ok:'
    for x, y in EXIST_OK:
        print '  %s -> %s' % (x, y)

    print 'Just ommit.'

if ERROR or EXIST_ERROR:
    import sys
    sys.exit(1)


if OK:
    print 'The following ip->instance binding success:'
    for x, y in OK:
        newip = db.query(IPPool).filter_by( ip=x ).first()
        newip.instance_id = y
        print '  %s -> %s' % (x, y)

    db.commit()
    print 'Done !'


# insert new permission
from app.account.models import Permission
if db.query(Permission).filter_by(codename='network.add').first():
    print '"network.add" permission is exist already!'
else:
    p = Permission('Can add another NIC configure', 'network.add')
    db.add(p)
    db.commit()
    print 'Add "network.add" permission success.'
