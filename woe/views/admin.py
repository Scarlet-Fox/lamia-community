from woe import app
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from flask.ext.login import login_required, current_user
import flask_admin as admin
from flask_admin import helpers, expose
from flask_admin.contrib.sqla import ModelView
# from flask_admin.contrib.mongoengine import ModelView
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
    column_list = ("id", "label",)

    column_formatters = {
        'label': _label_formatter_
    }

    column_filters = ["id", ]

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin) or current_user.login_name == "scarlet"

class RoleView(ModelView):
    can_create = True
    can_delete = True
    column_list = ("id", "role",)

    column_formatters = {
        'role': _label_formatter_
    }

    column_filters = ["id", ]

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin) or current_user.login_name == "scarlet"

class UserView(ModelView):
    can_create = False
    can_delete = False
    column_list = ("id", "login_name", "display_name", "email_address", "banned", "validated", "hidden_last_seen")
    # column_searchable_list = ('login_name', 'display_name','about_me')
    # form_excluded_columns = ("ignored_users", "ignored_user_signatures","followed_by", "pending_friends", "rejected_friends", "friends")

    column_filters = ["id", "login_name", "email_address", "display_name", "banned", "validated"]
    form_excluded_columns = ["status_updates", "private_messages", "notifications", "booped_posts"]

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin) or current_user.login_name == "scarlet"

class FollowView(ModelView):
    can_create = False
    can_delete = False
    column_list = ("id", "user", "following")
    column_sortable_list = (('following',sqlm.FollowingUser.following_id),)

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin) or current_user.login_name == "scarlet"

class NotificationView(ModelView):
    can_delete = False
    column_list = (
        "id",
        "created",
        "category",
        "author",
        "user",
        "message",
    )
    column_filters = ("acknowledged", "id")

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin) or current_user.login_name == "scarlet"

class CategoryView(ModelView):
    can_delete = False
    column_list = (
        "id",
        "name",
        "parent",
        "weight",
    )
    form_excluded_columns = ("recent_post", "recent_topic")

    column_filters = ["id", ]
    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin) or current_user.login_name == "scarlet"

class TopicView(ModelView):
    can_delete = False
    column_list = ("id", "title","created")
    column_filters = ["id", "slug", "sticky","hidden","locked","label"]
    # column_searchable_list = ('title',)
    form_excluded_columns = ("moderators", "recent_post", "editor")

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin) or current_user.login_name == "scarlet"

class StatusView(ModelView):
    can_delete = False
    column_list = ("id", "author","attached_to_user","created","replies", "hidden", "locked", "muted")
    # column_filters = ["author_name","attached_to_user_name", "hidden", "locked", "muted"]
    form_excluded_columns = ("participants", "comments")

    column_filters = ["id", ]
    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin) or current_user.login_name == "scarlet"

class StatusCommentView(ModelView):
    can_delete = False
    column_list = ("id", "author","created","status")
    # column_filters = ["author_name","attached_to_user_name", "hidden", "locked", "muted"]
    form_excluded_columns = ("status",)

    column_filters = ["id", ]

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin) or current_user.login_name == "scarlet"

class PostView(ModelView):
    can_delete = False
    column_list = ("id", "topic", "created", "author")
    # column_filters = ('topic_name', 'author_name', 'html', 'old_ipb_id', 'hidden')
    form_excluded_columns = ("boops", "topic", "editor", "character", "avatar")

    column_filters = ["id", ]

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin) or current_user.login_name == "scarlet"

class AttachView(ModelView):
    can_delete = False
    column_list = ("id", "path", "mimetype", "size_in_bytes", "x_size", "created_date", "used_in")
    # column_filters = ("owner_name", 'linked','mimetype','origin_domain','origin_url','alt','extension', "do_not_convert")

    column_filters = ["id", ]

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin) or current_user.login_name == "scarlet"

