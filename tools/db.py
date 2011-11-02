from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref

Base = declarative_base()
engine = create_engine('mysql://root@localhost/stream', echo=True)
Session = sessionmaker(bind=engine)
session = Session()
