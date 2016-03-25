from woe import app
from woe.parsers import ForumPostParser
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session
from flask.ext.login import login_user, logout_user, current_user, login_required
import arrow, time, math
from woe.utilities import get_top_frequences, scrub_json, humanize_time, ForumHTMLCleaner
from woe.views.dashboard import broadcast
import woe.sqlmodels as sqlm
from woe import sqla
from sqlalchemy.orm.attributes import flag_modified

@app.route('/messages/<pk>/edit-post/<post>', methods=['GET'])
@login_required
def get_post_html_in_pm_topic(pk, post):
    try:
        topic = sqla.session.query(sqlm.PrivateMessage).filter_by(id=pk)[0]
    except IndexError:
        return abort(404)

    try:
        post = sqla.session.query(sqlm.PrivateMessageReply).filter_by(id=post, pm=topic)[0]
    except IndexError:
        return abort(404)

    return json.jsonify(content=post.message, author=post.author.display_name)

@app.route('/messages/<pk>/kick-from-topic/<upk>', methods=['POST'])
@login_required
def kick_from_pm_topic(pk, upk):
    try:
        topic = sqla.session.query(sqlm.PrivateMessage).filter_by(id=pk)[0]
    except IndexError:
        return abort(404)

    if not current_user._get_current_object() == topic.author:
        return abort(404)

    try:
        target_user = sqla.session.query(sqlm.User).filter_by(id=upk)[0]
    except IndexError:
        return abort(404)

    try:
        pm_user = sqla.session.query(sqlm.PrivateMessageUser).filter_by(
            pm = topic,
            author = target_user
        )[0]
    except IndexError:
        return abort(404)

    pm_user.blocked = True
    pm_user.exited = True
    sqla.session.add(pm_user)
    sqla.session.commit()

    return json.jsonify(url='/messages/'+str(topic.id))

@app.route('/messages/<pk>/add-to-pm', methods=['POST'])
@login_required
def add_to_pm(pk):
    try:
        topic = sqla.session.query(sqlm.PrivateMessage).filter_by(id=pk)[0]
    except IndexError:
        return abort(404)

    if not current_user._get_current_object() == topic.author:
        return abort(404)

    request_json = request.get_json(force=True)

    try:
        to_add = list(
                sqla.session.query(sqlm.User) \
                    .filter(sqlm.User.id.in_(request_json.get("authors"))) \
                    .all()
            )
    except:
        to_add = []

    for user in to_add:
        try:
            participant = sqla.session.query(sqlm.PrivateMessageUser).filter_by(
                pm = topic,
                author = user
            )[0]
            continue
        except IndexError:
            pass

        participant = sqlm.PrivateMessageUser(
                author = user,
                pm = topic
            )
        sqla.session.add(participant)
        sqla.session.commit()

    return app.jsonify(url="/messages/"+str(topic.id))

@app.route('/messages/<pk>/leave-topic', methods=['POST'])
@login_required
def leave_pm_topic(pk):
    try:
        topic = sqla.session.query(sqlm.PrivateMessage).filter_by(id=pk)[0]
    except IndexError:
        return abort(404)

    try:
        pm_user = sqla.session.query(sqlm.PrivateMessageUser).filter_by(
            pm = topic,
            author = current_user._get_current_object()
        )[0]
    except IndexError:
        return abort(404)

    pm_user.exited = True
    sqla.session.add(pm_user)
    sqla.session.commit()

    return json.jsonify(url='/messages')

