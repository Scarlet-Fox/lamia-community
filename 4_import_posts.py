import MySQLdb
import MySQLdb.cursors
from woe.models.core import User
from woe.models.forum import Post, Category, Topic, PostHistory
import arrow, os, shutil
from PIL import Image

db = MySQLdb.connect(user="root", db="woe", cursorclass=MySQLdb.cursors.DictCursor,charset='latin1',use_unicode=True)
c=db.cursor()
c.execute("select * from ipsposts limit 100;")

for p in c.fetchall():
    post = Post()
    try:
        post.topic = Topic.objects(old_ipb_id=p["topic_id"])[0]
    except IndexError:
        continue

    post.topic_name = post.topic.title
    post.html = p["post"].encode("latin1")
    post.author = User.objects(old_member_id=p["author_id"])[0]
    post.author_name = post.author.login_name
    post.created = arrow.get(p["post_date"]).replace(hours=-12).datetime
    post.old_ipb_id = p["pid"]
    if int(p["queued"]) != 0:
        post.hidden = True
    else:
        post.hidden = False
    post.save()
    
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
    
for topic in Topic.objects():
    topic_posts = Post.objects(topic=topic)
    topic.post_count = len(topic_posts)
    try:
        recent_post = topic_posts[len(topic_posts)-1]
    except IndexError:
        continue
    topic.last_post_by = recent_post.author
    topic.last_post_date = recent_post.created
    topic.last_post_author_avatar = recent_post.author.get_avatar_url("40")
    
    post_counts = {} #u.pk: count
    
    for post in topic_posts:
        if not post_counts.has_key(str(post.author.pk):
            post_counts[str(post.author.pk)] = 0
            
        post_counts[str(post.author.pk)] += 1
        
    topic.user_post_counts = post_counts
    topic.save()
    
for category in Category.objects():
    try:
        category_most_recent_topic = Topic.objects(category=category).order_by("-last_post_date")[0]
    except IndexError:
        continue
    category.last_topic_name = category_most_recent_topic.title
    category.last_post_by = category_most_recent_topic.last_post_by
    category.last_post_date = category_most_recent_topic.last_post_date
    category.last_post_author_avatar = category_most_recent_topic.last_post_author_avatar
    
    category.save()