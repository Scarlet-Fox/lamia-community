import mongoengine as db

import re
import django
django.setup()
import scarletsweb.models as psql
from django.contrib.auth.models import User as SQLUser

db.connect("woe_main")
class Role(db.DynamicDocument):
    pre_html = db.StringField(required=True)
    role = db.StringField(required=True)
    post_html = db.StringField(required=True)

    def __unicode__(self):
        return unicode(self.role)

class UserActivity(db.DynamicEmbeddedDocument):
    content = db.GenericReferenceField()
    category = db.StringField(required=True)
    created = db.DateTimeField(required=True)
    data = db.DictField()

class DisplayNameHistory(db.DynamicEmbeddedDocument):
    name = db.StringField(required=True)
    date = db.DateTimeField(required=True)

class ProfileField(db.DynamicEmbeddedDocument):
    field = db.StringField(required=True)
    value = db.StringField(required=True)

class ModNote(db.DynamicEmbeddedDocument):
    date = db.DateTimeField(required=True)
    note = db.StringField(required=True)
    reference = db.GenericReferenceField()
    INCIDENT_LEVELS = (
        ("Other", "???"),
        ("Wat", "Something Weird"),
        ("Minor", "Just A Heads Up"),
        ("Major", "Will Need a Talking To"),
        ("Extreme", "Worthy of Being Banned")
    )
    incident_level = db.StringField(choices=INCIDENT_LEVELS, required=True)

class User(db.DynamicDocument):
    data = db.DictField(default={})
    login_name = db.StringField(required=True, unique=True)
    display_name = db.StringField(required=True, unique=True)
    password_hash = db.StringField()
    email_address = db.EmailField(required=True)
    how_did_you_find_us = db.StringField(default="")
    emails_muted = db.BooleanField(default=False)
    is_allowed_during_construction = db.BooleanField(default=False)
    roles = db.ListField(db.ReferenceField(Role, reverse_delete_rule=db.PULL))

    # Forgot password stuff
    password_forgot_token = db.StringField()
    password_forgot_token_date = db.DateTimeField()

    # Customizable display values

    title = db.StringField(default="")
    location = db.StringField(default="")
    about_me = db.StringField(default="")
    avatar_extension = db.StringField()

    # User group names!
    group_pre_html = db.StringField(default="")
    group_name = db.StringField(default="")
    group_post_html = db.StringField(default="")

    # avatar_sizes
    avatar_full_x = db.IntField()
    avatar_full_y = db.IntField()
    avatar_60_x = db.IntField()
    avatar_60_y = db.IntField()
    avatar_40_x = db.IntField()
    avatar_40_y = db.IntField()
    avatar_timestamp = db.StringField(default="")

    information_fields = db.ListField(db.EmbeddedDocumentField(ProfileField))
    social_fields = db.ListField(db.EmbeddedDocumentField(ProfileField))
    time_zone = db.StringField(default='US/Pacific')

    # Restoring account
    password_token = db.StringField()
    password_token_age = db.DateTimeField()

    # Background details
    topic_pagination = db.IntField(default=20)
    post_pagination = db.IntField(default=20)

    last_sent_notification_email = db.DateTimeField()
    auto_acknowledge_notifications_after = db.IntField()
    last_looked_at_notifications = db.DateTimeField()

    signatures = db.ListField(db.StringField())
    birth_d = db.IntField()
    birth_m = db.IntField()
    birth_y = db.IntField()
    hide_age = db.BooleanField(default=True)
    hide_birthday = db.BooleanField(default=True)
    hide_login = db.BooleanField(default=False)
    banned = db.BooleanField(default=False)
    validated = db.BooleanField(default=False)
    over_thirteen = db.BooleanField(default=False)

    warning_points = db.IntField(default=0)

    display_name_history = db.ListField(db.EmbeddedDocumentField(DisplayNameHistory))
    mod_notes = db.ListField(db.EmbeddedDocumentField("ModNote"))

    ALLOWED_INFO_FIELDS = (
        'Gender',
        'Favorite color',
    )

    ALLOWED_SOCIAL_FIELDS = (
        'Website',
        'DeviantArt'
        'Skype',
        'Steam',
        'Tumblr'
    )

    # Blocks
    ignored_users = db.ListField(db.ReferenceField("User", reverse_delete_rule=db.PULL)) # Topics, Blogs, Statuses, PMs
    ignored_user_signatures = db.ListField(db.ReferenceField("User", reverse_delete_rule=db.PULL))

    remain_anonymous = db.BooleanField(default=False)

    # NOTE MOD NOTES ARE AUTO SENT VIA BOTH
    notification_preferences = db.DictField()

    # Friends and social stuff
    followed_by = db.ListField(db.ReferenceField("User"))
    pending_friends = db.ListField(db.ReferenceField("User"))
    rejected_friends = db.ListField(db.ReferenceField("User"))
    friends = db.ListField(db.ReferenceField("User"))
    profile_feed = db.ListField(db.EmbeddedDocumentField(UserActivity))

    # Moderation options
    disable_posts = db.BooleanField(default=False)
    disable_status = db.BooleanField(default=False)
    disable_status_participation = db.BooleanField(default=False)
    disable_pm = db.BooleanField(default=False)
    disable_topics = db.BooleanField(default=False)
    hellban = db.BooleanField(default=False)
    ban_date = db.DateTimeField()

    # Statistics
    joined = db.DateTimeField(required=True)
    posts_count = db.IntField(default=0)
    topic_count = db.IntField(default=0)
    status_count = db.IntField(default=0)
    status_comment_count = db.IntField(default=0)
    last_seen = db.DateTimeField()
    hidden_last_seen = db.DateTimeField()
    last_at = db.StringField(default="Watching forum index.")
    last_at_url = db.StringField(default="/")
    smile_usage = db.DictField()
    post_frequency = db.DictField()

    # Migration related
    old_member_id = db.IntField(default=0)
    legacy_password = db.BooleanField(default=False)
    ipb_salt = db.StringField()
    ipb_hash = db.StringField()

    # Permissions
    is_admin = db.BooleanField(default=False)
    is_mod = db.BooleanField(default=False)

    meta = {
        'indexes': [
            'old_member_id',
            'display_name',
            'login_name',
            'email_address',
            'password_forgot_token',
            'banned'
        ]
    }

    def __unicode__(self):
        return self.login_name

    def get_hash(self):
        return self.password_hash[-40:]

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

    def get_id(self):
        return self.login_name

    def get_notification_count(self):
        return Notification.objects(user=self, seen=False).count()

    def get_dashboard_notifications(self):
        return Notification.objects(user=self, acknowledged=False).count()

    def get_recent_notifications(self, count=15):
        notifications = Notification.objects(user=self, acknowledged=False)[:15]
        content_already_in = {}
        return notifications

    def is_authenticated(self):
        return True # Will only ever return True.

    def is_anonymous(self):
        return False # Will only ever return False. Anonymous = guest user. We don't support those.

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
                self.save()
                return True
            else:
                return False
        else:
            return bcrypt.check_password_hash(self.password_hash.encode('utf-8'), password.strip().encode('utf-8'))

    def get_avatar_url(self, size=""):
        if size != "":
            size = "_"+size

        if not self.avatar_extension:
            return "/static/no_profile_avatar"+size+".png"
        else:
            return "/static/avatars/"+str(self.avatar_timestamp)+str(self.pk)+size+self.avatar_extension

