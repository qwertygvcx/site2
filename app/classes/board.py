from sqlalchemy import *
from sqlalchemy.orm import relationship
from app.__main__ import Base
import time
from flask import g
from app.classes.post import *
#from helpers.time import *


class Board(Base):

    __tablename__ = "boards"

    id = Column(Integer, Sequence('boards_id_seq'), primary_key=True)
    name = Column(String(5))
    title = Column(String(25))
    description = Column(String(255))
    creator_id = Column(Integer, ForeignKey("users.id"))
    created_utc = Column(Integer)
    creation_ip = Column(String(255))
    private = Column(Boolean, default=False)

    posts = relationship("Post", primaryjoin="Post.board_id == Board.id")

    def __repr__(self):
        return f'<Board(id={self.id}, name="{self.name}")'

    def __init__(self, **kws):

        if "created_utc" not in kws:
            kws["created_utc"] = int(time.time())

        super().__init__(**kws)

    @property
    def permalink(self):
        return "/%s/" % self.name

    def get_listing(self, page=1, limit=25, query=None):

        posts = g.db.query(Post).filter(
            Post.board_id == self.id,
            Post.parent_id == None)

        posts = posts.order_by(Post.last_bump_utc.desc())

        if query:
            # escape pqsl wildcards
            query = query.replace('%', '\%')
            query = query.replace('_', '\_')

            posts = posts.filter(or_(
                    Post.title.ilike(f'%{query}%'),
                    Post.body_html.ilike(f'%{query}%')
                )
            )

        has_next = posts.count() > page*limit

        return (posts.offset(limit * (page - 1)).limit(limit).all(), has_next)
    