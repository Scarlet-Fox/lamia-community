from woe import app
from woe.parsers import ForumPostParser
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session, send_from_directory
from flask.ext.login import login_required, current_user
from woe.utilities import scrub_json, humanize_time, ForumHTMLCleaner, parse_search_string_return_q, parse_search_string, get_preview_for_email
from mongoengine.queryset import Q
import arrow, json
from woe.views.dashboard import broadcast
from woe import sqla
import woe.sqlmodels as sqlm

@app.route('/status/<status>/replies', methods=['GET'])
def status_update_replies(status):
    try:
        status = sqla.session.query(sqlm.StatusUpdate).filter_by(id=status)[0]
    except:
        return abort(404)

    if status.hidden == True and (current_user._get_current_object().is_admin != True or current_user._get_current_object().is_mod != True):
        return abort(404)

    replies = []
    for reply in sqla.session.query(sqlm.StatusComment).filter_by(status=status, hidden=False).order_by(sqlm.StatusComment.created):
        parsed_reply = {}
        parsed_reply["text"] = reply.message
        parsed_reply["user_name"] = reply.author.display_name
        parsed_reply["author_login_name"] = reply.author.login_name
        parsed_reply["user_avatar"] = reply.author.get_avatar_url("40")
        parsed_reply["user_avatar_x"] = reply.author.avatar_40_x
        parsed_reply["user_avatar_y"] = reply.author.avatar_40_y
        parsed_reply["is_admin"] = current_user.is_admin
        parsed_reply["time"] = humanize_time(reply.created)
        parsed_reply["idx"] = reply.id
        replies.append(parsed_reply)

    return app.jsonify(replies=replies, count=status.get_comment_count())

@app.route('/status/<status>', methods=['GET'])
def display_status_update(status):
    try:
        status = sqla.session.query(sqlm.StatusUpdate).filter_by(id=status)[0]
    except:
        return abort(404)

    if status.hidden == True and (current_user._get_current_object().is_admin != True or current_user._get_current_object().is_mod != True):
        return abort(404)

    if current_user._get_current_object().is_admin == True:
        mod = True
    else:
        mod = False

    status.last_viewed=arrow.utcnow().datetime.replace(tzinfo=None)

    sqla.session.add(status)
    sqla.session.commit()

    return render_template(
        "status_update.jade",
        page_title="%s - %s's Status Update - Casual Anime" % (
            get_preview_for_email(status.message),
            unicode(status.author.display_name)),
            status=status,
            mod=mod
        )

@app.route('/clear-status-updates', methods=['POST',])
@login_required
def clear_status_update_parameters():
    session["count"] = 15
    session["authors"] = []
    session["search"] = ""

    return app.jsonify(url="/status-updates")

@app.route('/status-updates', methods=['GET', 'POST'])
@login_required
def status_update_index():
    count = session.get("count", 15)
    authors = session.get("authors", [])
    search = session.get("search", "")

    if request.method == 'POST':
        request_json = request.get_json(force=True)

        count = int(request_json.get("count", 15))
        if count > 1000:
            count = 1000
        session["count"] = count

        search = request_json.get("search", "")[0:100]
        session["search"] = search

        if request_json.get("authors"):
            author_objects = list(
                        sqla.session.query(sqlm.User) \
                            .filter(sqlm.User.id.in_(request_json.get("authors"))) \
                            .all()
                    )
            session["authors"] = [{"id": a.id, "text": a.display_name} for a in author_objects]
            authors = [{"id": a.id, "text": a.display_name} for a in author_objects]

    query_ = sqla.session.query(sqlm.StatusUpdate).filter_by(hidden=False)
    if authors:
        query_ = query_.filter(sqlm.StatusUpdate.author_id.in_([a["id"] for a in authors]))
    status_updates = parse_search_string(search, sqlm.StatusUpdate, query_, ["message",]).order_by(sqla.desc(sqlm.StatusUpdate.created))[:count]

    if request.method == 'POST':
        parsed_statuses = []
        for status in status_updates:
            parsed_status = {}

            parsed_status["_id"] = status.id
            parsed_status["profile_address"] = url_for('view_profile', login_name=status.author.login_name)
            parsed_status["user_name"] = status.author.display_name
            parsed_status["message"] = status.message
            parsed_status["user_avatar"] = status.author.get_avatar_url("40")
            if status.attached_to_user != None:
                parsed_status["attached_to_user"] = status.attached_to_user.display_name
                parsed_status["attached_to_user_url"] = url_for('view_profile', login_name=status.attached_to_user.login_name)
            else:
                parsed_status["attached_to_user"] = False
            parsed_status["user_avatar_x"] = status.author.avatar_40_x
            parsed_status["user_avatar_y"] = status.author.avatar_40_y
            parsed_status["created"] = humanize_time(status.created)
            parsed_status["comment_count"] = status.get_comment_count()
            parsed_statuses.append(parsed_status)
        return app.jsonify(status_updates=parsed_statuses)
    else:
        return render_template("core/status_index.jade", page_title="Status Updates - Casual Anime", status_updates=status_updates, count=count, search=search, authors=json.dumps(authors))