class Fingerprint(db.DynamicDocument):
    user = db.ReferenceField("User", required=True, reverse_delete_rule=db.CASCADE)
    user_name = db.StringField(required=True)
    last_seen = db.DateTimeField(required=True)
    fingerprint = db.DictField(required=True)
    fingerprint_factors = db.IntField(required=True, default=0)
    fingerprint_hash = db.StringField(required=True)

    def compute_similarity_score(self, stranger):
        score = 0.0
        attributes = {}

        for key in self.fingerprint.keys():
            attributes[key] = 1

        for key in stranger.fingerprint.keys():
            attributes[key] = 1

        max_score = float(len(attributes.keys()))
        for attribute in attributes.keys():
            if self.fingerprint.get(attribute, None) == stranger.fingerprint.get(attribute, None):
                score += 1

        return score/max_score

    meta = {
        'ordering': ['-last_seen'],
        'indexes': [
            "fignerprint_hash",
            "user_name",
            "last_seen"
            "-last_seen"
        ]
    }

class IPAddress(db.DynamicDocument):
    user = db.ReferenceField("User", required=True, reverse_delete_rule=db.CASCADE)
    user_name = db.StringField(required=True)
    ip_address = db.StringField(required=True)
    last_seen = db.DateTimeField()

    meta = {
        'ordering': ['-last_seen'],
        'indexes': [
            'last_seen',
            '-last_seen',
            'ip_address',
            'user',
            'user_name'
        ]
    }

class Ban(db.DynamicDocument):
    user = db.ReferenceField("User", required=True, reverse_delete_rule=db.CASCADE)

class PrivateMessageParticipant(db.DynamicEmbeddedDocument):
    user = db.ReferenceField("User", required=True)
    left_pm = db.BooleanField(default=False)
    blocked = db.BooleanField(default=False)
    do_not_notify = db.BooleanField(default=False)
    last_read = db.DateTimeField()

