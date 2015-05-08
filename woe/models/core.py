from woe import db
from woe import bcrypt

class ModNote(db.EmbeddedDocument):
    date = db.DateTimeField(required=True)
    note = db.StringField(required=True)
    reference = db.GenericEmbeddedDocumentField()
    INCIDENT_LEVELS = (
        ("Other", "???"),
        ("Wat", "Something Weird"),
        ("Minor", "Just A Heads Up"),
        ("Major", "Will Need a Talking To"),
        ("Extreme", "Worthy of Being Banned")
    )
    incident_level = db.StringField(choices=INCIDENT_LEVELS)

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
    
    # Friends
    friends = db.ListField(db.ReferenceField("User"))
    
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
        