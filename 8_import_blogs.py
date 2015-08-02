import MySQLdb, arrow
import MySQLdb.cursors
from woe.models.roleplay import Character
from woe.models.core import User, Attachment
from woe.models.blogs import *
import json, os, re, HTMLParser, mimetypes
from slugify import slugify
from wand.image import Image
from mongoengine.queryset import Q

settings_file = json.loads(open("config.json").read())
db = MySQLdb.connect(user=settings_file["woe_old_user"], db=settings_file["woe_old_db"], passwd=settings_file["woe_old_pass"], cursorclass=MySQLdb.cursors.DictCursor,charset='latin1',use_unicode=True)

blog_cursor = db.cursor()
blog_cursor.execute("select * from ipsblog_blogs;")
blogs = blog_cursor.fetchall()

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

for b in blogs:
    if b["blog_type"] != "local":
        continue
        
    new_blog = Blog()
    new_blog.creator = User.objects(old_member_id=b["member_id"])[0]
    new_blog.creator_name = new_blog.creator.login_name
    
    if new_blog.creator.banned:
        new_blog.disabled = True
    
    new_blog.old_ipb_id = b["blog_id"]
    try:
        new_blog.name = HTMLParser.HTMLParser().unescape(b["blog_name"].encode("latin1"))
    except:
        new_blog.name = b["blog_name"].encode("latin1")
    new_blog.description = b["blog_desc"].encode("latin1")
    new_blog.views = b["blog_num_views"]
    
    if b["blog_disabled"] == 1:
        new_blog.disabled = True
    
    if b["blog_owner_only"] == 1:
        new_blog.privacy_settings = "you"
    else:
        new_blog.privacy_settings = "members"
        
    new_blog.slug = get_blog_slug(new_blog.name)
        
    new_blog.save()