class PrivateMessageTopic(db.DynamicDocument):
    title = db.StringField(required=True)
    creator = db.ReferenceField("User", required=True)
    creator_name = db.StringField(required=True)
    last_reply_name = db.StringField()

    created = db.DateTimeField(required=True)
    last_reply_by = db.ReferenceField("User")
    last_reply_time = db.DateTimeField()

    message_count = db.IntField(default=0)
    participating_users = db.ListField(db.ReferenceField("User"))
    blocked_users = db.ListField(db.ReferenceField("User"))
    users_left_pm = db.ListField(db.ReferenceField("User"))
    participants = db.ListField(db.EmbeddedDocumentField(PrivateMessageParticipant))
    participant_count = db.IntField(default=0)
    last_seen_by = db.DictField() # User : last_seen_utc

    labels = db.ListField(db.StringField())
    old_ipb_id = db.IntField()

    meta = {
        'ordering': ['-last_reply_time'],
        'indexes': [
            'old_ipb_id',
            '-last_reply_time',
            {
                'fields': ['$title',],
                'default_language': 'english'
            },
            'participating_users',
            'blocked_users',
            'users_left_pm'
        ]
    }

class PrivateMessage(db.DynamicDocument):
    message = db.StringField(required=True)
    author = db.ReferenceField("User", required=True, reverse_delete_rule=db.CASCADE)
    author_name = db.StringField(required=True)
    topic = db.ReferenceField("PrivateMessageTopic", reverse_delete_rule=db.CASCADE)
    topic_name = db.StringField(required=True)
    topic_creator_name = db.StringField(required=True)
    created = db.DateTimeField(required=True)
    modified = db.DateTimeField()

    meta = {
        'ordering': ['created'],
        'indexes': [
            'topic',
            'created',
            {
                'fields': ['$message',],
                'default_language': 'english'
            }
        ]
    }

class Notification(db.DynamicDocument):
    user = db.ReferenceField("User", required=True, reverse_delete_rule=db.CASCADE)
    user_name = db.StringField(required=True)
    text = db.StringField(required=True)
    description = db.StringField()
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
    category = db.StringField(choices=NOTIFICATION_CATEGORIES, required=True)
    created = db.DateTimeField(required=True)
    url = db.StringField(required=True)
    content = db.GenericReferenceField()
    author = db.ReferenceField("User", required=True, reverse_delete_rule=db.CASCADE)
    author_name = db.StringField(required=True)
    acknowledged = db.BooleanField(default=False)
    seen = db.BooleanField(default=False)
    emailed = db.BooleanField(default=False)
    priority = db.IntField(default=0)

    meta = {
        'ordering': ['-created'],
        'indexes': [
            '-created',
            'user',
            'author',
            'acknowledged',
            'priority',
            'category'
        ]
    }

class ReportComment(db.DynamicDocument):
    author = db.ReferenceField("User", required=True, reverse_delete_rule=db.CASCADE)
    created = db.DateTimeField(required=True)
    text = db.StringField(required=True)

class Report(db.DynamicDocument):
    content_type = db.StringField(required=True)
    content_pk = db.StringField(required=True)
    url = db.StringField(required=True)
    report = db.StringField(required=True)
    content_reported = db.StringField(required=True)
    initiated_by = db.ReferenceField("User", required=True, reverse_delete_rule=db.CASCADE)
    initiated_by_u = db.StringField(required=True)
    STATUS_CHOICES = (
        ('ignored', 'Ignored'),
        ('open', 'Open'),
        ('feedback', 'Feedback Requested'),
        ('waiting', 'Waiting'),
        ('action taken', 'Action Taken')
    )
    status = db.StringField(choices=STATUS_CHOICES, default='open')
    created = db.DateTimeField(required=True)
    handled_by = db.ReferenceField("User", reverse_delete_rule=db.CASCADE)
    handled_by_u = db.StringField()

    meta = {
        'ordering': ['-created'],
        'indexes': [
            '-created',
            'initiated_by_u',
            'initiated_by',
            'status',
            {
                'fields': ['$content_reported',],
                'default_language': 'english'
            },
            'content_type',
            'content_pk',
            'url'
        ]
    }

class Log(db.DynamicDocument):
    method = db.StringField()
    path = db.StringField()
    ip_address = db.StringField()
    agent_platform = db.StringField()
    agent_browser = db.StringField()
    agent_browser_version = db.StringField()
    agent = db.StringField()
    user = db.ReferenceField("User", reverse_delete_rule=db.CASCADE)
    user_name = db.StringField(default="")
    time = db.DateTimeField()
    error = db.BooleanField()
    error_name = db.StringField()
    error_code = db.StringField()
    error_description = db.StringField()

    meta = {
        'ordering': ['-time'],
        'indexes': [
            '-time',
            'method',
            'path',
            'ip_address',
            'agent_platform',
            'agent_browser',
            'agent_browser_version',
            'agent',
            'user',
            'user_name',
            'time',
            'error'
        ]
    }

