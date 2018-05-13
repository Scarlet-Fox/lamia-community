import MySQLdb
import MySQLdb.cursors
from woe.models.core import User
from woe.models.forum import Post, Category, Topic, PostHistory
import arrow, os, shutil
from PIL import Image
import json, re
settings_file = json.loads(open("config.json").read())

db = MySQLdb.connect(user=settings_file["ipb_import_user"], db=settings_file["ipb_import_db"], passwd=settings_file["ipb_import_pass"], cursorclass=MySQLdb.cursors.DictCursor,charset='latin1',use_unicode=True)
c=db.cursor()
c.execute("select * from ipsposts;")

url_bbcode_re = re.compile("(\[url\](.*?)\[\/url\])")
url_bbcode_re_variant = re.compile("(\[url=(.*?)\](.*?)\[\/url\])")

for p in c.fetchall():
    post = Post()
    try:
        post.topic = Topic.objects(old_ipb_id=p["topic_id"])[0]
    except IndexError:
        continue

    post.topic_name = post.topic.title
    post.html = p["post"].encode("latin1")
    
    urls = url_bbcode_re.findall(post.html)
    for url in urls:
        post.html = post.html.replace(url[0], """<a href="%s">%s</a>""" % (url[1], url[1]))
    
    urls = url_bbcode_re_variant.findall(post.html)
    for url in urls:
        post.html = post.html.replace(url[0], """<a href="%s">%s</a>""" % (url[1], url[2]))
        
    post.author = User.objects(old_member_id=p["author_id"])[0]
    post.author_name = post.author.login_name
    post.created = arrow.get(p["post_date"]).replace(hours=-12).datetime
    post.old_ipb_id = p["pid"]
    if int(p["queued"]) != 0:
        post.hidden = True
    else:
        post.hidden = False
    post.save()
    
c.close()
    
likes_c = db.cursor()
likes_c.execute("select * from ipsreputation_index where type='pid';")
for l in likes_c.fetchall():
    try:
        post = Post.objects(old_ipb_id=l["type_id"])[0]
    except IndexError:
        continue
    user = User.objects(old_member_id=l["member_id"])[0]
    post.update(add_to_set__boops=user)
    post.update(inc__boop_count=1)
likes_c.close()
  
history_c = db.cursor()
history_c.execute("select * from ipspost_history;")
for h in history_c.fetchall():
    try:
        post = Post.objects(old_ipb_id=h["pid"])[0]
    except IndexError:
        continue
    history = PostHistory()
    history.creator = post.author
    history.created = arrow.get(h["post_date"]).replace(hours=-12).datetime
    history.html = h["post"].encode("latin1")
    post.update(add_to_set__history=history)
history_c.close()
 
for topic in Topic.objects():
    topic_posts = Post.objects(topic=topic)
    topic.post_count = Post.objects(topic=topic, hidden=False).count()
    try:
        recent_post = Post.objects(topic=topic).order_by("-created")[0]
    except IndexError:
        continue
    try:
        topic.first_post = Post.objects(topic=topic, hidden=False).order_by("created")[0]
    except IndexError:
        continue
    topic.last_post_by = recent_post.author
    topic.last_post_date = recent_post.created
    topic.last_post_author_avatar = recent_post.author.get_avatar_url("60")
    
    post_counts = {} #u.pk: count
    
    for post in topic_posts:
        if not post_counts.has_key(str(post.author.pk)):
            post_counts[str(post.author.pk)] = 0
            
        post_counts[str(post.author.pk)] += 1
        
    topic.user_post_counts = post_counts
    topic.save()
    
for category in Category.objects():
    try:
        category_most_recent_topic = Topic.objects(category=category).order_by("-last_post_date")[0]
    except IndexError:
        continue
    category.last_topic = category_most_recent_topic
    category.last_topic_name = category_most_recent_topic.title
    category.last_post_by = category_most_recent_topic.last_post_by
    category.last_post_date = category_most_recent_topic.last_post_date
    category.last_post_author_avatar = category_most_recent_topic.last_post_author_avatar
    category.post_count = sum(Topic.objects(category=category).scalar("post_count"))
    
    category.save()
    
for u in User.objects():
    u.update(post_count=Post.objects(author=u).count())
    u.update(topic_count=Topic.objects(creator=u).count())
    