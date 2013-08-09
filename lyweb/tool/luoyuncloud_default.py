# account init
def init_account(user, db):

    import logging, datetime

    from app.resource.models import Resource
    from app.auth.models import Group
    from app.site.models import SiteConfig
    from app.account.models import UserProfile

    logging.debug('Init account "%s".' % user.username)

    now = datetime.datetime.now()
    expired_date = now + datetime.timedelta( seconds = 365 * 3600 * 24 )

    # default resource
    cpu = SiteConfig.get(db, 'account.default.cpu', 1)
    memory = SiteConfig.get(db, 'account.default.memory', 256)
    storage = SiteConfig.get(db, 'account.default.storage', 2)
    instance = SiteConfig.get(db, 'account.default.instance', 3)

    for t, s in [
        ( Resource.T_CPU, cpu ),
        ( Resource.T_MEMORY, memory ),
        ( Resource.T_STORAGE, storage ),
        ( Resource.T_INSTANCE, instance ) ]:

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

    # update user resource
    user.profile.update_resource_total()

    language_id = SiteConfig.get(db, 'account.default.language', 61)
    user.language_id = language_id

    # default group
    gid = SiteConfig.get(db, 'account.default.group', 2)
    g = db.query(Group).get( gid )
    if g:
        user.groups = [ g ]

    db.commit()
