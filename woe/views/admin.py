from woe import app
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from flask.ext.login import login_required, current_user
import flask_admin as admin
from flask_admin import helpers, expose
from flask_admin.contrib.mongoengine import ModelView
from woe.models.core import User
from woe.models.forum import Category, Topic

class AuthAdminIndexView(admin.AdminIndexView):
    @expose('/')
    def index(self):
        if not (current_user.is_authenticated() and current_user.is_admin):
            return redirect("/")
        return super(AuthAdminIndexView, self).index()

admin = admin.Admin(app, index_view=AuthAdminIndexView())

class UserView(ModelView):
    can_create = False
    can_delete = False
    column_list = ("login_name", "display_name", "email_address", "banned", "validated")
    column_filters = ["banned","validated","disable_posts","disable_status","disable_status_participation","disable_pm","disable_topics"]
    column_searchable_list = ('login_name', 'display_name','about')
    
    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

class CategoryView(ModelView):
    can_delete = False
    column_list = ("name", "parent", "weight", "view_count", "topic_count")
    
    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

class TopicView(ModelView):
    can_delete = False
    column_list = ("title","created","creator", 'view_count')
    column_filters = ["sticky","hidden","closed"]
    column_searchable_list = ('title',)
    
    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

admin.add_view(UserView(User))
admin.add_view(CategoryView(Category))
admin.add_view(TopicView(Topic))