@app.route('/status/<status>/reply', methods=['POST'])
@login_required
def make_status_update_reply(status):
    try:
        status = sqla.session.query(sqlm.StatusUpdate).filter_by(id=status)[0]
    except:
        return abort(404)

    if status.hidden == True and (current_user._get_current_object().is_admin != True or current_user._get_current_object().is_mod != True):
        return abort(404)

    if status.muted and current_user._get_current_object() != status.author:
        return app.jsonify(error="This status update is silenced. Shhh!")

    if (current_user in [u.ignoring for u in status.author.ignored_users]) and not current_user.is_admin:
        return app.jsonify(error="User has blocked you.")

    try:
        if not (current_user._get_current_object().is_admin or current_user._get_current_object().is_mod) and \
                (sqla.session.query(sqlm.StatusUpdateUser). \
                filter_by(status=status, author=current_user._get_current_object())[0].blocked):
            return app.jsonify(error="You have been blocked from this status update.")
    except IndexError:
        pass

    if status.locked:
        return app.jsonify(error="This status update is locked.")

    if status.get_comment_count() > 199:
        return app.jsonify(error="This status update is full!")

    request_json = request.get_json(force=True)

    if request_json.get("reply", "").strip() == "":
        return app.jsonify(error="Your status update is empty.")

    cleaner = ForumHTMLCleaner()
    try:
        _html = cleaner.escape(request_json.get("reply", ""))
    except:
        return abort(500)

    user_last_comment = False
    for comment in status.comments:
        if comment.author == current_user._get_current_object():
            user_last_comment = comment
    if user_last_comment:
        difference = (arrow.utcnow().datetime - arrow.get(user_last_comment.created).datetime).seconds
        if difference < 5:
            return app.jsonify(error="Please wait %s seconds before you can reply again." % (5 - difference))

    sc = sqlm.StatusComment()
    sc.created = arrow.utcnow().datetime.replace(tzinfo=None)
    sc.message = _html
    sc.author = current_user._get_current_object()
    sc.status = status

    sqla.session.add(sc)
    sqla.session.commit()

    status.replies = status.get_comment_count()
    status.last_replied = arrow.utcnow().datetime.replace(tzinfo=None)

    sqla.session.add(status)
    sqla.session.commit()

    if not current_user._get_current_object() in status.participants:
        status.participants.append(current_user._get_current_object())

    clean_html_parser = ForumPostParser()
    parsed_reply = {}
    parsed_reply["text"] = sc.message
    parsed_reply["user_name"] = sc.author.display_name
    parsed_reply["user_avatar"] = sc.author.get_avatar_url("40")
    parsed_reply["user_avatar_x"] = sc.author.avatar_40_x
    parsed_reply["author_login_name"] = sc.author.login_name
    parsed_reply["user_avatar_y"] = sc.author.avatar_40_y
    parsed_reply["time"] = humanize_time(sc.created)

    send_notify_to_users = []
    for user in sqla.session.query(sqlm.StatusUpdateUser).filter_by(status=status).all():
        if user.author == current_user._get_current_object():
            continue

        if user.ignoring:
            continue

        if user.author == status.author:
            continue

        send_notify_to_users.append(user.author)

    broadcast(
        to=send_notify_to_users,
        category="status",
        url="/status/"+str(status.id),
        title="%s replied to %s's status update" % (
            unicode(current_user._get_current_object().display_name),
            unicode(status.author.display_name),
            ),
        description=status.message,
        content=status,
        author=current_user._get_current_object()
        )

    if current_user._get_current_object() != status.author:
        broadcast(
            to=[status.author],
            category="status",
            url="/status/"+str(status.id),
            title="%s replied to your status update" % (unicode(current_user._get_current_object().display_name)),
            description=status.message,
            content=status,
            author=current_user._get_current_object()
            )

    return app.jsonify(newest_reply=parsed_reply, count=status.get_comment_count(), success=True)

@app.route('/create-status', methods=['POST'], defaults={'target': False})
@app.route('/create-status/<target>', methods=['POST'])
@login_required
def create_new_status(target):
    request_json = request.get_json(force=True)
    attached_to_user = False

    if target:
        try:
            target_user = sqla.session.query(sqlm.User).filter_by(login_name=target)[0]
            if target_user == current_user._get_current_object():
                return app.jsonify(error="No talking to yourself.")

            if (current_user in [u.ignoring for u in target_user.ignored_users]) and not current_user.is_admin:
                return app.jsonify(error="User has blocked you.")

            attached_to_user = target_user
        except IndexError:
            target_user = None
    else:
        target_user = None

    if len(request_json.get("message", "").strip()) == 0:
        return app.jsonify(error="Your status update is empty.")

    cleaner = ForumHTMLCleaner()
    try:
        _html = cleaner.escape(request_json.get("message", "").strip())
    except:
        return abort(500)

    status = sqlm.StatusUpdate()
    if attached_to_user:
        status.attached_to_user = attached_to_user
        status.participants.append(attached_to_user)
    status.author = current_user._get_current_object()
    status.message = _html
    status.participants.append(status.author)
    status.created = arrow.utcnow().datetime.replace(tzinfo=None)
    status.replies = 0
    sqla.session.add(status)
    sqla.session.commit()

    if target_user:
        broadcast(
          to=[target_user,],
          category="profile_comment",
          url="/status/"+unicode(status.id),
          title="%s has commented on your profile" % (unicode(status.author.display_name),),
          description=status.message,
          content=status,
          author=status.author
          )

    send_notify_to_users = []
    for user in status.author.followed_by():
        if target_user:
            if user == target_user:
                continue
        send_notify_to_users.append(user)

    broadcast(
      to=send_notify_to_users,
      category="user_activity",
      url="/status/"+unicode(status.id),
      title="%s created a status update" % (unicode(status.author.display_name),),
      description=status.message,
      content=status,
      author=status.author
      )

    return app.jsonify(url="/status/"+unicode(status.id))

