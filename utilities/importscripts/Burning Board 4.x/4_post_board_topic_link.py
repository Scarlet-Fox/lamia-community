import MySQLdb	
import MySQLdb.cursors
import sys
sys.path.append('.')
import woe.sqlmodels as sqlm
from woe import sqla
from slugify import slugify
import arrow, os, shutil	
from wand.image import Image	
from sqlalchemy.exc import IntegrityError
import phpserialize	
import HTMLParser
import json

settings_file = json.loads(open("config.json").read())	

sqla.engine.execute(
    """UPDATE topic SET view_count=0 WHERE view_count IS NULL"""
)

topic_ids = sqla.engine.execute(
    """SELECT id FROM topic"""
)

for _id in topic_ids:
    topic_recent_post = sqla.engine.execute(
        """SELECT id FROM post WHERE topic_id=%s AND hidden=False ORDER BY created DESC LIMIT 1""" % _id[0]
    )
    
    p_idx = 0
    for p in topic_recent_post:
        p_idx += 1
        sqla.engine.execute(
            """UPDATE topic SET recent_post_id=%s WHERE id=%s""" % (p[0], _id[0])
        )
        
    topic_first_post = sqla.engine.execute(
        """SELECT id FROM post WHERE topic_id=%s AND hidden=False ORDER BY created ASC LIMIT 1""" % _id[0]
    )
    
    p_idx = 0
    for p in topic_first_post:
        p_idx += 1
        sqla.engine.execute(
            """UPDATE topic SET first_post_id=%s WHERE id=%s""" % (p[0], _id[0])
        )
    
    if p_idx == 0:
        sqla.engine.execute(
            """UPDATE topic SET hidden=True WHERE id=%s""" % (_id[0],)
        )
        
    topic_post_count = sqla.engine.execute(
        """SELECT COUNT(id) FROM post WHERE topic_id=%s AND hidden=False""" % _id[0]
    )
    for c in topic_post_count:
        sqla.engine.execute(
            """UPDATE topic SET post_count=%s WHERE id=%s""" % (int(c[0]), _id[0],)
        )

category_ids = sqla.engine.execute(
    """SELECT id FROM category"""
)

for _id in category_ids:
    category_recent_topic = sqla.engine.execute(
        """SELECT topic.id, p.id FROM topic
        JOIN post p ON topic.recent_post_id = p.id
        WHERE category_id=%s AND topic.hidden=False 
        ORDER BY p.created DESC LIMIT 1""" % (_id[0],)
    )
    
    for t in category_recent_topic:
        sqla.engine.execute(
            """UPDATE category SET recent_topic_id=%s, recent_post_id=%s WHERE id=%s""" % (t[0], t[1], _id[0])
        )
    