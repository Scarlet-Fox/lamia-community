from woe import app
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from flask.ext.login import login_required, current_user
import flask_admin as admin
from flask_admin import helpers, expose
from flask_admin.contrib.mongoengine import ModelView
from woe.models.core import User, StatusUpdate, Attachment, PrivateMessageTopic, PrivateMessage, Notification
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
    column_list = ("login_name", "display_name", "email_address", "banned", "validated", "status_count", "status_comment_count","last_seen")
    column_filters = ["banned","validated","disable_posts","disable_status","disable_status_participation","disable_pm","disable_topics","old_member_id"]
    column_searchable_list = ('login_name', 'display_name','about')
    
    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

class NotificationView(ModelView):
    can_delete = False
    column_list = ("category", "author_name", "user_name", "text", "url", "created")
    column_filters = ["acknowledged", "user_name"]
    
    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

class CategoryView(ModelView):
    can_delete = False
    column_list = ("name", "parent", "weight", "view_count", "post_count", "topic_count")
    
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
    column_filters = ('topic_name', 'author_name', 'html', 'old_ipb_id', 'hidden')
    
    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

class AttachView(ModelView):
    can_delete = False
    column_list = ("owner_name", "path", "mimetype", "size_in_bytes", "x_size", "created_date", "used_in")
    column_filters = ("owner_name", 'linked','mimetype','origin_domain','origin_url','alt','extension')
    
    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

class PrivateMessageTopicView(ModelView):
    can_delete = False
    column_list = ("title", "creator_name", "created", "last_reply_time", "last_reply_name", "message_count", "participant_count")
    column_filters = ("creator_name","title","last_reply_name")
    
    def is_accessible(self):
        return current_user.login_name in ["luminescence", "zoop"]

class PrivateMessageView(ModelView):
    can_delete = False
    column_list = ("topic_name", "topic_creator_name", "created", "author_name", "message")
    column_filters = ("topic_name", "topic_creator_name", "author_name", "message")    
    
    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.login_name in ["luminescence", "zoop"])

admin.add_view(UserView(User))
admin.add_view(StatusView(StatusUpdate))
admin.add_view(NotificationView(Notification))
admin.add_view(PrivateMessageTopicView(PrivateMessageTopic, category='Private Messages'))
admin.add_view(PrivateMessageView(PrivateMessage, category='Private Messages'))
admin.add_view(CategoryView(Category, category='Forum'))
admin.add_view(TopicView(Topic, category='Forum'))
admin.add_view(PostView(Post, category='Forum'))
admin.add_view(PrefixView(Prefix, category='Forum'))
admin.add_view(AttachView(Attachment))