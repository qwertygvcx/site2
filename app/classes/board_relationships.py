from sqlalchemy import *
from app.__main__ import Base
from sqlalchemy.orm import relationship
import time


class ModRelationship(Base):

	__tablename__ = 'mods'

	id = Column(Integer, Sequence('mods_id_seq'), primary_key=True)
	board_id = Column(Integer, ForeignKey('boards.id'))
	user_id = Column(Integer, ForeignKey('users.id'))
	created_utc = Column(Integer)

	""" permissions """
	perm_content = Column(Boolean, default=True) # delete/pin posts, schedule megathreads
	perm_users = Column(Boolean, default=True) # manage mods, bans, and approved users
	perm_config = Column(Boolean, default=True) # edit board settings (banner, visiblity etc)
	perm_styling = Column(Boolean, default=True) # edit board css

	def __repr__(self):
		return f'<ModRelationship(id={self.id})>'

	def __init__(self, **kws):

		if "created_utc" not in kws:
			kws["created_utc"] = int(time.time())

		super().__init__(**kws)
