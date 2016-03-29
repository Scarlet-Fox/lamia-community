from woe import sqla as db
from sqlalchemy.dialects.postgresql import JSONB
from woe.utilities import ipb_password_check
from slugify import slugify
from woe import bcrypt
from flask.ext.login import current_user
from wand.image import Image
from threading import Thread
import arrow, re, os, math
from mako.template import Template
from mako.lookup import TemplateLookup

_mylookup = TemplateLookup(directories=['woe/templates/mako'])

############################################################
# Private Message Models
############################################################

class PrivateMessageUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_pm_u_author", ondelete="CASCADE"), index=True)
    author = db.relationship("User", foreign_keys="PrivateMessageUser.author_id")

    pm_id = db.Column(db.Integer, db.ForeignKey('private_message.id',
        name="fk_pm_u_pm", ondelete="CASCADE"), index=True)
    pm = db.relationship("PrivateMessage", foreign_keys="PrivateMessageUser.pm_id")
    __table_args__ = (db.UniqueConstraint('author_id', 'id', name='unique_user_pm_user'),)

    ignoring = db.Column(db.Boolean, default=False)
    exited = db.Column(db.Boolean, default=False)
    blocked = db.Column(db.Boolean, default=False)
    viewed = db.Column(db.Boolean, default=False)
    last_viewed = db.Column(db.DateTime, index=True)

    def __repr__(self):
        return "<PrivateMessageUser: (user='%s', pm='%s')>" % (self.author.display_name, self.pm.title)

class PrivateMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)
    count = db.Column(db.Integer, default=0)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_pm_author", ondelete="CASCADE"))
    author = db.relationship("User", foreign_keys="PrivateMessage.author_id")

    last_reply_id = db.Column(db.Integer, db.ForeignKey('private_message_reply.id',
        name="fk_pm_lastreply"), index=True)
    last_reply = db.relationship("PrivateMessageReply", foreign_keys="PrivateMessage.last_reply_id")

    participants = db.relationship("User", secondary="private_message_user", backref="private_messages")

    created = db.Column(db.DateTime)
    old_mongo_hash = db.Column(db.String, nullable=True, index=True)
    last_seen_by = db.Column(JSONB)

    def participant_objects(self):
        return PrivateMessageUser.query.filter_by(pm=self).all()

    def __repr__(self):
        return "<PrivateMessage: (title='%s')>" % (self.title, )

class PrivateMessageReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_pm_r_author", ondelete="CASCADE"))
    author = db.relationship("User", foreign_keys="PrivateMessageReply.author_id")

    pm_id = db.Column(db.Integer, db.ForeignKey('private_message.id',
        name="fk_pm_r_pm", ondelete="CASCADE"))
    pm = db.relationship("PrivateMessage", foreign_keys="PrivateMessageReply.pm_id")

    message = db.Column(db.Text)
    old_mongo_hash = db.Column(db.String, nullable=True, index=True)

    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime, nullable=True)
    pm_title = db.Column(db.String, default="")

    def __repr__(self):
        return "<PrivateMessageReply: (created='%s', user='%s', pm='%s')>" % (self.created, self.user.display_name, self.pm.title)

############################################################
# Status Update Models
############################################################

class StatusUpdateUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_status_user_author", ondelete="CASCADE"))
    author = db.relationship("User", foreign_keys="StatusUpdateUser.author_id")

    status_id = db.Column(db.Integer, db.ForeignKey('status_update.id',
        name="fk_status_user_status", ondelete="CASCADE"))
    status = db.relationship("StatusUpdate", foreign_keys="StatusUpdateUser.status_id")
    __table_args__ = (db.UniqueConstraint('author_id', 'id', name='unique_user_status_user'),)

    ignoring = db.Column(db.Boolean, default=False)
    blocked = db.Column(db.Boolean, default=False)
    viewed = db.Column(db.Integer, default=0)
    last_viewed = db.Column(db.DateTime)

    def __repr__(self):
        return "<StatusUpdateUser: (user='%s', status='%s')>" % (self.user.display_name, self.status.message[0:50])

class StatusComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_status_comment_author", ondelete="CASCADE"))
    author = db.relationship("User")
    created = db.Column(db.DateTime)
    hidden = db.Column(db.Boolean, default=False)

    status_id = db.Column(db.Integer, db.ForeignKey('status_update.id',
        name="fk_status_comment_status", ondelete="CASCADE"))
    status = db.relationship("StatusUpdate", backref="comments")

    def __repr__(self):
        return "<StatusComment: (created='%s', author='%s')>" % (self.created, self.author.display_name)

class StatusUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_status_update_author", ondelete="CASCADE"), index=True)
    author = db.relationship("User", foreign_keys="StatusUpdate.author_id")
    attached_to_user_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_status_update_attachedtouser", ondelete="CASCADE"), index=True)
    attached_to_user = db.relationship("User", foreign_keys="StatusUpdate.attached_to_user_id")

    participants = db.relationship("User", secondary="status_update_user", backref="status_updates")

    last_replied = db.Column(db.DateTime)
    last_viewed = db.Column(db.DateTime)
    replies = db.Column(db.Integer, default=0)
    created = db.Column(db.DateTime, index=True)
    hidden = db.Column(db.Boolean, default=False)
    muted = db.Column(db.Boolean, default=False)
    locked = db.Column(db.Boolean, default=False)

    old_mongo_hash = db.Column(db.String, nullable=True, index=True)

    def get_comment_count(self):
        count = db.session.query(StatusComment).filter(StatusComment.status_id==self.id).count()
        return count

    def blocked(self):
        return db.session.query(StatusUpdateUser).filter(StatusComment.status_id==self.id).filter_by(blocked=True).all()

    def __repr__(self):
        return "<StatusUpdate: (created='%s', author='%s', message='%s')>" % (self.created, self.author.display_name, self.message[0:50])

