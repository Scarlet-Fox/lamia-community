from woe import db
from slugify import slugify
from . import core

class Flag(db.DynamicEmbeddedDocument):
    flagger = db.ReferenceField(core.User, required=True)
    flag_date = db.DateTimeField(required=True)
    flag_weight = db.IntField(default=1)

class PostHistory(db.DynamicEmbeddedDocument):
    creator = db.ReferenceField(core.User, required=True)
    created = db.DateTimeField(required=True)
    html = db.StringField(required=True)
    reason = db.StringField()
    data = db.DictField()

class Post(db.DynamicDocument):
    # Basics
    html = db.StringField(required=True)
    author = db.ReferenceField(core.User, required=True)
    author_name = db.StringField(required=True)
    topic = db.ReferenceField("Topic", required=True)
    topic_name = db.StringField(required=True)
    
    created = db.DateTimeField(required=True)
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
    boops = db.ListField(db.ReferenceField(core.User))
    boop_count = db.IntField(default=0)
    
    old_ipb_id = db.IntField()

    meta = {
        'indexes': [
            'old_ipb_id',
            '-created',
            'created',
            'topic',
            'hidden',
            {
                'fields': ['$html',],
                'default_language': 'english'
            }
        ],
        'ordering': ['created']
    }

class Prefix(db.DynamicDocument):
    pre_html = db.StringField()
    post_html = db.StringField()
    prefix = db.StringField(required=True, unique=True)
    
    def __unicode__(self):
        return self.prefix

class PollChoice(db.DynamicEmbeddedDocument):
    user = db.ReferenceField(core.User)
    choice = db.IntField()

class Poll(db.DynamicEmbeddedDocument):
    poll_question = db.StringField(required=True)
    poll_options = db.ListField(db.StringField(), required=True)
    poll_votes = db.ListField(db.EmbeddedDocumentField(PollChoice)) # User : Question

class Topic(db.DynamicDocument):
    # Basics
    slug = db.StringField(required=True, unique=True)
    category = db.ReferenceField("Category", required=True)
    title = db.StringField(required=True)
    creator = db.ReferenceField(core.User, required=True)
    created = db.DateTimeField(required=True)
    
    sticky = db.BooleanField(default=False)
    hidden = db.BooleanField(default=False)
    closed = db.BooleanField(default=False)
    close_message = db.StringField(default="")
    announcement = db.BooleanField(default=False)
    
    polls = db.ListField(db.EmbeddedDocumentField(Poll))
    poll_show_voters = db.BooleanField(default=False)
    
    # Prefixes
    pre_html = db.StringField()
    post_html = db.StringField()
    prefix = db.StringField()
    prefix_reference = db.ReferenceField(Prefix)
    
    # Background info
    watchers = db.ListField(db.ReferenceField(core.User))
    topic_moderators = db.ListField(db.ReferenceField(core.User))
    banned_from_topic = db.ListField(db.ReferenceField(core.User))
    user_post_counts = db.DictField()
    data = db.DictField()
    last_seen_by = db.DictField() # User : last_seen_utc
    
    # Tracking
    first_post = db.ReferenceField(Post)
    post_count = db.IntField(default=0)
    view_count = db.IntField(default=0)
    last_post_by = db.ReferenceField(core.User)
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
        'ordering': ['sticky', '-created'],
        'indexes': [
            'old_ipb_id',
            '-created',
            'created',
            'category',
            'slug',
            {
                'fields': ['$title',],
                'default_language': 'english'
            }
        ]
    }

class Category(db.DynamicDocument):
    name = db.StringField(required=True)
    slug = db.StringField(required=True, unique=True)
    parent = db.ReferenceField("Category")
    root_category = db.BooleanField(default=True)
    
    # Background info
    weight = db.IntField(default=0)
    category_moderators = db.ListField(db.ReferenceField(core.User))
    user_post_counts = db.DictField()
    data = db.DictField()
    
    # Security
    restricted = db.BooleanField(default=True)
    allow_only = db.ListField(db.ReferenceField(core.User))
    allowed_prefixes = db.ListField(db.StringField())
    
    # Tracking
    prefix_frequency = db.DictField()
    topic_count = db.IntField(default=0)
    post_count = db.IntField(default=0)
    view_count = db.IntField(default=0)
    last_topic = db.ReferenceField(Topic)
    last_topic_name = db.StringField()
    last_post_by = db.ReferenceField(core.User)
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

def get_topic_slug(title):
    slug = slugify(title, max_length=100, word_boundary=True, save_order=True)
    
    def try_slug(slug, count=0):
        new_slug = slug
        if count > 0:
            new_slug = slug+"-"+str(count)
            
        if len(Topic.objects(slug=new_slug)) == 0:
            return new_slug
        else:
            return try_slug(slug, count+1)
    
    return try_slug(slug)