class StatusViewer(db.DynamicEmbeddedDocument):
    last_seen = db.DateTimeField(required=True)
    user = db.ReferenceField("User", required=True)

class StatusComment(db.DynamicEmbeddedDocument):
    text = db.StringField(required=True)
    author = db.ReferenceField("User", required=True)
    created = db.DateTimeField(required=True)
    hidden = db.BooleanField(default=False)

class StatusUpdate(db.DynamicDocument):
    attached_to_user = db.ReferenceField("User", reverse_delete_rule=db.CASCADE)
    attached_to_user_name = db.StringField(default="")
    author = db.ReferenceField("User", required=True, reverse_delete_rule=db.CASCADE)
    author_name = db.StringField(default="")
    message = db.StringField(required=True)
    comments = db.ListField(db.EmbeddedDocumentField(StatusComment))

    # Fake-Realtime stuff
    viewing = db.ListField(db.EmbeddedDocumentField(StatusViewer))

    # Notification stuff
    participants = db.ListField(db.ReferenceField("User", reverse_delete_rule=db.PULL))
    ignoring = db.ListField(db.ReferenceField("User", reverse_delete_rule=db.PULL))
    blocked = db.ListField(db.ReferenceField("User", reverse_delete_rule=db.PULL))

    # Mod stuff
    hidden = db.BooleanField(default=False)
    locked = db.BooleanField(default=False)
    muted = db.BooleanField(default=False)

    # Tracking
    view_count = db.IntField(default=0)
    viewers = db.IntField(default=0)
    participant_count = db.IntField(default=0)
    created = db.DateTimeField()
    last_replied = db.DateTimeField()
    last_viewed = db.DateTimeField()
    replies = db.IntField(default=0)
    hot_score = db.IntField(default=0) # Replies - Age (basically)

    old_ipb_id = db.IntField()

    meta = {
        'ordering': ['-created'],
        'indexes': [
            'old_ipb_id',
            '-created',
            'last_replied',
            'author',
            'attached_to_user',
            {
                'fields': ['$**',],
                'default_language': 'english'
            }
        ]
    }

    def get_comment_count(self):
        count = 0
        for c in self.comments:
            if not c.hidden:
                count += 1
        return count

class Attachment(db.DynamicDocument):
    owner_name = db.StringField(required=True)
    path = db.StringField(required=True)
    mimetype = db.StringField(required=True)
    extension = db.StringField(required=True)
    size_in_bytes = db.IntField(required=True)
    created_date = db.DateTimeField(required=True)
    do_not_convert = db.BooleanField(default=False)
    owner = db.ReferenceField("User", required=True, reverse_delete_rule=db.CASCADE)
    used_in = db.IntField(default=1)
    old_ipb_id = db.IntField()
    alt = db.StringField(default="")

    x_size = db.IntField()
    y_size = db.IntField()

    file_hash = db.StringField()
    linked = db.BooleanField(default=False)
    origin_url = db.StringField()
    origin_domain = db.StringField()
    caption = db.StringField(default="")

    # RP Specific
    character = db.ReferenceField("Character")
    character_name = db.StringField()
    character_gallery = db.BooleanField(default=False)
    character_emote = db.BooleanField(default=False)

    meta = {
        'indexes': [
            'file_hash',
            'origin_url',
            'origin_domain',
        ]
    }

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

class Category(db.DynamicDocument):
    name = db.StringField(required=True)
    slug = db.StringField(required=True, unique=True)
    parent = db.ReferenceField("Category", reverse_delete_rule=db.CASCADE)
    root_category = db.BooleanField(default=True)

    # Background info
    weight = db.IntField(default=0)
    user_post_counts = db.DictField()
    data = db.DictField()

    # Security
    restricted = db.BooleanField(default=False)
    allowed_users = db.ListField(db.ReferenceField("User", reverse_delete_rule=db.PULL))
    allowed_prefixes = db.ListField(db.StringField())

    # Tracking
    prefix_frequency = db.DictField()
    topic_count = db.IntField(default=0)
    post_count = db.IntField(default=0)
    view_count = db.IntField(default=0)
    last_topic = db.ReferenceField("Topic")
    last_topic_name = db.StringField()
    last_post_by = db.ReferenceField("User", reverse_delete_rule=db.NULLIFY)
    last_post_date = db.DateTimeField()
    last_post_author_avatar = db.StringField()

    # IPB migration
    old_ipb_id = db.IntField()

    meta = {
        'ordering': ['parent','weight'],
        'indexes': [
            'parent',
            'root_category',
            'weight',
            'slug'
        ]
    }

    def __unicode__(self):
        return self.name

class Prefix(db.DynamicDocument):
    pre_html = db.StringField()
    post_html = db.StringField()
    prefix = db.StringField(required=True, unique=True)

    def __unicode__(self):
        return self.prefix