db.Index('_status_user_created', StatusUpdate.author_id, StatusUpdate.created)

############################################################
# Core Site Models
############################################################

class SiteTheme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    theme_css = db.Column(db.String)
    base_css = db.Column(db.String)
    weight = db.Column(db.Integer, default=0)
    created = db.Column(db.DateTime)

    def __repr__(self):
        return "<SiteTheme: (name='%s')>" % (self.name,)

############################################################
# Security Models
############################################################

class IPAddress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.Text)
    last_seen = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_ipaddress_user", ondelete="CASCADE"))
    user = db.relationship("User")

    __table_args__ = (db.UniqueConstraint('user_id', 'id', name='unique_user_ip_addy'),)

    def __repr__(self):
        return "<IPAddress: (ip_address='%s', user=)>" % (self.ip_address,)

class Fingerprint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    json = db.Column(JSONB)
    factors = db.Column(db.Integer, default=0)
    fingerprint_hash = db.Column(db.String, default="")
    last_seen = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_fingerprint_user", ondelete="CASCADE"))
    user = db.relationship("User")
    __table_args__ = (db.UniqueConstraint('user_id', 'fingerprint_hash', name='unique_user_hash'),)

    def __repr__(self):
        return "<Fingerprint: (factors='%s', user=)>" % (self.factors,)

    def compute_similarity_score(self, stranger):
        score = 0.0
        attributes = {}

        for key in self.json.keys():
            attributes[key] = 1

        for key in stranger.json.keys():
            attributes[key] = 1

        max_score = float(len(attributes.keys()))
        for attribute in attributes.keys():
            if self.json.get(attribute, None) == stranger.json.get(attribute, None):
                score += 1

        return score/max_score

class SiteLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    method = db.Column(db.String, default="")
    path = db.Column(db.String, default="", index=True)
    ip_address = db.Column(db.String, default="")
    agent_platform = db.Column(db.String, default="")
    agent_browser = db.Column(db.String, default="")
    agent_browser_version = db.Column(db.String, default="")
    agent = db.Column(db.String, default="")
    time = db.Column(db.DateTime, index=True)
    error = db.Column(db.Boolean, default=False)
    error_name = db.Column(db.String, default="")
    error_code = db.Column(db.String, default="")
    error_description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_sitelog_user", ondelete="SET NULL"), nullable=True, index=True)
    user = db.relationship("User")

    def __repr__(self):
        return "%s %s %s %s :: %s %s %s %s" % (self.time.isoformat(), self.method, self.path, self.ip_address, self.agent, self.agent_browser, self.agent_browser_version, self.agent_platform)


############################################################
# Core User Models
############################################################

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pre_html = db.Column(db.String, default="")
    role = db.Column(db.String, default="", unique=True)
    post_html = db.Column(db.String, default="")

    def __repr__(self):
        return "<Role: (role='%s')>" % (self.role,)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    snippet = db.Column(db.Text)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_notification_user", ondelete="CASCADE"), index=True)
    user = db.relationship("User", backref="notifications", foreign_keys="Notification.user_id")

    author_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_notification_author", ondelete="CASCADE"))
    author = db.relationship("User", foreign_keys="Notification.author_id")

    NOTIFICATION_CATEGORIES = (
        ("blog", "Blog Entries", "new blog entries on subscribed blogs", "detailed", "blog entry", "blog entries"),
        ("blogcomments", "Blog Comments", "new blog comments on subscribed entries", "detailed", "blog comment", "blog comments"),
        ("topic", "Topics", "new posts in followed topics", "listed", "topic", "topics"),
        ("pm", "Private Messages", "new private messages and replies", "detailed", "private message", "private messages"),
        ("mention", "Mentioned", "topic mentions", "listed", "mention", "mentions"),
        ("topic_reply", "Topic Replies", "replies to you in a topic", "detailed", "topic reply", "topic replies"),
        ("boop", "Boops", "all boops received", "summarized", "boop", "boops"),
        ("mod", "Moderation", "moderation related", "listed", "mod action", "mod actions"),
        ("status", "Status Updates", "all status update notifications", "listed", "status", "statuses"),
        ("new_member", "New Members", "new member announcements", "listed", "new member", "new members"),
        ("user_activity", "Followed User Activity", "new topics and statuses by followed members", "listed", "followed activity", "followed activities"),
        ("friend", "Friend Requests", "new friend requests and approvals", "listed", "friend", "friends"),
        # ("announcement", "Announcements"),
        # ("profile_comment","Profile Comments"),
        # ("rules_updated", "Rule Update"),
        # ("faqs", "FAQs Updated"),
        # ("streaming", "Streaming"),
        # ("other", "Other")
    )

    # TODO: message_frequency = db.Column(db.Integer)

    category = db.Column(db.String, default="")
    created = db.Column(db.DateTime)
    url = db.Column(db.String, default="")
    acknowledged = db.Column(db.Boolean, default=False, index=True)
    seen = db.Column(db.Boolean, default=False, index=True)
    emailed = db.Column(db.Boolean, default=False, index=True)
    priority = db.Column(db.Integer, default=0)

    def __repr__(self):
        return "<Notification: (user='%s', message='%s')>" % (self.user.display_name, self.message)

class IgnoringUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_ignoringuser_user", ondelete="CASCADE"))
    user = db.relationship("User", foreign_keys=user_id)
    ignoring_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_ignoringuser_ignoring", ondelete="CASCADE"))
    ignoring = db.relationship("User", foreign_keys=ignoring_id)
    __table_args__ = (db.UniqueConstraint('user_id', 'ignoring_id', name='unique_user_ignoring'),)
    created = db.Column(db.DateTime)

    distort_posts = db.Column(db.Boolean, default=True)
    block_sigs = db.Column(db.Boolean, default=True)
    block_pms = db.Column(db.Boolean, default=True)
    block_blogs = db.Column(db.Boolean, default=True)
    block_status = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return "<IgnoredUser: (user='%s', ignoring='%s')>" % (self.user.display_name, self.ignoring.display_name)

class FollowingUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_followinguser_user", ondelete="CASCADE"))
    user = db.relationship("User", foreign_keys="FollowingUser.user_id")
    following_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_followinguser_following", ondelete="CASCADE"))
    following = db.relationship("User", foreign_keys="FollowingUser.following_id")
    __table_args__ = (db.UniqueConstraint('user_id', 'following_id', name='unique_user_following'),)
    created = db.Column(db.DateTime)

    def __repr__(self):
        return "<FollowingUser: (user='%s', following='%s')>" % (self.user.display_name, self.following.display_name)

class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_friendship_user", ondelete="CASCADE"))
    user = db.relationship("User", foreign_keys="Friendship.user_id")
    friend_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_friendship_friend", ondelete="CASCADE"))
    friend = db.relationship("User", foreign_keys="Friendship.friend_id")
    __table_args__ = (db.UniqueConstraint('user_id', 'friend_id', name='unique_user_friend'),)
    created = db.Column(db.DateTime)

    pending = db.Column(db.Boolean, default=True)
    blocked = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return "<Friendship: (user='%s', friend='%s', pending='%s', blocked='%s')>" % (self.user.display_name, self.friend.display_name, self.pending, self.blocked)

