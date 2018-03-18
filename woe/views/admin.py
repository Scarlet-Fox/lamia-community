from woe import app
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from flask.ext.login import login_required, current_user
import flask_admin as admin
from flask_admin import helpers, expose
from flask_admin.contrib.sqla import ModelView
from woe import sqla
import woe.sqlmodels as sqlm
from jinja2 import Markup

class AuthAdminIndexView(admin.AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_mod and not current_user.is_admin:
            return redirect("/")
        return super(AuthAdminIndexView, self).index()

admin = admin.Admin(app, index_view=AuthAdminIndexView())


