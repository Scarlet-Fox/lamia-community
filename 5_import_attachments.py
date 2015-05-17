import MySQLdb
import MySQLdb.cursors
from woe.models.core import User, Attachment
from woe.models.forum import Post
import mimetypes, arrow

db = MySQLdb.connect(user="root", db="woe", cursorclass=MySQLdb.cursors.DictCursor,charset='latin1',use_unicode=True)
c=db.cursor()
c.execute("select * from ipsposts;")

for a in c.fetchall():
    attach = Attachment()
    attach.path = a["attach_location"]
    attach.mimetype = mimetypes.guesstype(a["attach_location"])
    attach.extension = attach_ext
    if attach.extension not in ["zip", "png", "gif", "jpg", "jpeg", "mp3"]:
        continue
    attach.size_in_bytes = a["attach_filesize"]
    attach.created_date = arrow.get(p["post_date"]).replace(hours=-12).datetime
    attach.owner = User.objects(old_ipb_id=p["attach_member_id"])[0]
    attach.old_ipb_id = a["attach_id"]
    attach.save()
    
for a in Attachment.objects():
    