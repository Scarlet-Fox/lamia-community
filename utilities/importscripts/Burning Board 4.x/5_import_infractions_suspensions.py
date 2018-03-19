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
        SELECT * FROM 
        zuforum.wcf1_user_infraction_warning
    """
)

warning_ids = {}

for i in c.fetchall():
    new_infraction = Infraction(
        title = i["title"],
        explanation = i["reason"],
        points = int(i["points"]),
        created = arrow.get(i["time"]).datetime,
        author = User.query.filter_by(legacy_id=int(i["judgeID"]))[0],
        recipient = User.query.filter_by(legacy_id=int(i["userID"]))[0],
    )
    
    expires = int(i["expires"])
    
    if expires == 0:
        new_infraction.forever = True
    else:
        new_infraction.forever = False
        new_infraction.expires = arrow.get(i["expires"]).datetime

    sqla.session.add(new_infraction)
    sqla.session.commit()
    
    warning_ids[int(i["userWarningID"])] = new_infraction.id
    
    

c=db.cursor()
c.execute(
    """
        SELECT * FROM 
        zuforum.wcf1_user_infraction_suspension
    """
)

for s in c.fetchall():
    new_suspension = Ban(
        recipient = User.query.filter_by(legacy_id=int(s["userID"]))[0],
        explanation = "Imported.",
        created = arrow.get(s["time"]).datetime
    )
    
    expires = int(i["expires"])
    
    if s["warningID"] != None:
        new_suspension = Infraction.query.filter_by(id=warning_ids[int(s["warningID"])])[0]
    else:
        new_suspension = None
    
    if expires == 0:
        new_suspension.forever = True
    else:
        new_suspension.forever = False
        new_suspension.expires = arrow.get(s["expires"]).datetime
        
    sqla.session.add(new_suspension)
    sqla.session.commit()