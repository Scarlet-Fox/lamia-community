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

@app.route('/member/<login_name>/mod-panel')
@login_required
def user_moderation_panel(login_name):
    if current_user._get_current_object().is_admin != True:
        abort(404)

    try:
        user = User.objects(login_name=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    last_five_ip_addresses = IPAddress.objects(user=user)[0:5]

    fingerprints_with_top_matches = {}
    most_recent_fingerprints = Fingerprint.objects(user=user)[0:5]

    for recent_fingerprint in most_recent_fingerprints:
        matches = []
        other_fingerprints = Fingerprint.objects(
            user__ne=user,
            fingerprint_factors__gte = recent_fingerprint.fingerprint_factors-6,
            fingerprint_factors__lte = recent_fingerprint.fingerprint_factors+6
        )
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
        title="Mod Details for %s - World of Equestria" % (unicode(user.display_name),),
        recent_fingerprints=most_recent_fingerprints,
        top_fingerprint_matches=fingerprints_with_top_matches)

@app.route('/member/<login_name>')
@login_required
def view_profile(login_name):
    try:
        user = User.objects(login_name=login_name.strip().lower())[0]
    except IndexError:
        abort(404)
    parser = ForumPostParser()
    try:
        user.about_me = parser.parse(user.about_me)
    except:
        user.about_me = ""
    return render_template("profile.jade", profile=user, page_title="%s - World of Equestria" % (unicode(user.display_name),))

@app.route('/member/<login_name>/validate-user', methods=['POST'])
@login_required
def validate_user(login_name):
    try:
        user = User.objects(login_name=login_name.strip().lower())[0]
    except IndexError:
        return abort(404)

    if current_user._get_current_object().is_admin != True:
        return abort(404)

    user.update(validated=True)

    return app.jsonify(url="/member/"+unicode(login_name))

@app.route('/member/<login_name>/toggle-ignore', methods=['POST'])
@login_required
def toggle_ignore_user(login_name):
    try:
        user = User.objects(login_name=login_name.strip().lower())[0]
    except IndexError:
        return abort(404)

    if current_user._get_current_object() == user:
        return abort(404)

    if user in current_user._get_current_object().ignored_users:
        c = current_user._get_current_object()
        c.ignored_users.remove(user)
        c.save()
    else:
        current_user._get_current_object().update(add_to_set__ignored_users=user)

    return app.jsonify(url="/member/"+unicode(login_name))

@app.route('/member/<login_name>/toggle-follow', methods=['POST'])
@login_required
def toggle_follow_user(login_name):
    try:
        user = User.objects(login_name=login_name.strip().lower())[0]
    except IndexError:
        return abort(404)

    if current_user in user.ignored_users:
        user.update(add_to_set__ignored_users=current_user._get_current_object())
        return abort(404)

    if current_user._get_current_object() == user:
        return abort(404)

    if current_user._get_current_object() in user.followed_by:
        user.followed_by.remove(current_user._get_current_object())
        user.save()
    else:
        user.update(add_to_set__followed_by=current_user._get_current_object())

    return app.jsonify(url="/member/"+unicode(login_name))

@app.route('/member/<login_name>/change-avatar-title', methods=['GET', 'POST'])
@login_required
def change_avatar_or_title(login_name):
    try:
        user = User.objects(login_name=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user != user and not current_user.is_admin:
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

            form.avatar_image.save(filename=os.path.join(app.config["AVATAR_UPLOAD_DIR"],timestamp + str(user.pk) + extension))

            form.fourty_image.save(filename=os.path.join(app.config["AVATAR_UPLOAD_DIR"],timestamp + str(user.pk) + "_40" + extension))
            form.sixty_image.save(filename=os.path.join(app.config["AVATAR_UPLOAD_DIR"],timestamp + str(user.pk) + "_60" + extension))

            user.avatar_extension = extension
            user.avatar_timestamp = timestamp
            user.avatar_full_x, user.avatar_full_y = form.avatar_image.size
            user.avatar_40_x, user.avatar_40_y = form.fourty_image.size
            user.avatar_60_x, user.avatar_60_y = form.sixty_image.size
        user.title = form.title.data
        user.save()
        return redirect("/member/"+user.login_name)
    else:
        filename = None
        form.title.data = user.title

    return render_template("profile/change_avatar.jade", profile=user, form=form, page_title="Change Avatar and Title - World of Equestria")

@app.route('/member/<login_name>/change-settings', methods=['GET', 'POST'])
@login_required
def change_user_settings(login_name):
    try:
        user = User.objects(login_name=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user._get_current_object() != user and not current_user._get_current_object().is_admin:
        abort(404)

    form = UserSettingsForm(csrf_enabled=False)

    if form.validate_on_submit():
        user.update(time_zone=form.time_zone.data)
        return redirect("/member/"+user.login_name)
    else:
        form.time_zone.data = user.time_zone

    return render_template("profile/change_user_settings.jade", profile=user, form=form, page_title="Change Settings - World of Equestria")

@app.route('/member/<login_name>/change-account', methods=['GET', 'POST'])
@login_required
def change_display_name_password(login_name):
    try:
        user = User.objects(login_name=login_name.strip().lower())[0]
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
            dnh = DisplayNameHistory(name=user.display_name, date=arrow.utcnow().datetime)
            user.display_name_history.append(dnh)
            user.display_name = form.display_name.data.strip()

        if form.email.data.strip() != user.email_address:
            user.email_address = form.email.data

        user.save()

        return redirect("/member/"+user.login_name)
    else:
        form.display_name.data = user.display_name
        form.email.data = user.email_address

    return render_template("profile/change_account.jade", profile=user, form=form, page_title="Change Account Details - World of Equestria")

@app.route('/member/<login_name>/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile(login_name):
    try:
        user = User.objects(login_name=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user != user and not current_user.is_admin:
        abort(404)

    if request.method == 'POST':
        cleaner = ForumHTMLCleaner()
        user.about_me = cleaner.clean(request.form.get("about_me"))
        user.save()
        parser = ForumPostParser()
        user.about_me = parser.parse(user.about_me)
        return json.jsonify(about_me=user.about_me)
    else:
        return json.jsonify(content=user.about_me)

@app.route('/member/<login_name>/remove-avatar', methods=['POST'])
@login_required
def remove_avatar(login_name):
    try:
        user = User.objects(login_name=login_name.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user != user and not current_user.is_admin:
        abort(404)
    try:
        os.remove(os.path.join(app.config["AVATAR_UPLOAD_DIR"],user.avatar_timestamp + str(user.pk) + user.avatar_extension))
        os.remove(os.path.join(app.config["AVATAR_UPLOAD_DIR"],user.avatar_timestamp + str(user.pk) + "_40" + user.avatar_extension))
        os.remove(os.path.join(app.config["AVATAR_UPLOAD_DIR"],user.avatar_timestamp + str(user.pk) + "_60" + user.avatar_extension))
    except OSError:
        pass
    user.avatar_extension = None
    user.avatar_timestamp = ""
    user.save()
    return redirect("/member/"+user.login_name)
