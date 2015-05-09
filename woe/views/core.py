from woe import login_manager
from woe import app
from woe.models.core import User
from woe.forms.core import LoginForm
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from flask.ext.login import login_user, logout_user

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
    form = LoginForm(csrf_enabled=False)
    if form.validate_on_submit():
        login_user(form.user)
        flash('Welcome back!')
        return redirect('/')
        
    return render_template("sign_in.jade", form=form)
    
@app.route('/sign-out', methods=['POST'])
def sign_out():
    logout_user()
    return redirect('/')