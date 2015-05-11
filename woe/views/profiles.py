from woe.models.core import User
from woe import app
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from flask.ext.login import login_required
import arrow

@app.route('/user/<login_name>')
@login_required
def view_profile(login_name):
    try:
        user = User.objects(login_name=login_name.strip().lower())[0]
    except IndexError:
        abort(404)
    return render_template("profile.jade", profile=user)