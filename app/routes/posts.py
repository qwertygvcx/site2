from flask import (
	Blueprint,
	render_template,
	redirect,
	request,
	abort,
	url_for
)
from app.classes.post import *
from app.helpers.wrappers import *
from app.helpers.get import *
from app.helpers.parser import *
import os
import time
from werkzeug.utils import secure_filename

posts_blueprint = Blueprint('posts_blueprint', __name__)

class PostException(Exception):
	pass


def truncate(text):
	r = text[0:10]
	if len(text) > 10:
		r += "... "

	return r


@posts_blueprint.get('/<boardname>/thread/<pid>')
@auth_desired
def get_post_view(boardname, pid):

	boardname = boardname.lower()
	post = get_post(pid)

	if not post:
		abort(404)

	if post.board.name != boardname:
		return redirect(post.permalink)

	replies = post.reply_listing()

	return render_template('boards/post.html', post=post, replies=replies, v=g.v)


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

			if 'sage' not in options:
				parent.last_bump_utc = int(time.time())
				g.db.add(parent)

		new_post = Post(
			title=title,
			anon=anon,
			body=body,
			creation_ip=request.remote_addr,
			author_id=g.v.id,
			parent_id=pid,
			board_id=board.id
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
