from woe import login_manager
from woe import app
from woe.models.core import User
from flask import abort, redirect, url_for, request, render_template, make_response

@login_manager.user_loader
def load_user(login_name):
    try:
        return User.objects(login_name=login_name)[0]
    except IndexError:
        return None

