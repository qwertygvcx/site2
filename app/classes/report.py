from sqlalchemy import *
from app.__main__ import Base
from sqlalchemy.orm import relationship
import time


class Report(Base):

	__tablename__ = 'reports'

	id = Column(Integer, Sequence('reports_id_seq'), primary_key=True)
	post_id = Column(Integer, ForeignKey('posts.id'))
	user_id = Column(Integer, ForeignKey('users.id'))
	reason = Column(String(255))
	is_global = Column(Boolean, default=False)
	created_utc = Column(Integer)
	creation_ip = Column(String(255))

	post = relationship('Post', primaryjoin='Report.post_id == Post.id', uselist=False)
	user = relationship('User', primaryjoin='Report.user_id == User.id', uselist=False)

	def __repr__(self):
		return f'<Report(id={self.id})>'

	def __init__(self, **kws):

		if "created_utc" not in kws:
			kws["created_utc"] = int(time.time())

		super().__init__(**kws)
