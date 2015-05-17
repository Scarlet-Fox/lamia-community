import MySQLdb
import MySQLdb.cursors
from woe.models.forum import Topic, Category, Poll, PollChoice
from woe.models.core import User
from slugify import slugify
import HTMLParser
import arrow
from unidecode import unidecode
import phpserialize

db = MySQLdb.connect(user="root", db="woe", cursorclass=MySQLdb.cursors.DictCursor,charset='latin1',use_unicode=True)
c = db.cursor()
c.execute("select * from ipstopics;")
c = c.fetchall()
h = HTMLParser.HTMLParser()

def get_topic_slug(title):
    slug = slugify(title, max_length=100, word_boundary=True, save_order=True)
    
    def try_slug(slug, count=0):
        new_slug = slug
        if count > 0:
            new_slug = slug+"-"+str(count)
            
        if len(Topic.objects(slug=new_slug)) == 0:
            return new_slug
        else:
            return try_slug(slug, count+1)
    
    return try_slug(slug)
    
for t in c:
    topic = Topic()
    
    if len(Category.objects(old_ipb_id=t["forum_id"])) == 0:
        continue
    
    topic.category = Category.objects(old_ipb_id=t["forum_id"])[0] 
    topic.old_ipb_id = t["tid"]
    topic.title = t["title"].encode("latin1")
    topic.slug = get_topic_slug(topic.title)
    if t["state"] == "closed":
        topic.closed = True
    else: 
        topic.closed = False
    
    if t["approved"] == -1:
        topic.hidden = True
    else:
        topic.hidden = False
    
    if t["pinned"] == 1:
        topic.sticky = True
    else:
        topic.sticky = False
    
    topic.view_count = t["views"]
    
    topic.created = arrow.get(t["start_date"]).datetime
    topic.creator = User.objects(old_member_id=t["starter_id"])[0]
    topic.save()
    
    poll_cursor = db.cursor()
    poll_cursor.execute("select * from ipspolls where tid=%s;", [topic.old_ipb_id,])
    for poll in poll_cursor.fetchall():
        try:
            choices = poll["choices"].encode("latin1")
            poll_data = phpserialize.loads(str(choices), charset="latin1", decode_strings=True)
        except ValueError:
            continue
        
        for poll_data_group in poll_data.keys():
            poll_data_group_data = poll_data[poll_data_group]
            new_poll = Poll()            
            new_poll.poll_question = poll_data_group_data["question"]
            for choice in poll_data_group_data["choice"].values():
                new_poll.poll_options.append(choice)
            
            poll_votes = db.cursor()
            poll_votes.execute("select * from ipsvoters where tid=%s;", [topic.old_ipb_id,])
            for vote in poll_votes.fetchall():
                poll_vote_data = phpserialize.loads(vote["member_choices"], charset="latin1", decode_strings=True)
                poll_vote_user = User.objects(old_member_id=vote["member_id"])[0]
                
                try:
                    vote = PollChoice(user=poll_vote_user, choice=int(poll_vote_data[poll_data_group][0])-1)
                except KeyError:
                    continue
                new_poll.poll_votes.append(vote)
            
            topic.polls.append(new_poll)
        
    topic.save()
            
categories = Category.objects()
for cat in categories:
    topics = Topic.objects(category=cat)
    category_views = 0
    category_topics = 0
    for topic in topics:
        category_views += topic.view_count
        category_topics += 1
        
    cat.view_count = category_views
    cat.topic_count = category_topics
    cat.save()