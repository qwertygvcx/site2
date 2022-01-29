from flask import (
	Blueprint,
	request,
	render_template,
	g,
	redirect,
	abort
)
from app.helpers.wrappers import *
from app.classes.board import *
from app.helpers.get import get_board
import re, time

boards = Blueprint('boards', __name__)
valid_name_regex = re.compile('^[a-zA-Z0-9-_]{3,20}$')



def overboard_listing(page=1, limit=25, query=None):

	posts = g.db.query(Post).filter(Post.parent_id == None)

	posts = posts.order_by(Post.created_utc.desc())

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


class BoardError(Exception):
	pass


def can_make_board(user) -> bool:

	if user.admin:
		return True

	created_board_recently = bool(g.db.query(Board).filter(
		Board.creator_id == user.id,
		Board.created_utc > int(time.time()) - 60*60*24*3).first())

	return not created_board_recently


@boards.get('/c/create')
@auth_required
def get_create():

	return render_template('boards/create.html', v=g.v)


@boards.post('/c/create')
@auth_required
def post_create():

	try:
		name = request.form.get("name", "")
		name = name.strip().lower()
		if not valid_name_regex.fullmatch(name) or name == "c":
			raise BoardError("invalid name")

		# check if board already exists
		already_exists = bool(g.db.query(Board).filter_by(name=name).first())
		if already_exists:
			raise BoardError("a board with that name already exists")

		title = request.form.get("title", "")
		if len(title) > 20:
			raise BoardError("title must be shorter than 20 characters")

		desc = request.form.get("desc", "")
		if len(desc) > 255:
			raise BoardError("description cannot be longer than 255 characters")

		if not can_make_board(g.v):
			raise BoardError("you can only make one board every 3 days")

		new_board = Board(
			name=name,
			title=title,
			description=desc,
			creation_ip=request.remote_addr,
			creator_id=g.v.id
		)

		g.db.add(new_board)
		g.db.flush()

		return redirect(new_board.permalink)

	except BoardError as e:
		return render_template('boards/create.html', v=g.v, error=str(e)), 400


@boards.get('/*/')
@auth_desired
def overboard():

	page = int(request.args.get("page", 1))
	limit = min(int(request.args.get("limit", 25)), 200)

	listing = overboard_listing(page=page, limit=limit)
	posts = listing[0]
	has_next = listing[1]

	return render_template(
		'boards/index.html',
		v=g.v,
		posts=posts,
		has_next=has_next,
		page=page,
		limit=limit
	)


@boards.get('/*/catalog')
@auth_desired
def overboard_catalog():

	page = int(request.args.get("page", 1))
	limit = min(int(request.args.get("limit", 25)), 200)
	query = request.args.get("filter")

	listing = overboard_listing(page=page, limit=limit, query=query)
	posts = listing[0]
	has_next = listing[1]

	return render_template(
		'boards/catalog.html',
		v=g.v,
		posts=posts,
		has_next=has_next,
		page=page,
		limit=limit,
		query=query
	)


@boards.get('/<name>/')
@auth_desired
def get_board_page(name):

	b = get_board(name)
	if not b:
		abort(404)

	page = int(request.args.get("page", 1))
	limit = min(int(request.args.get("limit", 25)), 200)

	listing = b.get_listing(page=page, limit=limit)
	posts = listing[0]
	has_next = listing[1]

	return render_template(
		'boards/index.html',
		v=g.v,
		board=b,
		posts=posts,
		has_next=has_next,
		page=page,
		limit=limit
	)


@boards.get('/<name>/catalog')
@auth_desired
def get_board_catalog(name):

	b = get_board(name)
	if not b:
		abort(404)

	page = int(request.args.get("page", 1))
	limit = min(int(request.args.get("limit", 25)), 200)
	query = request.args.get("filter")

	listing = b.get_listing(page=page, limit=limit, query=query)
	posts = listing[0]
	has_next = listing[1]

	return render_template(
		'boards/catalog.html',
		v=g.v,
		board=b,
		posts=posts,
		has_next=has_next,
		page=page,
		limit=limit,
		query=query
	)
