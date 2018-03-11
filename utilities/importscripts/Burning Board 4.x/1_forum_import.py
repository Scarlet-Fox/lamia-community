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

# IMPORT SECTIONS

c=db.cursor()
c.execute(
    """
        SELECT * FROM zuforum.wbb1_board 
        WHERE boardType = 1 AND parentID is null
        ORDER BY position asc
    """
)

for s in c.fetchall():
    new_section = Section(
        name = s["title"],
        slug = slugify(s["title"], max_length=100, word_boundary=True, save_order=True),
        weight = int(s["position"])*10
    )
    
    try:
        sqla.session.add(new_section)
        sqla.session.commit()
    except IntegrityError as e:
        sqla.session.rollback()
        continue

c.close()

# IMPORT BOARDS

c=db.cursor()
c.execute(
    """
        SELECT b.*,
        parent.title AS parent_title,
        parent.boardType AS parent_board_type
        FROM zuforum.wbb1_board b
        JOIN zuforum.wbb1_board parent ON b.parentID = parent.boardID
        WHERE b.boardType = 0 AND b.parentID IS NOT NULL
        ORDER BY b.position asc
    """
)

for _cat in c.fetchall():
    slug = slugify(_cat["title"], max_length=100, word_boundary=True, save_order=True)
    
    if slug.strip() == "":
        slug = "_"
        
    new_category = Category(
        name = _cat["title"],
        slug = slug,
        weight = int(_cat["position"])*10,
        restricted = True,
        description = _cat["description"],
    )
    
    if _cat["parent_board_type"] == 1:
        imported_section = Section.query.filter_by(
            slug=slugify(_cat["parent_title"], max_length=100, word_boundary=True, save_order=True)
            ).one()
        new_category.section = imported_section
        
    try:
        sqla.session.add(new_category)
        sqla.session.commit()
    except IntegrityError as e:
        sqla.session.rollback()
        continue

c.close()

# SETUP SUB-BOARDS

c=db.cursor()
c.execute(
    """
        SELECT b.*,
        parent.title AS parent_title,
        parent.boardType AS parent_board_type
        FROM zuforum.wbb1_board b
        JOIN zuforum.wbb1_board parent ON b.parentID = parent.boardID
        WHERE b.boardType = 0 AND b.parentID IS NOT NULL
        ORDER BY b.position asc
    """
)

for _cat in c.fetchall():
    slug = slugify(_cat["title"], max_length=100, word_boundary=True, save_order=True)
    
    if slug.strip() == "":
        slug = "_"
        
    new_category = Category.query.filter_by(
        slug = slug
    ).one()
    
    if _cat["parent_board_type"] == 0:
        imported_section = Category.query.filter_by(
            slug=slugify(_cat["parent_title"], max_length=100, word_boundary=True, save_order=True)
            ).one()
        new_category.parent = imported_section
        
    try:
        sqla.session.add(new_category)
        sqla.session.commit()
    except IntegrityError as e:
        sqla.session.rollback()
        continue

c.close()

# Add guest account
new_user = User(
    login_name = "_Guest Account_",
    my_url = "_guest_account_",
    display_name = "_Guest Account_",
    email_address = "@"
)
new_user.set_password("_guest_account_")
new_user.joined = arrow.utcnow().datetime
new_user.over_thirteeen = False
new_user.validated = False
new_user.how_did_you_find_us = "Guest Account for Import"

try:
    sqla.session.add(new_user)
    sqla.session.commit()
except:
    sqla.session.rollback()

# Add topics

c=db.cursor()
c.execute(
    """
        SELECT t.*,
        board.title AS board_name
        FROM zuforum.wbb1_thread t
        JOIN zuforum.wbb1_board board ON t.boardID = board.boardID
    """
)

link_errors = 0

guest_account = User.query.filter_by(my_url="_guest_account_").one()
