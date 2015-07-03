from woe.models.core import User, DisplayNameHistory, IPAddress, Fingerprint
from woe.parsers import ForumPostParser
from woe.forms.core import AvatarTitleForm, DisplayNamePasswordForm, UserSettingsForm
from woe import app
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash
from flask.ext.login import login_required, current_user
from werkzeug import secure_filename
import os
import arrow
from woe.utilities import ForumHTMLCleaner, humanize_time, parse_search_string_return_q
from mongoengine.queryset import Q
from woe.models.roleplay import Character

@app.route('/characters')
@login_required
def character_database():
    return render_template("roleplay/characters.jade", page_title="Characters - World of Equestria")

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