class PrivateMessageTopicView(ModelView):
    can_delete = False
    column_list = ("id", "title", "author")
    # column_list = ("title", "created", "last_reply_time", "last_reply_name", "message_count", "participant_count")
    # column_filters = ("creator_name","title","last_reply_name")
    # form_excluded_columns = ("participating_users", "blocked_users","users_left_pm")

    column_filters = ["id", ]
    def is_accessible(self):
        return current_user.login_name in ["scarlet", "zoop"]

class IPAddressView(ModelView):
    column_list = ("id", "user", "ip_address", "last_seen")
    column_filters = ("ip_address", "user_id")

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

class LogView(ModelView):
    column_list = ("id", "user", "ip_address", "time", "method", "path", "error", "error_code")
    column_filters = ("user_id", "ip_address", "time", "path", "method", "error", "error_code")

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

class FingerprintView(ModelView):
    column_list = ("id", "user", "fingerprint_hash", "factors", "last_seen")
    column_filters = ("user_id", "fingerprint_hash", "factors", "last_seen")

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

class CharacterView(ModelView):
    can_delete = False
    column_list = ("id", "author", "name", "created",)
    column_filters = ("author_id", "name", "created")
    column_searchable_list = ("name", "appearance", "personality", "backstory", "other")

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

class ReportView(ModelView):
    column_list = ("id", "author", "url", "status", "created")
    column_filters = ("url",)

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

class ThemeView(ModelView):
    column_list = ("id", "name")

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

class BlogView(ModelView):
    column_list = ("id", "name")

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

class BlogEntryView(ModelView):
    column_list = ("id", "title")
    form_excluded_columns = ("character", "avatar", "editor")

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

class BlogCommentView(ModelView):
    column_list = ("id", "b_e_title")

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

class FriendshipView(ModelView):
    column_list = ("id", "user", "friend")

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

class SignatureView(ModelView):
    column_list = ("id", "user")

    def is_accessible(self):
        return (current_user.is_authenticated() and current_user.is_admin)

admin.add_view(LabelView(sqlm.Label, sqla.session))
admin.add_view(CharacterView(sqlm.Character, sqla.session))
admin.add_view(ReportView(sqlm.Report, sqla.session))
admin.add_view(BlogView(sqlm.Blog, sqla.session, category='Blog'))
admin.add_view(BlogEntryView(sqlm.BlogEntry, sqla.session, category='Blog'))
admin.add_view(BlogCommentView(sqlm.BlogComment, sqla.session, category='Blog'))
admin.add_view(ThemeView(sqlm.SiteTheme, sqla.session, category='Core'))
admin.add_view(AttachView(sqlm.Attachment, sqla.session, category='Core'))
admin.add_view(LogView(sqlm.SiteLog, sqla.session, category='Core'))
admin.add_view(IPAddressView(sqlm.IPAddress, sqla.session, category='Core'))
admin.add_view(FingerprintView(sqlm.Fingerprint, sqla.session, category='Core'))
admin.add_view(UserView(sqlm.User, sqla.session, category='Members'))
admin.add_view(FollowView(sqlm.FollowingUser, sqla.session, category='Members'))
admin.add_view(RoleView(sqlm.Role, sqla.session, category='Members'))
admin.add_view(FriendshipView(sqlm.Friendship, sqla.session, category='Members'))
admin.add_view(SignatureView(sqlm.Signature, sqla.session, category='Members'))
admin.add_view(NotificationView(sqlm.Notification, sqla.session, category='Members'))
admin.add_view(StatusView(sqlm.StatusUpdate, sqla.session, category='Members'))
admin.add_view(StatusCommentView(sqlm.StatusComment, sqla.session, category='Members'))
admin.add_view(PrivateMessageTopicView(sqlm.PrivateMessage, sqla.session, category='Members'))
admin.add_view(PostView(sqlm.Post, sqla.session, category='Forum'))
admin.add_view(TopicView(sqlm.Topic, sqla.session, category='Forum'))
admin.add_view(CategoryView(sqlm.Category, sqla.session, category='Forum'))

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
