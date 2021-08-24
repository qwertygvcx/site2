from sqlalchemy import *
#from sqlalchemy.orm import relationship
from app.__main__ import Base
#import time
#from flask import g
#from helpers.time import *


class Board(Base):

    __tablename__ = "boards"

    id = Column(Integer, Sequence('boards_id_seq'), primary_key=True)
    name = Column(String(5))
    title = Column(String(25))
    description = Column(String(255))
    created_utc = Column(Integer)
    creation_ip = Column(String(255))
    private = Column(Boolean, default=False)
