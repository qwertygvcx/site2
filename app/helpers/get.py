from flask import g
from app.classes import *

def get_user(name):

	return g.db.query(User).filter(User.username.ilike(name)).first()


def get_user_by_id(id):

	return g.db.query(User).filter_by(id=id).first()