class PollChoice(db.DynamicEmbeddedDocument):
    user = db.ReferenceField("User")
    choice = db.IntField()

class Poll(db.DynamicEmbeddedDocument):
    poll_question = db.StringField(required=True)
    poll_options = db.ListField(db.StringField(), required=True)
    poll_votes = db.ListField(db.EmbeddedDocumentField(PollChoice)) # User : Question

class Topic(db.DynamicDocument):
    # Basics
    slug = db.StringField(required=True, unique=True)
    category = db.ReferenceField("Category", required=True, reverse_delete_rule=db.CASCADE)
    title = db.StringField(required=True)
    creator = db.ReferenceField("User", required=True, reverse_delete_rule=db.CASCADE)
    created = db.DateTimeField(required=True)

    sticky = db.BooleanField(default=False)
    hidden = db.BooleanField(default=False)
    closed = db.BooleanField(default=False)
    close_message = db.StringField(default="")
    announcement = db.BooleanField(default=False)

    polls = db.ListField(db.EmbeddedDocumentField(Poll))
    poll_show_voters = db.BooleanField(default=False)

    # Hidden posts
    hidden_posts = db.IntField(default=0)

    # Prefixes
    pre_html = db.StringField()
    post_html = db.StringField()
    prefix = db.StringField()
    prefix_reference = db.ReferenceField("Prefix", reverse_delete_rule=db.NULLIFY)

    # Background info
    watchers = db.ListField(db.ReferenceField("User", reverse_delete_rule=db.PULL))
    topic_moderators = db.ListField(db.ReferenceField("User", reverse_delete_rule=db.PULL))
    banned_from_topic = db.ListField(db.ReferenceField("User", reverse_delete_rule=db.PULL))
    user_post_counts = db.DictField()
    data = db.DictField()
    last_seen_by = db.DictField() # User : last_seen_utc
    last_swept = db.DateTimeField()

    # Tracking
    first_post = db.ReferenceField("Post")
    post_count = db.IntField(default=0)
    view_count = db.IntField(default=0)
    last_post_by = db.ReferenceField("User", reverse_delete_rule=db.NULLIFY)
    last_post_date = db.DateTimeField()
    last_post_author_avatar = db.StringField()

    # IPB migration
    old_ipb_id = db.IntField()

    def is_topic_mod(self, user):
        if user in self.topic_moderators or user.is_mod or user.is_admin:
            return 1
        else:
            return 0

    meta = {
        'ordering': ['sticky', '-last_post_date'],
        'indexes': [
            'old_ipb_id',
            '-created',
            '-sticky',
            'created',
            'category',
            'slug',
            {
                'fields': ['$title',],
                'default_language': 'english'
            }
        ]
    }

class Flag(db.DynamicEmbeddedDocument):
    flagger = db.ReferenceField("User", required=True)
    flag_date = db.DateTimeField(required=True)
    flag_weight = db.IntField(default=1)

class PostHistory(db.DynamicEmbeddedDocument):
    creator = db.ReferenceField("User", required=True)
    created = db.DateTimeField(required=True)
    html = db.StringField(required=True)
    reason = db.StringField()
    data = db.DictField()

class Post(db.DynamicDocument):
    # Basics
    html = db.StringField(required=True)
    author = db.ReferenceField("User", required=True, reverse_delete_rule=db.CASCADE)
    author_name = db.StringField(required=True)
    topic = db.ReferenceField("Topic", required=True, reverse_delete_rule=db.CASCADE)
    topic_name = db.StringField(required=True)

    created = db.DateTimeField(required=True)
    modified = db.DateTimeField()
    data = db.DictField()
    history = db.ListField(db.EmbeddedDocumentField(PostHistory))

    # Moderation
    edited = db.DateTimeField()
    editor = db.ReferenceField("User", reverse_delete_rule=db.CASCADE)

    hidden = db.BooleanField(default=False)
    hide_message = db.StringField()
    flag_score = db.IntField(default=0)
    flag_clear_date = db.DateTimeField()
    flags = db.ListField(db.EmbeddedDocumentField(Flag))
    boops = db.ListField(db.ReferenceField("User", reverse_delete_rule=db.PULL))
    boop_count = db.IntField(default=0)
    position_in_topic = db.IntField()

    old_ipb_id = db.IntField()

    meta = {
        'indexes': [
            'old_ipb_id',
            '-created',
            'created',
            'topic',
            'hidden',
            'position_in_topic',
            {
                'fields': ['$html',],
                'default_language': 'english'
            }
        ],
        'ordering': ['created']
    }

