#/usr/bin/env python

import ConfigParser
import settings

def get_sql_uri():

    cf = ConfigParser.ConfigParser()
    cf.read( settings.LUOYUN_CONFIG_PATH )

    if cf.has_option('db', 'db_host'):
        LY_DBHOST = cf.get('db', 'db_host')
    else:
        LY_DBHOST = '127.0.0.1'

    if cf.has_option('db', 'db_type'):
        LY_DBTYPE = cf.get('db', 'db_type')
    else:
        LY_DBTYPE = 'postgresql+psycopg2'

    if cf.has_option('db', 'db_name'):
        LY_DBNAME = cf.get('db', 'db_name')
    else:
        LY_DBNAME = 'luoyun'

    if cf.has_option('db', 'db_user'):
        LY_DBUSER = cf.get('db', 'db_user')
    else:
        LY_DBUSER = 'luoyun'

    if cf.has_option('db', 'db_password'):
        LY_DBPASS = cf.get('db', 'db_password')
    else:
        LY_DBPASS = 'luoyun'

    # DB Connect format: "postgresql+psycopg2://username:password@HOST_ADDRESS/DB_NAME"
    return "%s://%s:%s@%s/%s" % ( LY_DBTYPE, LY_DBUSER, LY_DBPASS, LY_DBHOST, LY_DBNAME )



from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
#from sqlalchemy import Column, Integer, String, Sequence

#engine = create_engine('sqlite:///:memory:', echo=True)
#engine = create_engine('sqlite:///sqlite-test.db', echo=True)

#postgresql+psycopg2://user:password@host:port/dbname[?key=value&key=value...].
#postgresql+psycopg2://user:password@/dbname?host=/var/lib/postgresql", client_encoding = utf8
dbengine = create_engine(get_sql_uri(), echo=False, client_encoding = 'utf8')


ORMBase = declarative_base()


#ORMBase.metadata.create_all(engine)


from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=dbengine)
#Session = sessionmaker()
#Session.configure(bind=engine)
dbsession = Session()
db=dbsession

def get_new_session():
    dbengine = create_engine(get_sql_uri(), echo=False, client_encoding = 'utf8')
    Session = sessionmaker(bind=dbengine)
    return Session()


#dbsession.commit()

#dbengine.dispose()



# TODO:
# http://lepture.com/work/tornado-ext/
