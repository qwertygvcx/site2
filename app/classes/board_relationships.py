from sqlalchemy import *
from app.__main__ import Base
from sqlalchemy.orm import relationship
import time, datetime, math


class ModRelationship(Base):

	__tablename__ = 'mods'

	id = Column(Integer, Sequence('mods_id_seq'), primary_key=True)
	board_id = Column(Integer, ForeignKey('boards.id'))
	user_id = Column(Integer, ForeignKey('users.id'))
	created_utc = Column(Integer)
	mod_level = Column(Integer, default=1)

	""" permissions """
	perm_full = Column(Boolean, default=True)
	perm_content = Column(Boolean, default=True) # delete/pin posts, schedule megathreads
	perm_users = Column(Boolean, default=True) # manage mods, bans, and approved users
	perm_config = Column(Boolean, default=True) # edit board settings (banner, visiblity etc)
	perm_styling = Column(Boolean, default=True) # edit board css

	user = relationship("User", primaryjoin="ModRelationship.user_id == User.id", uselist=False)

	def __repr__(self):
		return f'<ModRelationship(id={self.id})>'

	def __init__(self, **kws):

		if "created_utc" not in kws:
			kws["created_utc"] = int(time.time())

		super().__init__(**kws)

	@property
	def perms_string(self):

		if self.perm_full:
			return "full permissions"

		perms = []
		all_perms = [x for x in self.__dict__ if x.startswith('perm_')]
		for p in all_perms:
			perm = self.__dict__[p]
			if perm:
				perms += [p.lstrip('perm_')]

		if len(perms) == 0:
			return "no permissions"

		return ",".join(perms)

	@property
	def created(self):
		d = math.floor((int(time.time()) - self.created_utc) / (24*60*60))
		if d == 0:
			return "today"
		else:
			return f"{d} day(s) ago"

	@property
	def added(self):
		return datetime.datetime.fromtimestamp(self.created_utc).strftime('%c')

	""" returns a list of all permission strings """
	@classmethod
	def permissions(cls) -> list:
		return [p for p in cls.__dict__ if p.startswith("perm_")]


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
			return math.ceil((self.expires_utc-int(time.time())) / (24*60*60))
		else:
			return 0

	@property
	def expires(self):
		return datetime.datetime.fromtimestamp(self.expires_utc).strftime('%c')
