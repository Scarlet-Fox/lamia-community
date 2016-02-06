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

import htmllib

def unescape(s):
    p = htmllib.HTMLParser(None)
    p.save_bgn()
    p.feed(s)
    return p.save_end()

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
    new_blog.name = unescape(b["blog_name"].encode("latin1"))
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
    
blog_entry_cursor = db.cursor()
blog_entry_cursor.execute("select * from ipsblog_entries;")
blog_entries = blog_entry_cursor.fetchall()

def get_blog_entry_slug(title, blog):
    slug = slugify(title, max_length=100, word_boundary=True, save_order=True)
    
    def try_slug(slug, count=0):
        new_slug = slug
        if count > 0:
            new_slug = slug+"-"+str(count)
            
        if len(BlogEntry.objects(slug=new_slug, blog=blog)) == 0:
            return new_slug
        else:
            return try_slug(slug, count+1)
    
    return try_slug(slug)

for e in blog_entries:
    new_entry = BlogEntry()
    new_entry.blog = Blog.objects(old_ipb_id=e["blog_id"])[0]
    new_entry.title = unescape(e["entry_name"].encode("latin1"))
    new_entry.slug = get_blog_entry_slug(new_entry.title, new_entry.blog)
    new_entry.html = e["entry"].encode("latin1")
    new_entry.author = User.objects(old_member_id=e["entry_author_id"])[0]
    new_entry.author_name = new_entry.author.login_name
    new_entry.old_ipb_id = e["entry_id"]
    new_entry.blog_name = new_entry.blog.name
    new_entry.created = arrow.get(e["entry_date"]).replace(hours=-12).datetime
    new_entry.edited = arrow.get(e["entry_edit_time"]).replace(hours=-12).datetime
    new_entry.view_count = e["entry_views"]
    
    if e["entry_status"] == "published":
        new_entry.draft = False
        new_entry.published = new_entry.created
    
    if e["entry_locked"] == 1:
        new_entry.locked = True
    
    new_entry.save()
    
blog_comments_cursor = db.cursor()
blog_comments_cursor.execute("select * from ipsblog_comments;")
blog_comments = blog_comments_cursor.fetchall()
    
for c in blog_comments:
    new_comment = BlogComment()
    new_comment.html = c["comment_text"].encode("latin1")
    new_comment.author = User.objects(old_member_id=c["member_id"])[0]
    new_comment.author_name = new_entry.author.login_name
    try:
        new_comment.blog_entry = BlogEntry.objects(old_ipb_id=c["entry_id"])[0]
    except:
        pass
    new_comment.blog_entry_name = new_comment.blog_entry.title
    new_comment.blog = new_comment.blog_entry.blog
    new_comment.blog_name = new_comment.blog.name
    new_comment.created = arrow.get(c["comment_date"]).replace(hours=-12).datetime
    new_comment.save()
    
for blog in Blog.objects():
    try:
        blog.last_entry = BlogEntry.objects(blog=blog, draft=False, published__ne=None).order_by("-created")[0]
        blog.last_entry_date = blog.last_entry.created
    except:
        pass
    try:
        blog.last_comment = BlogComment.objects(blog=blog).order_by("-created")[0]
        blog.last_comment_date = blog.last_comment.created
    except:
        pass
    blog.comment_count = BlogComment.objects(blog=blog).count()
    blog.entry_count = BlogEntry.objects(blog=blog).count()
    blog.save()
    
for entry in BlogEntry.objects():
    entry.comment_count = BlogComment.objects(blog_entry=entry).count()
    try:
        entry.last_comment = BlogComment.objects(blog_entry=entry).order_by("-created")[0]
        entry.last_comment_date = entry.last_comment.created
    except:
        pass
    entry.save()
    
for a in Attachment.objects():
    try:
        entry = BlogEntry.objects(html__contains="[attachment=%s:" % a.old_ipb_id)[0]
    except:
        continue
    
    html = entry.html
    attachment_tags = re.findall("(\[attachment=(\d+).*?\])", entry.html)
    for result in attachment_tags:
        html = html.replace(result[0],"[attachment=%s:%s]" % (str(a.pk), a.x_size))
        
    entry.update(html=html)