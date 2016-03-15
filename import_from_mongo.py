from woe import app
from woe import sqla
from woe.sqlmodels import *
import woe.models.core as core
import woe.models.forum as forum
import woe.models.roleplay as rp
import woe.models.blogs as blogs
from datetime import datetime

sqla.drop_all()
sqla.create_all()

for mongo_user in core.User.objects():
    new_user = User()
    if mongo_user.login_name in ["scarlet", "zoop", "artemis"]:
        new_user.is_admin = True
        new_user.is_mod = True
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
    new_user.password_hash = mongo_user.password_hash
    new_user.legacy_password = mongo_user.legacy_password
    new_user.ipb_salt = mongo_user.ipb_salt
    new_user.ipb_hash = mongo_user.ipb_hash
    new_user.posts_count = mongo_user.posts_count
    new_user.topic_count = mongo_user.topic_count
    new_user.status_count = mongo_user.status_count
    new_user.status_comment_count = mongo_user.status_comment_count
    sqla.session.add(new_user)
    sqla.session.commit()

for mongo_user in core.User.objects():
    for ig_user in mongo_user.ignored_users:
        try:
            user = sqla.session.query(User).filter_by(old_mongo_hash=str(mongo_user.id)).first()
            ignoring = sqla.session.query(User).filter_by(old_mongo_hash=str(ig_user.id)).first()

            new_ignore = IgnoringUser()
            new_ignore.user = user
            new_ignore.ignoring = ignoring
            new_ignore.created = datetime.now()

            sqla.session.add(new_ignore)
            sqla.session.commit()
        except:
            sqla.session.rollback()
            continue

for status_update in core.StatusUpdate.objects():
    new_status_update = StatusUpdate()

    try:
        profile_user = sqla.session.query(User).filter_by(old_mongo_hash=str(status_update.attached_to_user.id)).first()
        new_status_update.attached_to_profile = profile_user
    except:
        pass

    new_status_update.message = status_update.message
    new_status_update.last_replied = status_update.last_replied
    new_status_update.last_viewed = status_update.last_viewed
    new_status_update.replies = status_update.replies
    new_status_update.locked = status_update.locked
    new_status_update.muted = status_update.muted
    new_status_update.hidden = status_update.hidden

    status_author = sqla.session.query(User).filter_by(old_mongo_hash=str(status_update.author.id)).first()
    new_status_update.author = status_author
    new_status_update.created = status_update.created
    new_status_update.old_mongo_hash = str(status_update.id)
    sqla.session.add(new_status_update)
    sqla.session.commit()

    for participant in status_update.participants:
        sql_user = sqla.session.query(User).filter_by(old_mongo_hash=str(participant.id)).first()
        status_update_user_cls = StatusUpdateUser()
        status_update_user_cls.author = sql_user
        status_update_user_cls.status = new_status_update

        if participant in status_update.blocked:
            status_update_user_cls.blocked = True
        if participant in status_update.ignoring:
            status_update_user_cls.ignoring = True
        sqla.session.add(status_update_user_cls)
        sqla.session.commit()

    for comment in status_update.comments:
        sql_comment_author = sqla.session.query(User).filter_by(old_mongo_hash=str(comment.author.id)).first()
        sql_comment = StatusComment()
        sql_comment.author = sql_comment_author
        sql_comment.created = comment.created
        sql_comment.message = comment.text
        sql_comment.hidden = comment.hidden
        sql_comment.status = new_status_update
        sqla.session.add(sql_comment)
        sqla.session.commit()

for character in rp.Character.objects():
    sql_user = sqla.session.query(User).filter_by(old_mongo_hash=str(character.creator.id)).first()
    sql_character = Character()

    sql_character.author = sql_user
    sql_character.created = character.created
    sql_character.modified = character.modified

    sql_character.name = character.name
    sql_character.slug = character.slug
    sql_character.age = character.age
    sql_character.species = character.species
    sql_character.appearance = character.appearance
    sql_character.personality = character.personality
    sql_character.backstory = character.backstory
    sql_character.other = character.other
    sql_character.motto = character.motto
    sql_character.legacy_avatar_field = character.legacy_avatar_field
    sql_character.legacy_gallery_field = character.legacy_gallery_field
    sql_character.old_mongo_hash = str(character.id)
    sqla.session.add(sql_character)
    sqla.session.commit()

