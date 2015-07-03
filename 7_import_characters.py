import MySQLdb, arrow
import MySQLdb.cursors
from woe.models.roleplay import Character
from woe.models.core import User, Attachment
from woe.models.forum import Post
import json, os
from slugify import slugify
from wand.image import Image
from mongoengine.queryset import Q

settings_file = json.loads(open("config.json").read())

db = MySQLdb.connect(user=settings_file["woe_old_user"], db=settings_file["woe_old_db"], passwd=settings_file["woe_old_pass"], cursorclass=MySQLdb.cursors.DictCursor,charset='latin1',use_unicode=True)

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

c=db.cursor()
c.execute("select * from ipsccs_custom_database_4;")
for character in c.fetchall():
    c = Character()
    c.name = character["field_23"].encode("latin1")
    c.age = character["field_25"].encode("latin1")
    c.old_character_id = character["primary_id_field"]
    c.creator = User.objects(old_member_id=character["member_id"])[0]
    c.creator_name = c.creator.login_name
    c.creator_display_name = c.creator.display_name
    if c.creator.banned:
        continue
    c.created = arrow.get(character["record_saved"]).datetime
    c.modified = arrow.get(character["record_updated"]).datetime
    c.slug = get_character_slug(c.name)
    c.species = character["field_24"].encode("latin1")
    c.appearance = character["field_34"].encode("latin1")
    c.personality = character["field_21"].encode("latin1")
    c.backstory = character["field_22"].encode("latin1")
    c.other = character["field_26"].encode("latin1")
    c.legacy_avatar_field = character["field_43"].encode("latin1")
    c.legacy_gallery_field = character["field_27"].encode("latin1")
    #c.save()
    
    posts = Post.objects(Q(html__contains="[postcharacter=%s|" % (c.old_character_id,)) | Q(html__contains="[postcharacter=%s]" % (c.old_character_id,)) | Q(html__contains="[character=%s]" % (c.old_character_id,)) | Q(html__contains="[character=%s|" % (c.old_character_id,)))
    c.posts = posts
    c.post_count = len(posts)
    
    for post in posts:
        if post.topic not in c.roleplays:
            c.roleplays.append(post.topic)
    
    c.save()
    
    for post in posts:            
        post.data["character"] = str(c.pk)
        post.save()
    