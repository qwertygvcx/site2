from sqlalchemy import *
#from sqlalchemy.orm import relationship
from app.__main__ import Base
import time
#from flask import g
from app.helpers.hash import *


class User(Base):

	__tablename__ = "users"

	id = Column(Integer, Sequence('users_id_seq'), primary_key=True)
	name = Column(String(20))
	passhash = Column(String)
	admin = Column(Boolean, default=False)
	created_utc = Column(Integer, default=0)
	creation_ip = Column(String(255))
	# post anon by default
	post_anon = Column(Boolean, default=False)
	# increment to log the user out everywhere
	login_nonce = Column(Integer, default=1)

	""" admin stuff """
	# id of the admin who banned the user, 0 if not banned
	_banned = Column(Integer, default=0)
	# when the user was banned
	banned_utc = Column(Integer, default=0)
	# when the ban expires, 0 for permanent ban
	unban_utc = Column(Integer, default=0)
	# reason for the ban
	ban_reason = Column(String(255))

	deleted_utc = Column(Integer, default=0)

	def __init__(self, **kwargs):

		if 'created_utc' not in kwargs:
			kwargs['created_utc'] = int(time.time())

		if 'password' in kwargs:
			kwargs['passhash'] = hash_password(kwargs['password'])
			kwargs.pop('password')

		super().__init__(**kwargs)

	def check_password(self, string):
		return check_password(string, self.passhash)
