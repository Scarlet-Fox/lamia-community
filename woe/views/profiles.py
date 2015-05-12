from woe.models.core import User
from woe.forms.core import AvatarTitleForm
from woe import app
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from flask.ext.login import login_required, current_user
from werkzeug import secure_filename
from os import path
import arrow

@app.route('/member/<login_name>')
@login_required
def view_profile(login_name):
    try:
        user = User.objects(login_name=login_name.strip().lower())[0]
    except IndexError:
        abort(404)
    return render_template("profile.jade", profile=user)
    
@app.route('/member/change-avatar-title', methods=['GET', 'POST'])
@login_required
def change_avatar_or_title():
    try:
        user = User.objects(login_name=current_user.login_name.strip().lower())[0]
    except IndexError:
        abort(404)
    
    form = AvatarTitleForm(csrf_enabled=False)
    
    if form.validate_on_submit():
        filename = str(user.pk) + "." + form.avatar.data.filename.split(".")[-1]
        form.avatar.data.save(path.join(app.config["AVATAR_UPLOAD_DIR"],filename))
    else:
        filename = None
        form.title.data = user.title
    
    return render_template("profile/change_avatar.jade", profile=user, form=form, filename=filename)