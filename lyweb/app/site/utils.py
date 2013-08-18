from .models import SiteConfig

from yweb import orm
from settings import runtime_data


def get_site_config(key, default_value=None):

    db = global_dbsession()
    v = SiteConfig.get(db, key, default_value)
    global_dbsession.remove()

    return v


def get_site_config_int(key, default_value=None):

    v = get_site_config(key, default_value)

    try:
        v = int(v)
    except:
        v = 0

    return v

        
