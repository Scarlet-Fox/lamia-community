from woe import app
from woe import sqla
from woe.sqlmodels import *
import woe.models.core as core
import woe.models.forum as forum
import woe.models.roleplay as rp
import woe.models.blogs as blogs

sqla.drop_all()
sqla.create_all()

for mongo_user in core.User.objects():
    new_user = User()
    new_user.login_name = mongo_user.login_name
    new_user.display_name = mongo_user.display_name
    new_user.email_address = mongo_user.email_address
    new_user.banned = mongo_user.banned
    new_user.validated = mongo_user.validated
    new_user.joined = mongo_user.joined
    new_user.avatar_extension = mongo_user.avatar_extension
    new_user.avatar_full_x = mongo_user.avatar_full_x
    new_user.avatar_full_y = mongo_user.avatar_full_y
    new_user.avatar_60_x = mongo_user.avatar_60_x
    new_user.avatar_60_y = mongo_user.avatar_60_y
    new_user.avatar_40_x = mongo_user.avatar_40_x
    new_user.avatar_40_y = mongo_user.avatar_40_y
    new_user.avatar_timestamp = mongo_user.avatar_timestamp
    new_user.my_url = mongo_user.login_name
    new_user.how_did_you_find_us = mongo_user.how_did_you_find_us
    new_user.is_allowed_during_construction = mongo_user.is_allowed_during_construction
    new_user.time_zone = mongo_user.time_zone
    new_user.over_thirteen = mongo_user.over_thirteen
    new_user.emails_muted = mongo_user.emails_muted
    new_user.old_mongo_hash = str(mongo_user.id)
    new_user.title = mongo_user.title
    new_user.about_me = mongo_user.about_me
    new_user.anonymous_login = False
    new_user.posts_count = mongo_user.posts_count
    new_user.topic_count = mongo_user.topic_count
    new_user.status_count = mongo_user.status_count
    new_user.status_comment_count = mongo_user.status_comment_count
    sqla.session.add(new_user)
    sqla.session.commit()
