from woe.parsers import ForumPostParser, emoticon_codes
from woe.forms.core import AvatarTitleForm, DisplayNamePasswordForm, UserSettingsForm
from woe import app
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from flask.ext.login import login_required, current_user
from werkzeug import secure_filename
import os
import arrow
from woe.utilities import ForumHTMLCleaner, strip_tags
from woe import sqla
import woe.sqlmodels as sqlm
import time
from threading import Thread
from multiprocessing import Process, Queue

@app.route('/member/<login_name>/mod-panel')
@login_required
def user_moderation_panel(login_name):
    if current_user._get_current_object().is_admin != True:
        abort(404)

    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    last_five_ip_addresses = sqla.session.query(sqlm.IPAddress).filter_by(user=user)[0:5]

    fingerprints_with_top_matches = {}
    most_recent_fingerprints = sqla.session.query(sqlm.Fingerprint).filter_by(user=user)[0:5]

    for recent_fingerprint in most_recent_fingerprints:
        matches = []
        other_fingerprints = sqla.session.query(sqlm.Fingerprint) \
            .filter_by(user=user) \
            .filter(sqlm.Fingerprint.factors > recent_fingerprint.factors-6) \
            .filter(sqlm.Fingerprint.factors < recent_fingerprint.factors+6)[0:5]

        for fingerprint in other_fingerprints:
            user_ = fingerprint.user
            hash_ = fingerprint.fingerprint_hash
            score = recent_fingerprint.compute_similarity_score(fingerprint)

            if len(matches) == 0:
                matches.append((user_, hash_, round(score*100,0)))
            else:
                if round(score*100,0) > matches[0][2]:
                    matches.insert(0,(user_, hash_, round(score*100,0)))
                else:
                    matches.append((user_, hash_, round(score*100,0)))

        fingerprints_with_top_matches[recent_fingerprint.fingerprint_hash] = matches[0:3]

    return render_template("profile/mod_panel.jade",
        profile=user,
        recent_ips=last_five_ip_addresses,
        title="Mod Details for %s - Scarlet's Web" % (unicode(user.display_name),),
        recent_fingerprints=most_recent_fingerprints,
        top_fingerprint_matches=fingerprints_with_top_matches)

def update_user_smileys(user):
    from woe import sqla
    import woe.sqlmodels as sqlm

    user_name = user.login_name

    try:
        post_count = sqla.session.query(sqlm.Post) \
            .join(sqlm.Post.topic) \
            .join(sqlm.Topic.category) \
            .filter(sqlm.Post.hidden==False, sqlm.Post.author==user) \
            .filter(sqlm.Category.slug != "welcome-mat").count()
    except:
        sqla.session.rollback()
        return

    if post_count < 10:
        return

    posts = list(sqla.session.query(sqlm.Post) \
        .join(sqlm.Post.topic) \
        .join(sqlm.Topic.category) \
        .filter(sqlm.Post.hidden==False, sqlm.Post.author==user) \
        .all())
    sqla.session.expunge_all()
    sqla.session.close()

    q = Queue()

    def compute(posts, q):
        emote_frequency = {}
        emotes = []

        for post in posts:
            for emote in emoticon_codes.keys():
                if emote in post.html:
                    if emote_frequency.has_key(emote):
                        emote_frequency[emote] += 1
                    else:
                        emote_frequency[emote] = 1

        emotes = emote_frequency.keys()
        emotes = sorted(emotes, key=lambda x: emote_frequency[x], reverse=True)
        q.put(emotes[0:6])

    process = Process(target=compute, args=(posts, q))
    process.start()
    favorite_emotes = q.get()
    process.join()

    user = sqlm.User.query.filter_by(login_name=user_name)[0]
    if user.data == None:
        user.data = {}

    new_data = user.data.copy()
    new_data["favorite_emotes"] = favorite_emotes
    user.data = new_data

    user.smileys_last_updated = arrow.utcnow().datetime.replace(tzinfo=None)

    sqla.session.add(user)
    sqla.session.commit()

