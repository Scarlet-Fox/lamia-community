from woe import app
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from flask.ext.login import login_required, current_user
import flask_admin as admin
from flask_admin import helpers, expose
from flask_admin.contrib.mongoengine import ModelView
from woe.models.core import User, StatusUpdate
from woe.models.forum import Category, Topic, Prefix, Post

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
    column_list = ("login_name", "display_name", "email_address", "banned", "validated", "status_count", "status_comment_count")
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
    column_list = ("title","created","creator", 'view_count', 'post_count')
    column_filters = ["sticky","hidden","closed","prefix"]
    column_searchable_list = ('title',)
    
    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)
        
class PrefixView(ModelView):
    can_delete = False
    column_list = ("prefix","pre_html","post_html")
    
    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

class StatusView(ModelView):
    can_delete = False
    column_list = ("author","attached_to_user","message","created","replies")
    column_filters = ["author_name","attached_to_user_name"]
    
    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

class PostView(ModelView):
    can_delete = False
    column_list = ("topic_name", "created", "author_name", "boop_count")
    column_filters = ('topic_name', 'author_name', 'html')
    
    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)
    
admin.add_view(UserView(User))
admin.add_view(CategoryView(Category))
admin.add_view(TopicView(Topic))
admin.add_view(PostView(Post))
admin.add_view(PrefixView(Prefix))
admin.add_view(StatusView(StatusUpdate))

