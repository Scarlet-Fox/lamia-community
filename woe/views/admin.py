from woe import app
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from flask.ext.login import login_required, current_user
import flask_admin as admin
from flask_admin import helpers, expose
from flask_admin.contrib.sqla import ModelView
# from flask_admin.contrib.mongoengine import ModelView
from woe.models.core import *
from woe.models.forum import *
from woe.models.roleplay import *
from woe.models.blogs import *
from woe import sqla
import woe.sqlmodels as sqlm
from jinja2 import Markup

class AuthAdminIndexView(admin.AdminIndexView):
    @expose('/')
    def index(self):
        if not (current_user.is_authenticated() and current_user.is_admin) and not current_user.login_name == "scarlet":
            return redirect("/")
        return super(AuthAdminIndexView, self).index()

admin = admin.Admin(app, index_view=AuthAdminIndexView())

def _label_formatter_(view, context, model, name):
    return Markup("""%s%s%s""" % (model.pre_html, model.label, model.post_html))

class LabelView(ModelView):
    can_create = True
    can_delete = True
    column_list = ("label",)

    column_formatters = {
        'label': _label_formatter_
    }

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin) or current_user.login_name == "scarlet"

class UserView(ModelView):
    can_create = False
    can_delete = False
    column_list = ("login_name", "display_name", "email_address", "banned", "validated", "hidden_last_seen")
    # column_searchable_list = ('login_name', 'display_name','about_me')
    # form_excluded_columns = ("ignored_users", "ignored_user_signatures","followed_by", "pending_friends", "rejected_friends", "friends")

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin) or current_user.login_name == "scarlet"

class NotificationView(ModelView):
    can_delete = False
    column_list = (
        "created",
        "category",
        "author",
        "user",
        "message",
    )
    column_filters = ("acknowledged",)

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin) or current_user.login_name == "scarlet"

class CategoryView(ModelView):
    can_delete = False
    column_list = (
        "name",
        "parent",
        "weight",
    )

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin) or current_user.login_name == "scarlet"

class TopicView(ModelView):
    can_delete = False
    column_list = ("title","created")
    # column_filters = ["sticky","hidden","closed","prefix"]
    # column_searchable_list = ('title',)
    # form_excluded_columns = ("watchers", "banned_from_topic", "first_post")

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin) or current_user.login_name == "scarlet"

class StatusView(ModelView):
    can_delete = False
    column_list = ("author","attached_to_user","created","replies", "hidden", "locked", "muted")
    # column_filters = ["author_name","attached_to_user_name", "hidden", "locked", "muted"]
    # form_excluded_columns = ("participants", "ignoring","blocked")

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin) or current_user.login_name == "scarlet"

class PostView(ModelView):
    can_delete = False
    column_list = ("topic", "created", "author")
    # column_filters = ('topic_name', 'author_name', 'html', 'old_ipb_id', 'hidden')
    # form_excluded_columns = ("boops", )

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

admin.add_view(LabelView(sqlm.Label, sqla.session))
admin.add_view(UserView(sqlm.User, sqla.session, category='Members'))
admin.add_view(NotificationView(sqlm.Notification, sqla.session, category='Members'))
admin.add_view(StatusView(sqlm.StatusUpdate, sqla.session, category='Members'))
admin.add_view(PostView(sqlm.Post, sqla.session, category='Forum'))
admin.add_view(TopicView(sqlm.Topic, sqla.session, category='Forum'))
admin.add_view(CategoryView(sqlm.Category, sqla.session, category='Forum'))

#
# class AttachView(ModelView):
#     can_delete = False
#     column_list = ("owner_name", "path", "mimetype", "size_in_bytes", "x_size", "created_date", "used_in")
#     column_filters = ("owner_name", 'linked','mimetype','origin_domain','origin_url','alt','extension', "do_not_convert")
#
#     def is_accessible(self):
#         return (current_user.is_authenticated() and current_user.is_admin)
#
# class PrivateMessageTopicView(ModelView):
#     can_delete = False
#     column_list = ("title", "creator_name", "created", "last_reply_time", "last_reply_name", "message_count", "participant_count")
#     column_filters = ("creator_name","title","last_reply_name")
#     form_excluded_columns = ("participating_users", "blocked_users","users_left_pm")
#
#     def is_accessible(self):
#         return current_user.login_name in ["luminescence", "zoop"]
#
# class PrivateMessageView(ModelView):
#     can_delete = False
#     column_list = ("topic_name", "topic_creator_name", "created", "author_name", "message")
#     column_filters = ("topic_name", "topic_creator_name", "author_name", "message")
#
#     def is_accessible(self):
#         return (current_user.is_authenticated() and current_user.login_name in ["luminescence", "zoop"])
#
# class IPAddressView(ModelView):
#     column_list = ("user_name", "ip_address", "last_seen")
#     column_filters = ("user_name", "ip_address", "last_seen")
#
#     def is_accessible(self):
#         return (current_user.is_authenticated() and current_user.is_admin)
#
# class LogView(ModelView):
#     column_list = ("user_name", "ip_address", "time", "method", "path", "error", "error_code")
#     column_filters = ("user_name", "ip_address", "time", "path", "method", "error", "error_code")
#
#     def is_accessible(self):
#         return (current_user.is_authenticated() and current_user.is_admin)
#
# class FingerprintView(ModelView):
#     column_list = ("user_name", "fingerprint_hash", "fingerprint_factors", "last_seen")
#     column_filters = ("user_name", "fingerprint_hash", "fingerprint_factors", "last_seen")
#
#     def is_accessible(self):
#         return (current_user.is_authenticated() and current_user.is_admin)
#
# class ReportView(ModelView):
#     column_list = ("initiated_by_u", "content_type", "content_pk", "url", "status", "created")
#     column_filters = ("initiated_by_u", "content_type", "content_pk", "url", "status", "created")
#
#     def is_accessible(self):
#         return (current_user.is_authenticated() and current_user.is_admin)
#
# class CharacterView(ModelView):
#     column_list = ("creator_name", "name", "created", "post_count")
#     column_filters = ("creator_name", "name", "created")
#     column_searchable_list = ('creator_name', "name", "appearance", "personality", "backstory", "other")
#     form_excluded_columns = ("creator", "creator_name","posts", "roleplays", "avatars", "gallery")
#
#     def is_accessible(self):
#         return (current_user.is_authenticated() and current_user.is_admin)
#
# class BlogView(ModelView):
#     column_list = ("creator_name", "name", "created", "disabled")
#     column_filters = ("name", "description", "disabled")
#     column_searchable_list = ("name", "description")
#
#     def is_accessible(self):
#         return (current_user.is_authenticated() and current_user.is_admin)
#
# class BlogEntryView(ModelView):
#     column_list = ("author_name", "title", "blog_name", "created", "draft", "locked", "hidden")
#     column_filters = ("author_name", "blog_name", "title", "created", "draft", "locked", "hidden")
#     column_searchable_list = ("title", "html")
#
#     def is_accessible(self):
#         return (current_user.is_authenticated() and current_user.is_admin)
#
# class BlogCommentView(ModelView):
#     column_list = ("author_name", "blog_entry_name", "blog_name", "created", "hidden")
#     column_filters = ("author_name", "blog_entry_name", "blog_name", "created", "hidden")
#     column_searchable_list = ("html",)
#
#     def is_accessible(self):
#         return (current_user.is_authenticated() and current_user.is_admin)
