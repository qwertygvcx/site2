from flask import Flask, render_template, g
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from os import environ


app = Flask(__name__, static_folder='./_static')

app.config['SECRET_KEY'] = environ.get('MASTER_KEY')

engine = create_engine(environ.get('DB_URL'), echo=True)
Base = declarative_base()

db_session = scoped_session(sessionmaker(bind=engine))

from app.classes.board import Board


@app.before_request
def before_request():

    g.db = db_session


@app.get("/")
def index():

    boards = g.db.query(Board).filter_by(private=False).all()

    return render_template("home.html", boards=boards)

# import routes
from app.routes import *

if __name__ == '__main__':
    app.run()
