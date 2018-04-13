from woe import login_manager, app
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from woe.utilities import get_top_frequences, scrub_json, humanize_time, ForumHTMLCleaner, parse_search_string_return_q, CategoryPermissionCalculator, md5
from flask.ext.login import login_required, current_user
import arrow, urllib2
from threading import Thread
import json as py_json
from woe import sqla
import woe.sqlmodels as sqlm
import hashlib
from sqlalchemy.orm.attributes import flag_modified
import time

def send_message(data):
    req = urllib2.Request(app.settings_file["talker_path"]+"/notify")
    req.add_header('Content-Type', 'application/json')
    response = urllib2.urlopen(req, py_json.dumps(data))

def broadcast(to, category, url, title, description, content, author, priority=0):
    
    # Hack for hidden areas of the forum
    try:
        if content.hidden == True:
            return
    except:
        pass
        
    if category not in [x[0] for x in sqlm.Notification.NOTIFICATION_CATEGORIES]:
        raise TypeError("Category is not defined in NOTIFICATION_CATEGORIES.")

    if to == "ALL":
        to = sqla.session.query(sqlm.User).filter_by(banned=False).all()

    now = arrow.utcnow()
    author = author

    send_to_logins = []
    notification_counts = {}
    dashboard_notifications = {}
    notification_ids = {}
    timestamp = None
    reference = None

    for u in to:
        try:
            if not type(u) == sqlm.User:
                user = sqla.session.query(sqlm.User).filter_by(banned=False).filter_by(login_name=u)[0]
            else:
                user = u
            try:
                if current_user._get_current_object() == user:
                    continue
            except:
                pass
        except IndexError:
            continue
        
        if type(content) == sqlm.Category:
            cat_perm_calculus = CategoryPermissionCalculator(user)
            if not cat_perm_calculus.can_view_topics(content.id, content.can_view_topics):
                return abort(404)
                
        if type(content) == sqlm.Topic:
            cat_perm_calculus = CategoryPermissionCalculator(user)
            if not cat_perm_calculus.can_view_topics(content.category.id, content.category.can_view_topics):
                return abort(404)

        if user.notification_preferences is None:
            user.notification_preferences = {}
            flag_modified(user, "notification_preferences")
            sqla.session.add(user)
            sqla.session.commit()

        if not user.notification_preferences.get(category, {"dashboard": True}).get("dashboard"):
            continue

        try:
            ignore = sqla.session.query(sqlm.IgnoringUser).filter_by(user=user, ignoring=author)[0]
            continue
        except:
            pass

        new_notification = sqlm.Notification(
            category = category,
            user = user,
            author = author,
            created = now.datetime.replace(tzinfo=None),
            url = url,
            message = title,
            priority = priority,
            snippet = description
        )

        sqla.session.add(new_notification)
        sqla.session.commit()

        send_to_logins.append(u.listener_token)
        notification_counts[u.listener_token] = u.get_notification_count()
        notification_ids[u.listener_token] = new_notification.id
        dashboard_notifications[u.listener_token] = u.get_dashboard_notifications()
        timestamp = new_notification.created

    data = {
        "users": send_to_logins,
        "count": notification_counts,
        "dashboard_count": dashboard_notifications,
        "category": category,
        "author": author.display_name,
        "member_name": author.login_name,
        "member_pk": unicode(author.id),
        "member_disp_name": author.display_name,
        "author_url": "/member/"+author.my_url,
        "author_avatar": author.get_avatar_url("40"),
        "time": humanize_time(now.datetime),
        "url": url,
        "stamp": humanize_time(timestamp),
        "text": title,
        "priority": priority,
        "id": notification_ids,
        "ref": reference
    }
    data["ref"] = md5(url+title)

    thread = Thread(target=send_message, args=(data, ))
    thread.start()

@app.route('/dashboard/ack_category', methods=["POST",])
@login_required
def acknowledge_category():
    notifications = sqla.session.query(sqlm.Notification) \
        .filter_by(seen=False, user=current_user._get_current_object()) \
        .update({sqlm.Notification.seen: True})

    request_json = request.get_json(force=True)

    notifications = sqla.session.query(sqlm.Notification) \
        .filter_by(acknowledged=False, user=current_user._get_current_object(), category=request_json.get("category","")) \
        .update({sqlm.Notification.acknowledged: True})

    _count = current_user._get_current_object().get_notification_count()
    thread = Thread(target=send_message, args=({"users": [current_user._get_current_object().login_name, ], "count_update": _count}, ))
    thread.start()
    return app.jsonify(success=True, count=_count)

@app.route('/dashboard/mark_seen', methods=["POST",])
@login_required
def mark_all_notifications():
    notifications = sqla.session.query(sqlm.Notification) \
        .filter_by(seen=False, user=current_user._get_current_object()) \
        .update({sqlm.Notification.seen: True})

    _count = current_user._get_current_object().get_notification_count()
    thread = Thread(target=send_message, args=({"users": [current_user._get_current_object().login_name, ], "count_update": _count}, ))
    thread.start()

    return app.jsonify(success=True)

