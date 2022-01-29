from sqlalchemy import *
from app.__main__ import Base
import time, datetime
from sqlalchemy.orm import relationship, backref
from .mutable_list import *
from flask import g


class Post(Base):

	__tablename__ = "posts"

	id = Column(Integer, Sequence('posts_id_seq'), primary_key=true)
	title = Column(String(50))
	body = Column(String(10000))
	body_html = Column(String)
	created_utc = Column(Integer)
	creation_ip = Column(String(255))
	author_id = Column(Integer, ForeignKey("users.id"))
	board_id = Column(Integer, ForeignKey("boards.id"))
	parent_id = Column(Integer, ForeignKey("posts.id"))
	anon = Column(Boolean, default=True)
	spam = Column(Boolean, default=False)
	archived = Column(Boolean, default=False)
	last_bump_utc = Column(Integer)
	attachment_url = Column(String(255))
	quoted_by = Column(MutableList.as_mutable(ARRAY(Integer)), default=[])

	attachment_size = Column(Integer)
	attachment_type = Column(String(20))
	attachment_name = Column(String(255))
	attachment_mimetype = Column(String(255))

	comment_count = Column(Integer, server_default=FetchedValue())

	replies = relationship('Post', backref=backref('parent', remote_side=[id]))
	board = relationship('Board', primaryjoin='Post.board_id == Board.id', uselist=False)
	author = relationship('User', primaryjoin='Post.author_id == User.id', uselist=False)

	def __repr__(self):
		return f'<Post(id={self.id})>'

	def __init__(self, **kws):

		if "created_utc" not in kws:
			kws["created_utc"] = int(time.time())

		super().__init__(**kws)

	@property
	def is_top_level(self):
		return not bool(self.parent_id)

	@property
	def permalink(self):
		if self.is_top_level:
			return self.board.permalink + 'thread/' + str(self.id)
		else:
			return self.parent.permalink + '#' + str(self.id)

	@property
	def no_anchor_link(self):
		if self.is_top_level:
			return self.board.permalink + 'thread/' + str(self.id)
		else:
			return self.parent.permalink

	@property
	def created_string(self):
		return datetime.datetime.fromtimestamp(self.created_utc).strftime('%c')

	@property
	def quote_count(self):
		return len(self.quoted_by)

	def reply_listing(self, limit=None):
		posts = g.db.query(Post).filter_by(parent_id=self.id).order_by(Post.created_utc.asc())

		if limit:
			posts = posts.limit(limit)

		return posts.all()

	def preview_replies(self):
		return self.reply_listing(limit=5)