user_role_table = db.Table('user_roles', db.metadata,
    db.Column('role_id', db.Integer, db.ForeignKey('role.id',
        name="fk_userrole_role", ondelete="CASCADE")),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id',
        name="fk_userrole_user", ondelete="CASCADE")))

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roles = db.relationship("Role",
                    secondary=user_role_table,
                    backref="users")

    data = db.Column(JSONB)
    time_online = db.Column(db.Integer, default=0)
    AVAILABLE_PROFILE_FIELDS = [
        "Discord",
        "DeviantArt",
        "Youtube",
        "Twitter",
        "Skype",
        "Tumblr",
        "Steam",
        "Nintendo Network",
        "PSN",
        "XBL",
        "Twitch"
    ]

    ignored_users = db.relationship("IgnoringUser",
            secondary="ignoring_user",
            primaryjoin="IgnoringUser.user_id == User.id",
            secondaryjoin="IgnoringUser.ignoring_id == User.id"
        )

    followed_users = db.relationship("FollowingUser",
            secondary="following_user",
            primaryjoin="FollowingUser.user_id == User.id",
            secondaryjoin="FollowingUser.following_id == User.id"
        )

    display_name = db.Column(db.String, unique=True)
    login_name = db.Column(db.String, unique=True)
    email_address = db.Column(db.String, unique=True)
    password_hash = db.Column(db.String, default="")
    joined = db.Column(db.DateTime, index=True)

    phrase_last_updated = db.Column(db.DateTime)
    smileys_last_updated = db.Column(db.DateTime)

    how_did_you_find_us = db.Column(db.Text, default="")
    is_allowed_during_construction = db.Column(db.Boolean, default=False)
    my_url = db.Column(db.String, unique=True)
    time_zone = db.Column(db.String, default="")
    theme_id = db.Column(db.Integer, db.ForeignKey('site_theme.id',
        name="fk_member_theme", ondelete="SET NULL"))
    theme = db.relationship("SiteTheme")

    banned = db.Column(db.Boolean, index=True, default=False)
    validated = db.Column(db.Boolean, default=False, index=True)
    over_thirteen = db.Column(db.Boolean, default=True)

    emails_muted = db.Column(db.Boolean, default=False)
    last_sent_notification_email = db.Column(db.DateTime, nullable=True)
    minimum_notifications_for_email = db.Column(db.Integer, default=5)
    minimum_time_between_emails = db.Column(db.Integer, default=360)

    title = db.Column(db.String, default="")
    minecraft = db.Column(db.String, default="")
    location = db.Column(db.String, default="")
    about_me = db.Column(db.Text, default="")
    anonymous_login = db.Column(db.Boolean, default=False)

    avatar_extension = db.Column(db.String, default="")
    avatar_full_x = db.Column(db.Integer, default=200)
    avatar_full_y = db.Column(db.Integer, default=200)
    avatar_60_x = db.Column(db.Integer, default=60)
    avatar_60_y = db.Column(db.Integer, default=60)
    avatar_40_x = db.Column(db.Integer, default=40)
    avatar_40_y = db.Column(db.Integer, default=40)
    avatar_timestamp = db.Column(db.String, default="")
    banner_image_custom = db.Column(db.String, default="")
    title_bar_background_custom = db.Column(db.String, default="")
    profile_background_custom = db.Column(db.String, default="")
    header_background_color = db.Column(db.String, default="")
    header_text_color = db.Column(db.String, default="")
    full_page_image = db.Column(db.Boolean, default=False)
    use_text_shadow = db.Column(db.Boolean, default=False)
    text_shadow_color = db.Column(db.String, default="")
    header_height = db.Column(db.Integer, default=460)
    no_images = db.Column(db.Boolean, default=False)

    password_forgot_token = db.Column(db.String, default="")
    password_forgot_token_date = db.Column(db.DateTime, nullable=True)

    posts_count = db.Column(db.Integer, default=0)
    topic_count = db.Column(db.Integer, default=0)
    status_count = db.Column(db.Integer, default=0)
    status_comment_count = db.Column(db.Integer, default=0)

    last_seen = db.Column(db.DateTime, nullable=True)
    legacy_password = db.Column(db.Boolean, nullable=True)
    ipb_salt = db.Column(db.String, nullable=True)
    ipb_hash = db.Column(db.String, nullable=True)
    hidden_last_seen = db.Column(db.DateTime, nullable=True, index=True)
    last_seen_at = db.Column(db.String, default="")
    last_at_url = db.Column(db.String, default="")

    is_admin = db.Column(db.Boolean, default=False)
    is_mod = db.Column(db.Boolean, default=False)

    display_name_history = db.Column(JSONB)
    notification_preferences = db.Column(JSONB)

    # Migration related
    old_mongo_hash = db.Column(db.String, nullable=True, index=True)

    def ignoring(self):
        return [u.ignoring for u in self.ignored_users]

    def get_custom_css(self):
        if current_user.no_images:
            return ""

        _template = _mylookup.get_template("profile.css")
        _rendered = _template.render(
                _banner_image=self.banner_image_custom,
                _header_height=self.header_height,
                _site_background_color=self.profile_background_custom,
                _section_image=self.title_bar_background_custom,
                _section_background_color=self.header_background_color,
                _section_text_color=self.header_text_color,
                _full_page_image=self.full_page_image,
                _use_text_shadow=self.use_text_shadow,
                _text_shadow_color=self.text_shadow_color
            )
        return _rendered

    def __repr__(self):
        return "%s" % (self.display_name)

    def get_text_id(self):
        return "%s" % (self.id, )

    def get_hash(self):
        return self.password_hash[-40:]

    def is_authenticated(self):
        return True # Will only ever return True.

    def rejected_friends(self):
        rejected = Friendship.query.filter_by(blocked=True) \
            .filter(db.or_(Friendship.user == self, Friendship.friend == self)).all()

        result = []
        for r in rejected:
            if r.user == self:
                result.append(r.friend)
            elif r.friend == self:
                result.append(r.user)
        return result

    def pending_friends(self):
        pending = Friendship.query.filter_by(blocked=False, pending=True) \
            .filter(db.or_(Friendship.user == self, Friendship.friend == self)).all()

        result = []
        for r in pending:
            if r.user == self:
                result.append(r.friend)
            elif r.friend == self:
                result.append(r.user)
        return result

    def friends(self):
        friends = Friendship.query.filter_by(blocked=False, pending=False) \
            .filter(db.or_(Friendship.user == self, Friendship.friend == self)).all()

        result = []
        for r in friends:
            if r.user == self:
                result.append(r.friend)
            elif r.friend == self:
                result.append(r.user)
        return result

    def set_password(self, password, rounds=12):
        self.legacy_password = None
        self.password_hash = bcrypt.generate_password_hash(password.strip().encode('utf-8'),rounds).encode('utf-8')

    def check_password(self, password):
        if self.legacy_password:
            if ipb_password_check(self.ipb_salt, self.ipb_hash, password):
                self.set_password(password)
                self.legacy_password = False
                self.ipb_salt = ""
                self.ipb_hash = ""
                return True
            else:
                return False
        else:
            return bcrypt.check_password_hash(self.password_hash.encode('utf-8'), password.strip().encode('utf-8'))

    def is_anonymous(self):
        return False # Will only ever return False. Anonymous = guest user. We don't support those.

    def is_active(self):
        if self.banned:
            return False
        if not self.validated:
            return False
        return True

    def get_roles(self):
        my_roles = []
        for role in self.roles:
            my_roles.append(role.pre_html+role.role+role.post_html)
        return my_roles

    def get_notification_count(self):
        return Notification.query.filter_by(seen=False, user=self).count()

    def get_dashboard_notifications(self):
        return Notification.query.filter_by(acknowledged=False, user=self).count()

    def get_recent_notifications(self, count=15):
        return Notification.query.filter_by(acknowledged=False, user=self).order_by(db.desc(Notification.created))[:10]

    def get_id(self):
        return self.login_name

    def followed_by(self):
        followed_me = FollowingUser.query.filter_by(following=self)
        users_following_me = [f.user for f in followed_me]
        return users_following_me

    def unread_private_messages(self):
        my_unread_messages = PrivateMessageUser.query.filter_by(author=self) \
            .join(PrivateMessage, PrivateMessageUser.pm_id == PrivateMessage.id) \
            .join(PrivateMessageReply, PrivateMessage.last_reply_id == PrivateMessageReply.id) \
            .filter(PrivateMessageUser.last_viewed.isnot(None)) \
            .filter(PrivateMessageReply.author != self) \
            .filter(PrivateMessageUser.last_viewed < PrivateMessageReply.created).count()
        return my_unread_messages

    def get_avatar_url(self, size=""):
        if current_user.no_images:
            return ""

        if size != "":
            size = "_"+size

        if not self.avatar_extension:
            return "/static/no_profile_avatar"+size+".png"
        else:
            if self.old_mongo_hash is not None:
                return "/static/avatars/"+str(self.avatar_timestamp)+str(self.old_mongo_hash)+size+self.avatar_extension
            else:
                return "/static/avatars/"+str(self.avatar_timestamp)+str(self.id)+size+self.avatar_extension

