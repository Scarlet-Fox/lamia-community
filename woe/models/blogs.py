from woe import db
from slugify import slugify
from woe.models.core import User

def get_blog_slug(title):
    slug = slugify(title, max_length=100, word_boundary=True, save_order=True)
    
    def try_slug(slug, count=0):
        new_slug = slug
        if count > 0:
            new_slug = slug+"-"+str(count)
            
        if len(Blog.objects(slug=new_slug)) == 0:
            return new_slug
        else:
            return try_slug(slug, count+1)
    
    return try_slug(slug)

class Blog(db.DynamicDocument):
    name = db.StringField(required=True)
    slug = db.StringField(required=True, unique=True)
    creator = db.ReferenceField("User", required=True, reverse_delete_rule=db.CASCADE)
    creator_name = db.StringField(required=True)
    
    description = db.StringField()
    blog_editors = db.ListField(db.ReferenceField("User", reverse_delete_rule=db.PULL))  
    blog_categories = db.ListField(db.StringField())  
    
    entry_count = db.IntField(default=0)
    comment_count = db.IntField(default=0)
    view_count = db.IntField(default=0)
    
    last_entry_date = db.DateTimeField()
    last_comment_date = db.DateTimeField()
    blog_subscribers = db.ListField(db.ReferenceField("User", reverse_delete_rule=db.PULL))  
    
    last_entry = db.ReferenceField("BlogEntry")
    last_comment = db.ReferenceField("BlogComment")

    PRIVACY_LEVELS = (
        ("all", "Everyone"),
        ("members", "Only Members"),
        ("friends", "Only Friends"),
        ("editors", "Only Editors"),
        ("you", "Only You")
    )
    privacy_setting = db.StringField(choices=PRIVACY_LEVELS, required=True)
    disabled = db.BooleanField(default=False)
    
    old_ipb_id = db.IntField()

class BlogHistory(db.DynamicEmbeddedDocument):
    creator = db.ReferenceField("User", required=True)
    created = db.DateTimeField(required=True)
    html = db.StringField(required=True)
    reason = db.StringField()
    data = db.DictField()

class BlogEntry(db.DynamicDocument):
    title = db.StringField(required=True)
    slug = db.StringField(required=True)
    html = db.StringField(required=True)
    author = db.ReferenceField("User", required=True, reverse_delete_rule=db.CASCADE)
    author_name = db.StringField(required=True)
    blog = db.ReferenceField("Blog", required=True, reverse_delete_rule=db.CASCADE)
    blog_name = db.StringField(required=True)
    category = db.StringField()

    created = db.DateTimeField(required=True)
    published = db.DateTimeField()
    data = db.DictField()
    history = db.ListField(db.EmbeddedDocumentField(BlogHistory))
    entry_subscribers = db.ListField(db.ReferenceField("User", reverse_delete_rule=db.PULL))  

    edited = db.DateTimeField()
    editor = db.ReferenceField("User", reverse_delete_rule=db.CASCADE)
    locked = db.BooleanField(default=False)
    hidden = db.BooleanField(default=False)    
    
    boops = db.ListField(db.ReferenceField("User", reverse_delete_rule=db.PULL))
    boop_count = db.IntField(default=0)
    comment_count = db.IntField(default=0)
    last_comment = db.ReferenceField("BlogComment")
    last_comment_date = db.DateTimeField()
    view_count = db.IntField(default=0)
    
    draft = db.BooleanField(default=True)
    hidden = db.BooleanField(default=False)
    hide_message = db.StringField()
    
    old_ipb_id = db.IntField()

class BlogComment(db.DynamicDocument):
    html = db.StringField(required=True)
    author = db.ReferenceField("User", required=True, reverse_delete_rule=db.CASCADE)
    author_name = db.StringField(required=True)
    blog_entry = db.ReferenceField("BlogEntry", required=True, reverse_delete_rule=db.CASCADE)
    blog_entry_name = db.StringField(required=True)
    blog = db.ReferenceField("Blog", required=True, reverse_delete_rule=db.CASCADE)
    blog_name = db.StringField(required=True)

    created = db.DateTimeField(required=True)
    modified = db.DateTimeField()
    data = db.DictField()
    history = db.ListField(db.EmbeddedDocumentField(BlogHistory))

    edited = db.DateTimeField()
    editor = db.ReferenceField("User", reverse_delete_rule=db.CASCADE)
    
    boops = db.ListField(db.ReferenceField("User", reverse_delete_rule=db.PULL))
    boop_count = db.IntField(default=0)
    
    hidden = db.BooleanField(default=False)
    hide_message = db.StringField()
    
    def __unicode__(self):
        return unicode(self.html)