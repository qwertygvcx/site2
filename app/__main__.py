from flask import Flask, render_template, g, session, request
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from os import environ
import time
import secrets


app = Flask(__name__, static_folder='_static')

app.config['SECRET_KEY'] = environ.get('MASTER_KEY')
app.config['SITE_COLOR'] = environ.get('SITE_COLOR')
app.config['SITE_NAME'] = environ.get('SITE_NAME')

# import jinja filters and globals
from app.helpers.jinja import *

engine = create_engine(environ.get('DB_URL'), echo=True)
Base = declarative_base()

db_session = scoped_session(sessionmaker(bind=engine))

from app.classes.board import Board
from app.helpers.wrappers import auth_desired


@app.before_request
def before_request():

    g.db = db_session
    g.time = int(time.time())

    if 'session_id' not in session:
        session['session_id'] = secrets.token_hex(16)


@app.get("/")
@auth_desired
def index(v):

    boards = g.db.query(Board).filter_by(private=False).all()

    return render_template("home.html", boards=boards, v=v)


# import routes
from app.routes import *
app.register_blueprint(auth)
app.register_blueprint(settings)
app.register_blueprint(user_blueprint)


@app.post('/logout')
def logout():

    session.pop('user_id')
    session.pop('login_nonce')

    return redirect(request.referrer)


@app.after_request
def after_request(response):

    try:
        g.db.commit()
    except AttributeError:
        pass
    except BaseException:
        g.db.rollback()
        abort(500)

    return response


@app.teardown_appcontext
def teardown(e):
    """ always close db, even after failed requests """
    g.db.close()


if __name__ == '__main__':
    app.run()