class Character(db.DynamicDocument):
    slug = db.StringField(required=True, unique=True)
    old_character_id = db.IntField()
    creator = db.ReferenceField("User", reverse_delete_rule=db.NULLIFY)
    creator_name = db.StringField(required=True)
    creator_display_name = db.StringField(required=True)

    name = db.StringField(required=True)
    age = db.StringField()
    species = db.StringField()
    appearance = db.StringField()
    personality = db.StringField()
    backstory = db.StringField()
    other = db.StringField()
    motto = db.StringField(default="")
    created = db.DateTimeField(required=True)
    hidden = db.BooleanField(default=False)
    modified = db.DateTimeField()

    avatars = db.ListField(db.ReferenceField("Attachment", reverse_delete_rule=db.PULL))
    default_avatar = db.ReferenceField("Attachment", reverse_delete_rule=db.NULLIFY)
    legacy_avatar_field = db.StringField()
    gallery = db.ListField(db.ReferenceField("Attachment", reverse_delete_rule=db.PULL))
    default_gallery_image = db.ReferenceField("Attachment", reverse_delete_rule=db.NULLIFY)
    legacy_gallery_field = db.StringField()

    posts = db.ListField(db.ReferenceField("Post", reverse_delete_rule=db.PULL))
    post_count = db.IntField()
    roleplays = db.ListField(db.ReferenceField("Topic", reverse_delete_rule=db.PULL))

    def __unicode__(self):
        return self.name

    def get_avatar(self, size=200):
        if self.default_avatar:
            return self.default_avatar.get_specific_size(size)
        elif self.legacy_avatar_field:
            return "/static/uploads/"+self.legacy_avatar_field
        else:
            return ""

    def get_portrait(self, size=250):
        if self.default_gallery_image:
            return self.default_gallery_image.get_specific_size(size)
        elif self.legacy_gallery_field:
            return "/static/uploads/"+self.legacy_gallery_field
        else:
            return ""

###############################################################
# Import Users
###############################################################

for mongo_user in User.objects():
    new_user = SQLUser()
    profile = psql.UserProfile()

    new_user.username = re.sub('[^A-Za-z0-9\s\-]+', '', mongo_user.login_name).replace("  ", "_").replace(" ", "_")
    new_user.password = "bcrypt$"+mongo_user.password_hash
    new_user.email = mongo_user.email_address
    new_user.is_staff = mongo_user.is_admin
    new_user.is_superuser = mongo_user.is_admin
    new_user.is_active = mongo_user.validated
    new_user.date_joined = mongo_user.joined
    try:
        new_user.save()
    except:
        new_user.username = new_user.username+"_"
        new_user.save()

    profile.profile_user = new_user
    profile.my_url = new_user.username
    profile.display_name = mongo_user.display_name
    profile.how_did_you_find_us = mongo_user.how_did_you_find_us
    profile.is_allowed_during_construction = mongo_user.is_allowed_during_construction
    profile.time_zone = mongo_user.time_zone
    profile.banned = mongo_user.banned
    profile.validated = mongo_user.validated
    profile.over_thirteen = mongo_user.over_thirteen
    profile.emails_muted = mongo_user.emails_muted
    profile.old_mongo_hash = str(mongo_user.id)
    profile.title = mongo_user.title
    profile.about_me = mongo_user.about_me
    profile.anonymous_login = False

    profile.avatar_extension = mongo_user.avatar_extension
    profile.avatar_full_x = mongo_user.avatar_full_x
    profile.avatar_full_y = mongo_user.avatar_full_y
    profile.avatar_60_x = mongo_user.avatar_60_x
    profile.avatar_60_y = mongo_user.avatar_60_y
    profile.avatar_40_x = mongo_user.avatar_40_x
    profile.avatar_40_y = mongo_user.avatar_40_y
    profile.avatar_timestamp = mongo_user.avatar_timestamp

    profile.posts_count = mongo_user.posts_count
    profile.topic_count = mongo_user.topic_count
    profile.status_count = mongo_user.status_count
    profile.status_comment_count = mongo_user.status_comment_count
    profile.save()

for mongo_user in User.objects():
    for ig_user in mongo_user.ignored_users:
        try:
            source = psql.UserProfile.objects.get(old_mongo_hash=str(mongo_user.id))
            target = psql.UserProfile.objects.get(old_mongo_hash=str(ig_user.id))

            new_ignore = psql.IgnoredUser(is_ignoring=source, is_ignored=target)
            new_ignore.save()

            source.save()
        except:
            continue

