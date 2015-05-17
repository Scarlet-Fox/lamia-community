import MySQLdb
import MySQLdb.cursors
from woe.models.core import User, Attachment
from woe.models.forum import Post
import mimetypes, arrow, re

db = MySQLdb.connect(user="root", db="woe", cursorclass=MySQLdb.cursors.DictCursor,charset='latin1',use_unicode=True)
c=db.cursor()
c.execute("select * from ipsattachments;")

for a in c.fetchall():
    attach = Attachment()
    attach.path = a["attach_location"]
    attach.mimetype = mimetypes.guess_type(a["attach_location"])[0]
    if attach.mimetype == None:
        continue
    attach.extension = a["attach_ext"]
    if attach.extension not in ["zip", "png", "gif", "jpg", "jpeg", "mp3"]:
        continue
    attach.size_in_bytes = a["attach_filesize"]
    attach.created_date = arrow.get(a["attach_date"]).replace(hours=-12).datetime
    try:
        attach.owner = User.objects(old_member_id=a["attach_member_id"])[0]
        attach.owner_name = attach.owner.login_name
    except IndexError:
        continue
    attach.old_ipb_id = a["attach_id"]
    attach.save()
    
for a in Attachment.objects():
    try:
        post = Post.objects(html__contains="[attachment=%s:" % a.old_ipb_id)[0]
    except:
        continue
    
    html = post.html
    attachment_tags = re.findall("(\[attachment=(\d+).*\])", post.html)
    for result in attachment_tags:
        html = html.replace(result[0],"[attachment=%s]" % (str(a.pk), ))
        
    post.update(html=html)
    a.update(add_to_set__present_in=post)
    a.update(inc__used_in=1)