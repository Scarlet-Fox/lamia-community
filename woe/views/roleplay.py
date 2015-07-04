from woe.models.core import User, Attachment
from woe.parsers import ForumPostParser
from woe.forms.roleplay import CharacterForm
from woe import app
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from flask.ext.login import login_required, current_user
from werkzeug import secure_filename
import os
import arrow, hashlib, mimetypes, time
from woe.utilities import ForumHTMLCleaner, humanize_time, parse_search_string_return_q
from mongoengine.queryset import Q
from woe.models.roleplay import Character, CharacterHistory, get_character_slug
from wand.image import Image

@app.route('/characters')
@login_required
def character_database():
    return render_template("roleplay/characters.jade", page_title="Characters - World of Equestria")

@app.route('/characters/<slug>/gallery', methods=["GET",])
@login_required
def character_gallery(slug):
    try:
        character = Character.objects(slug=slug.strip().lower())[0]
    except IndexError:
        abort(404) 
    
    images = Attachment.objects(character=character, character_gallery=True, character_emote=False)
    emotes = Attachment.objects(character=character, character_gallery=True, character_emote=True)
        
    return render_template("roleplay/character_gallery.jade", character=character, images=images, emotes=emotes, page_title="%s's Gallery - Character Database - World of Equestria" % unicode(character.name))

@app.route('/characters/<slug>/manage-gallery', methods=["GET",])
@login_required
def manage_gallery(slug):
    try:
        character = Character.objects(slug=slug.strip().lower())[0]
    except IndexError:
        abort(404) 
        
    if current_user._get_current_object() != character.creator and not current_user._get_current_object().is_admin:
        return abort(404)
        
    images = Attachment.objects(character=character, character_gallery=True)
        
    return render_template("roleplay/manage_gallery.jade", character=character, images=images, page_title="Edit %s's Gallery - Character Database - World of Equestria" % unicode(character.name))

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

        character = Character()
        character.age = form.age.data
        character.species =form.species.data
        character.name = form.name.data
        character.motto = form.motto.data
        character.appearance = form.appearance.data
        character.personality = form.personality.data
        character.backstory = form.backstory.data
        character.other = form.other.data
        character.created = arrow.utcnow().datetime
        character.post_count = 0
        character.slug = get_character_slug(character.name)
        character.creator = current_user._get_current_object()
        character.creator_name = current_user._get_current_object().login_name
        character.creator_display_name = current_user._get_current_object().display_name
        character.save()
        return redirect("/characters/"+unicode(character.slug))
    else:
        pass
    
    return render_template("roleplay/new_character.jade", form=form, page_title="Create a Character - World of Equestria")

@app.route('/characters/<slug>/edit-profile', methods=["GET","POST"])
@login_required
def character_edit_profile(slug):
    try:
        character = Character.objects(slug=slug.strip().lower())[0]
    except IndexError:
        return abort(404)
        
    if current_user._get_current_object() != character.creator and not current_user._get_current_object().is_admin:
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
            
        c = CharacterHistory(creator=current_user._get_current_object(),
                created=arrow.utcnow().datetime,
                data={
                    "age": character.age,
                    "species": character.species,
                    "name": character.name,
                    "motto": character.motto,
                    "appearance": character.appearance,
                    "personality": character.personality,
                    "backstory": character.backstory,
                    "other": character.other
                }
            )
        character.history.append(c)
        character.age = form.age.data
        character.species =form.species.data
        character.name = form.name.data
        character.motto = form.motto.data
        character.appearance = form.appearance.data
        character.personality = form.personality.data
        character.backstory = form.backstory.data
        character.other = form.other.data
        character.save()
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
    
    return render_template("roleplay/edit_character_profile.jade", character=character, form=form, page_title="Editing %s - Character Database - World of Equestria" % (unicode(character.name),))    

