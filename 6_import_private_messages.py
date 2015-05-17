import MySQLdb, arrow
import MySQLdb.cursors
from woe.models.core import User, PrivateMessageTopic, PrivateMessageParticipant, PrivateMessage

db = MySQLdb.connect(user="root", db="woe", cursorclass=MySQLdb.cursors.DictCursor,charset='latin1',use_unicode=True)

c=db.cursor()
c.execute("select * from ipsmessage_topics;")
for msg in c.fetchall():
    topic = PrivateMessageTopic()
    topic.title = msg["mt_title"].encode("latin1")
    topic.creator = User.objects(old_member_id=msg["mt_starter_id"])[0]
    topic.creator_name = User.objects(old_member_id=msg["mt_starter_id"])[0].login_name
    topic.created = arrow.get(msg["mt_start_time"]).replace(hours=-12).datetime
    topic.old_ipb_id = msg["mt_id"]
    topic.save()
c.close()

msg_cursor = db.cursor()
msg_cursor.execute("select * from ipsmessage_posts order by msg_date")
for reply in msg_cursor.fetchall():
    topic = PrivateMessageTopic.objects(old_ipb_id=reply["msg_topic_id"])[0]
    m = PrivateMessage()
    m.message = reply["msg_post"].encode("latin1")
    m.author = User.objects(old_member_id=reply["msg_author_id"])[0]
    m.created = arrow.get(reply["msg_date"]).replace(hours=-12).datetime
    m.author_name = m.author.login_name
    m.topic = topic
    m.topic_name = topic.title
    m.topic_creator_name = topic.creator_name
    m.save()
    
    topic.update(last_reply_by=m.author)
    topic.update(last_reply_name=m.author.login_name)
    topic.update(last_reply_time=m.created)
    topic.update(inc__message_count=1)
msg_cursor.close()
    
peep = db.cursor()
peep.execute("select * from ipsmessage_topic_user_map")
for p in peep.fetchall():
    topic = PrivateMessageTopic.objects(old_ipb_id=p["map_topic_id"])
    participant = PrivateMessageParticipant()
    participant.user = User.objects(old_member_id=p["map_user_id"])[0]
    if p["map_user_active"] == "0":
        participant.left_pm = True
    participant.last_read = arrow.get(p["map_read_time"]).replace(hours=-12).datetime
    topic.update(add_to_set__participants=participant)
    topic.update(inc__participant_count=1)
peep.close()
    