class Signature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_user_signature", ondelete="CASCADE"), index=True)
    owner = db.relationship("User", foreign_keys="Signature.owner_id")
    name = db.Column(db.String, default="")
    html = db.Column(db.Text)
    created = db.Column(db.DateTime, index=True)
    active = db.Column(db.Boolean, default=True, index=True)

############################################################
# Moderation Models
############################################################

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, default="")
    content_type = db.Column(db.String, default="")
    content_id = db.Column(db.Integer)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_report_author", ondelete="CASCADE"))
    author = db.relationship("User")

    report = db.Column(db.Text)

    STATUS_CHOICES = (
        ('ignored', 'Ignored'),
        ('open', 'Open'),
        ('feedback', 'Feedback Requested'),
        ('waiting', 'Waiting'),
        ('action taken', 'Action Taken')
    )

    status = db.Column(db.String, default="open")
    created = db.Column(db.DateTime)

    def __repr__(self):
        return "<Report: (content_type='%s', content_id='%s')>" % (self.content_type, self.content_id)

class ReportComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime)
    comment = db.Column(db.Text)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_reportcomment_author", ondelete="CASCADE"))
    author = db.relationship("User")
    report_id = db.Column(db.Integer, db.ForeignKey('report.id',
        name="fk_reportcomment_report", ondelete="CASCADE"))
    report = db.relationship("Report")

    def __repr__(self):
        return "<ReportComment: (created='%s', comment='%s')>" % (self.created, self.comment[0:30])

############################################################
# Attachment Models
############################################################

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String, default="")
    mimetype = db.Column(db.String, default="")
    extension = db.Column(db.String, default="")

    size_in_bytes = db.Column(db.Integer, default=0)
    created_date = db.Column(db.DateTime)
    do_not_convert = db.Column(db.Boolean, default=False)
    alt = db.Column(db.String, default="")

    old_mongo_hash = db.Column(db.String, nullable=True, index=True)

    x_size = db.Column(db.Integer, default=100)
    y_size = db.Column(db.Integer, default=100)

    file_hash = db.Column(db.String, default="")
    linked = db.Column(db.Boolean, default=False)
    origin_url =  db.Column(db.String, default="")
    origin_domain = db.Column(db.String, default="")
    caption = db.Column(db.String, default="")

    owner_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_attachment_owner", ondelete="SET NULL"))
    owner = db.relationship("User")

    character_id = db.Column(db.Integer, db.ForeignKey('character.id',
        name="fk_attachment_character", ondelete="SET NULL"), nullable=True)
    character = db.relationship("Character", foreign_keys="Attachment.character_id")
    character_gallery = db.Column(db.Boolean, default=False)
    character_gallery_weight = db.Column(db.Integer, default=0)
    character_avatar = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return "<Attachment: (path='%s')>" % (self.path,)

    def get_specific_size(self, width=200):
        network_path = os.path.join("/static/uploads", self.path)
        file_path = os.path.join(os.getcwd(), "woe/static/uploads", self.path)
        size_network_path = os.path.join("/static/uploads", self.path+".attachment_resized."+str(width)+"."+self.extension)
        size_file_path = os.path.join(os.getcwd(), "woe/static/uploads", self.path+".attachment_resized."+str(width)+"."+self.extension)

        if self.do_not_convert or width > self.x_size:
            return network_path

        if os.path.exists(size_file_path):
            return size_network_path
        else:
            def convert_image():
                try:
                    source_image = Image(filename=file_path)
                except:
                    self.do_not_convert = True
                    self.save()

                original_x = source_image.width
                original_y = source_image.height

                if original_x != width:
                    resize_measure = float(width)/float(original_x)
                    try:
                        source_image.resize(int(round(original_x*resize_measure)),int(round(original_y*resize_measure)))
                    except:
                        self.do_not_convert = True
                        self.save()

                try:
                    source_image.save(filename=size_file_path)
                except:
                    self.do_not_convert = True
                    self.save()

            thread = Thread(target=convert_image, args=())
            thread.start()
            return network_path

############################################################
# Roleplay Models
############################################################

