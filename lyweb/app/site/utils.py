from .models import SiteConfig

from yweb.orm import global_dbsession


def get_site_config(key, default_value=None):

    db = global_dbsession()
    v = SiteConfig.get(db, key, default_value)

    return v


def get_site_config_int(key, default_value=None):

    v = get_site_config(key, default_value)

    try:
        v = int(v)
    except:
        v = 0

    return v

        
