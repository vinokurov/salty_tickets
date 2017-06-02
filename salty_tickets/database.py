from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from salty_tickets import config

__author__ = 'vnkrv'

SQLALCHEMY_DATABASE_URI = "mysql+pymysql://{username}:{password}@{hostname}/{databasename}".format(
            username=config.DATABASE_USERNAME,
            password=config.DATABASE_PASSWORD,
            hostname=config.DATABASE_HOSTNAME,
            databasename=config.DATABASE_DBNAME,
)

engine = create_engine('sqlite:////tmp/test.db', convert_unicode=True)
# engine = create_engine(SQLALCHEMY_DATABASE_URI, convert_unicode=True, pool_size=100, pool_recycle=280)

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

# def init_db():
#     # import all modules here that might define models so that
#     # they will be registered properly on the metadata.  Otherwise
#     # you will have to import them first before calling init_db()
#     from .models import *
#     Base.metadata.create_all(bind=engine)