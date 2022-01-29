from flask import (
	Blueprint,
	request,
	g,
	session,
	render_template,
	abort
)
from app.helpers.wrappers import get_logged_in_user

settings = Blueprint('settings', __name__, url_prefix='/c/settings')


@settings.before_request
def settings_before_request():
	""" these endpoints all require a logged in account """
	v = get_logged_in_user()

	if not v:
		abort(401)

	g.v = v


@settings.get('/')
def settings_index():

	return render_template('settings/index.html', v=g.v)


@settings.post('/logout_everywhere')
def logout_everywhere():

	# confirm password
	if not g.v.check_password(request.form.get('password', '')):
		return render_template(
			'settings/index.html',
			error='invalid password',
			v=g.v
		)

	# increment login nonce
	g.v.login_nonce += 1

	session.pop('user_id')
	session.pop('login_nonce')

	return render_template(
		'message.html',
		title='action successful',
		message='you have been logged out everywhere.'
	)
