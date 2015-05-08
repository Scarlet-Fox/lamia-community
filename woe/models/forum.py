from woe import db
from . import core

class Flag(db.EmbeddedDocument):
    flagger = db.ReferenceField(core.User)
    flag_date = db.DateTimeField()

class Post(db.Document):
    # Basics
    html = db.StringField()
    author = db.ReferenceField(core.User)
    topic = db.ReferenceField("Topic")
    
    created = db.DateTimeField()
    modified = db.DateTimeField()
    data = db.DictField()
    
    # Moderation
    edited = db.DateTimeField()
    editor = db.ReferenceField(core.User)
    
    hidden = db.BooleanField(default=False)
    hide_message = db.StringField()
    flag_score = db.IntField(default=0)
    flag_clear_date = db.DateTimeField()
    flags = db.EmbeddedDocumentField(Flag)
    
class Topic(db.Document):
    # Basics
    title = db.StringField()
    creator = db.ReferenceField(core.User)
    created = db.DateTimeField
    
    # Tracking
    post_count = db.IntField
    
