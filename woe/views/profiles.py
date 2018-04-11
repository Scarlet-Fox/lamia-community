from woe.parsers import ForumPostParser, emoticon_codes
from woe.forms.core import AvatarTitleForm, DisplayNamePasswordForm, UserSettingsForm, SiteCustomizationForm
from woe.forms.signatures import NewSignature
from woe import app
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session
from flask.ext.login import login_required, current_user
from werkzeug import secure_filename
import os
import arrow
from woe.utilities import ForumHTMLCleaner, strip_tags
from woe import sqla
import woe.sqlmodels as sqlm
import time
from woe.views.dashboard import broadcast
from threading import Thread
from multiprocessing import Process, Queue
from sqlalchemy.orm.attributes import flag_modified
from woe.email_utilities import send_mail_w_template

try:
    import cPickle as pickle
except ImportError:
    import pickle

# @app.route('/member/<login_name>/mod-panel')
# @login_required
# def user_moderation_panel(login_name):
#     if current_user._get_current_object().is_admin != True:
#         abort(404)
#
#     try:
#         user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
#     except IndexError:
#         abort(404)
#
#     last_five_ip_addresses = sqla.session.query(sqlm.IPAddress).filter_by(user=user)[0:5]
#
#     fingerprints_with_top_matches = {}
#     most_recent_fingerprints = sqla.session.query(sqlm.Fingerprint).filter_by(user=user)[0:5]
#
#     for recent_fingerprint in most_recent_fingerprints:
#         matches = []
#         other_fingerprints = sqla.session.query(sqlm.Fingerprint) \
#             .filter(sqlm.Fingerprint.factors > recent_fingerprint.factors-1) \
#             .filter(sqlm.Fingerprint.factors < recent_fingerprint.factors+1) \
#
#
#         for fingerprint in other_fingerprints:
#             user_ = fingerprint.user
#             hash_ = fingerprint.fingerprint_hash
#             score = recent_fingerprint.compute_similarity_score(fingerprint)
#             matches.append((user_, hash_, round(score,0)))
#
#
#         fingerprints_with_top_matches[recent_fingerprint.fingerprint_hash] = matches[0:3]
#
#     return render_template("profile/mod_panel.jade",
#         profile=user,
#         recent_ips=last_five_ip_addresses,
#         title="Mod Details for %s - %%GENERIC SITENAME%%" % (unicode(user.display_name),),
#         recent_fingerprints=most_recent_fingerprints,
#         top_fingerprint_matches=fingerprints_with_top_matches)

