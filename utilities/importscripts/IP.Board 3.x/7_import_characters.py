# A forum specific import script for IPB 3.x - showing an import from a custom database (in this case, one containing RP characters)

import MySQLdb, arrow
import MySQLdb.cursors
from woe.models.roleplay import Character
from woe.models.core import User, Attachment
from woe.models.forum import Post
import json, os, re, HTMLParser, mimetypes
from slugify import slugify
from wand.image import Image
from mongoengine.queryset import Q

settings_file = json.loads(open("config.json").read())

db = MySQLdb.connect(user=settings_file["ipb_import_user"], db=settings_file["ipb_import_db"], passwd=settings_file["ipb_import_pass"], cursorclass=MySQLdb.cursors.DictCursor,charset='latin1',use_unicode=True)

def get_character_slug(name):
    slug = slugify(name, max_length=100, word_boundary=True, save_order=True)
    if slug.strip() == "":
        slug="_"
    
    def try_slug(slug, count=0):
        new_slug = slug
        if count > 0:
            new_slug = slug+"-"+str(count)
            
        if len(Character.objects(slug=new_slug)) == 0:
            return new_slug
        else:
            return try_slug(slug, count+1)
    
    return try_slug(slug)

blockquote_re = re.compile("<blockquote.*?</blockquote>", re.DOTALL)

c=db.cursor()
c.execute("select * from ipsccs_custom_database_4;")
for character in c.fetchall():
    c = Character()
    c.name = HTMLParser.HTMLParser().unescape(character["field_23"].encode("latin1"))
    c.age = HTMLParser.HTMLParser().unescape(character["field_25"].encode("latin1"))
    c.old_character_id = character["primary_id_field"]
    c.creator = User.objects(old_member_id=character["member_id"])[0]
    c.creator_name = c.creator.login_name
    c.creator_display_name = c.creator.display_name
    if c.creator.banned:
        continue
    c.created = arrow.get(character["record_saved"]).datetime
    c.modified = arrow.get(character["record_updated"]).datetime
    c.slug = get_character_slug(c.name)
    c.species = HTMLParser.HTMLParser().unescape(character["field_24"].encode("latin1"))
    c.appearance = character["field_34"].encode("latin1")
    c.personality = character["field_21"].encode("latin1")
    c.backstory = character["field_22"].encode("latin1")
    c.other = character["field_26"].encode("latin1")
    c.save()
    
    #Create avatar attachment
    legacy_avatar = character["field_43"].encode("latin1").strip()
    if legacy_avatar != "":
        attach = Attachment()
        attach.path = legacy_avatar
        attach.mimetype = mimetypes.guess_type(legacy_avatar)[0]
        if attach.mimetype == None:
            attach.mimetype = "Unknown."
        attach.extension = attach.path.split(".")[-1]
        if attach.extension not in ["png", "gif", "jpg", "jpeg"]:
            continue
        filesystem_path = os.path.join(os.getcwd(), "woe/static/uploads", legacy_avatar)
        try:
            image = Image(filename=filesystem_path)
            image_blob = image.make_blob()
        except:
            continue
        attach.size_in_bytes = len(image_blob)
        attach.created_date = c.created
        attach.owner = c.creator
        attach.owner_name = c.creator.login_name
        attach.alt = legacy_avatar
        attach.x_size = image.width
        attach.y_size = image.height
        attach.character = c
        attach.character_emote = True
        attach.character_gallery = True
        attach.character_name = c.name
        attach.save()
        c.default_avatar = attach

    legacy_gallery_field = character["field_27"].encode("latin1").strip()
    if legacy_gallery_field != "":
        attach = Attachment()
        attach.path = legacy_gallery_field
        attach.mimetype = mimetypes.guess_type(legacy_gallery_field)[0]
        if attach.mimetype == None:
            attach.mimetype = "Unknown."
        attach.extension = attach.path.split(".")[-1]
        if attach.extension not in ["png", "gif", "jpg", "jpeg"]:
            continue
        filesystem_path = os.path.join(os.getcwd(), "woe/static/uploads", legacy_gallery_field)
        try:
            image = Image(filename=filesystem_path)
            image_blob = image.make_blob()
        except:
            continue
        attach.size_in_bytes = len(image_blob)
        attach.created_date = c.created
        attach.owner = c.creator
        attach.owner_name = c.creator.login_name
        attach.alt = legacy_gallery_field
        attach.x_size = image.width
        attach.y_size = image.height
        attach.character = c
        attach.character_emote = False
        attach.character_gallery = True
        attach.character_name = c.name
        attach.save()
        c.default_gallery_image = attach
    
    posts = Post.objects(Q(html__contains="[postcharacter=%s|" % (c.old_character_id,)) | Q(html__contains="[postcharacter=%s]" % (c.old_character_id,)) | Q(html__contains="[character=%s]" % (c.old_character_id,)) | Q(html__contains="[character=%s|" % (c.old_character_id,)))
    
    for post in posts:
        post_html = blockquote_re.sub("", post.html)
        
        if post.author != c.creator:
            continue
        
        try:
            post_html.index("character=")
            if post.topic not in c.roleplays:
                c.roleplays.append(post.topic)
            c.posts.append(post)
        except:
            pass
            
    c.post_count = len(c.posts)
    c.save()
    
    for post in posts:            
        post.data["character"] = str(c.pk)
        post.save()
    