from woe import login_manager
from woe import app
from woe.models.core import User
from flask import abort, redirect, url_for, request, render_template, make_response, json

@login_manager.user_loader
def load_user(login_name):
    try:
        return User.objects(login_name=login_name)[0]
    except IndexError:
        return None

@app.route('/')
def index():
    return render_template("base.jade")

@app.route('/sign-in', methods=['GET', 'POST'])
def sign_in():
    return render_template("sign_in.jade")