#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ConfigParser
import settings

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


def get_sql_uri():

    cf = ConfigParser.ConfigParser()
    cf.read( settings.sitecfg )

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

    return "%s://%s:%s@%s/%s" % ( LY_DBTYPE, LY_DBUSER,
                                  LY_DBPASS, LY_DBHOST, LY_DBNAME )


DB_URI = get_sql_uri()

ORMBase = declarative_base()

dbengine = create_engine(DB_URI, echo=False)

Session = sessionmaker(bind=dbengine)

db = Session()