@app.route('/messages/<pk>/edit-post', methods=['POST'])
@login_required
def edit_post_in_pm_topic(pk):
    try:
        topic = sqla.session.query(sqlm.PrivateMessage).filter_by(id=pk)[0]
    except IndexError:
        return abort(404)

    try:
        pm_user = sqla.session.query(sqlm.PrivateMessageUser).filter_by(
            pm = topic,
            author = current_user._get_current_object()
        )[0]
    except IndexError:
        return abort(404)

    request_json = request.get_json(force=True)

    try:
        message = sqla.session.query(sqlm.PrivateMessageReply).filter_by(
            id = request_json.get("pk"),
            pm = topic
        )[0]
    except IndexError:
        return abort(404)

    if current_user._get_current_object() != message.author:
        return abort(404)

    if request_json.get("text", "").strip() == "":
        return app.jsonify(error="Your post is empty.")

    cleaner = ForumHTMLCleaner()
    try:
        post_html = cleaner.clean(request_json.get("post", ""))
    except:
        return abort(500)

    message.message = post_html
    message.modified = arrow.utcnow().datetime

    sqla.session.add(message)
    sqla.session.commit()

    clean_html_parser = ForumPostParser()
    return app.jsonify(html=clean_html_parser.parse(message.message), success=True)

@app.route('/messages/<pk>/new-post', methods=['POST'])
@login_required
def new_message_in_pm_topic(pk):
    try:
        topic = sqla.session.query(sqlm.PrivateMessage).filter_by(id=pk)[0]
    except IndexError:
        return abort(404)

    try:
        pm_user = sqla.session.query(sqlm.PrivateMessageUser).filter_by(
            pm = topic,
            author = current_user._get_current_object()
        )[0]
    except IndexError:
        return abort(404)

    request_json = request.get_json(force=True)

    if request_json.get("text", "").strip() == "":
        return app.jsonify(error="Your post is empty.")

    non_left_or_blocked_users = sqla.session.query(sqlm.PrivateMessageUser).filter_by(
        pm = topic,
        exited = False,
        blocked = False
    ).count()

    if non_left_or_blocked_users == 1:
        return app.jsonify(error="There is only one participant in this private message. Don't talk to yourself. :)")

    cleaner = ForumHTMLCleaner()
    try:
        post_html = cleaner.clean(request_json.get("post", ""))
    except:
        return abort(500)

    message = sqlm.PrivateMessageReply()
    message.message = post_html
    message.author = current_user._get_current_object()
    message.created = arrow.utcnow().datetime.replace(tzinfo=None)
    message.pm = topic
    message.pm_title = topic.title
    sqla.session.add(message)
    sqla.session.commit()

    topic.last_reply = message
    topic.count = topic.count+1
    sqla.session.add(topic)
    sqla.session.commit()

    clean_html_parser = ForumPostParser()
    parsed_post = {}
    parsed_post["created"] = humanize_time(message.created, "MMM D YYYY")
    parsed_post["modified"] = humanize_time(message.modified, "MMM D YYYY")
    parsed_post["html"] = clean_html_parser.parse(message.message)
    parsed_post["user_avatar"] = message.author.get_avatar_url()
    parsed_post["user_avatar_x"] = message.author.avatar_full_x
    parsed_post["user_avatar_y"] = message.author.avatar_full_y
    parsed_post["user_avatar_60"] = message.author.get_avatar_url("60")
    parsed_post["user_avatar_x_60"] = message.author.avatar_60_x
    parsed_post["user_avatar_y_60"] = message.author.avatar_60_y
    parsed_post["user_title"] = message.author.title
    parsed_post["_id"] = message.id
    parsed_post["author_name"] = message.author.display_name
    parsed_post["author_login_name"] = message.author.login_name
    post_count = sqla.session.query(sqlm.PrivateMessageReply).filter_by(pm=topic).count()

    notify_users = []
    for u in sqla.session.query(sqlm.PrivateMessageUser).filter_by(pm = topic):
        if u.author == message.author:
            continue
        if u.exited or u.blocked or u.ignoring:
            continue
        notify_users.append(u.author)

    broadcast(
        to=notify_users,
        category="pm",
        url="/messages/%s/page/1/post/%s" % (str(topic.id), str(message.id)),
        title="%s has replied to %s." % (unicode(message.author.display_name), unicode(topic.title)),
        description=message.message,
        content=topic,
        author=message.author
        )

    return app.jsonify(newest_post=parsed_post, count=post_count, success=True)

