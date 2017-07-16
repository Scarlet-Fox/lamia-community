from woe import sqla
from woe.sqlmodels import *
import woe.sqlmodels as sqlm
from sqlalchemy.orm.attributes import flag_modified
from woe.parsers import emoticon_codes
from woe.utilities import strip_tags

sqla.session.query(sqlm.TopTen).delete()

def pack_into_db(users, counts, name):
    topten = sqlm.TopTen()
    topten.name = name
    topten.users = users
    topten.counts = counts
    
    sqla.session.add(topten)
    sqla.session.commit()
    
    print name + ": " + str(topten.counts)
    print

posts = list(sqla.session.query(sqlm.Post).filter(sqlm.Post.hidden==False).all())
post_frequency = {}
post_users = []
word_frequency = {}
word_users = []

for post in posts:
    if post_frequency.has_key(post.author.login_name):
        post_frequency[post.author.login_name] += 1
    else:
        post_frequency[post.author.login_name] = 1
        
    if word_frequency.has_key(post.author.login_name):
        word_frequency[post.author.login_name] += len(strip_tags(post.html))
    else:
        word_frequency[post.author.login_name] = len(strip_tags(post.html))

post_users = post_frequency.keys()
post_users = sorted(post_users, key=lambda x: post_frequency[x], reverse=True)
pack_into_db(post_users, post_frequency, "post_count")

word_users = word_frequency.keys()
word_users = sorted(word_users, key=lambda x: word_frequency[x], reverse=True)
pack_into_db(word_users, word_frequency, "word_count")
# Save

topics = list(sqla.session.query(sqlm.Topic).filter(sqlm.Topic.hidden==False).all())
topic_frequency = {}
topic_users = []

for topic in topics:
    if topic_frequency.has_key(topic.author.login_name):
        topic_frequency[topic.author.login_name] += 1
    else:
        topic_frequency[topic.author.login_name] = 1

topic_users = topic_frequency.keys()
topic_users = sorted(topic_users, key=lambda x: topic_frequency[x], reverse=True)
pack_into_db(topic_users, topic_frequency, "topic_count")

# Save

updates = list(sqla.session.query(sqlm.StatusUpdate).filter(sqlm.StatusUpdate.hidden==False).all())
update_frequency = {}
update_users = []

for update in updates:
    if update_frequency.has_key(update.author.login_name):
        update_frequency[update.author.login_name] += 1
    else:
        update_frequency[update.author.login_name] = 1

update_users = update_frequency.keys()
update_users = sorted(update_users, key=lambda x: update_frequency[x], reverse=True)
pack_into_db(update_users, update_frequency, "status_count")

# Save

comments = list(sqla.session.query(sqlm.StatusComment).filter(sqlm.StatusComment.hidden==False).all())
comment_frequency = {}
comment_users = []

for comment in comments:
    if comment_frequency.has_key(comment.author.login_name):
        comment_frequency[comment.author.login_name] += 1
    else:
        comment_frequency[comment.author.login_name] = 1

comment_users = comment_frequency.keys()
comment_users = sorted(comment_users, key=lambda x: comment_frequency[x], reverse=True)
pack_into_db(comment_users, comment_frequency, "status_comments_count")

# Save

boops_given_frequency = {}
boops_given_users = []
boops_received_frequency = {}
boops_received_users = []

for user in list(sqla.session.query(sqlm.User).filter(sqlm.User.banned==False).all()):
    boops_given = sqla.session.query(sqlm.post_boop_table).filter(sqlm.post_boop_table.c.user_id == user.id).count()
    boops_received = sqla.session.query(sqlm.post_boop_table) \
        .join(sqlm.Post) \
        .filter(sqlm.Post.author == user) \
        .count()
    
    boops_given_users.append(user.login_name)
    boops_given_frequency[user.login_name] = boops_given
    boops_received_users.append(user.login_name)
    boops_received_frequency[user.login_name] = boops_received

boops_received_users = sorted(boops_received_users, key=lambda x: boops_received_frequency[x], reverse=True)
boops_given_users = sorted(boops_given_users, key=lambda x: boops_given_frequency[x], reverse=True)

pack_into_db(boops_received_users, boops_received_frequency, "boops_received")
pack_into_db(boops_given_users, boops_given_frequency, "boops_given")

# Save




