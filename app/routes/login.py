from flask import (
    render_template,
    Blueprint,
    session,
    request,
    redirect,
    g
)
import re, secrets
from app.classes.user import User
from app.helpers.wrappers import get_logged_in_user
from urllib.parse import unquote

auth = Blueprint('auth', __name__)

class AuthError(Exception):
    pass


@auth.before_request
def auth_before_request():
    """ disallow these endpoints from being accessed if the user is logged in """
    v = get_logged_in_user()

    if v:
        redirect_to = request.args.get('redirect', '/')
        redirect_to = unquote(redirect_to)

        if not redirect_to.startswith('/'):
            redirect_to = '/'

        return redirect(redirect_to)


@auth.get('/c/login')
def login_get():

    redirect_to = request.args.get('redirect', '/')
    redirect_to = unquote(redirect_to)

    if not redirect_to.startswith('/'):
        redirect_to = '/'

    return render_template("login.html", redirect=redirect_to)


@auth.post('/c/login')
def login_post():

    try:
        username = request.form.get('name', '').strip()
        password = request.form.get('password', '').strip()
        redirect_to = request.form.get('redirect', '/')

        if not username or not password:
            raise AuthError()

        user = g.db.query(User).filter(User.name.ilike(username)).first()
        if not user:
            raise AuthError()

        if not user.check_password(password):
            raise AuthError()

        session['user_id'] = user.id
        session['login_nonce'] = user.login_nonce
        session['session_id'] = secrets.token_hex(16)

        if not redirect_to.startswith('/'):
            redirect_to = '/'

        return redirect(redirect_to)

    except AuthError as e:
        return render_template('login.html', error="invalid username/password")


@auth.post('/c/register')
def signup():

    try:
        username = request.form.get('name', '').strip()
        password = request.form.get('password', '').strip()
        redirect_to = request.form.get('redirect', '/')

        if not username or not password:
            raise AuthError("invalid username/password")

        valid_name_regex = re.compile('^[a-zA-Z0-9_]{3,20}$')
        if not valid_name_regex.fullmatch(username):
            raise AuthError("username must be 3-20 characters long and cannot contain special characters")

        if len(password) < 3:
            raise AuthError("password must be at least 3 characters long")

        existing_user = g.db.query(User).filter(User.name.ilike(username)).first()
        if existing_user:
            raise AuthError("username already taken")

        new_user = User(
            name=username,
            password=password,
            creation_ip=request.remote_addr,
            post_anon=('anon' in request.form)
        )

        g.db.add(new_user)
        g.db.flush()

        session['user_id'] = new_user.id
        session['login_nonce'] = new_user.login_nonce
        session['session_id'] = secrets.token_hex(16)

        # don't allow redirect to other sites the spaghetti way
        if not redirect_to.startswith('/'):
            redirect_to = '/'

        return redirect(redirect_to)

    except AuthError as e:
        return render_template('login.html', error=str(e))
