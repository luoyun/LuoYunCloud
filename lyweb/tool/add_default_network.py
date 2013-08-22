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


from yweb.orm import create_session
dbsession = create_session()
db = dbsession()

from app.network.models import NetworkPool, IPPool
from IPy import IP


def add_to_ippool(N):

    start, end = IP( N.start ), IP( N.end )
    exclude_ips = N.exclude_ips

    NETWORK = '%s/%s' % (N.start, N.netmask)
    for x in IP(NETWORK, make_net=True):
        cur_ip = IP(x)
        if cur_ip > end:
            break

        if start <= cur_ip:
            ip_str = x.strNormal()
            if not exclude_ips.count(ip_str):
                if db.query(IPPool).filter_by(ip=ip_str).first():
                    logging.warning('ADD IP failed: %s is exists, ommit.' % ip_str)
                else:
                    db.add( IPPool(ip_str, N) )

    db.commit()


def add_default_network():

    N = NetworkPool(
        name        = '192.168.122.X',
        description = 'Add default network',
        start       = '192.168.122.120',
        end         = '192.168.122.254',
        netmask     = '255.255.255.0',
        gateway     = '192.168.122.1',
        nameservers = '8.8.8.8',
        exclude_ips = '' )

    db.add( N )
    add_to_ippool( N )



def usage():
    print '''
add_default_network.py : you can edit this file to config network

'''

def main():

    add_default_network()


if __name__ == '__main__':

    if len(sys.argv) != 1:
        usage()
    else:
        main()
