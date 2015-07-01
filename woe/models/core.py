from woe import db
from woe import app
from woe import bcrypt
from woe.utilities import ipb_password_check
from urllib import quote
import arrow, re, os, math
from flask.ext.login import current_user

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
        self.save()
        
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
            return ""
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
    
    meta = {
        'indexes': [
            'file_hash',
            'origin_url',
            'origin_domain',
        ]
    }

