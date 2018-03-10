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
    new_category = Category(
        name = _cat["title"],
        slug = slugify(_cat["title"], max_length=100, word_boundary=True, save_order=True),
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
    new_category = Category.query.filter_by(
        slug = slugify(_cat["title"], max_length=100, word_boundary=True, save_order=True)
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
category_cache = {}
user_cache = {}

for t in c.fetchall():
    new_topic = Topic(
        title=t["topic"],
        slug=find_topic_slug(t["topic"]),
        sticky=bool(t["isSticky"]),
        announcement=bool(t["isAnnouncement"]),
        hidden=bool(t["isDeleted"]),
        locked=bool(t["isDisabled"]) or bool(t["isClosed"]),
        created=arrow.get(t["time"]).datetime
    )
    
    if not category_cache.has_key(t["board_name"]):
        category=Category.query.filter_by(
            slug=slugify(t["board_name"], max_length=100, word_boundary=True, save_order=True)
        ).all()
    
        if len(category) == 0:
            __board_name = slugify(t["board_name"], max_length=100, word_boundary=True, save_order=True)
        
            if settings_file["import_db_topic_board_name_mapping"].has_key(__board_name):
                category=Category.query.filter_by(
                    slug=settings_file["import_db_topic_board_name_mapping"][__board_name]
                ).all()
            else:
                print "Topic category not found - topic #%s" % (t["threadID"],)
                continue
        
        new_topic.category = category[0]
        category_cache[t["board_name"]] = category[0]
    else:
        new_topic.category = category_cache[t["board_name"]]
    
    if not user_cache.has_key(t["userID"]):
        author=User.query.filter_by(
            legacy_id=t["userID"]
        ).all()
        
        if len(author) == 0:
            new_topic.author = guest_account
            user_cache[t["userID"]] = guest_account
        else:
            new_topic.author = author[0]
            user_cache[t["userID"]] = author[0]
    else:
        new_topic.author = user_cache[t["userID"]]
    
    try:
        sqla.session.add(new_topic)
        sqla.session.commit()
    except IntegrityError as e:
        sqla.session.rollback()
        print e
        continue
    
    p=db.cursor()
    p.execute(
        """
            SELECT * FROM zuforum.wbb1_post
            WHERE threadID = %s
            ORDER BY time ASC
        """ % (t["threadID"],)
    )
    
    for idx, _post in enumerate(p.fetchall()):
        new_post = Post(
            topic=new_topic,
            html=_post["message"],
            created=arrow.get(_post["time"]).datetime,
            hidden=bool(_post["isDeleted"]) or bool(_post["isDisabled"]) or bool(_post["isClosed"]),
            
        )
        
        if _post["editorID"]:
            new_post.modified = arrow.get(_post["lastEditTime"]).datetime
            if not user_cache.has_key(_post["editorID"]):
                editor=User.query.filter_by(
                    legacy_id=_post["editorID"]
                ).all()
        
                if len(editor) == 0:
                    new_post.editor = guest_account
                    user_cache[_post["editorID"]] = guest_account
                else:
                    new_post.editor = editor[0]
                    user_cache[_post["editorID"]] = editor[0]
            else:
                new_post.editor = user_cache[_post["editorID"]]
        
        if _post["userID"]:
            if not user_cache.has_key(_post["userID"]):
                author=User.query.filter_by(
                    legacy_id=_post["userID"]
                ).all()
        
                if len(author) == 0:
                    new_post.author = guest_account
                    user_cache[_post["userID"]] = guest_account
                else:
                    new_post.author = author[0]
                    user_cache[_post["userID"]] = author[0]
            else:
                new_post.author = user_cache[_post["userID"]]
    
        try:
            sqla.session.add(new_post)
            sqla.session.commit()
            if idx == 0:
                new_topic.recent_post = new_post
                sqla.session.add(new_topic)
                sqla.session.commit()
        except IntegrityError as e:
            sqla.session.rollback()
            print e
            continue

c.close()
