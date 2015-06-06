from woe import login_manager
from woe import app
from woe.models.core import User, DisplayNameHistory, StatusUpdate
from woe.models.forum import Category, Post
from collections import OrderedDict
from woe.forms.core import LoginForm, RegistrationForm
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session
from flask.ext.login import login_user, logout_user, login_required, current_user
from woe.utilities import get_top_frequences, scrub_json, humanize_time, ForumPostParser, ForumHTMLCleaner
import arrow

@app.route('/status/<status>/replies', methods=['GET'])
@login_required
def status_update_replies(status):
    try:
        status = StatusUpdate.objects(id=status)[0]
    except:
        return abort(404)
        
    if status.hidden == True:
        return abort(404)
        
    replies = []
    for reply in status.comments:
        parsed_reply = reply.to_mongo().to_dict()
        parsed_reply["user_name"] = reply.author.display_name
        parsed_reply["user_avatar"] = reply.author.get_avatar_url("40")
        parsed_reply["user_avatar_x"] = reply.author.avatar_40_x
        parsed_reply["user_avatar_y"] = reply.author.avatar_40_y
        parsed_reply["time"] = humanize_time(reply.created)
        replies.append(parsed_reply)
        
    return app.jsonify(replies=replies)

@app.route('/status/<status>', methods=['GET'])
@login_required
def display_status_update(status):
    print status
    
    try:
        status = StatusUpdate.objects(id=status)[0]
    except:
        return abort(404)
        
    if status.hidden == True:
        return abort(404)
        
    if current_user.is_admin == True or current_user._get_current_object() == status.author:
        mod = True
    else:
        mod = False
        
    status_updates = StatusUpdate.objects(attached_to_user=None)[:10]
    cleaned_statuses = []
    user_already_posted = []
    for recent_status in status_updates:
        if recent_status.author_name in user_already_posted:
            continue
        
        user_already_posted.append(recent_status.author_name)
        cleaned_statuses.append(recent_status)
            
    return render_template("status_update.jade", status_updates=cleaned_statuses, status=status, mod=mod)


@login_manager.user_loader
def load_user(login_name):
    try:
        user = User.objects(login_name=login_name)[0]
        user.update(last_seen=arrow.utcnow().datetime)
        return user
    except IndexError:
        return None

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