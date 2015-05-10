from woe import login_manager, app
from woe.models.core import User, Notification
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from flask.ext.login import login_required
import arrow

def broadcast(to, category, url, title, description, content, author):
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
        except IndexError:
            continue
        
        if not user.notification_preferences.get(category, {"dashboard": True}).get("dashboard"):
            continue
            
        if author in u.ignored_users:
            continue
            
        new_notification = Notification(
            category = category,
            user = user,
            author = author,
            created = now.datetime,
            url = url,
            text = title,
            description = description,
            content = content
        )
        new_notification.save()

@app.route('/dashboard')
@login_required
def view_dashboard():
    return render_template("dashboard.jade")