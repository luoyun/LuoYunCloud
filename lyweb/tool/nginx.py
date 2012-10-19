

def nginx_reload(db):
    ''' Reload nginx '''


    nginx = db.query(LuoYunConfig).filter_by(key='nginx').first()

