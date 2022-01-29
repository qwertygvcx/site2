from app.__main__ import app
from flask import redirect, g, request, url_for, render_template
from urllib.parse import urlencode, quote

@app.errorhandler(401)
def error_401(e):

	g.db.rollback()

	if request.method == "GET":
		url = request.path
		q = urlencode(dict(request.args))

		redirect_to = quote('{}?{}'.format(url, q), safe='')
		return redirect(url_for('auth.login_get', redirect=redirect_to))
	else:
		return render_template('errors/401.html')


@app.errorhandler(413)
def error_413(e):

	g.db.rollback()
	return render_template(
		'message.html',
		title="413 File too large",
		message=f"attachments cannot be larger than {app.config['MAX_ATTACHMENT_SIZE']}MB.",
		v=g.v
	), 413
