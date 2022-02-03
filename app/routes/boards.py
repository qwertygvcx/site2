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
from app.classes.board_relationships import *
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

		mod_rel = ModRelationship(
			user_id=g.v.id,
			board_id=new_board.id
		)

		g.db.add(mod_rel)

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

	mod = False
	if g.v:
		mod = b.get_mod(g.v)

	if mod:
		reveal_names = mod.perm_users
	else:
		reveal_names = False

	return render_template(
		'boards/index.html',
		v=g.v,
		board=b,
		posts=posts,
		has_next=has_next,
		page=page,
		limit=limit,
		mod=bool(mod),
		reveal_names=reveal_names
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


@boards.get('/<name>/mod')
@auth_required
def board_mod(name):

	b = get_board(name)
	if not b:
		abort(404)

	mod = b.get_mod(g.v)
	if not mod:
		abort(403)

	return render_template(
		'boards/mod_settings.html',
		v=g.v,
		board=b,
		mod=mod
	)


@boards.get('/<boardname>/mod/reports')
@auth_required
@mod_required("content")
def board_reports(board):

	page = int(request.args.get("page", 1))
	limit = min(int(request.args.get("limit", 25)), 200)

	posts = g.db.query(Post).filter_by(board_id=board.id).\
		options(joinedload(Post.reports)).\
		join(Report, Post.id == Report.post_id).\
		filter(Report.is_global == False)

	has_next = posts.count() > page*limit

	mod = board.get_mod(g.v)

	return render_template(
		'boards/listing.html',
		v=g.v,
		board=board,
		posts=posts.all(),
		has_next=has_next,
		page=page,
		limit=limit,
		mod_view=True,
		mod=mod,
		reveal_names=mod.perm_users,
		title="Reported posts",
		show_thread_link=True
	)


@boards.get('/<boardname>/mod/approved')
@auth_required
@mod_required("content")
def board_approved(board):

	page = int(request.args.get("page", 1))
	limit = min(int(request.args.get("limit", 25)), 200)

	posts = g.db.query(Post).filter_by(board_id=board.id, approved=True)

	has_next = posts.count() > page*limit

	mod = board.get_mod(g.v)

	return render_template(
		'boards/listing.html',
		v=g.v,
		board=board,
		posts=posts.all(),
		has_next=has_next,
		page=page,
		limit=limit,
		mod_view=True,
		mod=mod,
		reveal_names=mod.perm_users,
		title="Approved posts",
		show_thread_link=True
	)


@boards.get('/<boardname>/mod/bans')
@auth_required
@mod_required("users")
def board_bans(board):

	bans = g.db.query(BanRelationship).filter(
		and_(
			BanRelationship.board_id == board.id,
			or_(
				BanRelationship.expires_utc == 0,
				BanRelationship.expires_utc >= int(time.time())
			)
		)
	).options(
		joinedload(BanRelationship.user),
		joinedload(BanRelationship.banning_mod)
	)

	bans = bans.order_by(BanRelationship.created_utc.desc())
	bans = bans.all()

	return render_template('boards/bans.html', v=g.v, board=board, bans=bans)


@boards.post('/<boardname>/ban')
@auth_required
@mod_required("users")
def ban_from_board(board):

	username = request.form.get("target", "")
	reason = request.form.get("reason", "")

	try:
		post_id = int(request.form.get("post", 0))
	except:
		abort(400)

	try:
		duration = int(request.form.get("expiry", 0))
	except:
		duration = 0

	message = request.form.get("message", "")

	user = get_user(username)
	if not user:
		return render_template('message.html', title='invalid target', message='target user does not exist', v=g.v), 404

	if board.has_mod(user):
		return render_template('message.html', title='invalid target', message='you cannot ban yourself or other mods', v=g.v), 403

	post = get_post(post_id)
	is_valid_post = post and post.board_id == board.id and post.author_id == user.id
	if not is_valid_post:
		return render_template(
			'message.html',
			title='invalid post',
			message=f"The post you specified doesn't exist, doesn't belong to /{board.name}/, or wasn't created by {user.name}.",
			v=g.v
		), 404

	if not reason or not message:
		return render_template(
			'message.html',
			title='you must provide a reason',
			message='You must provide a reason for banning the user and a message to the banned user.',
			v=g.v
		), 400

	if duration:
		expires_utc = int(time.time()) + duration*60*60*24
	else:
		expires_utc = 0

	new_ban = BanRelationship(
		user_id=user.id,
		banning_mod_id=g.v.id,
		board_id=board.id,
		ban_reason=reason,
		ban_message=message,
		expires_utc=expires_utc,
		ban_ip=request.remote_addr,
		banned_for=post.id
	)

	g.db.add(new_ban)

	post.banned_for = True
	g.db.add(post)

	return redirect(post.permalink)


@boards.post('/<boardname>/unban')
@auth_required
@mod_required("users")
def unban_from_board(board):

	try:
		ban_id = int(request.form.get('id', 0))
		ban = board.get_ban_by_id(ban_id)
		g.db.delete(ban)
		return redirect(request.referrer)
	except:
		abort(400)
