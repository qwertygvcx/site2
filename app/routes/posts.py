from flask import (
	Blueprint,
	render_template,
	redirect,
	request,
	abort,
	url_for
)
from app.classes.post import *
from app.classes.report import *
from app.helpers.wrappers import *
from app.helpers.get import *
from app.helpers.parser import *
import os
import time
import shutil
from werkzeug.utils import secure_filename
from app.__main__ import app

posts_blueprint = Blueprint('posts_blueprint', __name__)

class PostException(Exception):
	pass


def truncate(text):
	r = text[0:10]
	if len(text) > 10:
		r += "... "

	return r


@posts_blueprint.get('/<boardname>/post/<pid>')
def get_post_by_id(boardname, pid):

	post = get_post(pid)
	if not post or post.board.name != boardname:
		abort(404)

	return redirect(post.permalink)


@posts_blueprint.get('/<boardname>/post/<pid>/report')
@auth_required
def report_post(boardname, pid):

	post = get_post(pid)
	if not post or post.board.name != boardname:
		abort(404)

	return render_template(
		'boards/report.html',
		post=post,
		v=g.v
	)


@posts_blueprint.post('/post/<pid>/report')
@auth_required
def submit_report(pid):

	post = get_post(pid)
	if not post:
		abort(404)

	existing_report = g.db.query(Report).filter(
		Report.user_id == g.v.id,
		Report.post_id == post.id).first()

	if existing_report:
		return render_template(
			'message.html',
			title="you already reported this post",
			message="Find something else to cry about already.",
			v=g.v
		), 409

	reason = request.form.get("reason", "")
	if len(reason) < 5:
		return render_template(
			'message.html',
			title="report reason too short",
			message="Please write an essay on why this exact post makes you so mad.",
			v=g.v
		), 403

	if len(reason) > 255:
		return render_template(
			'message.html',
			title="WORDS WORDS WORDS WORDS WORDS",
			message="shut the fuck up nigga",
			v=g.v
		), 413

	if not post.approved:
		report = Report(
			post_id=post.id,
			user_id=g.v.id,
			creation_ip=request.remote_addr,
			reason=reason
		)

		g.db.add(report)

	return render_template(
		'message.html',
		title="report submitted",
		message="You may now leave this page.",
		v=g.v
	), 403


@posts_blueprint.get('/<boardname>/thread/<pid>')
@auth_desired
def get_post_view(boardname, pid):

	boardname = boardname.lower()
	post = get_post(pid)

	if not post:
		abort(404)

	if post.board.name != boardname:
		return redirect(post.permalink)

	b = post.board
	mod = False
	if g.v:
		mod = b.get_mod(g.v)

	if mod:
		perm_users = mod.perm_users
	else:
		perm_users = False

	mod_view = mod and mod.perm_content and 'mod' in request.args

	replies = post.reply_listing(mod=mod_view)

	return render_template(
		'boards/post.html',
		board=b,
		post=post,
		replies=replies,
		v=g.v,
		reveal_names=perm_users,
		mod=mod,
		mod_view=mod_view
	)


