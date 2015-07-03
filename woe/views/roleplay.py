from woe.models.core import User
from woe.parsers import ForumPostParser
from woe.forms.roleplay import CharacterForm
from woe import app
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from flask.ext.login import login_required, current_user
from werkzeug import secure_filename
import os
import arrow
from woe.utilities import ForumHTMLCleaner, humanize_time, parse_search_string_return_q
from mongoengine.queryset import Q
from woe.models.roleplay import Character, CharacterHistory

@app.route('/characters')
@login_required
def character_database():
    return render_template("roleplay/characters.jade", page_title="Characters - World of Equestria")

@app.route('/characters/<slug>/edit-profile', methods=["GET","POST"])
@login_required
def character_edit_profile(slug):
    try:
        character = Character.objects(slug=slug.strip().lower())[0]
    except IndexError:
        abort(404)
    
    form = CharacterForm(csrf_enabled=False)
    if form.validate_on_submit():
        cleaner = ForumHTMLCleaner()
        try:
            name = cleaner.escape(form.name.data)
        except:
            return abort(500)
        try:
            species = cleaner.escape(form.species.data)
        except:
            return abort(500)
        try:
            motto = cleaner.escape(form.motto.data)
        except:
            return abort(500)
        try:
            age = cleaner.escape(form.age.data)
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