@app.route('/member/<login_name>')
def view_profile(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    parser = ForumPostParser()
    try:
        user.parsed_about_me = parser.parse(user.about_me, _object=user)
    except:
        user.parsed_about_me = ""
    # TODO STATS

    post_count = 0 # sqlm.Post.query.filter_by(hidden=False, author=user).count()
    topic_count = 0 # sqlm.Topic.query.filter_by(hidden=False, author=user).count()
    status_update_created = 0 # sqlm.StatusUpdate.query.filter_by(hidden=False, author=user).count()
    status_update_comments_created = 0 # sqlm.StatusComment.query.filter_by(hidden=False, author=user).count()
    
    age = False
    if user.birthday:
        today = arrow.utcnow().datetime
        age = today.year - user.birthday.year - ((today.month, today.day) < (user.birthday.month, user.birthday.day))
    
    boops_given = sqla.session.query(sqlm.post_boop_table).filter(sqlm.post_boop_table.c.user_id == user.id).count()
    boops_received = sqla.session.query(sqlm.post_boop_table) \
        .join(sqlm.Post) \
        .filter(sqlm.Post.author == user) \
        .count()
    
    if user.data != None:
        favorite_phrase = user.data.get("favorite_phrase", [])
        favorite_emotes = ["""<img src="/static/emotes/%s" />""" % emote for emote in user.data.get("favorite_emotes", [])]
    else:
        favorite_phrase = []
        favorite_emotes = []
    
    recent_visitor_logs = sqla.session.query(sqlm.SiteLog.user_id, sqla.func.max(sqlm.SiteLog.time).label("time")) \
        .filter(sqlm.SiteLog.user_id.isnot(None)) \
        .filter(sqlm.SiteLog.path.like("/member/"+unicode(user.my_url))) \
        .group_by(sqlm.SiteLog.user_id).order_by(sqla.desc(sqla.func.max(sqlm.SiteLog.time))).limit(5).subquery()
    
    recent_visitors = sqla.session.query(sqlm.User, recent_visitor_logs.c.time) \
        .join(recent_visitor_logs, sqla.and_(
            recent_visitor_logs.c.user_id == sqlm.User.id,
            recent_visitor_logs.c.user_id != user.id
        ))[:5]

    recent_posts = [] #sqla.session.query(sqlm.Post).filter_by(author=user, hidden=False) \
        # .join(sqlm.Post.topic) \
        # .filter(sqlm.Topic.category.has(sqlm.Category.restricted==False)) \
        # .order_by(sqla.desc(sqlm.Post.created))[:5]

    recent_topics = [] #sqla.session.query(sqlm.Topic).filter_by(author=user, hidden=False) \
        # .filter(sqlm.Topic.category.has(sqlm.Category.restricted==False)) \
        # .order_by(sqla.desc(sqlm.Topic.created))[:5]
    
    # try:
    #     label = sqla.session.query(sqlm.Label).filter_by(label="ask")[0]
    #     ask_me = sqla.session.query(sqlm.Topic).filter_by(author=user, hidden=False, label=label) \
    #         .order_by(sqla.desc(sqlm.Topic.created))[:5]
    # except IndexError:
    ask_me = []

    recent_status_updates = sqla.session.query(sqlm.StatusUpdate) \
        .filter_by(author=user, hidden=False) \
        .order_by(sqla.desc(sqlm.StatusUpdate.created))[:5]

    recent_status_updates_to_user = sqla.session.query(sqlm.StatusUpdate) \
        .filter_by(attached_to_user=user, hidden=False) \
        .order_by(sqla.desc(sqlm.StatusUpdate.created))[:5]

    if current_user in user.friends():
        recent_blog_entries = sqla.session.query(sqlm.BlogEntry) \
            .filter(sqlm.BlogEntry.author==user) \
            .join(sqlm.Blog, sqlm.BlogEntry.blog_id == sqlm.Blog.id) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqlm.BlogEntry.draft.isnot(True)) \
            .filter(sqlm.BlogEntry.published.isnot(None)) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all",
                sqlm.Blog.privacy_setting == "members",
                sqlm.Blog.privacy_setting == "friends"
            )) \
            .order_by(sqla.desc(sqlm.BlogEntry.published))[0:5]
    elif current_user.is_authenticated():
        recent_blog_entries = sqla.session.query(sqlm.BlogEntry) \
            .filter(sqlm.BlogEntry.author==user) \
            .join(sqlm.Blog, sqlm.BlogEntry.blog_id == sqlm.Blog.id) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqlm.BlogEntry.draft.isnot(True)) \
            .filter(sqlm.BlogEntry.published.isnot(None)) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all",
                sqlm.Blog.privacy_setting == "members"
            )) \
            .order_by(sqla.desc(sqlm.BlogEntry.published))[0:5]
    else:
        recent_blog_entries = sqla.session.query(sqlm.BlogEntry) \
            .filter(sqlm.BlogEntry.author==user) \
            .join(sqlm.Blog, sqlm.BlogEntry.blog_id == sqlm.Blog.id) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqlm.BlogEntry.draft.isnot(True)) \
            .filter(sqlm.BlogEntry.published.isnot(None)) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all",
            )) \
            .order_by(sqla.desc(sqlm.BlogEntry.published))[0:5]

    if user.data != None:
        if user.data.has_key("my_fields"):
            custom_fields = user.data["my_fields"]
        else:
            custom_fields = []
        available_fields = sqlm.User.AVAILABLE_PROFILE_FIELDS
    else:
        custom_fields = []
        available_fields = []

    return render_template(
        "profile.jade",
        profile=user,
        page_title="%s - %%GENERIC SITENAME%%" % (unicode(user.display_name),),
        post_count=post_count,
        custom_fields=custom_fields,
        available_fields=available_fields,
        topic_count=topic_count,
        status_update_count=status_update_created,
        favorite_phrase=favorite_phrase,
        common_emotes=favorite_emotes,
        boops_given=boops_given,
        boops_received=boops_received,
        recent_posts=recent_posts,
        recent_topics=recent_topics,
        recent_visitors=recent_visitors,
        recent_blog_entries=recent_blog_entries,
        recent_status_updates=recent_status_updates,
        recent_status_updates_to_user=recent_status_updates_to_user,
        status_update_comments_count=status_update_comments_created,
        ask_me=ask_me,
        age=age
        )

