from app.__main__ import app
from flask import render_template


@app.get("/*/login")
def login_get():

    return render_template("login.html")
