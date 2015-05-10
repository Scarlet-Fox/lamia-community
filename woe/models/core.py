from woe import db
from woe import bcrypt

class Fingerprint(db.Document):
    user = db.ReferenceField("User")
    fingerprint = db.DictField()
    last_seen = db.DateTimeField()
    
    def compute_similarity_score(self, stranger):
        max_score = float(len(self.fingerprint))
        score = 0.0
        
        for key, value in self.fingerprint.iteritems():
            if stranger.get(key, False) == value:
                score += 1
                
        return score/max_score
        
    def get_factors(self):
        return float(len(self.fingerprint))

class IPAddress(db.Document):
    user = db.ReferenceField("User")
    ip_address = db.StringField()
    last_seen = db.DateTimeField()
    
class Ban(db.Document):
    user = db.ReferenceField("User")
    ip_address = db.StringField()

class ModNote(db.EmbeddedDocument):
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
    incident_level = db.StringField(choices=INCIDENT_LEVELS)

class UserActivity(db.EmbeddedDocument):
    content = db.GenericReferenceField()
    category = db.StringField()
    created = db.DateTimeField()
    data = db.DictField()

class User(db.Document):
    login_name = db.StringField(required=True, unique=True)
    display_name = db.StringField(required=True, unique=True)
    password_hash = db.StringField()
    email_address = db.EmailField(required=True)
    emails_muted = db.BooleanField(default=False)
    
    # Customizable display values
    
    title = db.StringField(default="")
    location = db.StringField(default="")
    about = db.StringField(default="")
    
    information_fields = db.ListField(db.DictField())
    social_fields = db.ListField(db.DictField())
    
    # Background details

    last_sent_notification_email = db.DateTimeField()
    auto_acknowledge_notifications_after = db.IntField()
    last_looked_at_notifications = db.DateTimeField()
    
    signatures = db.ListField(db.StringField())
    timezone = db.IntField(default=0) # Relative to UTC
    hide_age = db.BooleanField(default=True)
    hide_birthday = db.BooleanField(default=True)
    hide_login = db.BooleanField(default=False)
    banned = db.BooleanField(default=False)
    validated = db.BooleanField(default=False)
    
    warning_points = db.IntField(default=0)
    
    display_name_history = db.ListField(db.DictField())
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
    
    # Notification preferences
    
    OPTIONS = (
        ("dash", "Dashboard"),
        ("email", "Email"),
        ("both", "Both")
    )
    
    # NOTE MOD NOTES ARE AUTO SENT VIA BOTH
    topics = db.StringField(choices=OPTIONS, default="dash")
    status = db.StringField(choices=OPTIONS, default="dash")
    quoted = db.StringField(choices=OPTIONS, default="dash")
    mention = db.StringField(choices=OPTIONS, default="dash")
    followed = db.StringField(choices=OPTIONS, default="dash")
    messages = db.StringField(choices=OPTIONS, default="dash")
    announcements = db.StringField(choices=OPTIONS, default="dash")
    
    # Friends and social stuff
    friends = db.ListField(db.ReferenceField("User"))
    profile_feed = db.ListField(db.EmbeddedDocumentField(UserActivity))
    
    # Moderation options
    disable_posts = db.BooleanField(default=False)
    disable_status = db.BooleanField(default=False)
    disable_status_participation = db.BooleanField(default=False)
    disable_pm = db.BooleanField(default=False)
    disable_topics = db.BooleanField(default=False)
    hellban = db.BooleanField(default=False)
    
    # Statistics
    joined = db.DateTimeField()
    posts = db.IntField(default=0)
    status_updates = db.IntField(default=0)
    status_comments = db.IntField(default=0)
    last_seen = db.DateTimeField()
    last_at = db.StringField(default="Watching forum index.")
    last_at_url = db.StringField(default="/")
    smile_usage = db.DictField()
    post_frequency = db.DictField()
    
    # Migration related
    old_member_id = db.IntField(default=1, unique=True)
    
    def __str__(self):
        return self.login_name
    
    def is_active(self):
        if self.banned:
            return False
        if not self.validated:
            return False
        return True
        
    def get_id(self):
        return self.login_name
        
    def is_authenticated(self):
        return True # Will only ever return True.
        
    def is_anonymous(self):
        return False # Will only ever return False. Anonymous = guest user. We don't support those.
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password.strip(),12)
        
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
        