@app.route('/member/<login_name>/validate-user', methods=['POST'])
@login_required
def validate_user(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user._get_current_object().is_admin != True:
        return abort(404)

    user.validated = True
    user.new_user_token = ""
    user.new_user_token_date = None
    
    broadcast(
        to=sqla.session.query(sqlm.User).filter_by(
            banned=False,
            ).filter(sqlm.User.login_name != user.login_name) \
            .filter(sqlm.User.hidden_last_seen > arrow.utcnow().replace(hours=-24).datetime.replace(tzinfo=None)) \
            .all(),
        category="new_member",
        url="/member/"+unicode(user.my_url),
        title="joined the forum! Greet them!",
        description="",
        content=user,
        author=user
        )

    broadcast(
        to=[user,],
        category="new_member",
        url="/category/welcome",
        title="Welcome! Click here to introduce yourself!",
        description="",
        content=user,
        author=user
        )
        
    sqla.session.add(user)
    sqla.session.commit()

    send_mail_w_template(
        send_to=[user,],
        template="manual_validation_welcome.txt",
        subject="Welcome to %%GENERIC SITENAME%%!",
        variables={
            "_user": user,
            "address": app.config['BASE'] + "/sign-in"
        }
    )

    return app.jsonify(url="/member/"+unicode(user.my_url))

@app.route('/member/<login_name>/signatures', methods=['GET'])
@login_required
def show_signatures(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    signatures = sqla.session.query(sqlm.Signature).filter_by(owner=user) \
        .order_by(sqla.desc(sqlm.Signature.created)).all()

    parser = ForumPostParser()
    for s in signatures:
        try:
            s.parsed = parser.parse(s.html, _object=s)
        except:
            s.parsed = ""

    return render_template("profile/view_signatures.jade", signatures=signatures, profile=user, page_title="%s's Signatures - %%GENERIC SITENAME%%" % (unicode(user.display_name),))

@app.route('/member/<login_name>/delete-signature/<id>', methods=['POST'])
@login_required
def delete_signature(login_name, id):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if user != current_user:
        abort(404)

    try:
        signature = sqla.session.query(sqlm.Signature).filter_by(id=id)[0]
    except IndexError:
        abort(404)

    sqla.session.query(sqlm.Signature).filter_by(id=id).delete()

    return app.jsonify(url="/member/"+unicode(user.my_url)+"/signatures")

@app.route('/member/<login_name>/toggle-active-signature/<id>', methods=['POST'])
@login_required
def toggle_active_signature(login_name, id):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if user != current_user:
        abort(404)

    try:
        signature = sqla.session.query(sqlm.Signature).filter_by(id=id)[0]
    except IndexError:
        abort(404)

    signature.active = not signature.active
    sqla.session.add(signature)
    sqla.session.commit()

    return app.jsonify(url="/member/"+unicode(user.my_url)+"/signatures")

@app.route('/member/<login_name>/edit-signature/<id>', methods=['GET', 'POST'])
@login_required
def edit_signature(login_name, id):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if user != current_user and not current_user.is_admin:
        abort(404)

    try:
        signature = sqla.session.query(sqlm.Signature).filter_by(id=id)[0]
    except IndexError:
        abort(404)

    form = NewSignature(csrf_enabled=False)
    if form.validate_on_submit():
        signature.name = form.name.data
        cleaner = ForumHTMLCleaner()
        signature.html = cleaner.clean(form.signature.data)
        signature.active = form.active.data
        sqla.session.add(signature)
        sqla.session.commit()
        return redirect("/member/"+unicode(user.my_url)+"/signatures")
    else:
        form.active.data = signature.active
        form.signature.data = signature.html
        form.name.data = signature.name

    return render_template("profile/edit_signature.jade", form=form, profile=user, signature=signature, page_title="Edit Signature - %%GENERIC SITENAME%%")

@app.route('/member/<login_name>/new-signature', methods=['GET', 'POST'])
@login_required
def new_signature(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if user != current_user:
        abort(404)

    form = NewSignature(csrf_enabled=False)
    if form.validate_on_submit():
        signature = sqlm.Signature()
        signature.name = form.name.data
        cleaner = ForumHTMLCleaner()
        signature.html = cleaner.clean(form.signature.data)
        signature.active = form.active.data
        signature.owner = user
        signature.owner_name = user.login_name
        signature.created = arrow.utcnow().datetime.replace(tzinfo=None)
        sqla.session.add(signature)
        sqla.session.commit()
        return redirect("/member/"+unicode(user.my_url)+"/signatures")

    return render_template("profile/new_signature.jade", form=form, profile=user, page_title="New Signature - %%GENERIC SITENAME%%")

@app.route('/member/<login_name>/friends', methods=['GET'])
def show_friends(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    my_friend_requests = sqlm.Friendship.query.filter_by(blocked=False, pending=True) \
        .filter(sqlm.Friendship.user == user).all()

    incoming_friend_requests = sqlm.Friendship.query.filter_by(blocked=False, pending=True) \
        .filter(sqlm.Friendship.friend == user).all()

    friend_status_updates = sqlm.StatusUpdate.query \
        .filter(sqlm.StatusUpdate.author_id.in_([u.id for u in user.friends()])) \
        .filter_by(hidden=False) \
        .order_by(sqla.desc(sqlm.StatusUpdate.created))[0:5]

    if current_user.is_authenticated():
        friend_blog_entries = sqla.session.query(sqlm.Blog) \
            .join(sqlm.Blog.recent_entry) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqlm.BlogEntry.draft.isnot(True)) \
            .filter(sqlm.BlogEntry.published.isnot(None)) \
            .filter(sqlm.BlogEntry.author_id.in_([u.id for u in user.friends()])) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all",
                sqlm.Blog.privacy_setting == "members"
            )) \
            .order_by(sqla.desc(sqlm.BlogEntry.published))[0:5]
    else:
        friend_blog_entries = sqla.session.query(sqlm.Blog) \
            .join(sqlm.Blog.recent_entry) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqlm.BlogEntry.draft.isnot(True)) \
            .filter(sqlm.BlogEntry.published.isnot(None)) \
            .filter(sqlm.BlogEntry.author_id.in_([u.id for u in user.friends()])) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all"
            )) \
            .order_by(sqla.desc(sqlm.BlogEntry.published))[0:5]

    return render_template(
            "profile/friends.jade",
            profile=user,
            my_friend_requests=my_friend_requests,
            incoming_friend_requests=incoming_friend_requests,
            friend_status_updates=friend_status_updates,
            friend_blog_entries=friend_blog_entries,
            page_title="%s's Friends - %%GENERIC SITENAME%%" % (unicode(user.display_name),),
        )

