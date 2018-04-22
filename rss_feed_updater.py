import arrow
import feedparser
from lamia import sqla
import lamia.sqlmodels as sqlm
from lamia import settings_file
from lamia.sqlmodels import *

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
            except:
                continue
            
            topic = Topic(
                    category=feed.category_for_topics,
                    author=feed.user_account_for_posting,
                    slug=sqlm.find_topic_slug(entry["title"]),
                    title=entry["title"],
                    created=arrow.utcnow().datetime.replace(tzinfo=None),
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
                    created=arrow.utcnow().datetime.replace(tzinfo=None)
                )
            sqla.session.add(post)
            sqla.session.commit()
            
            topic.first_post = post
            topic.recent_post = post
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
        