@app.route('/status/<status>/hide-reply/<idx>', methods=['POST'])
@login_required
def status_hide_reply(status, idx):
    try:
        comment = sqla.session.query(sqlm.StatusComment).filter_by(id=idx)[0]
    except:
        return abort(404)

    if (current_user._get_current_object().is_admin != True or current_user._get_current_object().is_mod != True):
        return abort(404)

    comment.hidden = True
    sqla.session.add(comment)
    sqla.session.commit()

    return app.jsonify(success=True)

@app.route('/status/<status>/toggle-silence/<user>', methods=['POST'])
@login_required
def toggle_status_blocking(status, user):
    try:
        status = sqla.session.query(sqlm.StatusUpdate).filter_by(id=status)[0]
        user = sqla.session.query(sqlm.User).filter_by(id=user)[0]
    except:
        return abort(404)

    if (current_user._get_current_object().is_admin != True or current_user._get_current_object().is_mod != True):
        return abort(404)

    if user == current_user._get_current_object():
        return abort(404)

    status_user = sqla.session.query(sqlm.StatusUpdateUser).filter_by(
        author=user, status=status)[0]

    status_user.blocked = not status_user.blocked

    sqla.session.add(status_user)
    sqla.session.commit()

    return app.jsonify(url="/status/"+unicode(status.id))

@app.route('/status/<status>/toggle-ignore', methods=['POST'])
@login_required
def toggle_status_ignoring(status):
    try:
        status = sqla.session.query(sqlm.StatusUpdate).filter_by(id=status)[0]
    except:
        return abort(404)

    try:
        status_user = sqla.session.query(sqlm.StatusUpdateUser).filter_by(status=status, author=current_user._get_current_object())[0]
    except IndexError:
        status_user = None

    if not status_user:
        try:
            status.participants.append(current_user._get_current_object())
            return app.jsonify(url="/status/"+str(status.id))
        except:
            return app.jsonify(url="/status/"+str(status.id))

    status_user.ignoring = not status_user.ignoring

    sqla.session.add(status_user)
    sqla.session.commit()

    return app.jsonify(url="/status/"+unicode(status.id))

@app.route('/status/<status>/toggle-hidden', methods=['POST'])
@login_required
def toggle_status_hide(status):
    try:
        status = sqla.session.query(sqlm.StatusUpdate).filter_by(id=status)[0]
    except:
        return abort(404)

    if current_user._get_current_object().is_admin != True or current_user._get_current_object().is_mod != True:
        return abort(404)

    if not status.hidden:
        if current_user._get_current_object() != status.author:
            broadcast(
                to=[status.author,],
                category="status",
                url="/status/"+str(status.id),
                title="Your status update was hidden",
                description=status.message,
                content=status,
                author=current_user._get_current_object()
                )

        broadcast(
            to=list(User.objects(is_admin=True)),
            category="mod",
            url="/status/"+str(status.id),
            title="%s's status update hidden" % (unicode(status.author.display_name),),
            description=status.message,
            content=status,
            author=current_user._get_current_object()
            )

    status.hidden=not status.hidden
    sqla.session.add(status)
    sqla.session.commit()
    return app.jsonify(url="/status/"+unicode(status.id))

@app.route('/status/<status>/toggle-mute', methods=['POST'])
@login_required
def toggle_status_mute(status):
    try:
        status = sqla.session.query(sqlm.StatusUpdate).filter_by(id=status)[0]
    except:
        return abort(404)

    if current_user._get_current_object() != status.author and (current_user._get_current_object().is_admin != True or current_user._get_current_object().is_mod != True):
        return abort(404)

    status.muted=not status.muted
    sqla.session.add(status)
    sqla.session.commit()
    return app.jsonify(url="/status/"+unicode(status.id))

@app.route('/status/<status>/toggle-lock', methods=['POST'])
@login_required
def toggle_status_lock(status):
    try:
        status = sqla.session.query(sqlm.StatusUpdate).filter_by(id=status)[0]
    except:
        return abort(404)

    if current_user._get_current_object().is_admin != True or current_user._get_current_object().is_mod != True:
        return abort(404)

    status.locked=not status.locked
    sqla.session.add(status)
    sqla.session.commit()
    return app.jsonify(url="/status/"+unicode(status.id))
