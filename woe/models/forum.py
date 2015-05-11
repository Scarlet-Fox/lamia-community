from woe import db
from . import core

class Flag(db.DynamicEmbeddedDocument):
    flagger = db.ReferenceField(core.User)
    flag_date = db.DateTimeField()

class PostHistory(db.DynamicEmbeddedDocument):
    creator = db.ReferenceField(core.User)
    created = db.DateTimeField()
    html = db.StringField()
    data = db.DictField()

class Post(db.DynamicDocument):
    # Basics
    html = db.StringField()
    author = db.ReferenceField(core.User)
    topic = db.ReferenceField("Topic")
    
    created = db.DateTimeField()
    modified = db.DateTimeField()
    data = db.DictField()
    history = db.ListField(db.EmbeddedDocumentField(PostHistory))
    
    # Moderation
    edited = db.DateTimeField()
    editor = db.ReferenceField(core.User)
    
    hidden = db.BooleanField(default=False)
    hide_message = db.StringField()
    flag_score = db.IntField(default=0)
    flag_clear_date = db.DateTimeField()
    flags = db.ListField(db.EmbeddedDocumentField(Flag))

class Prefix(db.DynamicDocument):
    pre_html = db.StringField()
    post_html = db.StringField()
    prefix = db.StringField()

class Poll(db.DynamicEmbeddedDocument):
    poll_question = db.StringField()
    poll_options = db.ListField(db.StringField())
    poll_votes = db.DictField() # User : Question

class Topic(db.DynamicDocument):
    # Basics
    category = db.ReferenceField("Category")
    title = db.StringField()
    creator = db.ReferenceField(core.User)
    created = db.DateTimeField()
    
    sticky = db.BooleanField()
    hidden = db.BooleanField()
    closed = db.BooleanField()
    close_message = db.StringField()
    announcement = db.BooleanField()
    
    polls = db.ListField(db.EmbeddedDocumentField(Poll))
    poll_show_voters = db.BooleanField(default=False)
    
    # Prefixes
    pre_html = db.StringField()
    post_html = db.StringField()
    prefix = db.StringField()
    
    # Background info
    watchers = db.ListField(db.ReferenceField(core.User))
    topic_moderators = db.ListField(db.ReferenceField(core.User))
    user_post_counts = db.DictField()
    data = db.DictField()
    last_seen_by = db.DictField() # User : last_seen_utc
    
    # Tracking
    post_count = db.IntField()
    view_count = db.IntField()
    last_post_by = db.ReferenceField(core.User)
    last_post_date = db.DateTimeField()
    last_post_author_avatar = db.StringField()

class Category(db.DynamicDocument):
    name = db.StringField()
    parent = db.ReferenceField("Category")
    root_category = db.BooleanField(default=True)
    
    # Background info
    weight = db.IntField()
    category_moderators = db.ListField(db.ReferenceField(core.User))
    user_post_counts = db.DictField()
    data = db.DictField()
    
    # Security
    restricted = db.BooleanField(default=False)
    allow_only = db.ListField(db.ReferenceField(core.User))
    
    # Tracking
    prefix_frequency = db.DictField()
    post_count = db.IntField()
    view_count = db.IntField()
    last_topic_name = db.StringField()
    last_post_by = db.ReferenceField(core.User)
    last_post_date = db.DateTimeField()
    last_post_author_avatar = db.StringField()

class Attachment(db.DynamicDocument):
    filename = db.StringField()
    mimetype = db.StringField()
    size_in_bytes = db.IntField()
    created_date = db.DateTimeField()
    last_modified_date = db.DateTimeField()
    owner = db.ReferenceField(core.User)
    present_in = db.ListField(db.GenericReferenceField())
