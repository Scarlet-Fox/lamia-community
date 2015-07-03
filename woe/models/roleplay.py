from woe import db
from slugify import slugify
from woe.models.core import User

def get_character_slug(name):
    slug = slugify(name, max_length=100, word_boundary=True, save_order=True)
    
    def try_slug(slug, count=0):
        new_slug = slug
        if count > 0:
            new_slug = slug+"-"+str(count)
            
        if len(Character.objects(slug=new_slug)) == 0:
            return new_slug
        else:
            return try_slug(slug, count+1)
    
    return try_slug(slug)

class Character(db.DynamicDocument):
    slug = db.StringField(required=True)
    old_character_id = db.IntField()
    creator = db.ReferenceField("User", reverse_delete_rule=db.NULLIFY)
    creator_name = db.StringField(required=True)
    creator_display_name = db.StringField(required=True)

    name = db.StringField(required=True)
    age = db.StringField(required=True)
    species = db.StringField(required=True)
    appearance = db.StringField()
    personality = db.StringField()
    backstory = db.StringField()
    other = db.StringField()
    created = db.DateTimeField(required=True)
    hidden = db.BooleanField(default=False)
    modified = db.DateTimeField()
    
    avatars = db.ListField(db.ReferenceField("Attachment", reverse_delete_rule=db.PULL))
    legacy_avatar_field = db.StringField()
    gallery = db.ListField(db.ReferenceField("Attachment", reverse_delete_rule=db.PULL))
    legacy_gallery_field = db.StringField()
    
    posts = db.ListField(db.ReferenceField("Post", reverse_delete_rule=db.PULL))
    post_count = db.IntField()
    roleplays = db.ListField(db.ReferenceField("Topic", reverse_delete_rule=db.PULL))
     
    def __unicode__(self):
        return self.name