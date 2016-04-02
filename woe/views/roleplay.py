from woe.parsers import ForumPostParser
from woe.forms.roleplay import CharacterForm
from woe import app
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from flask.ext.login import login_required, current_user
from werkzeug import secure_filename
import os
import arrow, hashlib, mimetypes, time
from woe.utilities import ForumHTMLCleaner, humanize_time, parse_search_string_return_q, parse_search_string
from mongoengine.queryset import Q
from wand.image import Image
import woe.sqlmodels as sqlm
from woe import sqla

@app.route('/characters')
def character_database():
    return render_template("roleplay/characters.jade", page_title="Characters - Scarlet's Web")

@app.route('/characters/<slug>/gallery', methods=["GET",])
def character_gallery(slug):
    try:
        character = sqla.session.query(sqlm.Character).filter_by(slug=slug.strip().lower())[0]
    except IndexError:
        abort(404)

    images = sqla.session.query(sqlm.Attachment).filter_by(
        character = character,
        character_avatar = False
        ).order_by("Attachment.character_gallery_weight").all()

    emotes = sqla.session.query(sqlm.Attachment).filter_by(
        character = character,
        character_avatar = True
        ).order_by("Attachment.character_gallery_weight").all()

    return render_template("roleplay/character_gallery.jade", character=character, images=images, emotes=emotes, page_title="%s's Gallery - Character Database - Scarlet's Web" % unicode(character.name))