class PrivateMessage(db.EmbeddedDocument):
    message = db.StringField()
    author = db.ReferenceField(User)
    
    created = db.DateTimeField()
    modified = db.DateTimeField()

class PrivateMessageParticipant(db.EmbeddedDocument):
    author = db.ReferenceField(User)
    left_pm = db.BooleanField(default=False)

class PrivateMessageTopic(db.Document):
    title = db.StringField()
    creator = db.ReferenceField(User)
    created = db.DateTimeField()
    last_message = db.DateTimeField()
    
    messages = db.ListField(db.EmbeddedDocumentField(PrivateMessage))
    participants = db.ListField(db.EmbeddedDocumentField(PrivateMessageParticipant))
    
    labels = db.ListField(db.StringField())
    
class PrivateMessageWatch(db.Document):
    user = db.ReferenceField(User)
    pm = db.ReferenceField(PrivateMessageTopic)
    
    do_not_notify = db.BooleanField(default=False)
    last_read = db.DateTimeField()
    
class Notification(db.Document):
    user = db.ReferenceField(User)
    text = db.StringField()
    NOTIFICATION_CATEGORIES = (
        ("topic", "Topics"),
        ("pm", "Private Messages"),
        ("topic_reply", "Topic Replies"),
        ("boop", "Boops"),
        ("mod", "Moderation"),
        ("status", "Status Updates"),
        ("new_member", "New Members"),
        ("announcement", "Announcements"),
        ("profile_comment","Profile Comments"),
        ("rules_updated", "Rule Update"),
        ("faqs", "FAQs Updated")
    )
    category = db.StringField(choices=NOTIFICATION_CATEGORIES)
    created = db.DateTimeField()
    acknowledged = db.BooleanField(default=False)

class ReportComment(db.Document):
    author = db.ReferenceField(User)
    created = db.DateTimeField()
    text = db.StringField()

class Report(db.Document):
    content = db.GenericReferenceField()
    text = db.StringField()
    initiated_by = db.ReferenceField(User)
    STATUS_CHOICES = ( 
        ('closed', 'Closed'), 
        ('open', 'Open'), 
        ('feedback', 'Feedback Requested'), 
        ('waiting', 'Waiting') 
    )
    status = db.StringField(choices=STATUS_CHOICES, default='open')
    created = db.DateTimeField()
    
class Log(db.Document):
    content = db.GenericReferenceField()
    user = db.ReferenceField(User)
    ip_address = db.ReferenceField(IPAddress)
    fingerprint = db.ReferenceField(Fingerprint)
    action = db.StringField()
    url = db.StringField()
    data = db.DictField()
    logged_at_time = db.DateTimeField()

class StatusViewer(db.EmbeddedDocument):
    last_seen = db.DateTimeField()
    user = db.ReferenceField(User)
    
class StatusComment(db.EmbeddedDocument):
    text = db.StringField()
    author = db.ReferenceField(User)
    created = db.DateTimeField()

class StatusUpdate(db.Document):
    attached_to_user = db.ReferenceField(User)
    author = db.ReferenceField(User)
    message = db.StringField()
    comments = db.ListField(db.EmbeddedDocumentField(StatusComment))
    
    # Realtime stuff
    viewing = db.ListField(db.EmbeddedDocumentField(StatusViewer))
    
    # Notification stuff
    participants = db.ListField(db.ReferenceField(User))
    ignoring = db.ListField(db.ReferenceField(User))
    
    # Mod stuff
    hidden = db.BooleanField(default=False)
    hide_message = db.StringField(default=False)
    
    # Tracking
    viewers = db.IntField(default=0)
    created = db.DateTimeField()
    replies = db.IntField(default=0)
    hot_score = db.IntField(default=0) # Replies - Age (basically)
