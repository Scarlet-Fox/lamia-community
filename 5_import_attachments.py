import MySQLdb
import MySQLdb.cursors
from woe.models.core import User, Attachment
from woe.models.forum import Post
import mimetypes, arrow, re
import hashlib
import json

settings_file = json.loads(open("config.json").read())

db = MySQLdb.connect(user=settings_file["woe_old_user"], db=settings_file["woe_old_db"], passwd=settings_file["woe_old_pass"], cursorclass=MySQLdb.cursors.DictCursor,charset='latin1',use_unicode=True)
c=db.cursor()
c.execute("select * from ipsattachments;")

for a in c.fetchall():
    attach = Attachment()
    attach.path = a["attach_location"].encode("latin1")
    attach.mimetype = mimetypes.guess_type(a["attach_location"])[0]
    if attach.mimetype == None:
        continue
    attach.extension = a["attach_ext"].encode("latin1")
    if attach.extension not in ["zip", "png", "gif", "jpg", "jpeg", "mp3"]:
        continue
    attach.size_in_bytes = a["attach_filesize"]
    attach.created_date = arrow.get(a["attach_date"]).replace(hours=-12).datetime
    try:
        attach.owner = User.objects(old_member_id=a["attach_member_id"])[0]
        attach.owner_name = attach.owner.login_name
    except IndexError:
        continue

    attach.alt = a["attach_file"]
    attach.old_ipb_id = a["attach_id"]
    attach.x_size = int(a["attach_img_width"])
    attach.y_size = int(a["attach_img_height"])
    attach.save()
c.close()

for a in Attachment.objects():
    try:
        post = Post.objects(html__contains="[attachment=%s:" % a.old_ipb_id)[0]
    except:
        continue
    
    html = post.html
    attachment_tags = re.findall("(\[attachment=(\d+).*?\])", post.html)
    for result in attachment_tags:
        html = html.replace(result[0],"[attachment=%s:%s]" % (str(a.pk), a.x_size))
        
    post.update(html=html)
    a.update(inc__used_in=1)