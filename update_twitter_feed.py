import twitter
import arrow
from lamia import sqla
import lamia.sqlmodels as sqlm
from lamia import settings_file
from lamia.sqlmodels import *

api = twitter.Api(consumer_key=settings_file["twitter_consumer_key"],
        consumer_secret=settings_file["twitter_consumer_secret"],
        access_token_key=settings_file["twitter_access_token_key"],
        access_token_secret=settings_file["twitter_access_token_secret"]
        )

statuses = api.GetUserTimeline(screen_name="CasualAnimeFans")

# class Tweet(db.Model):
#     id = db.Column(db.Text, primary_key=True)
#     time = db.Column(db.DateTime, index=True)
#     text = db.Column(db.Text)
#     retweeted = db.Column(db.Boolean, default=False, index=True)
#     raw_json = db.Column(JSONB)
#
#     def __repr__(self):
#         return "<Tweet: (text='%s')>" % (self.text,)

for s in statuses:
    
    count = sqla.session.query(sqlm.Tweet).filter_by(id=str(s.id)).count()
    
    if count == 0:
        tweet = Tweet()
        tweet.text = s.text
        tweet.id = str(s.id)
        tweet.time = arrow.get(s.created_at, "ddd MMM DD HH:mm:ss Z YYYY").datetime
        
        if s.retweeted_status:
            tweet.retweeted = True
            tweet.retweeted_from = s.retweeted_status.user.screen_name
        else:
            tweet.retweeted = False
            
        tweet.raw_json = s._json
        
        sqla.session.add(tweet)
        sqla.session.commit()
