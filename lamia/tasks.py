from lamia import app
import lamia.sqlmodels as sqlm
from lamia import settings_file
from lamia.sqlmodels import *

from wand.image import Image
from celery import Celery
from celery.schedules import crontab

import arrow
import feedparser
import os

from flask_sqlalchemy import SQLAlchemy
celery = app.celery

###############################################################################
# Logging function
###############################################################################

def log_task(name=False, recurring=False, meta=False):
    sqla = SQLAlchemy(app)
    
    task = sqlm.TaskLog(
        name=name,
        recurring=recurring,
        local_meta=meta,
        created=arrow.utcnow().datetime.replace(tzinfo=None)
    )
    
    sqla.session.add(task)
    sqla.session.commit()
    sqla.session.close()

###############################################################################
# RSS Feed updater
###############################################################################

@celery.task
def rss_feed_updater():
    sqla = SQLAlchemy(app)
    
    print("rss_feed_updater running")
    rss_feeds = RSSScraper.query.all()

    for feed in rss_feeds:
        if feed.user_account_for_posting == None:
            continue
        
        if feed.feed_type not in RSSScraper.TYPE_CHOICES:
            continue
        
        parsed_feed = feedparser.parse(feed.rss_feed_url)
    
        if feed.feed_type == "wordpress":
            for entry in parsed_feed["entries"]:
                try:
                    entry_id = int(entry["post-id"])
                    entry_content = entry["content"][0]["value"]
                    entry_published = arrow.get(entry["published_parsed"])
                except:
                    continue
                
                existing_content_count = RSSContent.query.filter_by(remote_id=entry_id).count()
                if existing_content_count > 0:
                    continue
            
                topic = Topic(
                        category=feed.category_for_topics,
                        author=feed.user_account_for_posting,
                        slug=sqlm.find_topic_slug(entry["title"]),
                        title=entry["title"],
                        created=entry_published.datetime.replace(tzinfo=None),
                        post_count=1
                    )
                sqla.session.add(topic)
                sqla.session.commit()
            
                more_link = """<div>[button="Click Here to View Post"]%s[/button]</div>""" % entry["id"]
            
                post = Post(
                        author=feed.user_account_for_posting,
                        html=entry["content"][0]["value"].replace("<p>", "<div>").replace("</p>", "</div>") + "\n\n" + more_link,
                        topic=topic,
                        t_title=topic.title,
                        created=entry_published.datetime.replace(tzinfo=None)
                    )
                sqla.session.add(post)
                sqla.session.commit()
            
                topic.first_post = post
                topic.recent_post = post
                topic.recent_post_time = post.created
                sqla.session.add(topic)

                rss_content = RSSContent(
                        remote_id = entry_id,
                        remote_url = entry["id"],
                        last_modified = arrow.utcnow().datetime.replace(tzinfo=None),
                        topic = topic,
                        scraper = feed
                    )

                sqla.session.add(rss_content)
                sqla.session.commit()

    sqla.session.close()
    log_task(name="rss_feed_updater", recurring=True, meta="")

###############################################################################
# Infraction pts calculator
###############################################################################

@celery.task
def infraction_point_calculator():
    sqla = SQLAlchemy(app)
    print("infraction_point_calculator running")
    
    sqla.engine.execute(
        """UPDATE \"user\" SET lifetime_infraction_points=0"""
    )
    sqla.engine.execute(
        """UPDATE \"user\" SET active_infraction_points=0"""
    )

    for infraction in sqlm.Infraction.query.all():
        user = infraction.recipient

        user.lifetime_infraction_points += infraction.points
    
        if arrow.now() < arrow.get(infraction.expires) and infraction.forever == False:
            user.active_infraction_points += infraction.points
        
        sqla.session.add(user)
        sqla.session.commit()
    
    sqla.session.close()
    log_task(name="infraction_point_calculator", recurring=True, meta="")

###############################################################################
# Basic user stats calculator
###############################################################################

@celery.task
def basic_user_stats_calculator():
    sqla = SQLAlchemy(app)
    print("basic_user_stats_calculator running")
    
    for user in sqlm.User.query.filter_by(banned=False):  
        user = sqla.session.merge(user)
        
        user.post_count = sqlm.Post.query.filter_by(hidden=False, author=user).count()
        user.topic_count = sqlm.Topic.query.filter_by(hidden=False, author=user).count()
        user.status_update_created = sqlm.StatusUpdate.query.filter_by(hidden=False, author=user).count()
        user.status_update_comments_created = sqlm.StatusComment.query.filter_by(hidden=False, author=user).count()
        user.boops_given = sqla.session.query(sqlm.post_boop_table).filter(sqlm.post_boop_table.c.user_id == user.id).count()
        user.boops_received = sqla.session.query(sqlm.post_boop_table) \
            .join(sqlm.Post) \
            .filter(sqlm.Post.author == user) \
            .count()
        
        sqla.session.add(user)
        sqla.session.commit()
        
        
    sqla.session.close()
    log_task(name="basic_user_stats_calculator", recurring=True, meta="")

###############################################################################
# Global stats calculator
###############################################################################

@celery.task
def basic_site_stats_calculator():
    sqla = SQLAlchemy(app)
    print("basic_site_stats_calculator running")
    
    cache.set("post_count", sqla.session.query(sqlm.Post).count(), timeout=0)
    cache.set("topic_count", sqla.session.query(sqlm.Topic).count(), timeout=0)
    cache.set("blog_entry_count", sqla.session.query(sqlm.BlogEntry).count(), timeout=0)
    cache.set("status_update_count", sqla.session.query(sqlm.StatusUpdate).count(), timeout=0)
    cache.set("status_comments_count", sqla.session.query(sqlm.StatusComment).count(), timeout=0)
    
    sqla.session.close()
    log_task(name="basic_site_stats_calculator", recurring=True, meta="")
    

###############################################################################
# Other misc. tasks
###############################################################################

@celery.task()
def verify_attachment(filepath, size):
    filepath = os.path.join(os.getcwd(), "lamia/static/uploads", filepath)
    sizepath = os.path.join(os.getcwd(), "lamia/static/uploads", 
        ".".join(filepath.split(".")[:-1])+".custom_size."+size+"."+filepath.split(".")[-1])
    
    if not os.path.exists(sizepath):
        image = Image(filename=filepath)
        xsize = image.width
        ysize = image.height
        resize_measure = min(float(size)/float(xsize),float(size)/float(ysize))
        image.resize(int(round(xsize*resize_measure)),int(round(ysize*resize_measure)))
        image.save(filename=sizepath)
        
    return True

@celery.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(settings_file["rss_feed_update_delay"], rss_feed_updater.s(), name='rss_feed_updater')
    sender.add_periodic_task(settings_file["infraction_point_calculator_delay"], infraction_point_calculator.s(), name='infraction_point_calculator')
    sender.add_periodic_task(settings_file["basic_user_stats_calculator_delay"], basic_user_stats_calculator.s(), name='basic_user_stats_calculator')
    sender.add_periodic_task(settings_file["basic_site_stats_calculator_delay"], basic_site_stats_calculator.s(), name='basic_site_stats_calculator_delay')
    
