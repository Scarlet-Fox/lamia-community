import MySQLdb
import MySQLdb.cursors
from woe.models.core import User
import arrow, os, shutil
from PIL import Image

db = MySQLdb.connect(user="root", db="woe", cursorclass=MySQLdb.cursors.DictCursor,charset='latin1',use_unicode=True)
c=db.cursor()
c.execute("select * from ipsmembers m left join ipsprofile_portal p ON m.member_id=p.pp_member_id;")

for u in c.fetchall():
    m = User()
    m.login_name = u["members_l_username"].encode("latin1")
    m.display_name = u["members_display_name"].encode("latin1")
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
        
    if m.login_name == "luminescence":
        m.is_admin = True
    
    try:
        m.title = u["title"].encode("latin1")
    except AttributeError:
        m.title = ""
    timestamp = str(arrow.utcnow().timestamp) + "_"
    m.set_password(str(timestamp)+str(arrow.utcnow().timestamp),3)
    m.validated = True
    m.save()
    
    old_avatar_location = os.path.join("/Users/Luminescence/Dropbox/WoE",u["pp_main_photo"])
    new_avatar_dir = "/Users/Luminescence/Documents/woe/woe/static/avatars/"
    
    if os.path.isfile(old_avatar_location):
        extension = "." + u["pp_main_photo"].split(".")[-1]
        shutil.copyfile(old_avatar_location, os.path.join(new_avatar_dir,timestamp+str(m.pk)+extension))
        image = Image.open(old_avatar_location)
        xsize, ysize = image.size
        
        resize_measure = min(40.0/float(xsize),40.0/float(ysize))
        fourty_image = image.copy()
        fourty_image.thumbnail([xsize*resize_measure,ysize*resize_measure]) 
        fourty_image.save(os.path.join(new_avatar_dir,timestamp+str(m.pk)+"_40"+extension))
        
        resize_measure = min(60.0/float(xsize),60.0/float(ysize))
        sixty_image = image.copy()
        sixty_image.thumbnail([xsize*resize_measure,ysize*resize_measure]) 
        sixty_image.save(os.path.join(new_avatar_dir,timestamp+str(m.pk)+"_60"+extension))
        
        m.avatar_extension = extension
        m.avatar_timestamp = timestamp
        m.avatar_full_x, m.avatar_full_y = image.size
        m.avatar_40_x, m.avatar_40_y = fourty_image.size
        m.avatar_60_x, m.avatar_60_y = sixty_image.size
        
        m.save()