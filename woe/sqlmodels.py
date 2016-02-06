from woe import sqla as db
from sqlalchemy.dialects.postgresql import JSONB
# TODO - Tie up relations
# TODO - add author, created, and mod flags to public content models

############################################################
# Private Message Models
############################################################

class PrivateMessageUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # related - user
    # related - private message

    ignoring = db.Column(db.Boolean)
    exited = db.Column(db.Boolean)
    blocked = db.Column(db.Boolean)
    viewed = db.Column(db.Integer)
    last_viewed = db.Column(db.DateTime)

    def __repr__(self):
        return "<PrivateMessageUser: (user='%s', pm='%s')>" % (self.user.display_name, self.pm.title)

class PrivateMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    count = db.Column(db.Integer)
    # related - user

    created = db.Column(db.Integer)
    old_mongo_hash = db.Column(db.String, nullable=True)

    def __repr__(self):
        return "<PrivateMessage: (title='%s')>" % (self.title, )

class PrivateMessageReply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # related - user
    # related - pm

    message = db.Column(db.Text)
    old_mongo_hash = db.Column(db.String, nullable=True)

    created = db.Column(db.DateTime)
    modified = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return "<PrivateMessageReply: (created='%s', user='%s', pm='%s')>" % (self.created, self.user.display_name, self.pm.title)

############################################################
# Status Update Models
############################################################

class StatusUpdateUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # related - user
    # related - status update

    ignoring = db.Column(db.Boolean)
    blocked = db.Column(db.Boolean)
    viewed = db.Column(db.Integer)
    last_viewed = db.Column(db.DateTime)

    def __repr__(self):
        return "<StatusUpdateUser: (user='%s', status='%s')>" % (self.user.display_name, self.status.message[0:50])

class StatusComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    # related - status update
    # related - user

    def __repr__(self):
        return "<StatusComment: (created='%s', user='%s', status='%s')>" % (self.created, self.user.display_name, self.status.message[0:50])

class StatusUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    # related - user

    last_replied = db.Column(db.DateTime)
    last_viewed = db.Column(db.DateTime)
    replies = db.Column(db.Integer)

    old_mongo_hash = db.Column(db.String, nullable=True)

    def __repr__(self):
        return "<StatusUpdate: (created='%s', user='%s', message='%s')>" % (self.created, self.user.display_name, self.message[0:50])

############################################################
# Core Site Models
############################################################

class SiteTheme(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    css = db.Column(db.Text)
    name = db.Column(db.String, unique=True)
    weight = db.Column(db.Integer)
    created = db.Column(db.DateTime)
    # related - user

    def __repr__(self):
        return "<SiteTheme: (name='%s')>" % (self.name,)

############################################################
# Security Models
############################################################

class IPAddress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.Text)
    last_seen = db.Column(db.DateTime)
    # related - user

    def __repr__(self):
        return "<IPAddress: (ip_address='%s', user=)>" % (self.ip_address,)

class Fingerprint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    json = db.Column(JSONB)
    factors = db.Column(db.Integer)
    last_seen = db.Column(db.DateTime)
    # related - user

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
    method = db.Column(db.String)
    path = db.Column(db.String)
    ip_address = db.Column(db.String)
    agent_platform = db.Column(db.String)
    agent_browser = db.Column(db.String)
    agent_browser_version = db.Column(db.String)
    agent = db.Column(db.String)
    time = db.Column(db.DateTime)
    error = db.Column(db.Boolean)
    error_name = db.Column(db.String)
    error_code = db.Column(db.String)
    error_description = db.Column(db.Text)

    def __repr__(self):
        return "%s %s %s :: %s %s %s %s" % (self.time.isoformat(), self.method, self.ip_address, self.agent, self.agent_browser, self.agent_browser_version, self.agent_platform)