for status_update in StatusUpdate.objects():
    new_status_update = psql.StatusUpdate()

    try:
        profile_user = psql.UserProfile.objects.get(old_mongo_hash=str(status_update.attached_to_user.id))
        new_status_update.attached_to_profile = profile_user
    except:
        pass

    new_status_update.message = status_update.message
    new_status_update.last_replied = status_update.last_replied
    new_status_update.last_viewed = status_update.last_viewed
    new_status_update.replies = status_update.replies

    status_author = psql.UserProfile.objects.get(old_mongo_hash=str(status_update.author.id))
    new_status_update.author = status_author
    new_status_update.created = status_update.created
    new_status_update.old_mongo_hash = str(status_update.id)
    new_status_update.save()

    for participant in status_update.participants:
        sql_user = psql.UserProfile.objects.get(old_mongo_hash=str(participant.id))
        status_update_user_cls = psql.StatusUpdateUser()
        status_update_user_cls.user = sql_user
        status_update_user_cls.status_update = new_status_update

        if participant in status_update.blocked:
            status_update_user_cls.blocked = True
        if participant in status_update.ignoring:
            status_update_user_cls.ignoring = True

        status_update_user_cls.save()

    for comment in status_update.comments:
        sql_comment_author = psql.UserProfile.objects.get(old_mongo_hash=str(comment.author.id))
        sql_comment = psql.StatusComment()
        sql_comment.author = sql_comment_author
        sql_comment.created = comment.created
        sql_comment.message = comment.text
        sql_comment.hidden = comment.hidden
        sql_comment.status_update = new_status_update
        sql_comment.save()

for character in Character.objects():
    sql_user = psql.UserProfile.objects.get(old_mongo_hash=str(character.creator.id))
    sql_character = psql.Character()

    sql_character.author = sql_user
    sql_character.created = character.created
    sql_character.modified = character.modified

    sql_character.name = character.name
    sql_character.slug = character.slug
    sql_character.age = character.age
    sql_character.species = character.species
    sql_character.appearance = character.appearance
    sql_character.backstory = character.backstory
    sql_character.other = character.other
    sql_character.motto = character.motto
    sql_character.old_mongo_hash = str(character.id)
    sql_character.save()

for attachment in Attachment.objects():
    sql_user = psql.UserProfile.objects.get(old_mongo_hash=str(attachment.owner.id))
    sql_attachment = psql.Attachment()

    sql_attachment.path = attachment.path
    sql_attachment.mimetype = attachment.mimetype
    sql_attachment.extension = attachment.extension
    sql_attachment.size_in_bytes = attachment.size_in_bytes
    sql_attachment.created_date = attachment.created_date
    sql_attachment.do_not_convert = attachment.do_not_convert
    sql_attachment.user = sql_user
    sql_attachment.old_mongo_hash = str(attachment.id)
    sql_attachment.alt = attachment.alt
    sql_attachment.x_size = attachment.x_size
    sql_attachment.y_size = attachment.y_size
    if attachment.file_hash is None:
        sql_attachment.file_hash = ""
    else:
        sql_attachment.file_hash = attachment.file_hash
    sql_attachment.linked = attachment.linked
    if attachment.origin_url is None:
        sql_attachment.origin_url = ""
    else:
        sql_attachment.origin_url = attachment.origin_url

    if attachment.origin_domain is None:
        sql_attachment.origin_domain = ""
    else:
        sql_attachment.origin_domain = attachment.origin_domain

    sql_attachment.caption = attachment.caption

    if attachment.character is not None:
        sql_character = psql.Character.objects.get(old_mongo_hash=str(attachment.character.id))

        sql_attachment.character = sql_character
        sql_attachment.character_gallery = True
        sql_attachment.character_avatar = attachment.character_emote

    sql_attachment.save()

for notification in Notification.objects():
    try:
        sql_user = psql.UserProfile.objects.get(old_mongo_hash=str(notification.user.id))
        sql_author = psql.UserProfile.objects.get(old_mongo_hash=str(notification.author.id))
    except:
        continue

    sql_notification = psql.Notification()
    sql_notification.user = sql_user
    sql_notification.originating_user = sql_author
    sql_notification.message = notification.text
    sql_notification.description = notification.description
    sql_notification.category = notification.category
    sql_notification.created = notification.created
    sql_notification.url = notification.url
    sql_notification.acknowledged = notification.acknowledged
    sql_notification.seen = notification.seen
    sql_notification.emailed = notification.emailed
    sql_notification.priority = notification.priority
    sql_notification.save()

