import MySQLdb
import MySQLdb.cursors
from woe.models.core import User, StatusUpdate, StatusComment
import arrow

db = MySQLdb.connect(user="root", db="woe", cursorclass=MySQLdb.cursors.DictCursor,charset='latin1',use_unicode=True)
c=db.cursor()
c.execute("select * from ipsmember_status_updates;")

user_status_count = {}
user_comment_count = {}

for s in c.fetchall():
    status = StatusUpdate()
    
    if s["status_member_id"] != s["status_author_id"]:
        status.attached_to_user = User.objects(old_member_id=s["status_member_id"])[0]
        status.attached_to_user_name = status.attached_to_user.login_name
    
    status.author = User.objects(old_member_id=s["status_author_id"])[0]
    status.author_name = status.author.login_name
    
    if not user_status_count.has_key(status.author):
        user_status_count[status.author] = 1
    else:
        user_status_count[status.author] += 1
    
    status.message = s["status_content"].encode("latin1")
    status.created = arrow.get(s["status_date"]).datetime
    status.old_ipb_id = s["status_id"]
    
    status_reply_cursor = db.cursor()
    status_reply_cursor.execute("select * from ipsmember_status_replies where reply_status_id=%s", [status.old_ipb_id,])
    participants = {status.author: 1}
    
    for status_reply in status_reply_cursor.fetchall():
        comment = StatusComment()
        comment.text = status_reply["reply_content"].encode("latin1")
        comment.created = arrow.get(status_reply["reply_date"]).datetime
        comment.author = User.objects(old_member_id=status_reply["reply_member_id"])[0]
        if not user_comment_count.has_key(comment.author):
            user_comment_count[comment.author] = 1
        else:
            user_comment_count[comment.author] += 1
        participants[comment.author] = 1
        status.comments.append(comment)
    
    status.replies = len(status.comments)
    status.participant_count = len(participants.keys())
    status.save()

for u in user_status_count.keys():
    u = User.objects(pk=u.pk)
    u.status_count = user_status_count[u]
    u.save()
    
for u in user_comment_count.keys():
    u = User.objects(pk=u.pk)
    u.status_comment_count = user_comment_count[u]
    u.save()