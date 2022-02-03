from sqlalchemy import *
from sqlalchemy.orm import relationship
from app.__main__ import Base
import time
from flask import g
from app.classes.post import *
from .board_relationships import *
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

    def get_listing(self, page=1, limit=25, query=None, mod=False):

        posts = g.db.query(Post).filter(
            Post.board_id == self.id,
            Post.parent_id == None,
            Post.pinned == False)

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

        if mod:
            posts = posts.options(joinedload(Post.reports.and_(Report.is_global == False)))

        has_next = posts.count() > page*limit
        posts = posts.offset(limit * (page - 1)).limit(limit).all()

        if page == 1:
            sticky = g.db.query(Post).filter_by(board_id=self.id, parent_id=None, pinned=True).first()
            if sticky:
                posts = [sticky] + posts

        return (posts, has_next)

    def get_mod(self, user, permission=None) -> ModRelationship:

        mod = g.db.query(ModRelationship).filter_by(board_id=self.id, user_id=user.id)

        if permission:
            mod = mod.filter(ModRelationship.__dict__[f'perm_{permission}'] == True)

        return mod.first()

    def has_mod(self, user, permission=None) -> bool:

        return bool(self.get_mod(user, permission=permission))

    def get_ban_by_id(self, id, check_expiry=True) -> BanRelationship:

        ban = g.db.query(BanRelationship).filter_by(board_id=self.id, id=id)

        if check_expiry:
            ban = ban.filter(or_(BanRelationship.expires_utc == 0, BanRelationship.expires_utc >= int(time.time())))

        return ban.first()

    def get_ban(self, user, check_expiry=True) -> BanRelationship:

        ban = g.db.query(BanRelationship).filter_by(board_id=self.id, user_id=user.id)

        if check_expiry:
            ban = ban.filter(or_(BanRelationship.expires_utc == 0, BanRelationship.expires_utc >= int(time.time())))

        return ban.first()

    def has_ban(self, user):

        return bool(self.get_ban(user))