@app.route('/member/<login_name>/request-friend', methods=['POST'])
@login_required
def request_friendship(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user._get_current_object() == user:
        return abort(404)

    if not current_user in user.rejected_friends():
        if current_user not in user.pending_friends() and current_user not in user.friends():
            friendship = sqlm.Friendship(
                    user = current_user,
                    friend = user,
                    created = arrow.utcnow().datetime.replace(tzinfo=None),
                )
            sqla.session.add(friendship)
            sqla.session.commit()

            broadcast(
              to=[user,],
              category="friend",
              url="/member/%s/friends" % (str(user.my_url)),
              title="sent you a friend request",
              description="",
              content=current_user,
              author=current_user
              )

    return app.jsonify(url="/member/"+unicode(user.my_url))

@app.route('/member/<login_name>/un-friend', methods=['POST'])
@login_required
def unfriend(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user._get_current_object() == user:
        return abort(404)

    if current_user in user.pending_friends() or current_user in user.friends():
        friends = sqlm.Friendship.query.filter_by(blocked=False) \
            .filter(sqla.or_(sqlm.Friendship.user == current_user, sqlm.Friendship.friend == current_user)) \
            .filter(sqla.or_(sqlm.Friendship.user == user, sqlm.Friendship.friend == user)) \
            .delete()

    return app.jsonify(url="/member/"+unicode(user.my_url))

@app.route('/member/<user>/friends/<friend>/deny', methods=['POST'])
@login_required
def deny_friend(user, friend):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=user.strip().lower())[0]
    except IndexError:
        abort(404)

    try:
        friend = sqla.session.query(sqlm.User).filter_by(my_url=friend.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user != friend:
        abort(404)

    try:
        friendship = sqlm.Friendship.query.filter_by(blocked=False, pending=True) \
            .filter(sqlm.Friendship.user == user, sqlm.Friendship.friend == friend).delete()
    except IndexError:
        abort(404)

    return app.jsonify(url="/member/"+unicode(friend.my_url)+"/friends")

@app.route('/member/<user>/friends/<friend>/cancel', methods=['POST'])
@login_required
def cancel_friend(user, friend):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=user.strip().lower())[0]
    except IndexError:
        abort(404)

    try:
        friend = sqla.session.query(sqlm.User).filter_by(my_url=friend.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user != user:
        abort(404)

    try:
        friendship = sqlm.Friendship.query.filter_by(blocked=False, pending=True) \
            .filter(sqlm.Friendship.user == user, sqlm.Friendship.friend == friend).delete()
    except IndexError:
        abort(404)

    return app.jsonify(url="/member/"+unicode(user.my_url)+"/friends")

@app.route('/member/<user>/friends/<friend>/approve', methods=['POST'])
@login_required
def approve_friend(user, friend):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=user.strip().lower())[0]
    except IndexError:
        abort(404)

    try:
        friend = sqla.session.query(sqlm.User).filter_by(my_url=friend.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user != friend:
        abort(404)

    try:
        friendship = sqlm.Friendship.query.filter_by(blocked=False, pending=True) \
            .filter(sqlm.Friendship.user == user, sqlm.Friendship.friend == friend)[0]
    except IndexError:
        abort(404)

    friendship.pending = False

    try:
        follow_preference = sqla.session.query(sqlm.FollowingUser) \
            .filter_by(
                    user=user,
                    following=friend
                )[0]
    except IndexError:
        follow_preference = sqlm.FollowingUser(
            user=user,
            following=friend,
            created=arrow.utcnow().datetime.replace(tzinfo=None)
        )
        sqla.session.add(follow_preference)
        sqla.session.commit()

    try:
        follow_preference = sqla.session.query(sqlm.FollowingUser) \
            .filter_by(
                    user=friend,
                    following=user
                )[0]
    except IndexError:
        follow_preference = sqlm.FollowingUser(
            user=friend,
            following=user,
            created=arrow.utcnow().datetime.replace(tzinfo=None)
        )
        sqla.session.add(follow_preference)
        sqla.session.commit()

    broadcast(
      to=[user,],
      category="friend",
      url="/member/%s/friends" % (str(user.my_url)),
      title="approved your friend request",
      description="",
      content=friend,
      author=friend
      )

    sqla.session.add(friendship)
    sqla.session.commit()

    return app.jsonify(url="/member/"+unicode(friend.my_url)+"/friends")

@app.route('/member/<login_name>/unignore-user/<target_name>', methods=['POST'])
@login_required
def unignore_user(login_name, target_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    try:
        target = sqla.session.query(sqlm.User).filter_by(my_url=target_name.strip().lower())[0]
    except IndexError:
        abort(404)

    try:
        ignore_del = sqla.session.query(sqlm.IgnoringUser).filter_by(user=user, ignoring=target).delete()
    except:
        abort(404)

    return app.jsonify(url="/member/"+unicode(user.my_url)+"/change-settings")

@app.route('/member/<login_name>/ignore-users', methods=['POST'])
@login_required
def ignore_users(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    request_json = request.get_json(force=True)
    try:
        to_ignore = list(
                sqla.session.query(sqlm.User) \
                    .filter(sqlm.User.id.in_(request_json.get("data"))) \
                    .all()
            )
    except:
        pass

    for user_ in to_ignore:
        if user_ in [u.ignoring for u in user.ignored_users]:
            continue

        if user_ == user:
            continue

        new_ignore = sqlm.IgnoringUser()
        new_ignore.user = user
        new_ignore.ignoring = user_
        new_ignore.created = arrow.utcnow().datetime.replace(tzinfo=None)
        sqla.session.add(new_ignore)
        sqla.session.commit()

    return app.jsonify(url="/member/"+unicode(user.my_url)+"/change-settings")

@app.route('/member/<login_name>/toggle-ignore', methods=['POST'])
@login_required
def toggle_ignore_user(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user._get_current_object() == user:
        return abort(404)

    existed = False
    try:
        ignore_setting = sqla.session.query(sqlm.IgnoringUser) \
            .filter_by(
                    user=current_user._get_current_object(),
                    ignoring=user
                )[0]
        existed = True
    except IndexError:
        ignore_setting = sqlm.IgnoringUser(
            user=current_user._get_current_object(),
            ignoring=user,
            created=arrow.utcnow().datetime.replace(tzinfo=None)
        )

    if existed:
        sqla.session.delete(ignore_setting)
        sqla.session.commit()
    else:
        sqla.session.add(ignore_setting)
        sqla.session.commit()

    return app.jsonify(url="/member/"+unicode(user.my_url))

@app.route('/member/toggle-sounds', methods=['POST'])
@login_required
def toggle_sounds():
    current_user.notification_sound = not current_user.notification_sound
    sqla.session.add(current_user)
    return app.jsonify(result=current_user.notification_sound)

@app.route('/member/toggle-images', methods=['POST'])
@login_required
def toggle_images():
    current_user.no_images = not current_user.no_images
    sqla.session.add(current_user)
    return app.jsonify(result=current_user.no_images)

@app.route('/member/toggle-stickybar', methods=['POST'])
@login_required
def toggle_stickybar():
    current_user.navbar_top = not current_user.navbar_top
    sqla.session.add(current_user)
    return app.jsonify(result=current_user.navbar_top)
    
@app.route('/member/<login_name>/toggle-follow', methods=['POST'])
@login_required
def toggle_follow_user(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        return abort(404)

    if current_user._get_current_object() == user:
        return abort(404)

    try:
        follow_preference = sqla.session.query(sqlm.FollowingUser) \
            .filter_by(
                    user=current_user._get_current_object(),
                    following=user
                )[0]
        sqla.session.delete(follow_preference)
        sqla.session.commit()
    except IndexError:
        follow_preference = sqlm.FollowingUser(
            user=current_user._get_current_object(),
            following=user,
            created=arrow.utcnow().datetime.replace(tzinfo=None)
        )
        sqla.session.add(follow_preference)
        sqla.session.commit()
        broadcast(
          to=[user,],
          category="followed",
          url="/member/%s" % (str(user.my_url)),
          title="followed your profile",
          description="",
          content=user,
          author=current_user
          )

    return app.jsonify(url="/member/"+unicode(user.my_url))

@app.route('/member/<login_name>/change-avatar-title', methods=['GET', 'POST'])
@login_required
def change_avatar_or_title(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user._get_current_object() != user and not current_user._get_current_object().is_admin:
        abort(404)

    form = AvatarTitleForm(csrf_enabled=False)

    if form.validate_on_submit():
        if form.avatar.data:
            timestamp = str(arrow.utcnow().timestamp) + "_"

            # if user.avatar_extension:
            #     try:
            #         os.remove(os.path.join(app.config["AVATAR_UPLOAD_DIR"],user.avatar_timestamp + str(user.pk) + user.avatar_extension))
            #         os.remove(os.path.join(app.config["AVATAR_UPLOAD_DIR"],user.avatar_timestamp + str(user.pk) + "_40" + user.avatar_extension))
            #         os.remove(os.path.join(app.config["AVATAR_UPLOAD_DIR"],user.avatar_timestamp + str(user.pk) + "_60" + user.avatar_extension))
            #     except OSError:
            #         pass

            extension = "." + form.avatar.data.filename.split(".")[-1].lower()

            form.avatar_image.save(filename=os.path.join(app.config["AVATAR_UPLOAD_DIR"],timestamp + str(user.id) + extension))

            form.fourty_image.save(filename=os.path.join(app.config["AVATAR_UPLOAD_DIR"],timestamp + str(user.id) + "_40" + extension))
            form.sixty_image.save(filename=os.path.join(app.config["AVATAR_UPLOAD_DIR"],timestamp + str(user.id) + "_60" + extension))

            user.avatar_extension = extension
            user.avatar_timestamp = timestamp
            user.old_mongo_hash = None
            user.avatar_full_x, user.avatar_full_y = form.avatar_image.size
            user.avatar_40_x, user.avatar_40_y = form.fourty_image.size
            user.avatar_60_x, user.avatar_60_y = form.sixty_image.size
        user.title = form.title.data
        sqla.session.add(user)
        sqla.session.commit()
        return redirect("/member/"+user.my_url)
    else:
        filename = None
        form.title.data = user.title

    return render_template("profile/change_avatar.jade", profile=user, form=form, page_title="Change Avatar and Title - %%GENERIC SITENAME%%")

@app.route('/member/<login_name>/toggle-notification-method', methods=['POST'])
@login_required
def toggle_notification_method(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user._get_current_object() != user and not current_user._get_current_object().is_admin:
        abort(404)

    request_json = request.get_json(force=True)

    if request_json.get("category") not in [x[0] for x in sqlm.Notification.NOTIFICATION_CATEGORIES]:
        abort(404)

    if request_json.get("method") not in ["email", "dashboard"]:
        abort(404)

    if user.notification_preferences == None:
        user.notification_preferences = {}

    if not user.notification_preferences.get(request_json.get("category"), False):
        user.notification_preferences[request_json.get("category")] = {"dashboard": True, "email": True}

    user.notification_preferences[request_json.get("category")][request_json.get("method")] = request_json.get("on_or_off")
    flag_modified(user, "notification_preferences")
    sqla.session.add(user)
    sqla.session.commit()
    return app.jsonify(success=True)

@app.route('/member/<login_name>/add-user-field', methods=['POST'])
@login_required
def add_custom_field(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user._get_current_object() != user and not current_user._get_current_object().is_admin:
        abort(404)

    request_json = request.get_json(force=True)

    if request_json.get("field", "") not in sqlm.User.AVAILABLE_PROFILE_FIELDS:
        abort(404)

    if request_json.get("value", "").strip() == "":
        abort(404)

    if user.data == None:
        user.data = {}

    tmp_data = user.data.copy()

    if tmp_data.has_key("my_fields"):
        tmp_data["my_fields"].append([request_json.get("field", ""), request_json.get("value", "")[:40].strip()])
    else:
        tmp_data["my_fields"] = [[request_json.get("field", ""), request_json.get("value", "")[:40].strip()],]

    user.data = tmp_data
    flag_modified(user, "data")

    sqla.session.add(user)
    sqla.session.commit()

    return app.jsonify(success=True)

@app.route('/member/<login_name>/remove-user-field', methods=['POST'])
@login_required
def remove_custom_field(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user._get_current_object() != user and not current_user._get_current_object().is_admin:
        abort(404)

    request_json = request.get_json(force=True)

    if request_json.get("field", "") not in sqlm.User.AVAILABLE_PROFILE_FIELDS:
        abort(404)

    if request_json.get("value", "").strip() == "":
        abort(404)

    tmp_data = user.data.copy()

    if not tmp_data.has_key("my_fields"):
        abort (404)

    for i, f in enumerate(tmp_data["my_fields"]):
        if f[0] == request_json.get("field", "") and f[1] == request_json.get("value", ""):
            tmp_data["my_fields"].pop(i)

    user.data = tmp_data
    flag_modified(user, "data")

    sqla.session.add(user)
    sqla.session.commit()

    return app.jsonify(success=True)

@app.route('/member/<login_name>/remove-customizations-profile', methods=['GET', 'POST'])
@login_required
def remove_customizations_from_profile(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user._get_current_object() != user and not current_user._get_current_object().is_admin:
        abort(404)


    user.banner_image_custom = None
    user.background_image_custom = None
    user.title_bar_background_custom = None
    user.profile_background_custom = None
    user.header_background_color = None
    user.header_text_color = None
    user._full_page_image = False
    user.header_height = 460

    sqla.session.add(user)
    sqla.session.commit()

    return app.jsonify(url="/member/"+user.my_url+"/customize-profile")

@app.route('/member/<login_name>/customize-profile', methods=['GET', 'POST'])
@login_required
def customize_user_profile(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user._get_current_object() != user and not current_user._get_current_object().is_admin:
        abort(404)

    form = SiteCustomizationForm(csrf_enabled=False)

    if form.validate_on_submit():
        timestamp = str(time.time())

        if form.banner.data:
            extension = "." + form.banner.data.filename.split(".")[-1].lower()
            banner_file_name = os.path.join(app.config["CUSTOMIZATIONS_UPLOAD_DIR"], "banner_" + timestamp + str(user.id) + extension)
            form.banner_image.save(filename=banner_file_name)
            user.banner_image_custom = "banner_" + timestamp + str(user.id) + extension
            user.header_height = form.banner_height

        if form.header.data:
            extension = "." + form.header.data.filename.split(".")[-1].lower()
            header_file_name = os.path.join(app.config["CUSTOMIZATIONS_UPLOAD_DIR"], "header_" + timestamp + str(user.id) + extension)
            form.header_image.save(filename=header_file_name)
            user.title_bar_background_custom = "header_" + timestamp + str(user.id) + extension

        if form.background_image.data:
            extension = "." + form.background_image.data.filename.split(".")[-1].lower()
            background_file_name = os.path.join(app.config["CUSTOMIZATIONS_UPLOAD_DIR"], "background_" + timestamp + str(user.id) + extension)
            form.background_image_file.save(filename=background_file_name)
            user.background_image_custom = "background_" + timestamp + str(user.id) + extension

        if form.background.data and form.background.data != "FFFFFF":
            user.profile_background_custom = form.background.data
        else:
            user.profile_background_custom = None

        if form.header_background.data and form.header_background.data != "FFFFFF":
            user.header_background_color = form.header_background.data
        else:
            user.header_background_color = None

        if form.header_text_color.data and form.header_text_color.data != "FFFFFF":
            user.header_text_color = form.header_text_color.data
        else:
            user.header_text_color = None

        if form.header_text_shadow_color.data and form.header_text_shadow_color.data != "FFFFFF":
            user.text_shadow_color = form.header_text_shadow_color.data
        else:
            user.text_shadow_color = None

        user.full_page_image = None
        user.use_text_shadow = form.use_text_shadow.data

        sqla.session.add(user)
        sqla.session.commit()
    else:
        form.background.data = user.profile_background_custom
        form.header_background.data = user.header_background_color
        form.header_text_color.data = user.header_text_color
        form.header_text_shadow_color.data = user.text_shadow_color
        form.use_text_shadow.data = user.use_text_shadow

    return render_template("profile/customize_profile.jade", profile=user, form=form, page_title="Customize Profile - %%GENERIC SITENAME%%")

@app.route('/unsubscribe-confirm', methods=['GET'])
def confirm_unsubscribe_from_all_emails():
    return render_template("unsubscribe_confirm.jade", page_title="Unsubscribed - %%GENERIC SITENAME%%")

@app.route('/member/<id>/<email>/unsubscribe', methods=['GET', 'POST'])
def unsubscribe_from_all_emails(id, email):
    try:
        user = sqla.session.query(sqlm.User).filter_by(id=id, email_address=email)[0]
    except IndexError:
        abort(404)

    if request.method == 'POST':
        user.emails_muted = True
        sqla.session.add(user)
        sqla.session.commit()
        return app.jsonify(url="/unsubscribe-confirm")
    else:
        return render_template("unsubscribe.jade", profile=user, page_title="Unsubscribe - %%GENERIC SITENAME%%")

@app.route('/member/<login_name>/change-settings', methods=['GET', 'POST'])
@login_required
def change_user_settings(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user._get_current_object() != user and not current_user._get_current_object().is_admin:
        abort(404)

    available_fields = sqlm.User.AVAILABLE_PROFILE_FIELDS

    if user.notification_preferences == None:
        user.notification_preferences = {}

    if user.data == None:
        tmp_data = {}
    else:
        tmp_data = user.data

    if tmp_data.has_key("my_fields"):
        current_fields = tmp_data["my_fields"]
    else:
        current_fields = []

    form = UserSettingsForm(csrf_enabled=False)

    if form.validate_on_submit():
        user.time_zone=form.time_zone.data
        user.theme = form.theme_object
        user.no_images = form.no_images.data
        user.emails_muted = form.no_emails.data
        user.birthday = form.birthday.data
        user.notification_sound = form.notification_sound.data
        user.all_notification_sounds = form.all_notification_sounds.data
        user.navbar_top = form.navbar_top.data
        user.minimum_time_between_emails = form.minimum_time_between_emails.data
        sqla.session.add(user)
        sqla.session.commit()
        return redirect("/member/"+user.my_url)
    else:
        form.no_images.data = user.no_images
        form.time_zone.data = user.time_zone
        if user.birthday:
            form.birthday.data = user.birthday
        form.no_emails.data = user.emails_muted
        form.notification_sound.data = user.notification_sound
        form.all_notification_sounds.data = user.all_notification_sounds
        form.navbar_top.data = user.navbar_top

        if user.minimum_time_between_emails == None:
            user.minimum_time_between_emails = 360
        form.minimum_time_between_emails.data = user.minimum_time_between_emails

        if user.theme == None:
            form.theme.data = "1"
        else:
            form.theme.data = str(user.theme.id)

    return render_template("profile/change_user_settings.jade", profile=user, NOTIFICATION_CATEGORIES=sqlm.Notification.NOTIFICATION_CATEGORIES, available_fields=available_fields, current_fields=current_fields, form=form, page_title="Change Settings - %%GENERIC SITENAME%%")

from itsdangerous import want_bytes
def invalidate_sessions(login_name): #default
    session_table = sqla.Table('sessions',sqla.metadata,autoload=True)
    all_sessions = sqla.session.query(session_table).all()
    
    current_session_cookie = "session:" + request.cookies.get(app.session_cookie_name)
    engine = sqla.engine
    
    for _session in all_sessions:
        session_data = _session[2]
        session_id = _session[1]
        try:
            parsed_session_data = pickle.loads(want_bytes(session_data))
        except:
            continue
        parsed_session_data["__id"] = session_id
        
        if parsed_session_data.get("user_id", None) == login_name and current_session_cookie != parsed_session_data["__id"]:
            statement = session_table.delete().where( session_table.c.session_id == parsed_session_data["__id"] )
            engine.execute(statement)
    
@app.route('/member/<login_name>/change-account', methods=['GET', 'POST'])
@login_required
def change_display_name_password(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user._get_current_object() != user and not current_user._get_current_object().is_admin:
        abort(404)

    form = DisplayNamePasswordForm(csrf_enabled=False)
    form.user_object = user
    form.current_user = current_user

    if form.validate_on_submit():
        if form.new_password.data != "":
            user.set_password(form.new_password.data.strip())
            invalidate_sessions(user.login_name)

        if form.display_name.data.strip() != user.display_name:
            dnh = {"name": user.display_name, "date": time.mktime(arrow.utcnow().datetime.replace(tzinfo=None).timetuple())}

            if user.display_name_history == None:
                user.display_name_history = []

            user.display_name_history.append(dnh)
            user.display_name = form.display_name.data.strip()

        if form.email.data.strip() != user.email_address:
            user.email_address = form.email.data

        sqla.session.add(user)
        sqla.session.commit()

        return redirect("/member/"+user.my_url)
    else:
        form.display_name.data = user.display_name
        form.email.data = user.email_address

    return render_template("profile/change_account.jade", profile=user, form=form, page_title="Change Account Details - %%GENERIC SITENAME%%")

@app.route('/member/<login_name>/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user._get_current_object() != user and not current_user._get_current_object().is_admin:
        abort(404)

    if request.method == 'POST':
        cleaner = ForumHTMLCleaner()
        user.about_me = cleaner.clean(request.form.get("about_me"))
        sqla.session.add(user)
        sqla.session.commit()
        parser = ForumPostParser()
        # user.about_me = parser.parse(user.about_me)
        return json.jsonify(about_me=parser.parse(user.about_me, _object=user))
    else:
        return json.jsonify(content=user.about_me)

@app.route('/member/<login_name>/remove-avatar', methods=['POST'])
@login_required
def remove_avatar(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if user.avatar_extension != None:
        if current_user._get_current_object() != user and not current_user._get_current_object().is_admin:
            abort(404)
        try:
            os.remove(os.path.join(app.config["AVATAR_UPLOAD_DIR"],user.avatar_timestamp + str(user.id) + user.avatar_extension))
            os.remove(os.path.join(app.config["AVATAR_UPLOAD_DIR"],user.avatar_timestamp + str(user.id) + "_40" + user.avatar_extension))
            os.remove(os.path.join(app.config["AVATAR_UPLOAD_DIR"],user.avatar_timestamp + str(user.id) + "_60" + user.avatar_extension))
        except OSError:
            pass

    user.avatar_extension = None
    user.avatar_timestamp = ""
    user.avatar_full_x, user.avatar_full_y = (200,200)
    user.avatar_40_x, user.avatar_40_y = (40,40)
    user.avatar_60_x, user.avatar_60_y = (60,60)
    sqla.session.add(user)
    sqla.session.commit()
    return redirect("/member/"+user.my_url)