for attachment in core.Attachment.objects():
    sql_user = sqla.session.query(User).filter_by(old_mongo_hash=str(attachment.owner.id)).first()
    sql_attachment = Attachment()

    sql_attachment.path = attachment.path
    sql_attachment.mimetype = attachment.mimetype
    sql_attachment.extension = attachment.extension
    sql_attachment.size_in_bytes = attachment.size_in_bytes
    sql_attachment.created_date = attachment.created_date
    sql_attachment.do_not_convert = attachment.do_not_convert
    sql_attachment.linked = attachment.linked
    sql_attachment.caption = attachment.caption
    sql_attachment.owner = sql_user
    sql_attachment.old_mongo_hash = str(attachment.id)
    sql_attachment.alt = attachment.alt
    sql_attachment.x_size = attachment.x_size
    sql_attachment.y_size = attachment.y_size
    sql_attachment.file_hash = attachment.file_hash
    sql_attachment.origin_url = attachment.origin_url
    sql_attachment.origin_domain = attachment.origin_domain
    sql_attachment.caption = attachment.caption

    if attachment.character is not None:
        sql_character = sqla.session.query(Character).filter_by(old_mongo_hash=str(attachment.character.id)).first()
        sql_attachment.character = sql_character
        sql_attachment.character_gallery = True
        sql_attachment.character_gallery_weight = 0
        sql_attachment.character_avatar = attachment.character_emote

    sqla.session.add(sql_attachment)
    sqla.session.commit()

for notification in core.Notification.objects(seen=False):
    try:
        sql_user = sqla.session.query(User).filter_by(old_mongo_hash=str(notification.user.id)).first()
        sql_author = sqla.session.query(User).filter_by(old_mongo_hash=str(notification.author.id)).first()
    except:
        continue

    sql_notification = Notification()
    sql_notification.user = sql_user
    sql_notification.author = sql_author
    sql_notification.message = notification.text
    sql_notification.category = notification.category
    sql_notification.created = notification.created
    sql_notification.url = notification.url
    sql_notification.acknowledged = notification.acknowledged
    sql_notification.seen = notification.seen
    sql_notification.emailed = notification.emailed
    sql_notification.priority = notification.priority

    sqla.session.add(sql_notification)
    sqla.session.commit()

for message_topic in core.PrivateMessageTopic.objects():
    sql_user = sqla.session.query(User).filter_by(old_mongo_hash=str(message_topic.creator.id)).first()
    sql_message_topic = PrivateMessage()
    sql_message_topic.created = message_topic.created
    sql_message_topic.author = sql_user
    sql_message_topic.title = message_topic.title
    sql_message_topic.count = message_topic.message_count
    sql_message_topic.old_mongo_hash = str(message_topic.id)
    sqla.session.add(sql_message_topic)
    sqla.session.commit()

    for message_user in message_topic.participating_users:
        sql_user = sqla.session.query(User).filter_by(old_mongo_hash=str(message_user.id)).first()
        sql_participant = PrivateMessageUser()
        sql_participant.author = sql_user
        sql_participant.pm = sql_message_topic
        if message_user in message_topic.blocked_users:
            sql_participant.blocked = True
        if message_user in message_topic.users_left_pm:
            sql_participant.exited = True

        sqla.session.add(sql_participant)
        sqla.session.commit()

    for message_reply in core.PrivateMessage.objects(topic=message_topic):
        sql_user = sqla.session.query(User).filter_by(old_mongo_hash=str(message_reply.author.id)).first()
        sql_message_reply = PrivateMessageReply()
        sql_message_reply.author = sql_user
        sql_message_reply.pm_title = sql_message_topic.title
        sql_message_reply.message = message_reply.message
        sql_message_reply.pm = sql_message_topic
        sql_message_reply.created = message_reply.created
        sql_message_reply.modified = message_reply.modified
        sql_message_reply.old_mongo_hash = str(message_reply.id)

        sqla.session.add(sql_message_reply)
        sqla.session.commit()

    sql_message_topic.last_reply = sqla.session.query(PrivateMessageReply).filter_by(pm=sql_message_topic). \
        order_by(PrivateMessageReply.created.desc()).first()
    sqla.session.add(sql_message_topic)
    sqla.session.commit()

