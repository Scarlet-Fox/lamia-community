import MySQLdb	
import MySQLdb.cursors
import sys
sys.path.append('.')
from woe.sqlmodels import *
from woe import sqla
from slugify import slugify
import arrow, os, shutil	
from wand.image import Image	
from sqlalchemy.exc import IntegrityError
import phpserialize	
import HTMLParser	
import json

def find_user_slug(_name):
    slug = slugify(_name, max_length=100, word_boundary=True, save_order=True)
    if slug.strip() == "":
        slug="_"

    def try_slug(slug, count=0):
        new_slug = slug
        if count > 0:
            new_slug = slug+"-"+str(count)

        if len(User.query.filter_by(my_url=new_slug).all()) == 0:
            return new_slug
        else:
            return try_slug(slug, count+1)

    return try_slug(slug)
    
def find_user_display_name_slug(_name):
    slug = _name

    def try_slug(slug, count=0):
        new_slug = slug
        if count > 0:
            new_slug = slug+"-"+str(count)

        if len(User.query.filter_by(display_name=new_slug).all()) == 0:
            return new_slug
        else:
            return try_slug(slug, count+1)

    return try_slug(slug)
    
def find_login_display_name_slug(_name):
    slug = _name

    def try_slug(slug, count=0):
        new_slug = slug
        if count > 0:
            new_slug = slug+"-"+str(count)

        if len(User.query.filter_by(login_name=new_slug).all()) == 0:
            return new_slug
        else:
            return try_slug(slug, count+1)

    return try_slug(slug)

def find_user_email_address_slug(_name):
    slug = _name

    def try_slug(slug, count=0):
        new_slug = slug
        if count > 0:
            new_slug = slug+"-"+str(count)

        if len(User.query.filter_by(email_address=new_slug).all()) == 0:
            return new_slug
        else:
            return try_slug(slug, count+1)

    return try_slug(slug)

settings_file = json.loads(open("config.json").read())	

db = MySQLdb.connect(
        user=settings_file["import_db_user"], 
        db=settings_file["import_db_name"], 
        passwd=settings_file["import_db_password"], 
        cursorclass=MySQLdb.cursors.DictCursor,
        charset='latin1',
        use_unicode=True
    )

c=db.cursor()
c.execute(
    """
        SELECT * FROM wcf1_user u
        LEFT JOIN wcf1_user_option_value ufo ON u.userID = ufo.userID
        ORDER BY u.lastActivityTime desc;
    """
)

for u in c.fetchall():
    user_dictionary = {}
    user_dictionary["Skype"] = u["userOption11"]
    user_dictionary["Icq"] = u["userOption10"]
    user_dictionary["Facebook"] = u["userOption12"]
    user_dictionary["Twitter"] = u["userOption13"]
    user_dictionary["Googleplus"] = u["userOption14"]
    user_dictionary["Homepage"] = u["userOption9"]
        
    new_user = User(
        joined = arrow.get(u["registrationDate"]).datetime,
        title = u["userTitle"],
        about_me = u["userOption1"],
        location = u["userOption5"],
        admin_comment = u["userOption8"]
    )
    
    if not ":" in u["password"][0:5]:
        new_user.password_hash = "bb4~"+u["password"]
    else:
        new_user.password_hash = u["password"].replace(":","~",1)
    
    new_user.my_url = find_user_slug(u["username"].strip().lower())
    new_user.display_name = find_user_display_name_slug(u["username"])
    new_user.email_address = find_user_email_address_slug(u["email"])
    new_user.login_name = find_login_display_name_slug(u["username"].strip().lower())
    new_user.legacy_id = int(u["userID"])
    
    try:
        new_user.birthday = arrow.get(u["userOption2"]).replace(days=1).datetime
    except:
        pass # fuck that
    
    new_user.validated = True
    
    if u["banned"] == 0:
        new_user.banned = False
    else: 
        new_user.banned = True
        
    if u["userOption15"]:
        new_user.time_zone = u["userOption15"]
        
    if u["userOption6"]:
        new_user.about_me = new_user.about_me + "<br><br><h3>Occupation</h3>" + u["userOption6"]
        
    if u["userOption7"]:
        new_user.about_me = new_user.about_me + "<br><br><h3>Hobbies</h3>" + u["userOption7"]
    
    user_data = {}
    user_data["my_fields"] = []
    
    for k, v in user_dictionary.items():
        user_data["my_fields"].append([k, v])
        
    new_user.data = user_data
    
    try:
        sqla.session.add(new_user)
        sqla.session.commit()
    except IntegrityError as e:
        sqla.session.rollback()
        print str(u["userID"])+"-"+u["username"]
        print e
        continue
        print 
        print
    
    if u["signature"]:
        if u["signature"].strip() != "":
            sig = Signature(
                owner=new_user,
                owner_name=new_user.display_name,
                name="Imported",
                html=u["signature"],
                created=arrow.utcnow().datetime.replace(tzinfo=None),
                active=True
            )
        
            sqla.session.add(sig)
            sqla.session.commit()
        