for message_topic in PrivateMessageTopic.objects():
    sql_user = psql.UserProfile.objects.get(old_mongo_hash=str(message_topic.creator.id))
    sql_message_topic = psql.PrivateMessage()
    sql_message_topic.created = message_topic.created
    sql_message_topic.author = sql_user
    sql_message_topic.title = message_topic.title
    sql_message_topic.message_count = message_topic.message_count
    sql_message_topic.old_mongo_hash = message_topic.id
    sql_message_topic.save()

    for message_reply in PrivateMessage.objects(topic=message_topic):
        sql_user = psql.UserProfile.objects.get(old_mongo_hash=str(message_reply.author.id))
        sql_message_reply = psql.PrivateMessageReply()
        sql_message_reply.author = sql_user
        sql_message_reply.message = message_reply.message
        sql_message_reply.private_message = sql_message_topic
        sql_message_reply.created = message_reply.created
        sql_message_reply.modified = message_reply.modified
        sql_message_reply.old_mongo_hash = str(message_reply.id)

        sql_message_reply.save()

    sql_message_topic.last_reply = psql.PrivateMessageReply.objects.filter(private_message=sql_message_topic).order_by("-created")[0]
    sql_message_topic.save()

    for message_user in message_topic.participating_users:
        sql_user = psql.UserProfile.objects.get(old_mongo_hash=str(message_user.id))
        sql_participant = psql.PrivateMessageUser()
        sql_participant.user = sql_user
        sql_participant.private_message = sql_message_topic
        if message_user in message_topic.blocked_users:
            sql_participant.blocked = True
        if message_user in message_topic.users_left_pm:
            sql_participant.exited = True
        sql_participant.save()

celly_hub = psql.Section.objects.create(
    name="Celestial Hub",
    weight=0
)

moony_hub = psql.Section.objects.create(
    name="Moonlight Symposium",
    weight=10
)

sunny_home = psql.Section.objects.create(
    name="Sunlight Homestead",
    weight=20
)

celestial_hub_categories = ["Latest News","Welcome Mat","Help Lab","Frequently Asked Questions"]
moonlight_symposium = ["Discussion", "Interrogations", "Anime", "Games", "Nintendo", "Art Show"]
sunlight_homestead = ["Roleplays", "Out of Character", "Meta Lounge", "Super Party Palace", "Minecraft"]

for i, category in enumerate(celestial_hub_categories):
    psql.Category.objects.create(
        name = category,
        slug = django.utils.text.slugify(category),
        section = celly_hub,
        weight = i*10
    )

for i, category in enumerate(moonlight_symposium):
    psql.Category.objects.create(
        name = category,
        slug = django.utils.text.slugify(category),
        section = moony_hub,
        weight = i*10
    )

for i, category in enumerate(sunlight_homestead):
    psql.Category.objects.create(
        name = category,
        slug = django.utils.text.slugify(category),
        section = sunny_home,
        weight = i*10
    )

for topic in Topic.objects():
    try:
        if topic.prefix is not None:
            psql.Label.objects.get_or_create(
                pre_html = topic.pre_html,
                post_html = topic.post_html,
                label = topic.prefix
            )
    except:
        continue

for topic in Topic.objects():
    sql_user = psql.UserProfile.objects.get(old_mongo_hash=str(topic.creator.id))
    sql_topic = psql.Topic()
    sql_topic.author = sql_user
    sql_topic.created = topic.created
    sql_topic.hidden = topic.hidden
    sql_topic.locked = topic.closed
    sql_topic.name = topic.title
    sql_topic.slug = topic.slug

    if topic.category.name in ["Commissions", "Requests"]:
        sql_topic.category = psql.Category.objects.get(name="Art Show")
    elif topic.category.name == "Scenarios":
        sql_topic.category = psql.Category.objects.get(name="Roleplays")
    elif topic.category.name == "Minecraft Discussion":
        sql_topic.category = psql.Category.objects.get(name="Minecraft")
    elif topic.category.name == "Out of Character Discussion":
        sql_topic.category = psql.Category.objects.get(name="Out of Character")
    elif topic.prefix == "Anime":
        sql_topic.category = psql.Category.objects.get(name="Anime")
        topic.prefix = None
    elif topic.prefix == "Games":
        sql_topic.category = psql.Category.objects.get(name="Games")
        topic.prefix = None
    else:
        sql_topic.category = psql.Category.objects.get(name=topic.category.name)

    if topic.prefix is not None:
        sql_prefix = psql.Label.objects.get(label=topic.prefix)
        sql_topic.label = sql_prefix

    sql_topic.save()

    for post in Post.objects(topic=topic):
        sql_user = psql.UserProfile.objects.get(old_mongo_hash=str(post.author.id))
        sql_post = psql.Post()

        sql_post.created = post.created
        sql_post.modified = post.modified
        sql_post.author = sql_user
        sql_post.html = post.html
        sql_post.topic = sql_topic
        sql_post.old_mongo_hash = str(post.id)
        sql_post.hidden = post.hidden

        if post.data.has_key("character"):
            sql_post.character = psql.Character.objects.get(old_mongo_hash=str(post.data["character"]))

        if post.data.has_key("avatar"):
            sql_post.avatar = psql.Attachment.objects.get(old_mongo_hash=str(post.data["avatar"]))

        sql_post.save()

        for user in post.boops:
            sql_booper = psql.UserProfile.objects.get(old_mongo_hash=str(user.id))
            sql_post.boops.add(sql_booper)

        sql_post.save()