celestial_hub_categories = ["Latest News","Welcome Mat","Help Lab","Frequently Asked Questions"]
starlight_amphitheater = ["Anime", "Manga", "World of Equestria", "Western Animation", "Music", "Other Media"]
moonlight_symposium = ["Chit Chat", "Interrogations", "Games", "Nintendo", "Art Show"]
sunlight_homestead = ["Super Party Palace", "Roleplays", "Out of Character", "Meta Lounge", "Minecraft"]

celestial = Section(name="Celestial Hub", weight=0, slug=slugify("Celestial Hub"))
starlight = Section(name="Starlight Amphitheater", weight=10, slug=slugify("Starlight Amphitheater"))
moonlight = Section(name="Moonlight Symposium", weight=20, slug=slugify("Moonlight Symposium"))
sunlight = Section(name="Sunlight Homestead", weight=30, slug=slugify("Sunlight Homestead"))
sqla.session.add(celestial)
sqla.session.add(starlight)
sqla.session.add(moonlight)
sqla.session.add(sunlight)
sqla.session.commit()

for i, category in enumerate(celestial_hub_categories):
    sqlcategory = Category(
        name = category,
        slug = slugify(category),
        section = celestial,
        weight = i*10
    )

    if category == "Frequently Asked Questions":
        sqlcategory.parent = sqla.session.query(Category).filter_by(name="Help Lab").first()

    sqla.session.add(sqlcategory)
    sqla.session.commit()

for i, category in enumerate(starlight_amphitheater):
    sqlcategory = Category(
        name = category,
        slug = slugify(category),
        section = starlight,
        weight = i*10
    )

    if category == "Manga":
        sqlcategory.parent = sqla.session.query(Category).filter_by(name="Anime").first()

    sqla.session.add(sqlcategory)
    sqla.session.commit()

for i, category in enumerate(moonlight_symposium):
    sqlcategory = Category(
        name = category,
        slug = slugify(category),
        section = moonlight,
        weight = i*10
    )

    if category == "Nintendo":
        sqlcategory.parent = sqla.session.query(Category).filter_by(name="Games").first()

    sqla.session.add(sqlcategory)
    sqla.session.commit()

for i, category in enumerate(sunlight_homestead):
    sqlcategory = Category(
        name = category,
        slug = slugify(category),
        section = sunlight,
        weight = i*10
    )

    if category == "Out of Character":
        sqlcategory.parent = sqla.session.query(Category).filter_by(name="Roleplays").first()

    if category == "Meta Lounge":
        sqlcategory.parent = sqla.session.query(Category).filter_by(name="Roleplays").first()

    sqla.session.add(sqlcategory)
    sqla.session.commit()

for topic in forum.Topic.objects():
    if topic.prefix is not None:
        label = sqla.session.query(Label).filter_by(label=topic.prefix).first()

        if label is None:
            sqllabel = Label(
                pre_html = topic.pre_html,
                post_html = topic.post_html,
                label = topic.prefix
            )
            sqla.session.add(sqllabel)
            sqla.session.commit()

