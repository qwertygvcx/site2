from .get import *
from flask import session, abort
from app.classes.user import User


def get_logged_in_user():

	if 'user_id' in session:
		v = g.db.query(User).filter(
			and_(
				User.id == session.get('user_id', 0),
				User.login_nonce == session.get('login_nonce', 0)
			)
		).first()

		if not v:
			# remove invalid data
			session.pop('user_id')
			session.pop('login_nonce')

		return v
	else:
		return None


def auth_desired(f):
	"""
	use this decorator if the function doesn't require
	a logged in account, but would benefit from one
	"""
	def wrapper(*args, **kwargs):
		v = get_logged_in_user()

		g.v = v

		return f(*args, **kwargs)

	wrapper.__name__ = f.__name__
	return wrapper


def auth_required(f):
	"""
	this decorator requires the user to be logged in,
	otherwise returns a 401 error
	"""
	def wrapper(*args, **kwargs):
		v = get_logged_in_user()

		if not v:
			abort(401)

		g.v = v

		return f(*args, **kwargs)

	wrapper.__name__ = f.__name__
	return wrapper


def mod_required(permission=None):
	def wrapper_maker(f):
		def wrapper(*args, **kwargs):

			boardname = kwargs.get("boardname")
			board = get_board(boardname)

			if not board:
				abort(404)

			has_mod = board.has_mod(g.v, permission)
			print(type(permission))
			if not has_mod:
				print("no mod")
				abort(403)

			# permabanned accounts can't moderate
			if g.v._banned and not g.v.unban_utc:
				abort(403)

			kwargs.pop('boardname')

			return f(*args, board=board, **kwargs)

		wrapper.__name__ = f.__name__
		return wrapper

	return wrapper_maker
