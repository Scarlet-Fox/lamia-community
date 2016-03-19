from woe import app
from woe.parsers import ForumPostParser
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session, send_from_directory
from flask.ext.login import login_required, current_user
from woe.utilities import scrub_json, humanize_time, ForumHTMLCleaner, parse_search_string_return_q
from mongoengine.queryset import Q
import arrow, json
from woe.views.dashboard import broadcast
from woe import sqla
import woe.sqlmodels as sqlm

@app.route('/status/<status>/replies', methods=['GET'])
@login_required
def status_update_replies(status):
    try:
        status = sqla.session.query(sqlm.StatusUpdate).filter_by(id=status)[0]
    except:
        return abort(404)

    if status.hidden == True and (current_user._get_current_object().is_admin != True or current_user._get_current_object().is_mod != True):
        return abort(404)

    replies = []
    for reply in sqla.session.query(sqlm.StatusComment).filter_by(status=status, hidden=False):
        parsed_reply = {}
        parsed_reply["text"] = reply.message
        parsed_reply["user_name"] = reply.author.display_name
        parsed_reply["author_login_name"] = reply.author.login_name
        parsed_reply["user_avatar"] = reply.author.get_avatar_url("40")
        parsed_reply["user_avatar_x"] = reply.author.avatar_40_x
        parsed_reply["user_avatar_y"] = reply.author.avatar_40_y
        parsed_reply["time"] = humanize_time(reply.created)
        parsed_reply["idx"] = reply.id
        replies.append(parsed_reply)

    return app.jsonify(replies=replies, count=status.get_comment_count())

@app.route('/status/<status>', methods=['GET'])
@login_required
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

    # has_viewed = False
    # for viewer in status.viewing:
    #     if viewer.user == current_user._get_current_object():
    #         viewer.last_seen = arrow.utcnow().datetime
    #         has_viewed = True
    #
    # if has_viewed == False:
    #     status.viewing.append(StatusViewer(user=current_user._get_current_object(), last_seen=arrow.utcnow().datetime))

    return render_template("status_update.jade", page_title="%s's Status Update - %s - Scarlet's Web" % (unicode(status.author.display_name), humanize_time(status.created)), status=status, mod=mod)

@app.route('/clear-status-updates', methods=['POST',])
@login_required
def clear_status_update_parameters():
    session["count"] = 40
    session["authors"] = []
    session["search"] = ""

    return app.jsonify(url="/status-updates")

@app.route('/status-updates', methods=['GET', 'POST'])
@login_required
def status_update_index():
    count = session.get("count", 40)
    authors = session.get("authors", [])
    search = session.get("search", "")

    if request.method == 'POST':
        request_json = request.get_json(force=True)

        try:
            count = int(request_json.get("count"), 10)
            if count > 1000:
                count = 1000
            session["count"] = count
        except:
            pass

        try:
            authors = request_json.get("authors", [])
            session["authors"] = authors
        except:
            pass

        try:
            search = request_json.get("search", "")[0:100]
            session["search"] = search
        except:
            pass

    query = {}

    try:
        users = User.objects(pk__in=authors)
        authors = [{"id": unicode(u.id), "text": u.display_name} for u in users]
    except:
        users = []
        authors = []

    user_q_ = Q()
    if len(users) > 0:
        user_q_ = Q(author__in=list(users))

    hidden_q_ = Q(hidden=False)

    search_q_ = Q()
    if search != "":
        search_q_ = parse_search_string_return_q(search, ["message",])

    status_updates = StatusUpdate.objects(user_q_ & search_q_ & hidden_q_)[:count]

    if request.method == 'POST':
        parsed_statuses = []
        for status in status_updates:
            parsed_status = status.to_mongo().to_dict()
            parsed_status["profile_address"] = url_for('view_profile', login_name=status.author.login_name)
            parsed_status["user_name"] = status.author.display_name
            parsed_status["message"] = status.message
            if status.old_ipb_id != None:
                parsed_status["ipb"] = True
            else:
                parsed_status["ipb"] = False
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
            del parsed_status["comments"]
            parsed_statuses.append(parsed_status)
        return app.jsonify(status_updates=parsed_statuses)
    else:
        return render_template("core/status_index.jade", page_title="Status Updates - Scarlet's Web", status_updates=status_updates, count=count, search=search, authors=json.dumps(authors))

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
        title="Reply to %s's Status Update" % (unicode(status.author.display_name),),
        description=status.message,
        content=status,
        author=current_user._get_current_object()
        )

    if current_user._get_current_object() != status.author:
        broadcast(
            to=[status.author],
            category="status",
            url="/status/"+str(status.id),
            title="Reply to Your Status Update",
            description=status.message,
            content=status,
            author=current_user._get_current_object()
            )

    return app.jsonify(newest_reply=parsed_reply, count=status.get_comment_count(), success=True)

@app.route('/create-status', methods=['POST'])
@login_required
def create_new_status():
    request_json = request.get_json(force=True)

    status = sqlm.StatusUpdate()
    status.author = current_user._get_current_object()

    if len(request_json.get("message", "")) == 0:
        return app.jsonify(error="Your status update is empty.")

    cleaner = ForumHTMLCleaner()
    try:
        _html = cleaner.escape(request_json.get("message", "").strip())
    except:
        return abort(500)

    status.message = _html
    status.participants.append(status.author)
    status.created = arrow.utcnow().datetime.replace(tzinfo=None)
    status.replies = 0

    sqla.session.add(status)
    sqla.session.commit()

    # TODO: FOLLOW
    # send_notify_to_users = []
    # for user in status.author.followed_by:
    #     if user not in status.author.ignored_users:
    #         send_notify_to_users.append(user)
    #
    # broadcast(
    #   to=send_notify_to_users,
    #   category="user_activity",
    #   url="/status/"+unicode(status.id),
    #   title="%s created a status update." % (unicode(status.author.display_name),),
    #   description=status.message,
    #   content=status,
    #   author=status.author
    #   )
    #
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

    if current_user._get_current_object() != status.author:
        if (current_user._get_current_object().is_admin != True or current_user._get_current_object().is_mod != True):
            return abort(404)

    if user == current_user._get_current_object():
        return abort(404)

    status_user = sqla.session.query(sqlm.StatusUpdateUser).filter_by(
        author=current_user._get_current_object(), status=status)

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
                title="Status update hidden.",
                description=status.message,
                content=status,
                author=current_user._get_current_object()
                )

        broadcast(
            to=list(User.objects(is_admin=True)),
            category="mod",
            url="/status/"+str(status.id),
            title="%s's status update hidden." % (unicode(status.author.display_name),),
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