@app.route('/messages/<pk>/posts', methods=['POST'])
def private_message_posts(pk):
    try:
        topic = sqla.session.query(sqlm.PrivateMessage).filter_by(id=pk)[0]
    except IndexError:
        return abort(404)

    try:
        pm_user = sqla.session.query(sqlm.PrivateMessageUser).filter_by(
            pm = topic,
            author = current_user._get_current_object()
        )[0]
    except IndexError:
        if current_user.login_name in ["scarlet", "zoop"]:
            pass
        else:
            return abort(404)

    request_json = request.get_json(force=True)

    try:
        pagination = int(request_json.get("pagination", 20))
        page = int(request_json.get("page", 1))
    except:
        pagination = 20
        page = 1

    posts = sqla.session.query(sqlm.PrivateMessageReply) \
        .filter_by(pm=topic).order_by(sqlm.PrivateMessageReply.created) \
        [(page-1)*pagination:page*pagination]

    post_count = sqla.session.query(sqlm.PrivateMessageReply) \
        .filter_by(pm=topic).count()
    parsed_posts = []

    for post in posts:
        clean_html_parser = ForumPostParser()
        parsed_post = {}
        parsed_post["created"] = humanize_time(post.created, "MMM D YYYY")
        parsed_post["modified"] = humanize_time(post.modified, "MMM D YYYY")
        parsed_post["html"] = clean_html_parser.parse(post.message)
        parsed_post["user_avatar"] = post.author.get_avatar_url()
        parsed_post["user_avatar_x"] = post.author.avatar_full_x
        parsed_post["user_avatar_y"] = post.author.avatar_full_y
        parsed_post["user_avatar_60"] = post.author.get_avatar_url("60")
        parsed_post["user_avatar_x_60"] = post.author.avatar_60_x
        parsed_post["user_avatar_y_60"] = post.author.avatar_60_y
        parsed_post["user_title"] = post.author.title
        parsed_post["author_name"] = post.author.display_name
        parsed_post["author_login_name"] = post.author.login_name
        parsed_post["_id"] = post.id

        if current_user.is_authenticated():
            if post.author.id == current_user._get_current_object().id:
                parsed_post["is_author"] = True
            else:
                parsed_post["is_author"] = False
        else:
            parsed_post["is_author"] = False

        if post.author.last_seen != None:
            if arrow.get(post.author.last_seen) > arrow.utcnow().replace(minutes=-15).datetime:
                parsed_post["author_online"] = True
            else:
                parsed_post["author_online"] = False
        else:
            parsed_post["author_online"] = False

        parsed_posts.append(parsed_post)

    return app.jsonify(posts=parsed_posts, count=post_count)