class Character(db.Model):
    author_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_character_author", ondelete="CASCADE"))
    author = db.relationship("User")

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, default="")
    slug = db.Column(db.String, unique=True)

    age = db.Column(db.String, default="")
    species = db.Column(db.String, default="")
    appearance = db.Column(db.Text, default="")
    personality = db.Column(db.Text, default="")
    backstory = db.Column(db.Text, default="")
    other = db.Column(db.Text, default="")
    motto = db.Column(db.String, default="")
    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime, nullable=True)
    hidden = db.Column(db.Boolean, default=False)

    character_history = db.Column(JSONB)
    old_mongo_hash = db.Column(db.String, nullable=True, index=True)

    default_avatar_id = db.Column(db.Integer, db.ForeignKey('attachment.id',
        name="fk_character_default_avatar", ondelete="SET NULL"))
    default_avatar = db.relationship("Attachment", foreign_keys="Character.default_avatar_id")
    legacy_avatar_field = db.Column(db.String)

    default_gallery_image_id = db.Column(db.Integer, db.ForeignKey('attachment.id',
        name="fk_character_default_gallery", ondelete="SET NULL"))
    default_gallery_image = db.relationship("Attachment", foreign_keys="Character.default_gallery_image_id")
    legacy_gallery_field = db.Column(db.String)

    def get_avatar(self, size=200):
        if current_user.no_images:
            return ""

        all_avatars = Attachment.query.filter_by(
            character = self,
            character_avatar = True
        ).order_by("Attachment.character_gallery_weight").all()

        if self.default_avatar:
            return self.default_avatar.get_specific_size(size)
        elif len(all_avatars) > 0:
            return all_avatars[0].get_specific_size(size)
        elif self.legacy_avatar_field:
            return "/static/uploads/"+self.legacy_avatar_field
        else:
            return ""

    def get_portrait(self, size=250):
        if current_user.no_images:
            return ""

        all_portraits = Attachment.query.filter_by(
            character = self,
            character_avatar = False
        ).order_by("Attachment.character_gallery_weight").all()

        if self.default_gallery_image:
            return self.default_gallery_image.get_specific_size(size)
        elif len(all_portraits) > 0:
            return all_portraits[0].get_specific_size(size)
        elif self.legacy_gallery_field:
            return "/static/uploads/"+self.legacy_gallery_field
        else:
            return ""

    def __repr__(self):
        return "<Character: (name='%s')>" % (self.name,)

def get_character_slug(name):
    slug = slugify(name, max_length=100, word_boundary=True, save_order=True)
    if slug.strip() == "":
        slug="_"

    def try_slug(slug, count=0):
        new_slug = slug
        if count > 0:
            new_slug = slug+"-"+str(count)

        if len(Character.query.filter_by(slug=new_slug).all()) == 0:
            return new_slug
        else:
            return try_slug(slug, count+1)

    return try_slug(slug)

############################################################
# Forum Models
############################################################

class Label(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pre_html = db.Column(db.String, default="")
    label = db.Column(db.String, default="", index=True)
    post_html = db.Column(db.String, default="")
    modern = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return "%s" % (self.label,)

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    slug = db.Column(db.String, unique=True)
    weight = db.Column(db.Integer, default=0)

    def __repr__(self):
        return "<Section: (name='%s', weight='%s')>" % (self.name, self.weight)

allowed_user_table = db.Table('category_allowed_users', db.metadata,
    db.Column('category_id', db.Integer, db.ForeignKey('category.id',
        name="fk_allowedcategoryuser_category", ondelete="CASCADE")),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id',
        name="fk_allowedcategoryuser_user", ondelete="CASCADE")))

allowed_label_table = db.Table('category_allowed_labels', db.metadata,
    db.Column('category_id', db.Integer, db.ForeignKey('category.id',
        name="fk_allowedcategorylabel_category", ondelete="CASCADE")),
    db.Column('label_id', db.Integer, db.ForeignKey('label.id',
        name="fk_allowedcategorylabel_label", ondelete="CASCADE")))

category_watchers_table = db.Table('category_watchers', db.metadata,
    db.Column('category_id', db.Integer, db.ForeignKey('category.id',
        name="fk_categorywatchers_category", ondelete="CASCADE")),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id',
        name="fk_categorywatchers_user", ondelete="CASCADE")))

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    parent_id = db.Column(db.Integer, db.ForeignKey('category.id',
        name="fk_category_categoryparent", ondelete="SET NULL"))
    parent = db.relationship("Category", backref="children", remote_side=[id])

    section_id = db.Column(db.Integer, db.ForeignKey('section.id',
        name="fk_category_section", ondelete="SET NULL"))
    section = db.relationship("Section")

    watchers = db.relationship("User",
                    secondary=category_watchers_table)
    allowed_users = db.relationship("User",
                    secondary=allowed_user_table)
    allowed_labels = db.relationship("Label",
                    secondary=allowed_label_table)

    recent_post_id = db.Column(db.Integer, db.ForeignKey('post.id',
        name="fk_category_recentpost", ondelete="SET NULL"))
    recent_post = db.relationship("Post", foreign_keys="Category.recent_post_id")
    recent_topic_id = db.Column(db.Integer, db.ForeignKey('topic.id',
        name="fk_category_recenttopic", ondelete="SET NULL"))
    recent_topic = db.relationship("Topic", foreign_keys="Category.recent_topic_id")

    name = db.Column(db.String, default="")
    slug = db.Column(db.String, unique=True)

    weight = db.Column(db.Integer, default=0)
    restricted = db.Column(db.Boolean, default=False)

    topic_count = db.Column(db.Integer, default=0)
    post_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return "<Category: (name='%s', weight='%s')>" % (self.name, self.weight)

topic_watchers_table = db.Table('topic_watchers', db.metadata,
    db.Column('topic_id', db.Integer, db.ForeignKey('topic.id',
        name="fk_topicwatchers_topic", ondelete="CASCADE")),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id',
        name="fk_topicwatchers_user", ondelete="CASCADE")))

topic_mods_table = db.Table('topic_moderators', db.metadata,
    db.Column('topic_id', db.Integer, db.ForeignKey('topic.id',
        name="fk_topicmods_topic", ondelete="CASCADE")),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id',
        name="fk_topicmods_user", ondelete="CASCADE")))