def update_user_last_phrase(user):
    from woe import sqla
    import woe.sqlmodels as sqlm

    user_name = user.login_name

    try:
        post_count = sqla.session.query(sqlm.Post) \
            .join(sqlm.Post.topic) \
            .join(sqlm.Topic.category) \
            .filter(sqlm.Post.hidden==False, sqlm.Post.author==user) \
            .filter(sqlm.Category.slug != "welcome-mat").count()
    except:
        sqla.session.rollback()
        return

    if post_count < 10:
        return

    posts = list(sqla.session.query(sqlm.Post) \
        .join(sqlm.Post.topic) \
        .join(sqlm.Topic.category) \
        .filter(sqlm.Post.hidden==False, sqlm.Post.author==user) \
        .filter(sqlm.Category.slug != "welcome-mat") \
        .filter(sqlm.Category.slug != "art-show") \
        .all())
    sqla.session.expunge_all()
    sqla.session.close()

    q = Queue()

    def compute(posts, q):
        phrase_frequency = {}
        phrases = []
        phrase_length = 6

        for post in posts:
            words = strip_tags(post.html)
            phrases_in_post = range(len(words)-phrase_length)
            post_phrases = {}

            for i_phrase in phrases_in_post:
                word_1 = words[i_phrase].lower().strip()
                word_2 = words[i_phrase+1].lower().strip()
                word_3 = words[i_phrase+2].lower().strip()
                word_4 = words[i_phrase+3].lower().strip()
                word_5 = words[i_phrase+4].lower().strip()
                word_6 = words[i_phrase+5].lower().strip()

                if word_1 == word_2 == word_3 == word_4 == word_5 == word_6:
                    continue

                phrase = unicode(word_1)+" "+unicode(word_2)+" "+unicode(word_3)+" "+unicode(word_4)+" "+unicode(word_5)+" "+unicode(word_6)
                phrase_check = [word_1, word_2, word_3, word_4, word_5, word_6]
                if "don" in phrase_check and "t" in phrase_check:
                    continue
                if "have" in phrase_check and "idea" in phrase_check:
                    continue
                if "youtube" in phrase_check:
                    continue
                if "url" in phrase_check:
                    continue
                if "com" in phrase_check:
                    continue
                if "cdn" in phrase_check:
                    continue
                if "vine" in phrase_check:
                    continue
                if "list" in phrase_check:
                    continue

                if post_phrases.has_key(phrase):
                    continue
                else:
                    post_phrases[phrase] = 1

                if phrase_frequency.has_key(phrase):
                    phrase_frequency[phrase] += 1
                else:
                    phrase_frequency[phrase] = 1

        phrases = phrase_frequency.keys()
        phrases = sorted(phrases, key=lambda x: phrase_frequency[x], reverse=True)
        q.put(phrases[0])

    process = Process(target=compute, args=(posts, q))
    process.start()
    favorite_phrase = q.get()
    process.join()

    user = sqlm.User.query.filter_by(login_name=user_name)[0]
    if user.data == None:
        user.data = {}

    new_data = user.data.copy()
    new_data["favorite_phrase"] = favorite_phrase
    user.data = new_data

    user.phrase_last_updated = arrow.utcnow().datetime.replace(tzinfo=None)

    sqla.session.add(user)
    sqla.session.commit()

