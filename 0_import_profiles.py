import MySQLdb
import MySQLdb.cursors
from woe.models.core import User
import arrow, os, shutil
from wand.image import Image
import phpserialize
import HTMLParser
import json
settings_file = json.loads(open("config.json").read())

db = MySQLdb.connect(user=settings_file["woe_old_user"], db=settings_file["woe_old_db"], passwd=settings_file["woe_old_pass"], cursorclass=MySQLdb.cursors.DictCursor,charset='latin1',use_unicode=True)
c=db.cursor()
c.execute("select * from ipsmembers m left join ipsprofile_portal p ON m.member_id=p.pp_member_id;")

blocks = {}


for u in c.fetchall():
    try:
        blocks[u["member_id"]] = phpserialize.loads(u["ignored_users"])
    except:
        blocks[u["member_id"]] = {}
    m = User()
    m.login_name = HTMLParser.HTMLParser().unescape(u["members_l_username"].encode("latin1"))
    m.display_name = HTMLParser.HTMLParser().unescape(u["members_display_name"].encode("latin1"))
    m.birth_d = u["bday_day"]
    m.birth_m = u["bday_month"]
    m.birth_y = u["bday_year"]
    m.old_member_id = u["member_id"]
    m.email_address = u["email"]
    m.about_me = u["pp_about_me"].encode("latin1")
    m.joined = arrow.get(u["joined"]).datetime
    m.legacy_password = True
    m.ipb_salt = u["members_pass_salt"]
    m.ipb_hash = u["members_pass_hash"]
    if u["member_banned"] == 1:
        m.banned = True
    else:
        m.banned = False
        
    if m.login_name == "luminescence" or m.login_name == "zoop":
        m.is_admin = True
        m.is_mod = True
    
    try:
        m.title = HTMLParser.HTMLParser().unescape(u["title"].encode("latin1"))
    except:
        try:
            m.title = u["title"].encode("latin1")
        except:
            m.title = ""
    timestamp = str(arrow.utcnow().timestamp) + "_"
    m.set_password(str(timestamp)+str(arrow.utcnow().timestamp),3)
    m.validated = True
    m.save()
    
    old_avatar_location = os.path.join(settings_file["woe_ipb_avatar_dir"],u["pp_main_photo"])
    new_avatar_dir = os.path.join(os.getcwd(),"woe/static/avatars/")
    
    if os.path.isfile(old_avatar_location):
        extension = "." + u["pp_main_photo"].split(".")[-1]
        shutil.copyfile(old_avatar_location, os.path.join(new_avatar_dir,timestamp+str(m.pk)+extension))
        image = Image(filename=old_avatar_location)
        xsize = image.width
        ysize = image.height
        
        resize_measure = min(40.0/float(xsize),40.0/float(ysize))
        fourty_image = image.clone()
        fourty_image.resize(int(round(xsize*resize_measure)),int(round(ysize*resize_measure))) 
        fourty_image.save(filename=os.path.join(new_avatar_dir,timestamp+str(m.pk)+"_40"+extension))
        
        resize_measure = min(60.0/float(xsize),60.0/float(ysize))
        sixty_image = image.clone()
        sixty_image.resize(int(round(xsize*resize_measure)),int(round(ysize*resize_measure))) 
        sixty_image.save(filename=os.path.join(new_avatar_dir,timestamp+str(m.pk)+"_60"+extension))
        
        m.avatar_extension = extension
        m.avatar_timestamp = timestamp
        m.avatar_full_x, m.avatar_full_y = image.size
        m.avatar_40_x, m.avatar_40_y = fourty_image.size
        m.avatar_60_x, m.avatar_60_y = sixty_image.size

        m.save()
        
for u in User.objects():
    user_blocks = blocks.get(u.old_member_id,{})
    for user in user_blocks.keys():
        blocked_user = User.objects(old_member_id=user)[0]
        blocks_against_user = user_blocks[user]
        
        if blocks_against_user.get("ignore_topics") == "1" or blocks_against_user.get("ignore_messages") == "1":
            u.ignored_users.append(blocked_user)
            
        if blocks_against_user.get("ignore_signatures") == "1":
            u.ignored_user_signatures.append(blocked_user)
    
    u.save()
    
c.close()