topic_banned_table = db.Table('topic_banned_users', db.metadata,
    db.Column('topic_id', db.Integer, db.ForeignKey('topic.id',
        name="fk_topicbanned_topic", ondelete="CASCADE")),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id',
        name="fk_topicbanned_user", ondelete="CASCADE")))

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id',
        name="fk_topic_category", ondelete="CASCADE"), index=True)
    category = db.relationship("Category", foreign_keys="Topic.category_id")
    author_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_topic_author", ondelete="CASCADE"), index=True)
    author = db.relationship("User", foreign_keys="Topic.author_id")

    editor_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_topic_editor", ondelete="SET NULL"), nullable=True)
    editor = db.relationship("User", foreign_keys="Topic.editor_id")

    label_id = db.Column(db.Integer, db.ForeignKey('label.id',
        name="fk_topic_label", ondelete="SET NULL"), nullable=True)
    label = db.relationship("Label", foreign_keys="Topic.label_id")

    watchers = db.relationship("User",
                    secondary=topic_watchers_table)
    moderators = db.relationship("User",
                    secondary=topic_mods_table)
    banned = db.relationship("User",
                    secondary=topic_banned_table)
    recent_post_id = db.Column(db.Integer, db.ForeignKey('post.id',
        name="fk_topic_recentpost", ondelete="SET NULL"))
    recent_post = db.relationship("Post", foreign_keys="Topic.recent_post_id")
    last_seen_by = db.Column(JSONB)

    title = db.Column(db.String)
    slug = db.Column(db.String, unique=True)
    sticky = db.Column(db.Boolean, default=False)
    announcement = db.Column(db.Boolean, default=False)
    hidden = db.Column(db.Boolean, default=False, index=True)
    locked = db.Column(db.Boolean, default=False)
    created = db.Column(db.DateTime, index=True)
    post_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return "<Topic: (title='%s', created='%s')>" % (self.title, self.created)

    def is_topic_mod(self, user):
        if user in self.moderators or user.is_mod or user.is_admin:
            return 1
        else:
            return 0

def find_topic_slug(title):
    slug = slugify(title, max_length=100, word_boundary=True, save_order=True)
    if slug.strip() == "":
        slug="_"

    def try_slug(slug, count=0):
        new_slug = slug
        if count > 0:
            new_slug = slug+"-"+str(count)

        if len(Topic.query.filter_by(slug=new_slug).all()) == 0:
            return new_slug
        else:
            return try_slug(slug, count+1)

    return try_slug(slug)

post_boop_table = db.Table('post_boops_from_users', db.metadata,
    db.Column('post_id', db.Integer, db.ForeignKey('post.id',
        name="fk_postboop_post", ondelete="CASCADE"), index=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id',
        name="fk_postboop_user", ondelete="CASCADE"), index=True))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id',
        name="fk_post_topic", ondelete="CASCADE"), index=True)
    topic = db.relationship("Topic", foreign_keys="Post.topic_id", cascade="delete")

    author_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_post_author", ondelete="CASCADE"), index=True)
    author = db.relationship("User", foreign_keys="Post.author_id")

    editor_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_post_editor", ondelete="SET NULL"), nullable=True)
    editor = db.relationship("User", foreign_keys="Post.editor_id")

    boops = db.relationship("User",
                    secondary=post_boop_table,
                    backref="booped_posts")

    character_id = db.Column(db.Integer, db.ForeignKey('character.id',
        name="fk_post_character", ondelete="SET NULL"), nullable=True)
    character = db.relationship("Character", foreign_keys="Post.character_id", backref="posts")

    avatar_id = db.Column(db.Integer, db.ForeignKey('attachment.id',
        name="fk_post_avatar", ondelete="SET NULL"), nullable=True)
    avatar = db.relationship("Attachment", foreign_keys="Post.avatar_id")

    html = db.Column(db.Text)
    modified = db.Column(db.DateTime, nullable=True)
    created = db.Column(db.DateTime, index=True)
    hidden = db.Column(db.Boolean, default=False, index=True)
    post_history = db.Column(JSONB)
    t_title = db.Column(db.String, default="")

    old_mongo_hash = db.Column(db.String, nullable=True, index=True)
    data = db.Column(JSONB)

    def __repr__(self):
        return "<Post: (author='%s', created='%s', topic='%s')>" % (self.author.display_name, self.created, self.topic.title[0:50])

blogcomment_boop_table = db.Table('blog_comment_boops', db.metadata,
    db.Column('blogcomment_id', db.Integer, db.ForeignKey('blog_comment.id',
        name="fk_boop_blogcomment", ondelete="CASCADE")),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id',
        name="fk_boop_blogcomment_user", ondelete="CASCADE")))

class BlogComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blog_entry_id = db.Column(db.Integer, db.ForeignKey('blog_entry.id',
        name="fk_blogcomment_blogentry", ondelete="CASCADE"), index=True)
    blog_entry = db.relationship("BlogEntry", foreign_keys="BlogComment.blog_entry_id", cascade="delete", backref="comments")
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id',
        name="fk_blogcomment_blog", ondelete="CASCADE"), index=True)
    blog = db.relationship("Blog", foreign_keys="BlogComment.blog_id", cascade="delete")

    author_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_blogcomment_author", ondelete="CASCADE"))
    author = db.relationship("User", foreign_keys="BlogComment.author_id")

    editor_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_blogcomment_editor", ondelete="SET NULL"), nullable=True)
    editor = db.relationship("User", foreign_keys="BlogComment.editor_id")

    boops = db.relationship("User",
                    secondary=blogcomment_boop_table)

    html = db.Column(db.Text)
    modified = db.Column(db.DateTime, nullable=True)
    created = db.Column(db.DateTime, index=True)
    hidden = db.Column(db.Boolean, default=False, index=True)
    comment_history = db.Column(JSONB)
    b_e_title = db.Column(db.String, default="")
    data = db.Column(JSONB)