@app.route('/dashboard/acknowledge_all', methods=["POST",])
@login_required
def ack_all_notifications():
    notifications = sqla.session.query(sqlm.Notification) \
        .filter_by(user=current_user._get_current_object()) \
        .update({
            sqlm.Notification.acknowledged: True,
            sqlm.Notification.seen: True,
            sqlm.Notification.emailed: True,
            })

    _count = 0
    thread = Thread(target=send_message, args=({"users": [current_user._get_current_object().login_name, ], "count_update": _count}, ))
    thread.start()

    return app.jsonify(success=True, url="/dashboard")

@app.route('/dashboard/ack_notification', methods=["POST",])
@login_required
def acknowledge_notification():
    notifications = sqla.session.query(sqlm.Notification) \
        .filter_by(seen=False, user=current_user._get_current_object()) \
        .update({sqlm.Notification.seen: True})

    request_json = request.get_json(force=True)
    try:
        notification = sqla.session.query(sqlm.Notification) \
            .filter_by(id=request_json.get("notification",""))[0]

        if notification.user != current_user._get_current_object():
            return app.jsonify(success=False)

        sqla.session.query(sqlm.Notification) \
            .filter_by(id=request_json.get("notification","")) \
            .update({sqlm.Notification.acknowledged: True})
    except:
        return app.jsonify(success=False)

    try:
        notifications = sqla.session.query(sqlm.Notification) \
            .filter_by(acknowledged=False, user=current_user._get_current_object(), url=notification.url) \
            .update({sqlm.Notification.acknowledged: True})
    except:
        return app.jsonify(success=False)

    _count = current_user._get_current_object().get_notification_count()
    thread = Thread(target=send_message, args=({"users": [current_user._get_current_object().login_name, ], "count_update": _count}, ))
    thread.start()
    return app.jsonify(success=True, count=_count)

@app.route('/dashboard/notifications', methods=["POST",])
@login_required
def dashboard_notifications():
    notifications = sqla.session.query(sqlm.Notification) \
        .filter_by(
            user=current_user._get_current_object(),
            acknowledged=False) \
        .order_by(sqla.desc(sqlm.Notification.created)).all()
    parsed_notifications = []

    for notification in notifications:
        try:
            parsed_ = {}
            parsed_["time"] = humanize_time(notification.created)
            parsed_["stamp"] = arrow.get(notification.created).timestamp
            parsed_["member_disp_name"] = notification.author.display_name
            parsed_["member_name"] = notification.author.my_url
            parsed_["member_pk"] = unicode(notification.author.id)
            parsed_["text"] = notification.message
            parsed_["id"] = notification.id
            parsed_["_id"] = notification.id
            parsed_["category"] = notification.category
            parsed_["url"] = notification.url
            parsed_["ref"] = md5(notification.url+notification.message)
            parsed_notifications.append(parsed_)
        except AttributeError:
            pass

    return app.jsonify(notifications=parsed_notifications)

@app.route('/dashboard')
@login_required
def view_dashboard():
    if current_user.is_admin:
        _followed_topics = sqla.session.query(sqlm.Topic) \
            .join(sqlm.topic_watchers_table) \
            .join(sqlm.Topic.recent_post) \
            .filter(sqlm.topic_watchers_table.c.user_id == current_user.id) \
            .order_by(sqlm.Post.created.desc())[:5]
    else:
        _followed_topics = sqla.session.query(sqlm.Topic) \
            .join(sqlm.topic_watchers_table) \
            .join(sqlm.Topic.recent_post) \
            .filter(sqlm.topic_watchers_table.c.user_id == current_user.id) \
            .filter(sqlm.Topic.category.has(sqlm.Category.restricted==False)) \
            .order_by(sqlm.Post.created.desc())[:5]

    _followed_blogs = sqla.session.query(sqlm.Blog) \
        .join(sqlm.blog_subscriber_table) \
        .join(sqlm.Blog.recent_entry) \
        .filter(sqlm.blog_subscriber_table.c.user_id == current_user.id) \
        .filter(sqlm.Blog.disabled.isnot(True)) \
        .filter(sqlm.BlogEntry.draft.isnot(True)) \
        .filter(sqlm.BlogEntry.published.isnot(None)) \
        .filter(sqla.or_(
            sqlm.Blog.privacy_setting == "all",
            sqlm.Blog.privacy_setting == "members"
        )) \
        .order_by(sqla.desc(sqlm.BlogEntry.published))[:5]

    return render_template("dashboard.jade",
        followed_topics = _followed_topics,
        followed_blogs = _followed_blogs,
        page_title="Your Dashboard - %%GENERIC SITENAME%%"
        )
