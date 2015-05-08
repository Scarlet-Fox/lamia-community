from woe import db
from woe import bcrypt

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
    meta = db.DictField()

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
        (0, "Dashboard"),
        (1, "Email"),
        (2, "Both")
    )
    
    # NOTE MOD NOTES ARE AUTO SENT VIA BOTH
    topics = db.StringField(choices=OPTIONS, default=0)
    status = db.StringField(choices=OPTIONS, default=0)
    quoted = db.StringField(choices=OPTIONS, default=0)
    mention = db.StringField(choices=OPTIONS, default=0)
    followed = db.StringField(choices=OPTIONS, default=0)
    messages = db.StringField(choices=OPTIONS, default=0)
    announcements = db.StringField(choices=OPTIONS, default=0)
    
    # Friends and social stuff
    friends = db.ListField(db.ReferenceField("User"))
    profile_feed = db.ListField(db.UserActivity())
    
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
    old_member_id = db.IntField(default=True)
    
    def __str__(self):
        return self.login_name
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password.strip(),12)
        
    def check_password(self, password):
        return bcrypt.bcrypt.check_password_hash(self.password_hash, password)
        
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
    content = db.GenericReferenceField()
    category = db.StringField()
    created = db.DateTimeField()
    acknowledged = db.BooleanField(default=False)