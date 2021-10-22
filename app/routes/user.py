from flask import Blueprint, request, render_template
from app.helpers.wrappers import *

user_blueprint = Blueprint('user_blueprint', __name__)
""" these do not always require a logged in accout """


@user_blueprint.get('/my_info')
@auth_required
def my_info(v):

	hide_fields = (
		'passhash',
		'_sa_instance_state'
	)

	data = {key:value for key, value in v.__dict__.items() if key not in hide_fields}
	data['_banned'] = bool(data['_banned'])

	return render_template('user/my_info.html', data=data, v=v)