blog_editor_table = db.Table('blog_editors', db.metadata,
    db.Column('blog_id', db.Integer, db.ForeignKey('blog.id',
        name="fk_editor_blog", ondelete="CASCADE")),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id',
        name="fk_editor_user", ondelete="CASCADE")))

blog_subscriber_table = db.Table('blog_subscribers', db.metadata,
    db.Column('blog_id', db.Integer, db.ForeignKey('blog.id',
        name="fk_subscriber_blog", ondelete="CASCADE")),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id',
        name="fk_subscriber_user", ondelete="CASCADE")))

blogentry_boop_table = db.Table('blog_entry_boops', db.metadata,
    db.Column('blogentry_id', db.Integer, db.ForeignKey('blog_entry.id',
        name="fk_boop_blogentry", ondelete="CASCADE")),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id',
        name="fk_boop_blogentry_user", ondelete="CASCADE")))

blogentry_subscriber_table = db.Table('blog_entry_subscribers', db.metadata,
    db.Column('blogentry_id', db.Integer, db.ForeignKey('blog_entry.id',
        name="fk_subscriber_blog_entry", ondelete="CASCADE")),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id',
        name="fk_subscriber_user_blog_entry", ondelete="CASCADE")))

class BlogEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, default="")
    slug = db.Column(db.String, default="", index=True)
    blog_id = db.Column(db.Integer, db.ForeignKey('blog.id',
        name="fk_blogentry_blog", ondelete="CASCADE"), index=True)
    blog = db.relationship("Blog", foreign_keys="BlogEntry.blog_id", cascade="delete")
    __table_args__ = (db.UniqueConstraint('blog_id', 'slug', name='unique_blog_entry_slug'),)

    author_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_blogentry_author", ondelete="CASCADE"), index=True)
    author = db.relationship("User", foreign_keys="BlogEntry.author_id")

    editor_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_blogentry_editor", ondelete="SET NULL"), nullable=True)
    editor = db.relationship("User", foreign_keys="BlogEntry.editor_id")

    boops = db.relationship("User",
                    secondary=blogentry_boop_table)

    subscribers = db.relationship("User",
                    secondary=blogentry_subscriber_table)

    character_id = db.Column(db.Integer, db.ForeignKey('character.id',
        name="fk_blogentry_character", ondelete="SET NULL"), nullable=True)
    character = db.relationship("Character", foreign_keys="BlogEntry.character_id", backref="blog_entries")

    avatar_id = db.Column(db.Integer, db.ForeignKey('attachment.id',
        name="fk_blogentry_avatar", ondelete="SET NULL"), nullable=True)
    avatar = db.relationship("Attachment", foreign_keys="BlogEntry.avatar_id")

    draft = db.Column(db.Boolean, default=True, index=True)
    html = db.Column(db.Text)
    modified = db.Column(db.DateTime, nullable=True)
    created = db.Column(db.DateTime, index=True)
    published = db.Column(db.DateTime, index=True)
    hidden = db.Column(db.Boolean, default=False, index=True)
    entry_history = db.Column(JSONB)
    b_title = db.Column(db.String, default="")
    data = db.Column(JSONB)
    featured = db.Column(db.Boolean, default=False)

    def comment_count(self):
        return BlogComment.query.filter_by(hidden=False, blog_entry=self).count()

class Blog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    slug = db.Column(db.String, unique=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id',
        name="fk_blog_owner", ondelete="CASCADE"))
    author = db.relationship("User", foreign_keys="Blog.author_id")
    description = db.Column(db.Text)

    editors = db.relationship("User",
                    secondary=blog_editor_table)

    entry_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)

    recent_entry_id = db.Column(db.Integer, db.ForeignKey('blog_entry.id',
    name="fk_blog_recententry", ondelete="SET NULL"))
    recent_entry = db.relationship("BlogEntry", foreign_keys="Blog.recent_entry_id")

    recent_comment_id = db.Column(db.Integer, db.ForeignKey('blog_comment.id',
    name="fk_blog_recentcomment", ondelete="SET NULL"))
    recent_comment = db.relationship("BlogComment", foreign_keys="Blog.recent_comment_id")

    subscribers = db.relationship("User",
                    secondary=blog_subscriber_table)

    PRIVACY_LEVELS = (
        ("all", "Everyone"),
        ("members", "Only Members"),
        ("friends", "Only Friends"),
        ("editors", "Only Editors"),
        ("you", "Only You")
    )

    privacy_setting = db.Column(db.String, default="members", index=True)
    disabled = db.Column(db.Boolean, index=True)

def find_blog_slug(title):
    slug = slugify(title, max_length=100, word_boundary=True, save_order=True)
    if slug.strip() == "":
        slug="_"

    def try_slug(slug, count=0):
        new_slug = slug
        if count > 0:
            new_slug = slug+"-"+str(count)

        if len(Blog.query.filter_by(slug=new_slug).all()) == 0:
            return new_slug
        else:
            return try_slug(slug, count+1)

    return try_slug(slug)

def find_blog_entry_slug(title, blog):
    slug = slugify(title, max_length=100, word_boundary=True, save_order=True)
    if slug.strip() == "":
        slug="_"

    def try_slug(slug, blog, count=0):
        new_slug = slug
        if count > 0:
            new_slug = slug+"-"+str(count)

        if len(BlogEntry.query.filter_by(slug=new_slug, blog=blog).all()) == 0:
            return new_slug
        else:
            return try_slug(slug, blog, count+1)

    return try_slug(slug, blog)
