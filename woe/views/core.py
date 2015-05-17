from woe import login_manager
from woe import app
from woe.models.core import User, DisplayNameHistory, StatusUpdate
from woe.models.forum import Category, Post
from collections import OrderedDict
from woe.forms.core import LoginForm, RegistrationForm
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session
from flask.ext.login import login_user, logout_user
import arrow

@login_manager.user_loader
def load_user(login_name):
    try:
        user = User.objects(login_name=login_name)[0]
        user.update(last_seen=arrow.utcnow().datetime)
        return user
    except IndexError:
        return None

@app.route('/')
def index():
    categories = OrderedDict()
    
    for category in Category.objects(root_category=True):
        categories[category.name] = [category,]
        for subcategory in Category.objects(parent=category):
            categories[category.name].append(subcategory)
    
    status_updates = StatusUpdate.objects(attached_to_user=None)[:5]
    
    online_users = User.objects(last_seen__gte=arrow.utcnow().replace(minutes=-15).datetime)
    post_count = Post.objects().count()
    member_count = User.objects(banned=False).count()
    newest_member = User.objects().order_by("-joined")[0]
    
    return render_template("index.jade", 
        categories=categories, status_updates=status_updates, online_users=online_users,
        post_count=post_count, member_count=member_count, newest_member=newest_member, 
        online_user_count=online_users.count())

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