@app.route('/messages/<pk>', methods=['GET'], defaults={'page': 1, 'post': ""})
@app.route('/messages/<pk>/page/<page>', methods=['GET'], defaults={'post': ""})
@app.route('/messages/<pk>/page/<page>/post/<post>', methods=['GET'])
def message_index(pk, page, post):
    try:
        topic = sqla.session.query(sqlm.PrivateMessage).filter_by(id=pk)[0]
    except IndexError:
        return abort(404)

    try:
        pm_user = sqla.session.query(sqlm.PrivateMessageUser).filter_by(
            pm = topic,
            author = current_user._get_current_object()
        )[0]
        pm_user.last_viewed = arrow.utcnow().datetime.replace(tzinfo=None)

        sqla.session.add(pm_user)
        print pm_user.last_viewed

        sqla.session.commit()

        if pm_user.exited or pm_user.blocked:
            return abort(404)

    except IndexError:
        sqla.session.rollback()
        if current_user.login_name in ["scarlet", "zoop"]:
            pass
        else:
            return abort(404)

    try:
        page = int(page)
    except:
        page = 1

    flag_modified(topic, "last_seen_by")
    if topic.last_seen_by is None:
        topic.last_seen_by = {}

    if post == "latest_post":
        try:
            post = sqla.session.query(sqlm.PrivateMessageReply).filter_by(pm=topic) \
                .order_by(sqla.desc(sqlm.PrivateMessageReply.created))[0]
        except:
            return abort(404)
    elif post == "last_seen":
        try:
            last_seen = arrow.get(topic.last_seen_by.get(str(current_user._get_current_object().id), arrow.utcnow().timestamp)).datetime
        except:
            last_seen = arrow.get(arrow.utcnow().timestamp).datetime

        try:
            post = sqla.session.query(sqlm.PrivateMessageReply).filter_by(pm=topic) \
                .filter(sqlm.PrivateMessageReply.created < last_seen) \
                .order_by(sqlm.PrivateMessageReply.created.desc())[0]
        except IndexError:
            try:
                post = sqla.session.query(sqlm.PrivateMessageReply).filter_by(pm=topic, id=post)[0]
            except IndexError:
                return abort(404)
    else:
        if post != "":
            try:
                post = sqla.session.query(sqlm.PrivateMessageReply).filter_by(pm=topic, id=post)[0]
            except IndexError:
                return abort(404)
        else:
            post = ""

    pagination = 20

    if post != "":
        try:
            topic.last_seen_by[str(current_user._get_current_object().id)] = arrow.utcnow().timestamp
            sqla.session.add(topic)
            sqla.session.commit()
        except:
            pass
        target_date = post.created
        posts_before_target = sqla.session.query(sqlm.PrivateMessageReply).filter_by(pm=topic) \
            .filter(sqlm.PrivateMessageReply.created < post.created) \
            .count()

        page = int(math.floor(float(posts_before_target)/float(pagination)))+1
        return render_template("core/messages_topic.jade", page_title="%s - Scarlet's Web" % (unicode(topic.title),), topic=topic, initial_page=page, initial_post=str(post.id))

    try:
        topic.last_seen_by[str(current_user._get_current_object().id)] = arrow.utcnow().timestamp
        sqla.session.add(topic)
        sqla.session.commit()
    except:
        pass

    return render_template("core/messages_topic.jade", page_title="%s - Scarlet's Web" % (unicode(topic.title),), topic=topic, initial_page=page,)

@app.route('/new-message', methods=['POST'])
@login_required
def create_message():
    request_json = request.get_json(force=True)

    if len(request_json.get("title", "").strip()) == 0:
        return app.jsonify(error="Please enter a title.")

    if request_json.get("text", "").strip() == "":
        return app.jsonify(error="Please enter actual text for your message.")

    if request_json.get("to") == None or not len(request_json.get("to", [""])) > 0:
        return app.jsonify(error="Choose who should receive your message.")

    topic = sqlm.PrivateMessage()
    topic.title = request_json.get("title", "").strip()
    topic.count = 1
    topic.author = current_user._get_current_object()
    topic.created = arrow.utcnow().datetime.replace(tzinfo=None)
    topic.last_seen_by = {}
    sqla.session.add(topic)
    sqla.session.commit()

    message = sqlm.PrivateMessageReply()
    message.message = request_json.get("html", "").strip()
    message.author = current_user._get_current_object()
    message.created = arrow.utcnow().datetime.replace(tzinfo=None)
    message.pm = topic
    message.pm_title = topic.title
    sqla.session.add(message)
    sqla.session.commit()

    topic.last_reply = message
    sqla.session.add(topic)
    sqla.session.commit()

    participant = sqlm.PrivateMessageUser(
            author = current_user._get_current_object(),
            pm = topic
        )
    sqla.session.add(participant)
    sqla.session.commit()

    to_notify = []

    for user_pk in request_json.get("to"):
        if user_pk == current_user._get_current_object().id:
            continue

        try:
            u = sqla.session.query(sqlm.User).filter_by(id=user_pk)[0]

            try:
                ignore_setting = sqla.session.query(sqlm.IgnoringUser).filter_by(
                        user = u,
                        ignoring = current_user._get_current_object()
                    )[0]

                if ignore_setting.block_pms:
                    return app.jsonify(error="You can not send a message to %s." % (u.display_name,))
            except IndexError:
                pass

            if u.banned:
                return app.jsonify(error="%s is banned, they will not receive your message." % (u.display_name,))

            if current_user._get_current_object() == u:
                return app.jsonify(error="Stop talking to yourself! (Remove yourself from the \"to\" list.)")

            new_participant = sqlm.PrivateMessageUser(
                    author = u,
                    pm = topic
                )
            sqla.session.add(new_participant)
            sqla.session.commit()
            to_notify.append(u)
        except IndexError:
            continue



    broadcast(
        to=to_notify,
        category="pm",
        url="/messages/"+str(topic.id),
        title="New Message: "+unicode(topic.title),
        description=message.message,
        content=topic,
        author=message.author
        )

    return app.jsonify(url="/messages/"+str(topic.id))

