from flask import (
	Blueprint,
	send_from_directory,
	make_response,
	request
)
from app.__main__ import app
import os

static_blueprint = Blueprint('static_blueprint', __name__)


@static_blueprint.get('/-/thread/<parent_id>/<pid>/<filename>')
def get_post_file(parent_id, pid, filename):

	path = os.path.join(app.static_folder, 'ugc/thread')
	path = os.path.join(path, parent_id)
	path = os.path.join(path, pid)
	resp = make_response(send_from_directory(path, filename, as_attachment='download' in request.args))

	resp.headers['Cache-Control'] = 'public, max-age=604800'

	return resp
