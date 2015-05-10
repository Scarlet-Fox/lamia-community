from woe import login_manager, app
from woe.models.core import User
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from flask.ext.login import login_required

@app.route('/dashboard')
@login_required
def view_dashboard():
    return render_template("dashboard.jade")