@posts_blueprint.post("/<boardname>/submit")
@posts_blueprint.post("/<boardname>/threads/<pid>/reply")
@auth_required
def submit(boardname, pid = None):

	try:

		board = get_board(boardname)
		if not board:
			raise PostException("invalid board")

		options = [x.strip() for x in request.form.get("options").strip().split()]
		anon = g.v.post_anon or "anon" in options
		title = request.form.get("title", "")
		body = request.form.get("body", "")

		if not title and not pid:
			raise PostException("a title is required for top-level threads")

		if len(title) > 50:
			raise PostException("title must be shorter than 50 characters")

		if len(body) < 2:
			raise PostException("body too short")

		if len(body) > 10000:
			raise PostException("body too long")

		if pid:
			parent = get_post(pid)
			title = ""
			if not parent:
				raise PostException("the post you're replying to has been deleted")

			if parent.archived and not board.has_mod(g.v):
				raise PostException("this post is archived. you cannot reply anymore.")

			if 'sage' not in options:
				parent.last_bump_utc = int(time.time())
				g.db.add(parent)

		mod = 'mod' in options and board.has_mod(g.v)

		new_post = Post(
			title=title,
			anon=anon,
			body=body,
			creation_ip=request.remote_addr,
			author_id=g.v.id,
			parent_id=pid,
			board_id=board.id,
			mod=mod
		)

		if not pid:
			new_post.last_bump_utc = int(time.time())

		g.db.add(new_post)
		g.db.flush()

		"""
		take care of attachments.
		attachments are saved to `/_static/ugc/thread/<parent id>/<post id>/<file name>`
		for top-level posts, the parent id is the same as its own id
		"""
		file = request.files.get("file")
		if file and file.mimetype.startswith(('image/', 'audio/', 'video/', 'application/pdf')):

			parent_id = str(pid if pid else new_post.id)
			path = os.path.join('./app/_static/ugc/thread', parent_id)
			path = os.path.join(path, str(new_post.id))
			# create directories
			os.makedirs(path, exist_ok=True)

			filename = secure_filename(file.filename)
			dirname = os.path.join(path, filename)
			extension = filename.split('.')[-1]

			file.save(dirname)
			new_post.attachment_url = url_for(
				'static_blueprint.get_post_file',
				parent_id=parent_id,
				pid=str(new_post.id),
				filename=filename
			)
			new_post.attachment_size = request.content_length // 1024
			new_post.attachment_type = extension.upper()
			new_post.attachment_name = truncate(".".join(filename.split('.')[:-1])) + '.' + extension
			new_post.attachment_mimetype = file.mimetype

		if pid:
			context = new_post
		else:
			context = None

		body_html = parse(body, context=context)
		new_post.body_html = body_html

		g.db.add(new_post)
		g.db.flush()

		return redirect(new_post.permalink)

	except PostException as e:
		return str(e), 400


@posts_blueprint.post('/<boardname>/post/<pid>/delete')
@auth_required
@mod_required('content')
def mod_delete_post(board, pid):

	post = get_post(pid)

	if not post:
		abort(404)

	if post.board_id != board.id:
		abort(400)

	if request.referrer.endswith('?mod'):
		redirect_to = board.permalink if post.is_top_level else post.parent.permalink+'?mod'
	else:
		redirect_to = request.referrer

	# delete files
	path = os.path.join(app.static_folder, 'ugc/thread')
	if post.is_top_level:
		path = os.path.join(path, str(post.id))
	else:
		path = os.path.join(path, str(post.parent_id))
		path = os.path.join(path, str(post.id))

	if os.path.exists(path):
		shutil.rmtree(path, ignore_errors=True)

	if post.is_top_level:
		for p in post.replies:

			for r in p.reports:
				g.db.delete(r)

			g.db.delete(p)

	for r in post.reports:
		g.db.delete(r)

	g.db.delete(post)

	return redirect(redirect_to)


@posts_blueprint.post('/<boardname>/thread/<pid>/options')
@auth_required
@mod_required('content')
def mod_update_post(board, pid):

	post = get_post(pid)

	if not post:
		abort(404)

	if post.board_id != board.id:
		abort(400)

	post.archived = 'archive' in request.form
	pin = 'sticky' in request.form

	# replace previous sticky
	if pin:
		prev = g.db.query(Post).filter_by(board_id=board.id, pinned=True).first()
		if prev:
			prev.pinned = False
			g.db.add(prev)

	post.pinned = pin

	return redirect(post.permalink+'?mod')


@posts_blueprint.post('/<boardname>/post/<pid>/close_reports')
@auth_required
@mod_required("content")
def mod_close_reports(board, pid):

	post = get_post(pid)

	if not post:
		abort(404)

	if post.board_id != board.id:
		abort(400)

	for report in post.reports:
		g.db.delete(report)

	return redirect(request.referrer)


@posts_blueprint.post('/<boardname>/post/<pid>/approve')
@auth_required
@mod_required("content")
def mod_approve(board, pid):

	post = get_post(pid)

	if not post:
		abort(404)

	if post.board_id != board.id:
		abort(400)

	for report in post.reports:
		g.db.delete(report)

	post.approved = True
	g.db.add(post)

	return redirect(request.referrer)


@posts_blueprint.post('/<boardname>/post/<pid>/unapprove')
@auth_required
@mod_required("content")
def mod_unapprove(board, pid):

	post = get_post(pid)

	if not post:
		abort(404)

	if post.board_id != board.id:
		abort(400)

	post.approved = False
	g.db.add(post)

	return redirect(request.referrer)
