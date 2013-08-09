import logging, datetime

# account init
def init_account(user, db):

    from app.site.utils import get_site_config_int
    from app.resource.models import Resource
    from app.auth.models import Group
    from app.site.models import SiteConfig
    from app.account.models import UserProfile

    logging.debug('Init account "%s".' % user.username)

    now = datetime.datetime.now()
    expired_date = now + datetime.timedelta( seconds = 365 * 3600 * 24 )

    # default resource
    cpu      = get_site_config_int('user.default.dynamic_cpu', 0)
    memory   = get_site_config_int('user.default.dynamic_memory', 0)
    storage  = get_site_config_int('user.default.dynamic_storage', 0)
    instance = get_site_config_int('user.default.dynamic_instance', 0)

    for t, s in [
        ( Resource.T_CPU, cpu ),
        ( Resource.T_MEMORY, memory ),
        ( Resource.T_STORAGE, storage ),
        ( Resource.T_INSTANCE, instance ) ]:

        print 's = "%s"' % s
        if not s: continue

        r = Resource( user = user, rtype = t, size = s,
                      effect_date = now,
                      expired_date = expired_date )

        db.add(r)

    # default profile
    profile = db.query(UserProfile).filter_by(
        user_id = user.id ).first()

    if not profile:
        # create user profile
        profile = UserProfile( user )
        db.add( profile )
        db.commit()

    language_id = SiteConfig.get(db, 'user.default.language', 61)
    user.language_id = language_id

    # default group
    gid = SiteConfig.get(db, 'user.default.group', 2)
    g = db.query(Group).get( gid )
    if g:
        user.groups = [ g ]

    db.commit()