############################################################
# Core User Models
############################################################

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pre_html = db.Column(db.String)
    role = db.Column(db.String)
    post_html = db.Column(db.String)
    # related - user

    def __repr__(self):
        return "<Role: (role='%s')>" % (self.role,)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    # related - user
    # related - user (originating)

    NOTIFICATION_CATEGORIES = (
        ("topic", "Topics"),
        ("pm", "Private Messages"),
        ("mention", "Mentioned"),
        ("topic_reply", "Topic Replies"),
        ("boop", "Boops"),
        ("mod", "Moderation"),
        ("status", "Status Updates"),
        ("new_member", "New Members"),
        ("announcement", "Announcements"),
        ("profile_comment","Profile Comments"),
        ("rules_updated", "Rule Update"),
        ("faqs", "FAQs Updated"),
        ("user_activity", "Followed User Activity"),
        ("streaming", "Streaming"),
        ("other", "Other")
    )

    category = db.Column(db.String)
    created = db.Column(db.DateTime)
    url = db.Column(db.DateTime)
    acknowledged = db.Column(db.Boolean)
    seen = db.Column(db.Boolean)
    emailed = db.Column(db.Boolean)
    priority = db.Column(db.Integer)

    def __repr__(self):
        return "<Notification: (user='%s', message='%s')>" % (self.user.display_name, self.message)

class IgnoringUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # related - user (ignoring other user)
    # related - user (ignored by other user)
    # ^ unique together
    created = db.Column(db.DateTime)

    distort_posts = db.Column(db.Boolean)
    block_sigs = db.Column(db.Boolean)
    block_pms = db.Column(db.Boolean)
    block_blogs = db.Column(db.Boolean)
    block_status = db.Column(db.Boolean)

    def __repr__(self):
        return "<IgnoredUser: (user='%s', ignoring='%s')>" % (self.user.display_name, self.ignored.display_name)

class FollowingUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # related - user (following other user)
    # related - user (followed by other user)
    # ^ unique together
    created = db.Column(db.DateTime)

    def __repr__(self):
        return "<FollowingUser: (user='%s', following='%s')>" % (self.user.display_name, self.following.display_name)

class Friendship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # related - user (ignoring other user)
    # related - user (ignored by other user)
    # ^ unique together
    created = db.Column(db.DateTime)

    pending = db.Column(db.Boolean)
    blocked = db.Column(db.Boolean)

    def __repr__(self):
        return "<Friendship: (user='%s', friend='%s', pending='%s', blocked='%s')>" % (self.user.display_name, self.friend.display_name, self.pending, self.blocked)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # related - roles

    data = db.Column(JSONB)

    display_name = db.Column(db.String)
    how_did_you_find_us = db.Column(db.Text)
    is_allowed_during_construction = db.Column(db.Boolean)
    my_url = db.Column(db.String)
    time_zone = db.Column(db.String)

    banned = db.Column(db.Boolean)
    validated = db.Column(db.Boolean)
    over_thirteen = db.Column(db.Boolean)

    emails_muted = db.Column(db.Boolean)
    last_sent_notification_email = db.Column(db.DateTime, nullable=True)

    title = db.Column(db.String)
    minecraft = db.Column(db.String)
    location = db.Column(db.String)
    about_me = db.Column(db.Text)
    anonymous_login = db.Column(db.Boolean)

    avatar_extension = db.Column(db.String)
    avatar_full_x = db.Column(db.Integer)
    avatar_full_y = db.Column(db.Integer)
    avatar_60_x = db.Column(db.Integer)
    avatar_60_y = db.Column(db.Integer)
    avatar_40_x = db.Column(db.Integer)
    avatar_40_y = db.Column(db.Integer)
    avatar_timestamp = db.Column(db.String)

    password_forgot_token = db.Column(db.String)
    password_forgot_token_date = db.Column(db.DateTime, nullable=True)

    posts_count = db.Column(db.Integer)
    topic_count = db.Column(db.Integer)
    status_count = db.Column(db.Integer)
    status_comment_count = db.Column(db.Integer)

    last_seen = db.Column(db.DateTime, nullable=True)
    hidden_last_seen = db.Column(db.DateTime, nullable=True)
    last_at = db.Column(db.String)
    last_at_url = db.Column(db.String)

    is_admin = db.Column(db.Boolean)
    is_mod = db.Column(db.Boolean)

    display_name_history = db.Column(JSONB)

    # Migration related
    old_mongo_hash = db.Column(db.String, nullable=True)

    def __repr__(self):
        return "<IgnoredUser: (name='%s')>" % (self.display_name)

############################################################
# Roleplay Models
############################################################

