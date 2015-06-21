from woe import login_manager, app
from woe.models.core import User, Notification
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from woe.utilities import get_top_frequences, scrub_json, humanize_time, ForumHTMLCleaner, parse_search_string_return_q
from flask.ext.login import login_required, current_user
import arrow, urllib2
import json as py_json

def broadcast(to, category, url, title, description, content, author, priority=0):
    if category not in [x[0] for x in Notification.NOTIFICATION_CATEGORIES]:
        raise TypeError("Category is not defined in NOTIFICATION_CATEGORIES.")
    
    if to == "ALL":
        to = User.objects()
        
    now = arrow.utcnow()
    author = author
    
    for u in to:
        try:
            if not type(u) == User:
                user = User.objects(login_name=to)[0]
            else:
                user = u
            try:
                if current_user._get_current_object() == user:
                    continue
            except:
                pass
        except IndexError:
            continue
        
        if not user.notification_preferences.get(category, {"dashboard": True}).get("dashboard"):
            continue
            
        if author in u.ignored_users:
            continue
            
        new_notification = Notification(
            category = category,
            user = user,
            user_name = user.login_name,
            author = author,
            author_name = author.login_name,
            created = now.datetime,
            url = url,
            text = title,
            description = description,
            priority = priority
        )
        
        if content != None:
            new_notification.content = content
        new_notification.save()
        
        data = {
            "users": [u.login_name, ],
            "count": u.get_notification_count(),
            "category": category,
            "author": author.display_name,
            "member_name": author.login_name,
            "member_pk": author.pk,
            "member_disp_name": author.display_name,
            "author_url": "/member/"+author.login_name,
            "time": humanize_time(now.datetime),
            "url": url,
            "stamp": arrow.get(new_notification.created).timestamp,
            "text": title,
            "priority": priority,
            "_id": str(new_notification.pk)
        }
        try:
            data["reference"] = str(new_notification.content.pk)
        except:
            data["reference"] = ""
        req = urllib2.Request(app.settings_file["listener"]+"/notify")
        req.add_header('Content-Type', 'application/json')
        response = urllib2.urlopen(req, py_json.dumps(data))

@app.route('/dashboard/ack_category', methods=["POST",])
@login_required
def acknowledge_category():
    request_json = request.get_json(force=True)
    notifications = Notification.objects(user=current_user._get_current_object(), acknowledged=False, category=request_json.get("category",""))
    notifications.update(acknowledged=True)
    return app.jsonify(success=True)

@app.route('/dashboard/ack_notification', methods=["POST",])
@login_required
def acknowledge_notification():
    request_json = request.get_json(force=True)
    try:
        notification = Notification.objects(pk=request_json.get("notification",""))[0]
    except:
        return app.jsonify(success=False)
    notification.update(acknowledged=True)
    
    try:
        notifications = Notification.objects(user=current_user._get_current_object(), acknowledged=False, content=notification.content, author=notification.author)
        notifications.update(acknowledged=True)
    except:
        return app.jsonify(success=False)
    
    return app.jsonify(success=True)

@app.route('/dashboard/notifications', methods=["POST",])
@login_required
def dashboard_notifications():
    notifications = Notification.objects(user=current_user._get_current_object(), acknowledged=False)
    parsed_notifications = []
    
    for notification in notifications:
        parsed_ = notification.to_mongo().to_dict()
        parsed_["time"] = humanize_time(notification.created)
        parsed_["stamp"] = arrow.get(notification.created).timestamp
        parsed_["member_disp_name"] = notification.author.display_name
        parsed_["member_name"] = notification.author.login_name
        parsed_["member_pk"] = notification.author.pk
        parsed_notifications.append(parsed_)
        
    return app.jsonify(notifications=parsed_notifications)

@app.route('/dashboard')
@login_required
def view_dashboard():
    return render_template("dashboard.jade", page_title="Your Dashboard - World of Equestria")