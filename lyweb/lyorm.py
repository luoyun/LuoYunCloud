#/usr/bin/env python

import settings

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
#from sqlalchemy import Column, Integer, String, Sequence

#engine = create_engine('sqlite:///:memory:', echo=True)
#engine = create_engine('sqlite:///sqlite-test.db', echo=True)

#postgresql+psycopg2://user:password@host:port/dbname[?key=value&key=value...].
#postgresql+psycopg2://user:password@/dbname?host=/var/lib/postgresql", client_encoding = utf8
dbengine = create_engine(settings.SQLALCHEMY_DATABASE_URI, echo=False, client_encoding = 'utf8')


ORMBase = declarative_base()


#ORMBase.metadata.create_all(engine)


from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=dbengine)
#Session = sessionmaker()
#Session.configure(bind=engine)
dbsession = Session()
db=dbsession


#dbsession.commit()

#dbengine.dispose()



# TODO:
# http://lepture.com/work/tornado-ext/
