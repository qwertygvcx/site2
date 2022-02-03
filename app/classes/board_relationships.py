from sqlalchemy import *
from app.__main__ import Base
from sqlalchemy.orm import relationship
import time, datetime


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


class BanRelationship(Base):

	__tablename__ = "bans"

	id = Column(Integer, Sequence('bans_id_seq'), primary_key=True)
	board_id = Column(Integer, ForeignKey('boards.id'))
	user_id = Column(Integer, ForeignKey('users.id'))
	banning_mod_id = Column(Integer, ForeignKey('users.id'))
	created_utc = Column(Integer)
	ban_ip = Column(String(255))

	# reason for ban, visible in mod logs and ban list
	ban_reason = Column(String(255))
	# ban message, visible to target user
	ban_message = Column(String(255))
	# id of post the user was banned for
	banned_for = Column(Integer)

	expires_utc = Column(Integer)

	user = relationship("User", primaryjoin="BanRelationship.user_id == User.id", uselist=False)
	banning_mod = relationship("User", primaryjoin="BanRelationship.banning_mod_id == User.id", uselist=False)

	def __repr__(self):
		return f'<BanRelationship(id={self.id})>'

	def __init__(self, **kws):

		if "created_utc" not in kws:
			kws["created_utc"] = int(time.time())

		super().__init__(**kws)

	@property
	def duration_days(self):
		if self.expires_utc:
			return (self.expires_utc-self.created_utc) // (24*60*60)
		else:
			return 0

	@property
	def expires(self):
		return datetime.datetime.fromtimestamp(self.expires_utc).strftime('%c')