@app.route('/characters/<slug>/view-posts/character-post-list-api', methods=["GET",])
@login_required
def character_recent_activity_api(slug):
    try:
        character = Character.objects(slug=slug.strip().lower())[0]
    except IndexError:
        abort(404) 
        
    try:
        draw = int(request.args.get("draw"))
    except:
        draw = 0
    
    table_data = []
    for i, post in enumerate(character.posts):
        table_data.append(
            [
                """<a href="/t/%s/page/1/post/%s">%s</a>""" % (
                        post.topic.slug,
                        post.pk,
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
@login_required
def character_recent_activity(slug):
    try:
        character = Character.objects(slug=slug.strip().lower())[0]
    except IndexError:
        abort(404)
        
    return render_template("roleplay/character_posts.jade", character=character, page_title="%s - Character Database - World of Equestria" % (unicode(character.name),))  

@app.route('/user-characters-api', methods=["POST",])
@login_required
def send_user_characters():
    characters = Character.objects(creator=current_user._get_current_object()).order_by("name")
    character_data = []
    for character in characters:
        parsed_character = {}
        parsed_character["name"] = character.name
        parsed_character["slug"] = character.slug
        try:
            parsed_character["default_avvie"] = character.default_avatar.get_specific_size(50)
        except:
            parsed_character["default_avvie"] = ""
        parsed_character["alternate_avvies"] = []
        
        if parsed_character["default_avvie"] != "":
            parsed_character["alternate_avvies"].append({"url": character.default_avatar.get_specific_size(50), "alt": character.default_avatar.alt})
            
        for attachment in Attachment.objects(character=character, character_emote=True, character_gallery=True).order_by("created_date"):
            if attachment == character.default_avatar:
                continue
            parsed_attachment = {}
            parsed_attachment["url"] = attachment.get_specific_size(50)
            parsed_attachment["alt"] = attachment.alt
            parsed_character["alternate_avvies"].append(parsed_attachment)
        character_data.append(parsed_character)
    return app.jsonify(characters=character_data)

@app.route('/character-list-api', methods=["GET",])
@login_required
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
    elif order == 4:
        order = "creator_display_name"
    else:
        order = "created"

    try:
        direction = request.args.get("order[0][dir]")
    except:
        direction = "desc"

    if direction == "desc":
        order = "-"+order
    
    query = request.args.get("search[value]", "")[0:100]
    
    character_count = Character.objects(hidden=False).count()
    filtered_character_count = Character.objects(Q(creator_display_name__icontains=query) | Q(name__icontains=query), hidden=False).count()
    characters = Character.objects(Q(creator_display_name__icontains=query) | Q(name__icontains=query), hidden=False).order_by(order)[current:current+length]
    
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
                character.creator_display_name
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
        character = Character.objects(slug=slug.strip().lower())[0]
    except IndexError:
        abort(404)
        
    if current_user._get_current_object().is_admin != True:
        return abort(404)
    
    character.update(hidden=not character.hidden)
    
    return app.jsonify(url="/characters/"+unicode(character.slug))

@app.route('/characters/<slug>', methods=["GET",])
@login_required
def character_basic_profile(slug):
    try:
        character = Character.objects(slug=slug.strip().lower())[0]
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
        
    return render_template("roleplay/character_profile.jade", character=character, page_title="%s - Character Database - World of Equestria" % (unicode(character.name),))

@app.route('/characters/<slug>/manage-gallery/toggle-emote', methods=["POST",])
@login_required
def toggle_character_gallery_image_emote(slug):
    request_json = request.get_json(force=True)
    
    try:
        character = Character.objects(slug=slug.strip().lower())[0]
    except IndexError:
        return abort(404) 
        
    if current_user._get_current_object() != character.creator and not current_user._get_current_object().is_admin:
        return abort(404)
        
    try:
        attachment = Attachment.objects(pk=request_json["pk"])[0]
    except IndexError:
        return abort(404)
        
    if attachment.character != character:
        return abort(404)
    
    attachment.update(character_emote=not attachment.character_emote)    
    return app.jsonify(success=True)

@app.route('/characters/<slug>/manage-gallery/remove-image', methods=["POST",])
@login_required
def remove_image_from_character_gallery(slug):
    request_json = request.get_json(force=True)
    
    try:
        character = Character.objects(slug=slug.strip().lower())[0]
    except IndexError:
        return abort(404) 
        
    if current_user._get_current_object() != character.creator and not current_user._get_current_object().is_admin:
        return abort(404)
        
    try:
        attachment = Attachment.objects(pk=request_json["pk"])[0]
    except IndexError:
        return abort(404)
        
    if attachment.character != character:
        return abort(404)
        
    if attachment == character.default_avatar:
        character.update(default_avatar=None)
        
    if attachment == character.default_gallery_image:
        character.update(default_gallery_image=None)
    
    attachment.update(character_gallery=False)    
    return app.jsonify(success=True)

@app.route('/characters/<slug>/manage-gallery/make-default-profile', methods=["POST",])
@login_required
def set_default_character_profile_image(slug):
    request_json = request.get_json(force=True)
    
    try:
        character = Character.objects(slug=slug.strip().lower())[0]
    except IndexError:
        return abort(404) 
        
    if current_user._get_current_object() != character.creator and not current_user._get_current_object().is_admin:
        return abort(404)
        
    try:
        attachment = Attachment.objects(pk=request_json["pk"])[0]
    except IndexError:
        return abort(404)
        
    if attachment.character != character:
        return abort(404)
        
    character.update(legacy_gallery_field=None)
    character.update(default_gallery_image=attachment)
    return app.jsonify(success=True)

@app.route('/characters/<slug>/manage-gallery/make-default-avatar', methods=["POST",])
@login_required
def set_default_character_avatar(slug):
    request_json = request.get_json(force=True)
    
    try:
        character = Character.objects(slug=slug.strip().lower())[0]
    except IndexError:
        return abort(404) 
        
    if current_user._get_current_object() != character.creator and not current_user._get_current_object().is_admin:
        return abort(404)
        
    try:
        attachment = Attachment.objects(pk=request_json["pk"])[0]
    except IndexError:
        return abort(404)
        
    if attachment.character != character:
        return abort(404)
        
    character.update(legacy_avatar_field=None)
    character.update(default_avatar=attachment)
    attachment.update(character_emote=True)
    return app.jsonify(success=True)

@app.route('/characters/<slug>/manage-gallery/edit-image', methods=["POST",])
@login_required
def edit_gallery_image(slug):
    request_json = request.get_json(force=True)
    
    try:
        character = Character.objects(slug=slug.strip().lower())[0]
    except IndexError:
        return abort(404) 
        
    if current_user._get_current_object() != character.creator and not current_user._get_current_object().is_admin:
        return abort(404)
        
    try:
        attachment = Attachment.objects(pk=request_json["pk"])[0]
    except IndexError:
        return abort(404)
        
    if attachment.character != character:
        return abort(404)
        
    cleaner = ForumHTMLCleaner()
    
    attachment.update(caption=cleaner.basic_escape(request_json.get("author", "")))
    attachment.update(alt=cleaner.basic_escape(request_json.get("caption", "")))
    attachment.update(origin_url=cleaner.basic_escape(request_json.get("source", "")))
    
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
            character = Character.objects(slug=slug.strip().lower())[0]
        except IndexError:
            abort(404) 
        
        if current_user._get_current_object() != character.creator and not current_user._get_current_object().is_admin:
            return abort(404)
        
        attach = Attachment()
        attach.character = character
        attach.character_name = character.name
        attach.character_gallery = True
        attach.character_emote = False
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
        upload_path = os.path.join(os.getcwd(), "woe/static/uploads", str(time.time())+"_"+str(current_user.pk)+filename)
        attach.path = str(time.time())+"_"+str(current_user.pk)+filename
        attach.save()
        image.save(filename=upload_path)
        
        if character.default_avatar == None and character.legacy_avatar_field == None:
            character.update(default_avatar=attach)
            
        if character.default_gallery_image == None and character.legacy_gallery_field == None:
            character.update(default_gallery_image=attach)
        
        return app.jsonify(attachment=str(attach.pk), xsize=attach.x_size)
    else:
        return abort(404)
