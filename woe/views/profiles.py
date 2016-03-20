from woe.models.core import User, DisplayNameHistory, IPAddress, Fingerprint
from woe.parsers import ForumPostParser
from woe.forms.core import AvatarTitleForm, DisplayNamePasswordForm, UserSettingsForm
from woe import app
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from flask.ext.login import login_required, current_user
from werkzeug import secure_filename
import os
import arrow
from woe.utilities import ForumHTMLCleaner
from woe import sqla
import woe.sqlmodels as sqlm
import time

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
    return render_template("profile.jade", profile=user, page_title="%s - Scarlet's Web" % (unicode(user.display_name),))

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
