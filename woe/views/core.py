from woe import login_manager
from woe import app
from woe.models.core import User, DisplayNameHistory
from woe.forms.core import LoginForm, RegistrationForm
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from flask.ext.login import login_user, logout_user
import arrow

@login_manager.user_loader
def load_user(login_name):
    try:
        return User.objects(login_name=login_name)[0]
    except IndexError:
        return None

@app.route('/')
def index():
    return render_template("base.jade")

@app.route('/hello/<pk>')
def confirm_register(pk):
    user = User.objects(pk=pk)[0]
    return render_template("welcome_new_user.jade", profile=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(csrf_enabled=False)
    if form.validate_on_submit():
        new_user = User(
            login_name = form.username.data.strip().lower(),
            display_name = form.username.data.strip(),
            email_address = form.email.data.strip().lower()
        )
        new_user.set_password(form.password.data.strip())
        new_user.joined = arrow.utcnow().datetime
        new_user.save()
        
        # Todo : Notify Admin Users
        
        return redirect('/hello/'+str(new_user.pk))
    
    return render_template("register.jade", form=form)

@app.route('/sign-in', methods=['GET', 'POST'])
def sign_in():
    form = LoginForm(csrf_enabled=False)
    if form.validate_on_submit():
        login_user(form.user)
        # TODO - get fingerprint
        return redirect('/')
        
    return render_template("sign_in.jade", form=form)
    
@app.route('/sign-out', methods=['POST'])
def sign_out():
    logout_user()
    return redirect('/')