@app.route('/new-message', methods=['GET'], defaults={'target': False})
@app.route('/new-message/<target>', methods=['GET'])
@login_required
def create_message_index(target):
    if target:
        try:
            target_user = sqla.session.query(sqlm.User).filter_by(login_name=target)[0]
        except IndexError:
            target_user = None
            pass

    return render_template("core/new_message.jade", target_user=target_user, page_title="New Private Message - Scarlet's Web")

@app.route('/message-topics', methods=['POST'])
@login_required
def messages_topics():
    request_json = request.get_json(force=True)
    page = request_json.get("page", 1)
    pagination = request_json.get("pagination", 20)

    if page < 1:
        page = 1

    try:
        minimum = (int(page)-1)*int(pagination)
        maximum = int(page)*int(pagination)
    except:
        minimum = 0
        maximum = 20

    messages_count = sqla.session.query(sqlm.PrivateMessage) \
        .join(sqlm.PrivateMessageUser.pm) \
        .filter(
            sqlm.PrivateMessageUser.author == current_user._get_current_object(),
            sqlm.PrivateMessageUser.blocked == False,
            sqlm.PrivateMessageUser.exited == False
            ).count()

    messages = sqla.session.query(sqlm.PrivateMessage) \
        .join(sqlm.PrivateMessageUser.pm) \
        .filter(
            sqlm.PrivateMessageUser.author == current_user._get_current_object(),
            sqlm.PrivateMessageUser.blocked == False,
            sqlm.PrivateMessageUser.exited == False
            ) \
        .join(sqlm.PrivateMessage.last_reply) \
        .order_by(sqlm.PrivateMessageReply.created.desc())[minimum:maximum]

    parsed_messages = []

    for message in messages:
        _parsed = {}

        pm_participants = sqla.session.query(sqlm.PrivateMessageUser).filter_by(
                    pm = message
                ).filter(sqlm.PrivateMessageUser.author!=current_user).all()

        last_viewed = sqla.session.query(sqlm.PrivateMessageUser.last_viewed).filter_by(
                    pm = message,
                    author=current_user
                )[0]

        _parsed["participants"] = [[u.author.login_name, u.author.display_name, ", "] for u in pm_participants]
        _parsed["participants"][-1][2] = ""

        _parsed["creator"] = message.author.display_name
        _parsed["created"] = humanize_time(message.created, "MMM D YYYY")

        if last_viewed[0] == None:
            _parsed["new_messages"] = False
        elif last_viewed[0] < message.last_reply.created and message.last_reply.author != current_user:
            _parsed["new_messages"] = True
        else:
            _parsed["new_messages"] = False

        _parsed["last_post_date"] = humanize_time(message.last_reply.created)
        _parsed["last_post_by"] = message.last_reply.author.display_name
        _parsed["last_post_x"] = message.last_reply.author.avatar_40_x
        _parsed["last_post_y"] = message.last_reply.author.avatar_40_y
        _parsed["last_post_by_login_name"] = message.last_reply.author.login_name
        _parsed["last_post_author_avatar"] = message.last_reply.author.get_avatar_url("40")
        _parsed["message_count"] = "{:,}".format(message.count)
        _parsed["_id"] = message.id
        _parsed["title"] = message.title
        try:
            _parsed["last_page"] = float(message.count)/float(pagination)
        except:
            _parsed["last_page"] = 1
        _parsed["last_pages"] = _parsed["last_page"] > 1
        parsed_messages.append(_parsed)

    return app.jsonify(topics=parsed_messages, count=messages_count)

@app.route('/messages', methods=['GET'])
@login_required
def messages_index():
    return render_template("core/messages.jade", page_title="Your Private Messages - Scarlet's Web")