class Character(db.Model):
    # related - user

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    slug = db.Column(db.String, unique=True)

    age = db.Column(db.String)
    species = db.Column(db.String)
    appearance = db.Column(db.Text)
    personality = db.Column(db.Text)
    backstory = db.Column(db.Text)
    other = db.Column(db.Text)
    motto = db.Column(db.String)
    modified = db.Column(db.DateTime, nullable=True)

    character_history = db.Column(JSONB)
    old_mongo_hash = db.Column(db.String, nullable=True)

    def __repr__(self):
        return "<Character: (name='%s')>" % (self.name,)

############################################################
# Moderation Models
############################################################

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String)
    content_type = db.Column(db.String)
    content_id = db.Column(db.Integer)
    # related - user

    report = db.Column(db.Text)

    STATUS_CHOICES = (
        ('ignored', 'Ignored'),
        ('open', 'Open'),
        ('feedback', 'Feedback Requested'),
        ('waiting', 'Waiting'),
        ('action taken', 'Action Taken')
    )

    status = db.Column(db.String)
    created = db.Column(db.DateTime)

    def __repr__(self):
        return "<Report: (content_type='%s', content_id='%s')>" % (self.content_type, self.content_id)

class ReportComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime)
    comment = db.Column(db.Text)
    # related - user
    # related - report

    def __repr__(self):
        return "<ReportComment: (created='%s', comment='%s')>" % (self.created, self.comment[0:30])

############################################################
# Attachment Models
############################################################

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String)
    mimetype = db.Column(db.String)
    extension = db.Column(db.String)

    size_in_bytes = db.Column(db.Integer)
    created_date = db.Column(db.DateTime)
    do_not_convert = db.Column(db.Boolean)
    alt = db.Column(db.String)

    old_mongo_hash = db.Column(db.String, nullable=True)

    x_size = db.Column(db.Integer)
    y_size = db.Column(db.Integer)

    file_hash = db.Column(db.String)
    linked = db.Column(db.Boolean)
    origin_url =  db.Column(db.String)
    origin_domain = db.Column(db.String)
    caption = db.Column(db.String)

    # related - user
    # related - character
    character_gallery = db.Column(db.Boolean)
    character_gallery_weight = db.Column(db.Integer)
    character_avatar = db.Column(db.Boolean)

    def __repr__(self):
        return "<Attachment: (path='%s')>" % (self.path,)

############################################################
# Forum Models
############################################################

class Label(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pre_html = db.Column(db.String)
    label = db.Column(db.String)
    post_html = db.Column(db.String)
    # related - user

    def __repr__(self):
        return "<Label: (label='%s')>" % (self.label,)

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    slug = db.Column(db.String, unique=True)
    weight = db.Column(db.Integer)

    def __repr__(self):
        return "<Section: (name='%s', weight='%s')>" % (self.name, self.weight)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # related - other category (optional)
    # related - section
    # association - allowed users
    # association - allowed labels
    # recent items

    name = db.Column(db.String)
    slug = db.Column(db.String, unique=True)

    weight = db.Column(db.Integer)
    restricted = db.Column(db.Boolean)

    topic_count = db.Column(db.Integer)
    post_count = db.Column(db.Integer)
    view_count = db.Column(db.Integer)

    def __repr__(self):
        return "<Category: (name='%s', weight='%s')>" % (self.name, self.weight)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # related - category
    # related - user
    # related - user
    # association - watchers
    # association - moderators
    # association - banned
    # recent items

    title = db.Column(db.String)
    slug = db.Column(db.String, unique=True)
    sticky = db.Column(db.Boolean)
    announcement = db.Column(db.Boolean)

    def __repr__(self):
        return "<Topic: (title='%s', created='%s')>" % (self.title, self.created)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # related - topic
    # related - author
    # related - editor
    # association - boops
    # related - custom avatar
    # related - character

    html = db.Column(db.Text)
    modified = db.Column(db.DateTime, nullable=True)

    old_mongo_hash = db.Column(db.String, nullable=True)
    data = db.Column(JSONB)

    def __repr__(self):
        return "<Post: (author='%s', created='%s', topic='%s')>" % (self.author.display_name, self.created, self.topic.title[0:50])
