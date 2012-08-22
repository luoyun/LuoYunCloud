import json

from IPy import IP

import settings

def get_network_pool(networkpool):
    ''' compute a network pool from configure

    sample of networkpool config is:

    networkpool = {
        'start':       ...,
        'end':         ...,
        'netmask':     ...,
        'gateway':     ...,
        'nameservers': ...,
        'exclude_ips': ...,
    }
    '''

    NETWORK_POOL = []

    start = IP( networkpool['start'] )
    end   = IP( networkpool['end'] )

    exclude_ips = networkpool['exclude_ips'].split()

    network = '%s/%s' % (networkpool['start'], networkpool['netmask'])
    for x in IP(network, make_net=True):
        if start <= IP(x) <= end:
            ip_str = x.strNormal()
            if ip_str not in exclude_ips:
                NETWORK_POOL.append( ip_str )

    return NETWORK_POOL


def set_network_pool(db):

    from app.system.models import LuoYunConfig
    networkpool = db.query(LuoYunConfig).filter_by( key = 'networkpool' ).first()

    if not networkpool:
        settings.NETWORK_POOL = [{}]
        return

    networkpool =  json.loads(networkpool.value)[0]

    # TODO: support multi network pool
    settings.NETWORK_POOL = [{
        'netmask'    : networkpool['netmask'],
        'gateway'    : networkpool['gateway'],
        'nameservers': networkpool['nameservers'],
        'pool'       : get_network_pool( networkpool ),
        }]