@app.route('/member/<login_name>')
@login_required
def view_profile(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    parser = ForumPostParser()
    try:
        user.about_me = parser.parse(user.about_me)
    except:
        user.about_me = ""

    post_count = sqlm.Post.query.filter_by(hidden=False, author=user).count()
    topic_count = sqlm.Topic.query.filter_by(hidden=False, author=user).count()
    status_update_created = sqlm.StatusUpdate.query.filter_by(hidden=False, author=user).count()
    status_update_comments_created = sqlm.StatusComment.query.filter_by(hidden=False, author=user).count()

    if user.phrase_last_updated == None:
        thread = Thread(target=update_user_last_phrase, args=(user,))
        thread.start()
    elif arrow.get(user.phrase_last_updated) < arrow.utcnow().replace(days=-1).datetime:
        thread = Thread(target=update_user_last_phrase, args=(user,))
        thread.start()

    if user.smileys_last_updated == None:
        thread = Thread(target=update_user_smileys, args=(user,))
        thread.start()
    elif arrow.get(user.smileys_last_updated) < arrow.utcnow().replace(days=-1).datetime:
        thread = Thread(target=update_user_last_phrase, args=(user,))
        thread.start()

    boops_given = sqla.session.query(sqlm.post_boop_table).filter(sqlm.post_boop_table.c.user_id == user.id).count()
    boops_received = sqla.session.query(sqlm.post_boop_table) \
        .join(sqlm.Post) \
        .filter(sqlm.Post.author == user) \
        .count()

    if user.data != None:
        favorite_phrase = user.data.get("favorite_phrase", [])
        favorite_emotes = ["""<img src="/static/emoticons/%s" />""" % emoticon_codes[emote] for emote in user.data.get("favorite_emotes", [])]
    else:
        favorite_phrase = []
        favorite_emotes = []

    return render_template(
        "profile.jade",
        profile=user,
        page_title="%s - Scarlet's Web" % (unicode(user.display_name),),
        post_count=post_count,
        topic_count=topic_count,
        status_update_count=status_update_created,
        favorite_phrase=favorite_phrase,
        common_emotes=favorite_emotes,
        boops_given=boops_given,
        boops_received=boops_received,
        status_update_comments_count=status_update_comments_created
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

    sqla.session.add(user)
    sqla.session.commit()

    return app.jsonify(url="/member/"+unicode(user.my_url))

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

    return app.jsonify(url="/member/"+unicode(user.my_url))

@app.route('/member/<login_name>/un-friend', methods=['POST'])
@login_required
def unfriend(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    # current_user.is_admin = False
    # sqla.session.add(current_user)
    # sqla.session.commit()

    if current_user._get_current_object() == user:
        return abort(404)

    if current_user in user.pending_friends() or current_user in user.friends():
        friends = sqlm.Friendship.query.filter_by(blocked=False) \
            .filter(sqla.or_(sqlm.Friendship.user == current_user, sqlm.Friendship.friend == current_user)) \
            .filter(sqla.or_(sqlm.Friendship.user == user, sqlm.Friendship.friend == user)) \
            .delete()

    return app.jsonify(url="/member/"+unicode(user.my_url))


# @app.route('/member/<login_name>/toggle-ignore', methods=['POST'])
# @login_required
# def toggle_ignore_user(login_name):
#     try:
#         user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
#     except IndexError:
#         abort(404)
#
#     if current_user._get_current_object() == user:
#         return abort(404)
#
#     try:
#         ignore_setting = sqla.session.query(sqlm.IgnoringUser) \
#             .filter_by(
#                     user=current_user._get_current_object(),
#                     ignoring=user
#                 )
#     except IndexError:
#         ignore_setting = sqlm.IgnoringUser(
#             user=current_user._get_current_object(),
#             ignoring=user,
#             created=arrow.utcnow().datetime.replace(tzinfo=None)
#         )
#
#     currently_ignored = ignore_setting.distort_posts or ignore_setting.block_sigs or ignore_setting.block_pms or ignore_setting.block_blogs or ignore_setting.block_status
#
#     if user in current_user._get_current_object().ignored_users:
#         c = current_user._get_current_object()
#         c.ignored_users.remove(user)
#         sqla.session.add(c)
#         sqla.session.commit()
#     else:
#         c = current_user._get_current_object()
#         c.ignored_users.append(user)
#         sqla.session.add(c)
#         sqla.session.commit()
#
#     return app.jsonify(url="/member/"+unicode(login_name))

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

    return app.jsonify(url="/member/"+unicode(login_name))

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
        return redirect("/member/"+user.login_name)
    else:
        filename = None
        form.title.data = user.title

    return render_template("profile/change_avatar.jade", profile=user, form=form, page_title="Change Avatar and Title - Scarlet's Web")

@app.route('/member/<login_name>/change-settings', methods=['GET', 'POST'])
@login_required
def change_user_settings(login_name):
    try:
        user = sqla.session.query(sqlm.User).filter_by(my_url=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user._get_current_object() != user and not current_user._get_current_object().is_admin:
        abort(404)

    form = UserSettingsForm(csrf_enabled=False)

    if form.validate_on_submit():
        user.time_zone=form.time_zone.data
        user.theme = form.theme_object
        sqla.session.add(user)
        sqla.session.commit()
        return redirect("/member/"+user.login_name)
    else:
        form.time_zone.data = user.time_zone
        if user.theme == None:
            form.theme.data = "1"
        else:
            form.theme.data = str(user.theme.id)

    return render_template("profile/change_user_settings.jade", profile=user, form=form, page_title="Change Settings - Scarlet's Web")

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

        return redirect("/member/"+user.login_name)
    else:
        form.display_name.data = user.display_name
        form.email.data = user.email_address

    return render_template("profile/change_account.jade", profile=user, form=form, page_title="Change Account Details - Scarlet's Web")

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
        user.about_me = parser.parse(user.about_me)
        return json.jsonify(about_me=user.about_me)
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
    return redirect("/member/"+user.login_name)