@app.route('/characters/<slug>/manage-gallery', methods=["GET",])
@login_required
def manage_gallery(slug):
    try:
        character = sqla.session.query(sqlm.Character).filter_by(slug=slug.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user._get_current_object() != character.author and not current_user._get_current_object().is_admin:
        return abort(404)

    images = sqla.session.query(sqlm.Attachment).filter_by(
        character = character
        ).order_by("Attachment.character_gallery_weight").all()

    return render_template("roleplay/manage_gallery.jade", character=character, images=images, page_title="Edit %s's Gallery - Character Database - Scarlet's Web" % unicode(character.name))

@app.route('/characters/new-character', methods=["GET","POST"])
@login_required
def create_character():
    form = CharacterForm(csrf_enabled=False)
    if form.validate_on_submit():
        cleaner = ForumHTMLCleaner()
        try:
            name = cleaner.basic_escape(form.name.data)
        except:
            return abort(500)
        try:
            species = cleaner.basic_escape(form.species.data)
        except:
            return abort(500)
        try:
            motto = cleaner.basic_escape(form.motto.data)
        except:
            return abort(500)
        try:
            age = cleaner.basic_escape(form.age.data)
        except:
            return abort(500)

        character = sqlm.Character()
        character.age = form.age.data
        character.species =form.species.data
        character.name = form.name.data
        character.motto = form.motto.data
        character.appearance = form.appearance.data
        character.personality = form.personality.data
        character.backstory = form.backstory.data
        character.other = form.other.data
        character.created = arrow.utcnow().datetime.replace(tzinfo=None)
        character.post_count = 0
        character.slug = sqlm.get_character_slug(character.name)
        character.author = current_user._get_current_object()
        sqla.session.add(character)
        sqla.session.commit()
        return redirect("/characters/"+unicode(character.slug))
    else:
        pass

    return render_template("roleplay/new_character.jade", form=form, page_title="Create a Character - Scarlet's Web")

@app.route('/characters/<slug>/edit-profile', methods=["GET","POST"])
@login_required
def character_edit_profile(slug):
    try:
        character = sqla.session.query(sqlm.Character).filter_by(slug=slug.strip().lower())[0]
    except IndexError:
        return abort(404)

    if current_user._get_current_object() != character.author and not current_user._get_current_object().is_admin:
        return abort(404)

    form = CharacterForm(csrf_enabled=False)
    if form.validate_on_submit():
        cleaner = ForumHTMLCleaner()
        try:
            name = cleaner.basic_escape(form.name.data)
        except:
            return abort(500)
        try:
            species = cleaner.basic_escape(form.species.data)
        except:
            return abort(500)
        try:
            motto = cleaner.basic_escape(form.motto.data)
        except:
            return abort(500)
        try:
            age = cleaner.basic_escape(form.age.data)
        except:
            return abort(500)

        c = {
                "author": current_user._get_current_object().id,
                "created": str(arrow.utcnow().datetime),
                "data": {
                        "age": character.age+"",
                        "species": character.species+"",
                        "name": character.name+"",
                        "motto": character.motto+"",
                        "appearance": character.appearance+"",
                        "personality": character.personality+"",
                        "backstory": character.backstory+"",
                        "other": character.other+""
                }
            }

        if character.character_history == None:
            character.character_history = []
        character.character_history.append(c)

        character.age = form.age.data
        character.species =form.species.data
        character.name = form.name.data
        character.motto = form.motto.data
        character.appearance = form.appearance.data
        character.personality = form.personality.data
        character.backstory = form.backstory.data
        character.other = form.other.data

        sqla.session.add(character)
        sqla.session.commit()

        return redirect("/characters/"+unicode(character.slug))
    else:
        form.name.data = character.name
        if character.age != None:
            form.age.data = character.age
        if character.species != None:
            form.species.data = character.species
        if character.motto != None:
            form.motto.data = character.motto
        if character.appearance != None:
            form.appearance.data = character.appearance
        if character.personality != None:
            form.personality.data = character.personality
        if character.backstory != None:
            form.backstory.data = character.backstory
        if character.other != None:
            form.other.data = character.other

    return render_template("roleplay/edit_character_profile.jade", character=character, form=form, page_title="Editing %s - Character Database - Scarlet's Web" % (unicode(character.name),))

@app.route('/characters/<slug>/view-posts/character-post-list-api', methods=["GET",])
def character_recent_activity_api(slug):
    try:
        character = sqla.session.query(sqlm.Character).filter_by(slug=slug.strip().lower())[0]
    except IndexError:
        abort(404)

    try:
        draw = int(request.args.get("draw"))
    except:
        draw = 0

    table_data = []

    posts = sqla.session.query(sqlm.Post).filter_by(character=character).all()

    for i, post in enumerate(posts):
        table_data.append(
            [
                """<a href="/t/%s/page/1/post/%s">%s</a>""" % (
                        post.topic.slug,
                        post.id,
                        post.topic.title
                    ),
                post.author.display_name,
                humanize_time(post.created),
                arrow.get(post.created).timestamp
            ]
        )
    data = {
        "draw": draw,
        "recordsTotal": len(table_data),
        "recordsFiltered": len(table_data),
        "data": table_data
    }
    return app.jsonify(data)

@app.route('/characters/<slug>/view-posts', methods=["GET",])
def character_recent_activity(slug):
    try:
        character = sqla.session.query(sqlm.Character).filter_by(slug=slug.strip().lower())[0]
    except IndexError:
        abort(404)

    return render_template("roleplay/character_posts.jade", character=character, page_title="%s - Character Database - Scarlet's Web" % (unicode(character.name),))

@app.route('/user-characters-api', methods=["POST",])
@login_required
def send_user_characters():
    characters = sqla.session.query(sqlm.Character).filter_by(
            author = current_user._get_current_object(),
            hidden = False
        ).order_by(sqlm.Character.name)
    character_data = []

    for character in characters:
        parsed_character = {}
        parsed_character["name"] = character.name
        parsed_character["slug"] = character.slug
        try:
            parsed_character["default_avvie"] = character.get_avatar(50)
        except:
            parsed_character["default_avvie"] = ""
        parsed_character["alternate_avvies"] = []

        for attachment in sqla.session.query(sqlm.Attachment) \
                .filter_by(character_avatar=True, character=character) \
                .order_by(sqlm.Attachment.character_gallery_weight):

            parsed_attachment = {}
            parsed_attachment["url"] = attachment.get_specific_size(50)
            parsed_attachment["alt"] = attachment.alt
            parsed_attachment["id"] = attachment.id
            parsed_character["alternate_avvies"].append(parsed_attachment)

        character_data.append(parsed_character)
    return app.jsonify(characters=character_data)

@app.route('/character-list-api', methods=["GET",])
def character_list_api():
    try:
        current = int(request.args.get("start"))
    except:
        current = 0

    try:
        draw = int(request.args.get("draw"))
    except:
        draw = 0

    try:
        length = int(request.args.get("length"))
    except:
        length = 10

    try:
        order = int(request.args.get("order[0][column]"))
    except:
        order = 4

    if order == 0:
        order = "name"
    elif order == 1:
        order = "age"
    elif order == 2:
        order = "species"
    elif order == 3:
        order = "created"
    else:
        order = "created"

    try:
        direction = request.args.get("order[0][dir]")
    except:
        direction = "desc"

    query = request.args.get("search[value]", "")[0:100]

    character_count = sqla.session.query(sqlm.Character).filter_by(hidden=False).count()
    filtered_character_count = parse_search_string(
            query, sqlm.Character, sqla.session.query(sqlm.Character), ["name",]
        ).filter_by(hidden=False).count()

    if direction == "desc":
        characters = parse_search_string(
                query, sqlm.Character, sqla.session.query(sqlm.Character), ["name",]
            ).order_by(sqla.desc(getattr(sqlm.Character, order)))[current:current+length]
    else:
        characters = parse_search_string(
                query, sqlm.Character, sqla.session.query(sqlm.Character), ["name",]
            ).order_by(getattr(sqlm.Character, order))[current:current+length]

    table_data = []
    for i, character in enumerate(characters):
        table_data.append(
            [
                """<a href="/characters/%s">%s</a>   """ % (
                        character.slug,
                        character.name
                    ),
                character.age,
                character.species,
                humanize_time(character.created),
                character.author.display_name
            ]
        )
    data = {
        "draw": draw,
        "recordsTotal": character_count,
        "recordsFiltered": filtered_character_count,
        "data": table_data
    }
    return app.jsonify(data)

@app.route('/characters/<slug>/toggle-hide', methods=["POST",])
@login_required
def toggle_hide_character(slug):
    try:
        character = sqla.session.query(sqlm.Character).filter_by(slug=slug.strip().lower())[0]
    except IndexError:
        abort(404)

    if current_user._get_current_object().is_admin != True:
        return abort(404)

    if character.hidden == None:
        character.hidden = True

    character.hidden = not character.hidden

    sqla.session.add(character)
    sqla.session.commit()

    return app.jsonify(url="/characters/"+unicode(character.slug))

@app.route('/characters/<slug>', methods=["GET",])
def character_basic_profile(slug):
    try:
        character = sqla.session.query(sqlm.Character).filter_by(slug=slug.strip().lower())[0]
    except IndexError:
        abort(404)
    parser = ForumPostParser()

    if character.appearance:
        character.appearance = parser.parse(character.appearance)

    if character.personality:
        character.personality = parser.parse(character.personality)

    if character.backstory:
        character.backstory = parser.parse(character.backstory)

    if character.other:
        character.other = parser.parse(character.other)

    return render_template("roleplay/character_profile.jade", character=character, page_title="%s - Character Database - Scarlet's Web" % (unicode(character.name),))

@app.route('/characters/<slug>/manage-gallery/toggle-emote', methods=["POST",])
@login_required
def toggle_character_gallery_image_emote(slug):
    request_json = request.get_json(force=True)

    try:
        character = sqla.session.query(sqlm.Character).filter_by(slug=slug.strip().lower())[0]
    except IndexError:
        return abort(404)

    if current_user._get_current_object() != character.author and not current_user._get_current_object().is_admin:
        return abort(404)

    try:
        attachment = sqla.session.query(sqlm.Attachment).filter_by(id=request_json["pk"])[0]
    except IndexError:
        return abort(404)

    if attachment.character != character:
        return abort(404)

    if attachment.character_avatar == None:
        attachment.character_avatar = True

    attachment.character_avatar = not attachment.character_avatar

    sqla.session.add(attachment)
    sqla.session.commit()

    return app.jsonify(success=True)

@app.route('/characters/<slug>/manage-gallery/remove-image', methods=["POST",])
@login_required
def remove_image_from_character_gallery(slug):
    request_json = request.get_json(force=True)

    try:
        character = sqla.session.query(sqlm.Character).filter_by(slug=slug.strip().lower())[0]
    except IndexError:
        return abort(404)

    if current_user._get_current_object() != character.author and not current_user._get_current_object().is_admin:
        return abort(404)

    try:
        attachment = sqla.session.query(sqlm.Attachment).filter_by(id=request_json["pk"])[0]
    except IndexError:
        return abort(404)

    if attachment.character != character:
        return abort(404)

    if attachment == character.default_avatar:
        character.default_avatar = None

    if attachment == character.default_gallery_image:
        character.default_gallery_image = None

    attachment.character_gallery = False
    attachment.character = None
    attachment.hidden = True

    sqla.session.add(character)
    sqla.session.add(attachment)
    sqla.session.commit()

    return app.jsonify(success=True)

@app.route('/characters/<slug>/manage-gallery/make-default-profile', methods=["POST",])
@login_required
def set_default_character_profile_image(slug):
    request_json = request.get_json(force=True)

    try:
        character = sqla.session.query(sqlm.Character).filter_by(slug=slug.strip().lower())[0]
    except IndexError:
        return abort(404)

    if current_user._get_current_object() != character.author and not current_user._get_current_object().is_admin:
        return abort(404)

    try:
        attachment = sqla.session.query(sqlm.Attachment).filter_by(id=request_json["pk"])[0]
    except IndexError:
        return abort(404)

    if attachment.character != character:
        return abort(404)

    character.legacy_gallery_field = None
    character.default_gallery_image = attachment

    sqla.session.add(character)
    sqla.session.commit()

    return app.jsonify(success=True)

@app.route('/characters/<slug>/manage-gallery/make-default-avatar', methods=["POST",])
@login_required
def set_default_character_avatar(slug):
    request_json = request.get_json(force=True)

    try:
        character = sqla.session.query(sqlm.Character).filter_by(slug=slug.strip().lower())[0]
    except IndexError:
        return abort(404)

    if current_user._get_current_object() != character.author and not current_user._get_current_object().is_admin:
        return abort(404)

    try:
        attachment = sqla.session.query(sqlm.Attachment).filter_by(id=request_json["pk"])[0]
    except IndexError:
        return abort(404)

    if attachment.character != character:
        return abort(404)

    character.legacy_avatar_field = None
    character.default_avatar = attachment
    # attachment.character_avatar = True

    sqla.session.add(character)
    sqla.session.commit()
    # sqla.session.add(attachment)
    # sqla.session.commit()

    return app.jsonify(success=True)

@app.route('/characters/<slug>/manage-gallery/edit-image', methods=["POST",])
@login_required
def edit_gallery_image(slug):
    request_json = request.get_json(force=True)

    try:
        character = sqla.session.query(sqlm.Character).filter_by(slug=slug.strip().lower())[0]
    except IndexError:
        return abort(404)

    if current_user._get_current_object() != character.author and not current_user._get_current_object().is_admin:
        return abort(404)

    try:
        attachment = sqla.session.query(sqlm.Attachment).filter_by(id=request_json["pk"])[0]
    except IndexError:
        return abort(404)

    if attachment.character != character:
        return abort(404)

    cleaner = ForumHTMLCleaner()

    attachment.caption=cleaner.basic_escape(request_json.get("author", ""))
    attachment.alt=cleaner.basic_escape(request_json.get("caption", ""))
    attachment.origin_url=cleaner.basic_escape(request_json.get("source", ""))

    sqla.session.add(attachment)
    sqla.session.commit()

    return app.jsonify(success=True)

@app.route('/characters/<slug>/manage-gallery/attach', methods=['POST',])
@login_required
def create_attachment_for_character(slug):
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        image = Image(file=file)
        img_bin = image.make_blob()
        img_hash = hashlib.sha512(img_bin).hexdigest()

        try:
            character = sqla.session.query(sqlm.Character).filter_by(slug=slug.strip().lower())[0]
        except IndexError:
            abort(404)

        if current_user._get_current_object() != character.author and not current_user._get_current_object().is_admin:
            return abort(404)

        _time = time.time()

        attach = sqlm.Attachment()
        attach.character = character
        attach.character_gallery = True
        attach.character_avatar = False
        attach.character_gallery_weight = 100000
        attach.extension = filename.split(".")[-1]
        attach.x_size = image.width
        attach.y_size = image.height
        attach.mimetype = mimetypes.guess_type(filename)[0]
        attach.size_in_bytes = len(img_bin)
        attach.owner_name = current_user._get_current_object().login_name
        attach.owner = current_user._get_current_object()
        attach.alt = filename
        attach.used_in = 0
        attach.created_date = arrow.utcnow().datetime
        attach.file_hash = img_hash
        attach.linked = False
        upload_path = os.path.join(os.getcwd(), "woe/static/uploads", str(_time)+"_"+str(current_user.id)+filename)
        attach.path = str(_time)+"_"+str(current_user.id)+filename

        sqla.session.add(attach)
        sqla.session.commit()

        image.save(filename=upload_path)

        if character.default_avatar == None and character.legacy_avatar_field == None:
            character.default_avatar = attach

        if character.default_gallery_image == None and character.legacy_gallery_field == None:
            character.default_gallery_image = attach

        sqla.session.add(character)
        sqla.session.commit()

        return app.jsonify(attachment=str(attach.id), xsize=attach.x_size)
    else:
        return abort(404)