for topic in forum.Topic.objects():
    sql_user = sqla.session.query(User).filter_by(old_mongo_hash=str(topic.creator.id)).first()
    sql_topic = Topic()
    sql_topic.author = sql_user
    sql_topic.created = topic.created
    sql_topic.hidden = topic.hidden
    sql_topic.locked = topic.closed
    sql_topic.title = topic.title
    sql_topic.slug = topic.slug

    if topic.category.name in ["Commissions", "Requests"]:
        sql_topic.category = sqla.session.query(Category).filter_by(name="Art Show").first()
    elif topic.category.name == "Scenarios":
        sql_topic.category = sqla.session.query(Category).filter_by(name="Roleplays").first()
    elif topic.category.name == "Minecraft Discussion":
        sql_topic.category = sqla.session.query(Category).filter_by(name="Minecraft").first()
    elif topic.category.name == "Out of Character Discussion":
        sql_topic.category = sqla.session.query(Category).filter_by(name="Out of Character").first()
    elif topic.category.name == "Discussion":
        sql_topic.category = sqla.session.query(Category).filter_by(name="Chit Chat").first()
    elif topic.prefix == "Anime":
        sql_topic.category = sqla.session.query(Category).filter_by(name="Anime").first()
        topic.prefix = None
    elif topic.prefix == "Games":
        sql_topic.category = sqla.session.query(Category).filter_by(name="Games").first()
        topic.prefix = None
    elif topic.prefix == "Ponies":
        sql_topic.category = sqla.session.query(Category).filter_by(name="World of Equestria").first()
        topic.prefix = None
    elif topic.prefix == "Media":
        sql_topic.category = sqla.session.query(Category).filter_by(name="Other Media").first()
        topic.prefix = None
    elif topic.prefix == "Music":
        sql_topic.category = sqla.session.query(Category).filter_by(name="Music").first()
        topic.prefix = None
    else:
        sql_topic.category = sqla.session.query(Category).filter_by(name=topic.category.name).first()

    if topic.prefix is not None:
        sql_prefix = sqla.session.query(Label).filter_by(label=topic.prefix).first()
        sql_topic.label = sql_prefix

    sql_topic.post_count = topic.post_count
    sql_topic.view_count = topic.view_count

    sqla.session.add(sql_topic)
    sqla.session.commit()

    for post in forum.Post.objects(topic=topic):
        sql_user = sqla.session.query(User).filter_by(old_mongo_hash=str(post.author.id)).first()
        sql_post = Post()

        sql_post.created = post.created
        sql_post.modified = post.modified
        sql_post.author = sql_user
        sql_post.html = post.html
        sql_post.topic = sql_topic
        sql_post.t_topic = sql_topic.title
        sql_post.old_mongo_hash = str(post.id)
        sql_post.hidden = post.hidden

        if post.data.has_key("character"):
            sql_post.character = sqla.session.query(Character).filter_by(old_mongo_hash=str(post.data["character"])).first()

        if post.data.has_key("avatar"):
            sql_post.avatar = sqla.session.query(Attachment).filter_by(old_mongo_hash=str(post.data["avatar"])).first()

        sqla.session.add(sql_post)
        sqla.session.commit()

        for user in post.boops:
            sql_booper = sqla.session.query(User).filter_by(old_mongo_hash=str(user.id)).first()
            sql_post.boops.append(sql_booper)

        sqla.session.add(sql_post)
        sqla.session.commit()

    sql_topic.recent_post = sqla.session.query(Post).filter_by(topic=sql_topic). \
        order_by(Post.created.desc()).first()

    sqla.session.add(sql_topic)
    sqla.session.commit()

for category in sqla.session.query(Category).all():
    recent_category_topic = sqla.session.query(Topic) \
        .join(Topic.recent_post).filter(Topic.category==category) \
        .order_by(Post.created.desc()).first()
    try:
        category.recent_topic = recent_category_topic
        category.recent_post = recent_category_topic.recent_post
    except:
        continue

    category.topic_count = sqla.session.query(Topic) \
        .join(Topic.recent_post).filter(Topic.category==category) \
        .order_by(Post.created.desc()).count()

    category.post_count = sqla.session.query(Post) \
        .join(Post.topic).filter(Topic.category==category) \
        .order_by(Post.created.desc()).count()

    sqla.session.add(recent_category_topic)
    sqla.session.commit()
