import MySQLdb
import MySQLdb.cursors
from woe.models.core import User
from woe.models.forum import Post, Category, Topic, PostHistory
import arrow, os, shutil
from PIL import Image

db = MySQLdb.connect(user="root", db="woe", cursorclass=MySQLdb.cursors.DictCursor,charset='latin1',use_unicode=True)
c=db.cursor()
c.execute("select * from ipsposts limit 1000;")

for p in c.fetchall():
    post = Post()
    try:
        post.topic = Topic.objects(old_ipb_id=p["topic_id"])[0]
    except IndexError:
        continue
        
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
