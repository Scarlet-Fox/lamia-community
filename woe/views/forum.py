from woe import app
from woe import sqla
from woe.parsers import ForumPostParser
from collections import OrderedDict
from woe.forms.core import LoginForm, RegistrationForm
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session
from flask.ext.login import login_user, logout_user, current_user, login_required
import arrow, time, math
from threading import Thread
import random
from woe.utilities import get_top_frequences, scrub_json, humanize_time, ForumHTMLCleaner, parse_search_string_return_q, parse_search_string, get_preview
from woe.views.dashboard import broadcast
import re, json
from datetime import datetime
import woe.sqlmodels as sqlm
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm import joinedload
from BeautifulSoup import BeautifulSoup

mention_re = re.compile("\[@(.*?)\]")
reply_re = re.compile(r'\[reply=(.+?):(post)(:.+?)?\]')
roll_re = re.compile(r'\[roll=(\d+)d(\d+)(?:\+(\d+)|\-(\d+))?\](.*?)\[\/roll\]', re.I)

@app.route('/category-list-api', methods=['GET'])
@login_required
def category_list_api():
    query = request.args.get("q", "")[0:300]
    if len(query) < 2:
        return app.jsonify(results=[])
    results = []
    
    if current_user._get_current_object().is_admin:
        q_ = parse_search_string(query, sqlm.Category, sqla.session.query(sqlm.Category), ["name",])
    else:
        if current_user.is_authenticated() == True:
            q_ = parse_search_string(query, sqlm.Category, sqla.session.query(sqlm.Category), ["name",]).all()
        
        for c in q_:
            if c.restricted == True:
                continue
            else:
                results.append({"text": unicode(c.name), "id": str(c.id)})
        
    return app.jsonify(results=results)

@app.route('/topic-list-api', methods=['GET'])
@login_required
def topic_list_api():
    query = request.args.get("q", "")[0:300]
    if len(query) < 2:
        return app.jsonify(results=[])
    results = []
    
    if current_user._get_current_object().is_admin:
        q_ = parse_search_string(query, sqlm.Topic, sqla.session.query(sqlm.Topic), ["title",])
    else:
        q_ = parse_search_string(query, sqlm.Topic, sqla.session.query(sqlm.Topic) , ["title",])
        
        for t in q_:
            if t.category.restricted == True:
                continue
            else:
                results.append({"text": unicode(t.title), "id": str(t.id)})
        
    return app.jsonify(results=results)

@app.route('/c/<slug>/toggle-follow', methods=['POST'])
@login_required
def toggle_follow_category(slug):
    try:
        category = sqla.session.query(sqlm.Category).filter_by(slug=slug)[0]
    except IndexError:
        return abort(404)
        
    if category.restricted == True and not current_user.is_admin and not current_user in category.allowed_users:
        return abort(404)

    if not current_user._get_current_object() in category.watchers:
        category.watchers.append(current_user._get_current_object())
    else:
        try:
            category.watchers.remove(current_user._get_current_object())
        except:
            pass

    try:
        sqla.session.add(category)
        sqla.session.commit()
    except:
        sqla.session.rollback()

    return app.jsonify(url="/category/"+unicode(category.slug)+"")

@app.route('/t/<slug>/toggle-follow', methods=['POST'])
@login_required
def toggle_follow_topic(slug):
    try:
        topic = sqla.session.query(sqlm.Topic).filter_by(slug=slug)[0]
    except IndexError:
        return abort(404)

    if current_user._get_current_object() in topic.banned:
        return abort(403)

    if not current_user._get_current_object() in topic.watchers:
        topic.watchers.append(current_user._get_current_object())
        if topic.author in topic.watchers:
            broadcast(
              to=[topic.author,],
              category="followed",
              url="/t/%s" % (str(topic.slug),),
              title="%s followed topic %s" % (unicode(current_user.display_name), unicode(topic.title)),
              description="",
              content=topic,
              author=current_user
              )
    else:
        try:
            topic.watchers.remove(current_user._get_current_object())
        except:
            pass

    try:
        sqla.session.add(topic)
        sqla.session.commit()
    except:
        sqla.session.rollback()

    return app.jsonify(url="/t/"+unicode(topic.slug)+"")

@app.route('/t/<slug>/new-post', methods=['POST'])
@login_required
def new_post_in_topic(slug):
    try:
        topic = sqla.session.query(sqlm.Topic).filter_by(slug=slug)[0]
    except IndexError:
        return abort(404)

    if current_user._get_current_object() in topic.banned:
        return abort(403)

    if topic.locked or topic.hidden:
        return app.jsonify(closed_topic=True, closed_message="This topic is closed.")

    request_json = request.get_json(force=True)

    if request_json.get("text", "").strip() == "":
        return app.jsonify(no_content=True)

    cleaner = ForumHTMLCleaner()
    try:
        post_html = cleaner.clean(request_json.get("post", ""))
    except:
        return abort(500)

    try:
        users_last_post = sqla.session.query(sqlm.Post).filter_by(author=current_user._get_current_object()) \
            .order_by(sqla.desc(sqlm.Post.created))[0]
        difference = (arrow.utcnow().datetime - arrow.get(users_last_post.created).datetime).seconds
        if difference < 30 and not current_user._get_current_object().is_admin:
            return app.jsonify(error="Please wait %s seconds before posting again." % (30 - difference))
    except:
        pass

    try:
        character = sqla.session.query(sqlm.Character).filter_by(slug=request_json.get("character"), \
            author=current_user._get_current_object(), hidden=False)[0]
    except:
        character = False

    try:
        avatar = sqla.session.query(sqlm.Attachment).filter_by(character=character, \
            character_gallery=True, character_avatar=True, id=request_json.get("avatar")) \
            .order_by(sqlm.Attachment.character_gallery_weight)[0]

        if avatar == None:
            avatar = sqla.session.query(sqlm.Attachment).filter_by(character=character, \
                character_gallery=True, character_avatar=True) \
                .order_by(sqlm.Attachment.character_gallery_weight)[0]
    except:
        avatar = False

    new_post = sqlm.Post()
    new_post.html = post_html
    new_post.author = current_user._get_current_object()
    new_post.author_name = current_user.login_name
    new_post.topic = topic
    new_post.t_title = topic.title
    new_post.created = arrow.utcnow().datetime.replace(tzinfo=None)
    try:
        if character:
            new_post.character = character
        if avatar:
            new_post.avatar = avatar
    except:
        pass

    sqla.session.add(new_post)
    sqla.session.commit()

    topic.recent_post = new_post
    topic.post_count += 1
    sqla.session.add(topic)

    category = topic.category
    category.recent_post = new_post
    category.recent_topic = topic
    category.post_count += 1
    sqla.session.add(category)
    sqla.session.commit()

    active_rolls = [] # (roll_id, spec, flavor, outcome)
    active_roll_ids = []
    inactive_rolls = [] # (roll_id, spec, flavor, outcome)

    post = new_post
    rolls = roll_re.findall(post.html)
    for i, roll in enumerate(rolls):
        if i > 50:
            continue

        if roll[2] == '':
            base = 0
        else:
            base = roll[2]

        if roll[3] == '':
            penalty = 0
        else:
            penalty = roll[3]

        if int(roll[0]) == 0 or int(roll[0]) > 1000:
            continue

        if int(roll[1]) == 0 or int(roll[1]) > 1000:
            continue

        try:
            roll = sqlm.DiceRoll.query.filter_by(
                order_of_roll = i,
                sides = roll[1],
                number_of_dice = roll[0],
                base = base,
                penalty = penalty,
                content_type = "post",
                content_id = post.id,
                flavor_text = roll[4],
                user = post.author
            )[0]
        except IndexError:
            roll = sqlm.DiceRoll(
                order_of_roll = i,
                sides = roll[1],
                number_of_dice = roll[0],
                base = base,
                penalty = penalty,
                content_type = "post",
                content_id = post.id,
                flavor_text = roll[4],
                created = arrow.utcnow().datetime.replace(tzinfo=None),
                user = post.author
            )
            sqla.session.add(roll)
            sqla.session.commit()

        active_roll_ids.append(roll.id)
        active_rolls.append([roll.id, roll.get_spec(), roll.flavor_text, roll.get_value()])

    all_rolls = sqlm.DiceRoll.query.filter_by(
        content_type = "post",
        content_id = post.id
    )

    for roll in all_rolls:
        if not roll.id in active_roll_ids:
            inactive_rolls.append([roll.id, roll.get_spec(), roll.flavor_text, roll.get_value()])

    clean_html_parser = ForumPostParser()
    parsed_post = {}
    parsed_post["created"] = humanize_time(new_post.created, "MMM D YYYY")
    parsed_post["modified"] = humanize_time(new_post.modified, "MMM D YYYY")
    parsed_post["html"] = clean_html_parser.parse(new_post.html, _object=new_post)
    parsed_post["active_rolls"] = active_rolls
    parsed_post["inactive_rolls"] = inactive_rolls
    parsed_post["_id"] = new_post.id
    parsed_post["user_avatar"] = new_post.author.get_avatar_url()
    parsed_post["user_avatar_x"] = new_post.author.avatar_full_x
    parsed_post["user_avatar_y"] = new_post.author.avatar_full_y
    parsed_post["user_avatar_60"] = new_post.author.get_avatar_url("60")
    parsed_post["user_avatar_x_60"] = new_post.author.avatar_60_x
    parsed_post["user_avatar_y_60"] = new_post.author.avatar_60_y
    parsed_post["user_title"] = new_post.author.title
    parsed_post["author_name"] = new_post.author.display_name
    parsed_post["author_login_name"] = new_post.author.my_url

    if new_post.character is not None:
        try:
            parsed_post["character_name"] = new_post.character.name
            parsed_post["character_slug"] = new_post.character.slug
        except:
            character = None
    else:
        character = None

    if new_post.avatar is not None:
        try:
            parsed_post["character_avatar_small"] = new_post.avatar.get_specific_size(60)
            parsed_post["character_avatar_large"] = new_post.avatar.get_specific_size(200)
            parsed_post["character_avatar"] = True
        except:
            avatar = None
    else:
        avatar = None

    parsed_post["is_author"] = True
    parsed_post["boop_count"] = 0
    parsed_post["one_boop"] = False
    post_count = topic.post_count

    mentions = mention_re.findall(post_html)
    to_notify_m = {}
    for mention in mentions:
        try:
            to_notify_m[mention] = sqla.session.query(sqlm.User).filter_by(login_name=mention)[0]
        except:
            continue

    broadcast(
      to=to_notify_m.values(),
      category="mention",
      url="/t/%s/page/1/post/%s" % (str(topic.slug), str(new_post.id)),
      title="%s mentioned you in %s" % (unicode(new_post.author.display_name), unicode(topic.title)),
      description=new_post.html,
      content=new_post,
      author=new_post.author
      )

    replies = reply_re.findall(post_html)
    to_notify = {}
    for reply_ in replies:
        try:
            to_notify[reply_] = sqla.session.query(sqlm.Post).filter_by(id=reply_[0])[0].author
        except:
            continue

    broadcast(
      to=to_notify.values(),
      category="topic_reply",
      url="/t/%s/page/1/post/%s" % (str(topic.slug), str(new_post.id)),
      title="%s replied to you in %s" % (unicode(new_post.author.display_name), unicode(topic.title)),
      description=new_post.html,
      content=new_post,
      author=new_post.author
      )

    notify_users = []
    for u in topic.watchers:
        if u == new_post.author:
            continue

        skip_user = False
        for _u in to_notify.values():
            if _u.id == u.id:
                skip_user = True
                break

        for _u in to_notify_m.values():
            if _u.id == u.id:
                skip_user = True
                break

        if skip_user:
            continue

        notify_users.append(u)

    broadcast(
        to=notify_users,
        category="topic",
        url="/t/%s/page/1/post/%s" % (str(topic.slug), str(new_post.id)),
        title="%s has replied to %s" % (unicode(new_post.author.display_name), unicode(topic.title)),
        description=new_post.html,
        content=topic,
        author=new_post.author
        )

    return app.jsonify(newest_post=parsed_post, count=post_count, success=True)

@app.route('/boop-post', methods=['POST'])
@login_required
def toggle_post_boop():
    request_json = request.get_json(force=True)

    try:
        post = sqla.session.query(sqlm.Post).filter_by(id=request_json.get("pk"))[0]
    except:
        return abort(404)

    if current_user._get_current_object() == post.author:
        return abort(404)

    if current_user._get_current_object() in post.boops:
        post.boops.remove(current_user._get_current_object())
    else:
        post.boops.append(current_user._get_current_object())
        broadcast(
            to=[post.author,],
            category="boop",
            url="/t/%s/page/1/post/%s" % (str(post.topic.slug), str(post.id)),
            title="%s has booped your post in %s!" % (unicode(current_user._get_current_object().display_name), unicode(post.topic.title)),
            description="",
            content=post,
            author=current_user._get_current_object()
            )

    sqla.session.add(post)
    sqla.session.commit()
    return app.jsonify(success=True)

@app.route('/recent', methods=['GET'], defaults={'page': 1})
@app.route('/recent/page/<page>', methods=['GET'])
def recent_posts(page):
    _starting = arrow.utcnow().replace(hours=-24).datetime.replace(tzinfo=None)
    pagination = 20
    
    try:
        page = int(page)
    except:
        page = 1
    
    recent_posts = sqla.session.query(sqlm.Post) \
        .join(sqlm.Post.topic) \
        .filter(sqlm.Topic.category.has(sqla.or_(
                sqlm.Category.restricted==False
            ))) \
        .filter(sqlm.Post.created > _starting) \
        .filter(sqla.or_(sqlm.Post.hidden == False, sqlm.Post.hidden == None)) \
        .order_by(sqla.desc(sqlm.Post.created)) \
        [(page-1)*pagination:page*pagination]
        
    recent_posts_count = sqla.session.query(sqlm.Post) \
        .join(sqlm.Post.topic) \
        .filter(sqlm.Topic.category.has(sqla.or_(
                sqlm.Category.restricted==False
            ))) \
        .filter(sqlm.Post.created > _starting) \
        .filter(sqla.or_(sqlm.Post.hidden == False, sqlm.Post.hidden == None)) \
        .order_by(sqla.desc(sqlm.Post.created)).count()
        
    pages = int(math.ceil(float(recent_posts_count)/float(pagination)))
    if pages > 10:
        pages = 10

    pages = [p+1 for p in range(pages)]
    
    clean_html_parser = ForumPostParser()    
    for post in recent_posts:
        post.preview = unicode(BeautifulSoup(clean_html_parser.parse(post.html, _object=post)[:900]))+"..."
    
    return render_template("forum/recent_posts.jade",
        page_title="Recent Posts - %%GENERIC SITENAME%%",
        posts=recent_posts,
        pages=pages,
        page=page)

@app.route('/t/<slug>/posts', methods=['POST'])
def topic_posts(slug):
    start = time.time()
    try:
        topic = sqla.session.query(sqlm.Topic).filter_by(slug=slug)[0]
    except IndexError:
        return abort(404)

    if topic.category.restricted == True and not current_user.is_admin and not current_user in topic.category.allowed_users:
        return abort(404)
        
    if current_user._get_current_object() in topic.banned:
        return abort(403)

    if topic.hidden and not (current_user._get_current_object().is_admin or current_user._get_current_object().is_mod):
        return abort(404)

    request_json = request.get_json(force=True)

    try:
        pagination = int(request_json.get("pagination", 20))
        page = int(request_json.get("page", 1))
    except:
        pagination = 20
        page = 1


    post_count = sqla.session.query(sqlm.Post).filter_by(topic=topic) \
        .filter(sqla.or_(sqlm.Post.hidden == False, sqlm.Post.hidden == None)).count()

    max_page = math.ceil(float(post_count)/float(pagination))
    if page > max_page:
        page = int(max_page)

    if page < 1:
        page = 1

    posts = sqla.session.query(sqlm.Post).filter_by(topic=topic) \
        .filter(sqla.or_(sqlm.Post.hidden == False, sqlm.Post.hidden == None)) \
        .order_by(sqlm.Post.created) \
        .paginate(page, pagination, False)

    parsed_posts = []

    first_post = sqla.session.query(sqlm.Post).filter_by(topic=topic) \
        .filter(sqla.or_(sqlm.Post.hidden == False, sqlm.Post.hidden == None)) \
        .order_by(sqlm.Post.created).paginate(1, pagination, False).items[0]

    author_signatures = {}
    author_signatures_id = {}
    
    t = time.time()
    
    for post in posts.items:
        clean_html_parser = ForumPostParser()

        active_rolls = [] # (roll_id, spec, flavor, outcome)
        active_roll_ids = []
        inactive_rolls = [] # (roll_id, spec, flavor, outcome)

        rolls = roll_re.findall(post.html)
        for i, roll in enumerate(rolls):
            if i > 50:
                continue

            if roll[2] == '':
                base = 0
            else:
                base = roll[2]

            if roll[3] == '':
                penalty = 0
            else:
                penalty = roll[3]

            if int(roll[0]) == 0 or int(roll[0]) > 1000:
                continue

            if int(roll[1]) == 0 or int(roll[1]) > 1000:
                continue

            try:
                roll = sqlm.DiceRoll.query.filter_by(
                    order_of_roll = i,
                    sides = roll[1],
                    number_of_dice = roll[0],
                    base = base,
                    penalty = penalty,
                    content_type = "post",
                    content_id = post.id,
                    flavor_text = roll[4],
                    user = post.author
                )[0]
            except IndexError:
                roll = sqlm.DiceRoll(
                    order_of_roll = i,
                    sides = roll[1],
                    number_of_dice = roll[0],
                    base = base,
                    penalty = penalty,
                    content_type = "post",
                    content_id = post.id,
                    flavor_text = roll[4],
                    created = arrow.utcnow().datetime.replace(tzinfo=None),
                    user = post.author
                )
                sqla.session.add(roll)
                sqla.session.commit()

            active_roll_ids.append(roll.id)
            active_rolls.append([roll.id, roll.get_spec(), roll.flavor_text, roll.get_value()])

        all_rolls = sqlm.DiceRoll.query.filter_by(
            content_type = "post",
            content_id = post.id
        )

        for roll in all_rolls:
            if not roll.id in active_roll_ids:
                inactive_rolls.append([roll.id, roll.get_spec(), roll.flavor_text, roll.get_value()])

        parsed_post = {}
        parsed_post["_id"] = post.id
        parsed_post["_tid"] = topic.id
        parsed_post["created"] = humanize_time(post.created, "MMM D YYYY")
        parsed_post["modified"] = humanize_time(post.modified, "MMM D YYYY")
        parsed_post["modified_by"] = False
        if post.post_history != None:
            try:
                if len(post.post_history) > 0:
                    parsed_post["modified_by"] = sqlm.User.query.filter_by(id=post.post_history[-1]["author"])[0].display_name
            except IndexError:
                pass
        parsed_post["html"] = clean_html_parser.parse(post.html, _object=post)
        parsed_post["roles"] = post.author.get_roles()
        parsed_post["user_avatar"] = post.author.get_avatar_url()
        parsed_post["user_avatar_x"] = post.author.avatar_full_x
        parsed_post["user_avatar_y"] = post.author.avatar_full_y
        parsed_post["user_avatar_60"] = post.author.get_avatar_url("60")
        parsed_post["user_avatar_x_60"] = post.author.avatar_60_x
        parsed_post["user_avatar_y_60"] = post.author.avatar_60_y
        parsed_post["user_title"] = post.author.title
        parsed_post["author_name"] = post.author.display_name
        parsed_post["active_rolls"] = active_rolls
        parsed_post["inactive_rolls"] = inactive_rolls

        if current_user.is_admin == True:
            parsed_post["is_admin"] = True
        else:
            parsed_post["is_admin"] = False

        if current_user.is_authenticated():
            if author_signatures.has_key(post.author.login_name):
                parsed_post["signature"] = author_signatures[post.author.login_name]
                parsed_post["signature_id"] = author_signatures_id[post.author.login_name]
            else:
                signatures = list(sqla.session.query(sqlm.Signature) \
                    .filter_by(owner=post.author, active=True).all())

                try:
                    signature = random.choice(signatures)
                    parsed_post["signature"] = clean_html_parser.parse(signature.html, _object=signature)
                    parsed_post["signature_id"] = signature.id
                except IndexError:
                    parsed_post["signature"] = False
                    parsed_post["signature_id"] = False

                author_signatures[post.author.login_name] = parsed_post["signature"]
                author_signatures_id[post.author.login_name] = parsed_post["signature_id"]
        else:
            parsed_post["signature"] = False
            parsed_post["signature_id"] = False

        if post == first_post:
            parsed_post["topic_leader"] = "/t/"+topic.slug+"/edit-topic"
        parsed_post["author_login_name"] = post.author.my_url
        parsed_post["has_booped"] = current_user._get_current_object() in post.boops
        parsed_post["boop_count"] = len(post.boops)
        if parsed_post["boop_count"] == 1:
            parsed_post["one_boop"] = True
        else:
            parsed_post["one_boop"] = False
        if current_user.is_authenticated():
            parsed_post["can_boop"] = current_user._get_current_object() != post.author
        else:
            parsed_post["can_boop"] = False

        if current_user.is_authenticated():
            if post.author.id == current_user.id:
                parsed_post["is_author"] = True
            else:
                parsed_post["is_author"] = False
        else:
            parsed_post["is_author"] = False

        if post.author.last_seen != None:
            if arrow.get(post.author.last_seen) > arrow.utcnow().replace(minutes=-15).datetime and post.author.anonymous_login != True:
                parsed_post["author_online"] = True
            else:
                parsed_post["author_online"] = False
        else:
            parsed_post["author_online"] = False
        
        hidden_character_avatar = False
        
        if post.character is not None:
            try:
                if not post.character.hidden:
                    character = post.character
                    parsed_post["character_name"] = character.name
                    parsed_post["character_slug"] = character.slug
                    parsed_post["character_motto"] = character.motto
                else:
                    hidden_character_avatar = True
            except:
                pass
        else:
            character = None

        if post.avatar is not None:
            try:
                if not hidden_character_avatar:
                    a = post.avatar
                    parsed_post["character_avatar_small"] = a.get_specific_size(60)
                    parsed_post["character_avatar_large"] = a.get_specific_size(200)
                    parsed_post["character_avatar"] = True
            except:
                pass
        # else:
        #     try:
        #         pass
        #         # parsed_post["character_avatar_small"] = character.default_avatar.get_specific_size(60)
        #         # parsed_post["character_avatar_large"] = character.default_avatar.get_specific_size(200)
        #         # parsed_post["character_avatar"] = True
        #     except:
        #         pass

        parsed_posts.append(parsed_post)
    
    print (time.time() - t) * 1000.0
    print "^ ms"
    
    return app.jsonify(posts=parsed_posts, count=post_count)

@app.route('/t/<slug>/edit-post', methods=['POST'])
@login_required
def edit_topic_post_html(slug):
    try:
        topic = sqla.session.query(sqlm.Topic).filter_by(slug=slug)[0]
    except IndexError:
        return abort(404)

    request_json = request.get_json(force=True)

    try:
        post = sqla.session.query(sqlm.Post).filter_by(topic=topic, id=request_json.get("pk")) \
            .filter(sqla.or_(sqlm.Post.hidden == False, sqlm.Post.hidden == None))[0]
    except:
        return abort(404)

    if current_user._get_current_object() != post.author and (current_user._get_current_object().is_admin != True and current_user._get_current_object().is_mod != True):
        return abort(404)

    if request_json.get("text", "").strip() == "":
        return app.jsonify(error="Your post is empty.")

    cleaner = ForumHTMLCleaner()
    try:
        post_html = cleaner.clean(request_json.get("post", ""))
    except:
        return abort(500)

    try:
        character = sqla.session.query(sqlm.Character).filter_by(slug=request_json.get("character"), \
            author=current_user._get_current_object()).filter(sqla.or_(sqlm.Character.hidden == False, \
            sqlm.Character.hidden == None))[0]
    except:
        character = False

    try:
        avatar = sqla.session.query(sqlm.Attachment).filter_by(character=character, \
            id=request_json.get("avatar")) \
            .first()

        if avatar == None:
            avatar = sqla.session.query(sqlm.Attachment).filter_by(character=character, \
                character_gallery=True, character_avatar=True) \
                .order_by(character_gallery_weight).first()[0]
    except:
        avatar = False

    history = {}
    history["author"] = current_user._get_current_object().id
    history["created"] = str(arrow.utcnow().datetime)
    history["old_html"] = post.html+""
    history["new_html"] = post_html
    history["old_data"] = post.data
    history["reason"] = request_json.get("edit_reason", "")

    if post.post_history == None:
        post.post_history = []

    post.post_history.append(history)
    flag_modified(post, "post_history")

    if current_user._get_current_object() != post.author:
        if request_json.get("edit_reason", "").strip() == "":
            return app.jsonify(error="Please include an edit reason for editing someone else's post.")

    post.html = post_html
    post.modified = arrow.utcnow().datetime.replace(tzinfo=None)

    if current_user._get_current_object() == post.author:
        if character:
            post.character = character
        else:
            try:
                post.character = None
            except:
                pass

        if avatar:
            post.avatar = avatar
        else:
            try:
                post.avatar = None
            except:
                pass

    sqla.session.add(post)
    sqla.session.commit()

    clean_html_parser = ForumPostParser()
    return app.jsonify(html=clean_html_parser.parse(post.html, _object=post), success=True)

@app.route('/t/<slug>/edit-post/<post>', methods=['GET'])
@login_required
def get_post_html_in_topic(slug, post):
    try:
        topic = sqla.session.query(sqlm.Topic).filter_by(slug=slug)[0]
    except IndexError:
        return abort(404)

    try:
        post = sqla.session.query(sqlm.Post).filter_by(topic=topic, id=post) \
            .filter(sqla.or_(sqlm.Post.hidden == False, sqlm.Post.hidden == None))[0]
    except:
        return abort(404)

    return app.jsonify(content=post.html, author=post.author.display_name)

@app.route('/t/<slug>/polls', methods=['POST'])
def topic_poll(slug):
    try:
        topic = sqla.session.query(sqlm.Topic).filter_by(slug=slug)[0]
    except IndexError:
        return abort(404)

    if current_user._get_current_object() in topic.banned:
        return abort(403)
        
    if topic.category.restricted == True and not current_user.is_admin and not current_user in topic.category.allowed_users:
        return abort(404)

    if topic.hidden and not (current_user._get_current_object().is_admin or current_user._get_current_object().is_mod):
        return abort(404)
    
    polls = sqla.session.query(sqlm.Poll).filter_by(topic=topic)
    polls_response = []
    
    for poll in polls:
        poll_dictionary = {}
        poll_dictionary["show_results"] = False
        poll_dictionary["closed"] = False
        poll_dictionary["private_names"] = False
        poll_dictionary["options"] = {}
        
        if poll.end_date != None and arrow.utcnow().datetime.replace(tzinfo=None) > poll.end_date:
            poll_dictionary["closed"] = True
            
        if poll.votes_private_until_end:
            if poll_dictionary["closed"] == True:
                poll_dictionary["show_results"] = True
            else:
                poll_dictionary["show_results"] = False
        
        if not votes_are_public:
            poll_dictionary["private_names"] = True
        
        poll_options = sqla.session.query(sqlm.PollOption).filter_by(poll=poll)
        for option in poll_options:
            poll_votes = option.option_votes
            poll_dictionary["options"][option.option_name] = []
            
            for vote in poll_votes:
                if poll_dictionary["private_names"]:
                    poll_dictionary["options"][option.option_name].append("Anonymouse")
                else:
                    poll_dictionary["options"][option.option_name].append(voter.display_name)
            

@app.route('/t/<slug>', methods=['GET'], defaults={'page': 1, 'post': ""})
@app.route('/t/<slug>/page/<page>', methods=['GET'], defaults={'post': ""})
@app.route('/t/<slug>/page/<page>/post/<post>', methods=['GET'])
def topic_index(slug, page, post):
    try:
        topic = sqla.session.query(sqlm.Topic).filter_by(slug=slug)[0]
    except IndexError:
        return abort(404)
    pagination = 20

    if current_user._get_current_object() in topic.banned:
        return abort(403)
        
    if topic.category.restricted == True and not current_user.is_admin and not current_user in topic.category.allowed_users:
        return abort(404)

    if topic.hidden and not (current_user._get_current_object().is_admin or current_user._get_current_object().is_mod):
        return abort(404)

    try:
        page = int(page)
    except:
        page = 1
    
    if current_user.is_authenticated():
        more_topics = sqla.session.query(sqlm.Topic) \
            .filter(sqlm.Topic.id != topic.id) \
            .filter(sqlm.Topic.hidden == False) \
            .filter(sqlm.Topic.recent_post.has(sqlm.Post.author != current_user)) \
            .filter(sqlm.Topic.category.has(sqlm.Category.restricted==False)) \
            .filter(sqlm.Topic.category.has(sqlm.Category.slug!="welcome")) \
            .filter(sqlm.Topic.category.has(sqlm.Category.slug!="faq-help")) \
            .filter(sqlm.Topic.category.has(sqlm.Category.slug!="news")) \
            .order_by(sqla.func.random())[:5]
    else:
        more_topics = sqla.session.query(sqlm.Topic) \
            .filter(sqlm.Topic.id != topic.id) \
            .filter(sqlm.Topic.hidden == False) \
            .filter(sqlm.Topic.category.has(sqlm.Category.restricted==False)) \
            .filter(sqlm.Topic.category.has(sqlm.Category.slug!="welcome")) \
            .filter(sqlm.Topic.category.has(sqlm.Category.slug!="faq-help")) \
            .filter(sqlm.Topic.category.has(sqlm.Category.slug!="news")) \
            .order_by(sqla.func.random())[:5]
            
    request.canonical = app.config['BASE'] + "/t/%s/page/%s" % (slug, page)

    meta_description = topic.title + " - Page %s" % (page,)

    try:
        first_post = sqla.session.query(sqlm.Post).filter_by(topic=topic) \
            .filter(sqla.or_(sqlm.Post.hidden == False, sqlm.Post.hidden == None)) \
            .order_by(sqlm.Post.created)[0]
        description_parsed = get_preview(first_post.html, 140)
        if description_parsed.strip() != "":
            meta_description = get_preview(first_post.html, 140) + " - Page %s" % (page,)
    except:
        sqla.session.rollback()
        pass

    if topic.last_seen_by == None:
        topic.last_seen_by = {}

    if post == "latest_post":
        try:
            post = sqla.session.query(sqlm.Post).filter_by(topic=topic) \
            .filter(sqla.or_(sqlm.Post.hidden == False, sqlm.Post.hidden == None)) \
            .order_by(sqla.desc(sqlm.Post.created))[0]
        except:
            sqla.session.rollback()
            return redirect("/t/"+unicode(topic.slug))

    elif post == "last_seen":
        try:
            last_seen = arrow.get(topic.last_seen_by.get(str(current_user._get_current_object().id), arrow.utcnow().timestamp)).datetime.replace(tzinfo=None)
        except:
            last_seen = arrow.get(arrow.utcnow().timestamp).datetime.replace(tzinfo=None)

        try:
            post = sqla.session.query(sqlm.Post).filter_by(topic=topic) \
                .filter(sqlm.Post.created < last_seen) \
                .filter(sqla.or_(sqlm.Post.hidden == False, sqlm.Post.hidden == None)) \
                .order_by(sqlm.Post.created.desc())[0]
        except:
            sqla.session.rollback()
            try:
                post = sqla.session.query(sqlm.Post).filter_by(topic=topic) \
                    .filter_by(id=post).filter(sqlm.Post.created < last_seen) \
                    .filter(sqla.or_(sqlm.Post.hidden == False, sqlm.Post.hidden == None)) \
                    .order_by(sqlm.Post.created.desc())[0]
            except:
                sqla.session.rollback()
                return redirect("/t/"+unicode(topic.slug))
    else:
        if post != "":
            try:
                last_seen = arrow.get(topic.last_seen_by.get(str(current_user._get_current_object().id), arrow.utcnow().timestamp)).datetime.replace(tzinfo=None)
            except:
                last_seen = arrow.get(arrow.utcnow().timestamp).datetime.replace(tzinfo=None)
            try:
                post = int(post)
                post = sqla.session.query(sqlm.Post).filter_by(topic=topic) \
                    .filter_by(id=post)[0]
            except:
                sqla.session.rollback()
                return redirect("/t/"+unicode(topic.slug))
        else:
            post = ""

    if post != "":
        if topic.view_count:
            topic.view_count = topic.view_count + 1
        else:
            topic.view_count = 1
        try:
            if topic.last_seen_by == None:
                topic.last_seen_by = {}
            topic.last_seen_by[str(current_user._get_current_object().id)] = arrow.utcnow().timestamp
            flag_modified(topic, "last_seen_by")
            sqla.session.add(topic)
            sqla.session.commit()
        except:
            sqla.session.rollback()
            pass
        target_date = post.created
        posts_before_target = sqla.session.query(sqlm.Post).filter_by(topic=topic) \
            .filter(sqla.or_(sqlm.Post.hidden == False, sqlm.Post.hidden == None)) \
            .filter(sqlm.Post.created < post.created) \
            .count()

        page = int(math.floor(float(posts_before_target)/float(pagination)))+1

        rp_topic = "false"
        if topic.category.slug in ["roleplays"]:
            rp_topic = "true"
        return render_template("forum/topic.jade", more_topics=more_topics, topic=topic, page_title="%s - %%GENERIC SITENAME%%" % unicode(topic.title), initial_page=page, initial_post=str(post.id), rp_area=rp_topic)

    topic.view_count = topic.view_count + 1
    try:
        topic.last_seen_by[str(current_user._get_current_object().id)] = arrow.utcnow().timestamp
        flag_modified(topic, "last_seen_by")
        sqla.session.add(topic)
        sqla.session.commit()
    except:
        sqla.session.rollback()
        pass

    rp_topic = "false"
    if topic.category.slug in ["roleplays", "scenarios"]:
        rp_topic = "true"
        
    return render_template("forum/topic.jade", more_topics=more_topics, topic=topic, meta_description=meta_description, page_title="%s - %%GENERIC SITENAME%%" % unicode(topic.title), initial_page=page, rp_area=rp_topic)

@app.route('/category/<slug>/filter-preferences', methods=['GET', 'POST'])
def category_filter_preferences(slug):
    try:
        category = sqla.session.query(sqlm.Category).filter_by(slug=slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)
    if not current_user.is_authenticated():
        return app.jsonify(preferences={})
    if category.restricted == True and not current_user.is_admin and not current_user in category.allowed_users:
        return abort(404)
        
    if current_user.data is None:
        tmp_data = {}
    else:
        tmp_data = current_user.data.copy()

    if request.method == 'POST':
        request_json = request.get_json(force=True)
        try:
            if len(request_json.get("preferences")) < 10:
                tmp_data["category_filter_preference_"+str(category.id)] = request_json.get("preferences")
        except:
            return app.jsonify(preferences={})

        current_user.data = tmp_data
        sqla.session.add(current_user)
        sqla.session.commit()
        preferences = tmp_data.get("category_filter_preference_"+str(category.id), {})
        return app.jsonify(preferences=preferences)
    else:
        preferences = tmp_data.get("category_filter_preference_"+str(category.id), {})
        return app.jsonify(preferences=preferences)

@app.route('/t/<slug>/edit-topic', methods=['GET', 'POST'])
@login_required
def edit_topic(slug):
    try:
        topic = sqla.session.query(sqlm.Topic).filter_by(slug=slug)[0]
        first_post = sqla.session.query(sqlm.Post).filter_by(topic=topic) \
            .filter(sqla.or_(sqlm.Post.hidden == False, sqlm.Post.hidden == None)) \
            .order_by(sqlm.Post.created)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    category = topic.category

    if request.method == 'POST':
        if current_user._get_current_object() != topic.author:
            if not current_user._get_current_object().is_admin and not current_user._get_current_object().is_mod:
                if current_user._get_current_object() not in topic.topic_moderators:
                    return abort(404)

        request_json = request.get_json(force=True)

        if request_json.get("title", "").strip() == "":
            return app.jsonify(error="Please enter a title.")

        if request_json.get("text", "").strip() == "":
            return app.jsonify(error="Please enter actual text for your topic.")

        if len(category.allowed_labels) > 0:
            if request_json.get("prefix", "").strip() == "":
                return app.jsonify(error="Please choose a label.")

            # if not request_json.get("prefix", "").strip() in category.allowed_labels:
            #     return app.jsonify(error="Please choose a valid label.")

        cleaner = ForumHTMLCleaner()
        try:
            post_html = cleaner.clean(request_json.get("html", ""))
        except:
            return abort(500)

        try:
            label = sqla.session.query(sqlm.Label).filter_by(label=request_json.get("prefix", "").strip())[0]
        except IndexError:
            label = ""
        post = first_post

        history = {}
        history["author"] = current_user._get_current_object().id
        history["created"] = str(arrow.utcnow().datetime)
        history["old_html"] = post.html+""
        history["new_html"] = post_html
        history["data"] = first_post.data
        history["reason"] = request_json.get("edit_reason", "")

        if post.post_history == None:
            post.post_history = []

        post.post_history.append(history)
        flag_modified(post, "post_history")

        if current_user._get_current_object() != topic.author:
            if request_json.get("edit_reason", "").strip() == "":
                return app.jsonify(error="Please include an edit reason for editing someone else's topic.")

        topic.title = request_json.get("title")[:100]
        if label != "":
            topic.label = label

        first_post.modified = arrow.utcnow().datetime.replace(tzinfo=None)
        first_post.html = post_html

        sqla.session.add(topic)
        sqla.session.add(first_post)
        sqla.session.commit()
        return app.jsonify(url="/t/"+topic.slug)
    else:
        return render_template("forum/edit_topic.jade", page_title="Edit Topic", category=category, topic=topic, first_post=first_post)

@app.route('/category/<slug>/new-topic', methods=['GET', 'POST'])
@login_required
def new_topic(slug):
    if request.method == 'POST':
        try:
            category = sqla.session.query(sqlm.Category).filter_by(slug=slug)[0]
        except IndexError:
            return abort(404)
        if category.restricted == True and not current_user.is_admin and not current_user in category.allowed_users:
            return abort(404)
            
        request_json = request.get_json(force=True)

        if request_json.get("title", "").strip() == "":
            return app.jsonify(error="Please enter a title.")

        if request_json.get("text", "").strip() == "":
            return app.jsonify(error="Please enter actual text for your post.")

        if len(category.allowed_labels) > 0:
            if request_json.get("prefix", "").strip() == "":
                return app.jsonify(error="Please choose a label.")

            try:
                label = sqla.session.query(sqlm.Label).filter_by(label=request_json.get("prefix", "").strip())[0]

            #     if not label in category.allowed_labels:
            #         return app.jsonify(error="Please choose a valid label.")
            except IndexError:
                sqla.session.rollback()
                return app.jsonify(error="Please choose a valid label.")

        cleaner = ForumHTMLCleaner()
        try:
            post_html = cleaner.clean(request_json.get("html", ""))
        except:
            return abort(500)

        try:
            users_last_topic = sqla.session.query(sqlm.Topic) \
                .filter_by(author=current_user._get_current_object()) \
                .order_by(sqla.desc(sqlm.Topic.created))[0]
            difference = (arrow.utcnow().datetime - arrow.get(users_last_topic.created).datetime).seconds
            if difference < 360 and not current_user._get_current_object().is_admin:
                return app.jsonify(error="Please wait %s seconds before you create another topic." % (360 - difference))
        except IndexError:
            pass

        new_topic = sqlm.Topic()
        new_topic.category = category
        new_topic.title = request_json.get("title")[:100]
        new_topic.slug = sqlm.find_topic_slug(new_topic.title)
        new_topic.author = current_user._get_current_object()
        new_topic.created = arrow.utcnow().datetime.replace(tzinfo=None)
        if request_json.get("prefix", "").strip() != "":
            new_topic.label = label
        new_topic.post_count = 1
        sqla.session.add(new_topic)
        sqla.session.commit()

        new_post = sqlm.Post()
        new_post.html = post_html
        new_post.author = current_user._get_current_object()
        new_post.topic = new_topic
        new_post.t_title = new_topic.title
        new_post.created = arrow.utcnow().datetime.replace(tzinfo=None)
        sqla.session.add(new_post)
        sqla.session.commit()

        category.recent_topic = new_topic
        category.recent_post = new_post
        category.post_count = category.post_count + 1
        category.topic_count = category.topic_count + 1
        new_topic.recent_post = new_post
        new_topic.watchers.append(new_topic.author)

        sqla.session.add(category)
        sqla.session.add(new_topic)
        sqla.session.commit()

        send_notify_to_users = []
        for user in new_post.author.followed_by():
            send_notify_to_users.append(user)

        broadcast(
          to=send_notify_to_users,
          category="user_activity",
          url="/t/"+unicode(new_topic.slug),
          title="%s created a new topic %s" % (unicode(new_post.author.display_name), unicode(new_topic.title)),
          description=new_post.html,
          content=new_topic,
          author=new_post.author
          )

        mentions = mention_re.findall(post_html)
        to_notify = {}
        for mention in mentions:
            try:
                to_notify[mention] = sqla.session.query(sqlm.User).filter_by(login_name=mention)[0]
            except IndexError:
                continue

        broadcast(
          to=to_notify.values(),
          category="mention",
          url="/t/"+unicode(new_topic.slug),
          title="%s mentioned you in new topic %s" % (unicode(new_post.author.display_name), unicode(new_topic.title)),
          description=new_post.html,
          content=new_topic,
          author=new_post.author
          )

        notify_users = []
        for u in category.watchers:
          if u == new_post.author:
              continue

          skip_user = False
          for _u in to_notify.values():
              if _u.id == u.id:
                  skip_user = True
                  break

          for _u in send_notify_to_users:
              if _u.id == u.id:
                  skip_user = True
                  break

          if skip_user:
              continue

          notify_users.append(u)

        broadcast(
          to=notify_users,
          category="topic",
          url="/t/%s" % (str(new_topic.slug),),
          title="Topic posted in %s : %s" % (unicode(category.name), unicode(new_topic.title)),
          description=new_post.html,
          content=new_topic,
          author=new_post.author
          )

        return app.jsonify(url="/t/"+new_topic.slug)
    else:
        try:
            category = sqla.session.query(sqlm.Category).filter_by(slug=slug)[0]
            if category.restricted == True and not current_user.is_admin and current_user not in category.allowed_users:
                return abort(404)
        except IndexError:
            return abort(404)

        return render_template("forum/new_topic.jade", page_title="Create New Topic", category=category)

@app.route('/category/<slug>/topics', methods=['POST'])
def category_topics(slug):
    try:
        category = sqla.session.query(sqlm.Category).filter_by(slug=slug)[0]
    except IndexError:
        return abort(404)
    if category.restricted == True and not current_user.is_admin and not current_user in category.allowed_users:
        return abort(404)

    if current_user.is_authenticated():
        preferences = current_user.data.get("category_filter_preference_"+str(category.id), {})
        prefixes = preferences.keys()
    else:
        prefixes = []
    
    """
SELECT t.id AS this_topic_id,
t.title AS topic_title,
t.slug AS topic_slug,
t.post_count AS topic_post_count,
t.view_count AS topic_view_count,
t.sticky AS topic_sticky,
t.locked AS topic_closed,
t.last_seen_by AS topic_last_seen_by,
l.pre_html AS topic_l_pre_html,
l.post_html AS topic_l_post_html,
l.label AS topic_l_prefix,
rp.created AS last_post_date,
fp.html AS first_post_html,
fpa.display_name AS first_post_author,
fp.created AS first_post_created,
rp.created AS topic_last_updated,
rpa.display_name AS last_post_author,
rpa.my_url AS last_post_link,
CASE
    WHEN rpa.avatar_extension != ''
    THEN 'avatars/' || rpa.avatar_timestamp || rpa.id || '_40' || rpa.avatar_extension 
    ELSE 'no_profile_avatar_40.png'
END AS last_post_avatar
FROM "topic" t
LEFT JOIN "label" l ON t.label_id = l.id
JOIN "post" fp ON t.recent_post_id = fp.id
JOIN "post" rp ON t.recent_post_id = rp.id
JOIN "user" fpa ON fp.author_id = fpa.id
JOIN "user" rpa ON rp.author_id = rpa.id
WHERE t.hidden = False
AND t.category_id = 36%s
ORDER BY t.sticky DESC,
t.recent_post_time DESC
LIMIT 20 OFFSET 0
    """
    
    request_json = request.get_json(force=True)
    page = request_json.get("page", 1)
    pagination = request_json.get("pagination", 15)

    try:
        minimum = (int(page)-1)*int(pagination)
        maximum = int(page)*int(pagination)
    except:
        minimum = 0
        maximum = 20

    if len(prefixes) > 0:
        topics = sqla.session.query(sqlm.Topic).filter(sqlm.Topic.category==category, sqlm.Topic.hidden==False, \
            sqlm.Label.label.in_(prefixes)).join(sqlm.Topic.label).join(sqlm.Topic.recent_post) \
        .order_by( \
            sqla.desc(sqlm.Topic.sticky), sqla.desc(sqlm.Post.created)).options(joinedload(sqlm.Topic.first_post)).paginate(page, pagination, False)
        topic_count = sqla.session.query(sqlm.Topic).filter(sqlm.Topic.category==category, sqlm.Topic.hidden==False, \
            sqlm.Label.label.in_(prefixes)).join(sqlm.Topic.label) \
        .count()
    else:
        topics = sqla.session.query(sqlm.Topic).filter(sqlm.Topic.category==category, sqlm.Topic.hidden==False) \
            .join(sqlm.Topic.recent_post) \
        .order_by( \
            sqla.desc(sqlm.Topic.sticky), sqla.desc(sqlm.Post.created)).options(joinedload(sqlm.Topic.first_post)).paginate(page, pagination, False)
        topic_count = sqla.session.query(sqlm.Topic).filter(sqlm.Topic.category==category, sqlm.Topic.hidden==False).count()

    parsed_topics = []
    for topic in topics.items:
        if current_user._get_current_object() in topic.banned:
            continue
        parsed_topic = {}
        parsed_topic["creator"] = topic.author.display_name
        parsed_topic["created"] = humanize_time(topic.created, "MMM D YYYY")

        parsed_topic["updated"] = False
        if topic.last_seen_by is None:
            topic.last_seen_by = {}

        if current_user.is_authenticated():
            if topic.last_seen_by.get(str(current_user._get_current_object().id)) != None:
                if arrow.get(topic.recent_post.created).timestamp > topic.last_seen_by.get(str(current_user._get_current_object().id)):
                    if topic.recent_post.author != current_user._get_current_object():
                        parsed_topic["updated"] = True

        if topic.label != None:
            try:
                parsed_topic["pre_html"] = topic.label.pre_html
                parsed_topic["post_html"] = topic.label.post_html
                parsed_topic["prefix"] = topic.label.label
            except:
                pass
        if topic.recent_post:
            parsed_topic["last_post_date"] = humanize_time(topic.recent_post.created)
            parsed_topic["last_post_by"] = topic.recent_post.author.display_name
            parsed_topic["last_post_x"] = topic.recent_post.author.avatar_40_x
            parsed_topic["last_post_y"] = topic.recent_post.author.avatar_40_y
            parsed_topic["last_post_by_login_name"] = topic.recent_post.author.my_url
            parsed_topic["last_post_author_avatar"] = topic.recent_post.author.get_avatar_url("60")
        parsed_topic["post_count"] = "{:,}".format(topic.post_count)
        parsed_topic["view_count"] = "{:,}".format(topic.view_count)
        try:
            parsed_topic["last_page"] = float(topic.post_count)/float(pagination)
        except:
            parsed_topic["last_page"] = 1
        parsed_topic["last_pages"] = parsed_topic["last_page"] > 1
        parsed_topic["closed"] = topic.locked
        parsed_topic["title"] = topic.title
        parsed_topic["sticky"] = topic.sticky
        parsed_topic["closed"] = topic.locked
        parsed_topic["slug"] = topic.slug        
        first_post = topic.first_post
        parsed_topic["preview"] = unicode(get_preview(first_post.html, 125))

        parsed_topics.append(parsed_topic)

    return app.jsonify(topics=parsed_topics, count=topic_count)

@app.route('/category/<slug>', methods=['GET'])
def category_index(slug):
    try:
        category = sqla.session.query(sqlm.Category).filter_by(slug=slug)[0]
    except IndexError:
        return abort(404)
    if category.restricted == True and not current_user.is_admin and not current_user in category.allowed_users:
        return abort(404)

    subcategories = sqla.session.query(sqlm.Category).filter_by(parent=category).all()
    prefixes = sqla.session.query(sqlm.Label.label, sqla.func.count(sqlm.Topic.id)) \
        .filter(sqlm.Topic.category==category) \
        .filter(sqlm.Topic.hidden==False) \
        .filter(sqlm.Label.label != "") \
        .join(sqlm.Topic.label).group_by(sqlm.Label.label) \
        .order_by(sqla.desc(sqla.func.count(sqlm.Topic.id))).all()

    return render_template("forum/category.jade", page_title="%s - %%GENERIC SITENAME%%" % unicode(category.name), category=category, subcategories=subcategories, prefixes=prefixes)

@app.route('/')
def index():
    hierarchy = OrderedDict()
    children = OrderedDict()
    
    top_level_categories = sqla.engine.execute(
        """
        SELECT c.name AS category_name,
        c.slug AS category_slug,
        c.restricted AS restricted,
        c.description AS category_description,
        s.name AS section_name,
        t.title AS last_topic_title,
        t.slug AS last_topic_slug,
        p.created AS last_topic_bumped,
        CASE
        WHEN u.avatar_extension != ''
        THEN 'avatars/' || u.avatar_timestamp || u.id || '_40' || u.avatar_extension 
        ELSE 'no_profile_avatar_40.png'
        END AS user_avatar,
        u.my_url AS user_url,
        parent.name AS parent_name
        FROM category c
        LEFT JOIN "section" s ON c.section_id = s.id
        LEFT JOIN "category" parent ON c.parent_id = parent.id
        JOIN "topic" t ON c.recent_topic_id = t.id
        JOIN "post" p ON c.recent_post_id = p.id
        JOIN "user" u ON p.author_id = u.id
        ORDER BY s.weight, c.weight ASC
        """
    )
    
    for _category in top_level_categories:
        category_dict = dict(_category)
        if category_dict["restricted"] == True and not current_user.is_admin:
            continue
        
        if category_dict["parent_name"] is None:
            if not hierarchy.has_key(category_dict["section_name"]):
                hierarchy[category_dict["section_name"]] = []
        
            hierarchy[category_dict["section_name"]].append(_category)
        else:
            if not children.has_key(category_dict["parent_name"]):
                children[category_dict["parent_name"]] = []
        
            children[category_dict["parent_name"]].append(_category)
    
    online_users = sqla.session.query(sqlm.User) \
        .filter(sqlm.User.hidden_last_seen > arrow.utcnow() \
        .replace(minutes=-15).datetime.replace(tzinfo=None)).all()

    # post_count = sqla.session.query(sqlm.Post) \
    #     .filter_by(hidden=False).count()
    #
    # member_count = sqla.session.query(sqlm.User) \
    #     .filter_by(banned=False).count()
    #

    try:
        newest_member = sqla.session.query(sqlm.User) \
            .filter_by(banned=False, validated=True) \
            .order_by(sqla.desc(sqlm.User.joined))[0]
    except IndexError:
        newest_member = None

    try:
        new_member_intro_topic = sqla.session.query(sqlm.Topic) \
            .join(sqlm.Topic.category) \
            .filter(sqlm.Topic.hidden==False, sqlm.Topic.author==newest_member) \
            .filter(sqlm.Category.slug == "welcome") \
            .order_by(sqlm.Topic.created.desc())[0]
    except IndexError:
        new_member_intro_topic = None

    try:
        timezone = current_user._get_current_object().time_zone
    except:
        timezone = "US/Pacific"
    
    # try:
    #     birthday_list = sqla.session.query(sqlm.User) \
    #         .filter(sqla.extract('month', sqlm.User.birthday) == arrow.utcnow().to(timezone).datetime.month) \
    #         .filter(sqla.extract('day', sqlm.User.birthday) == arrow.utcnow().to(timezone).datetime.day) \
    #         .order_by(sqlm.User.birthday.desc()).all()
    # except:
    birthday_list = []

    recently_replied_topics = []
    # recently_replied_topics = sqla.session.query(sqlm.Topic) \
    #     .filter(sqla.or_(sqlm.Topic.hidden == False, sqlm.Topic.hidden == None)) \
    #     .filter(sqlm.Topic.category.has(sqlm.Category.restricted==False)) \
    #     .join(sqlm.Topic.recent_post).order_by(sqlm.Post.created.desc())[:5]
    #
    
    recently_created_topics = []
    # recently_created_topics = sqla.session.query(sqlm.Topic) \
    #     .filter(sqla.or_(sqlm.Topic.hidden == False, sqlm.Topic.hidden == None)) \
    #     .filter(sqlm.Topic.category.has(sqlm.Category.restricted==False)) \
    #     .order_by(sqlm.Topic.created.desc())[:5]

    # status_update_authors = sqla.session.query(sqlm.StatusUpdate.author_id.label("author_id"), sqla.func.max(sqlm.StatusUpdate.created).label("created")) \
    #     .group_by(sqlm.StatusUpdate.author_id) \
    #     .filter(sqla.or_(sqlm.StatusUpdate.hidden == False, sqlm.StatusUpdate.hidden == None)) \
    #     .order_by(sqla.desc(sqla.func.max(sqlm.StatusUpdate.created))).limit(5).subquery()
    #
    # status_updates = sqla.session.query(sqlm.StatusUpdate) \
    #     .join(status_update_authors, sqla.and_(
    #         status_update_authors.c.author_id == sqlm.StatusUpdate.author_id,
    #         status_update_authors.c.created == sqlm.StatusUpdate.created
    #     )).order_by(sqla.desc(sqlm.StatusUpdate.created))[:5]
    
    status_updates = sqla.session.query(sqlm.StatusUpdate) \
        .filter(sqla.or_(sqlm.StatusUpdate.hidden == False, sqlm.StatusUpdate.hidden == None)) \
        .order_by(sqla.desc(sqlm.StatusUpdate.created)).paginate(1, 6, False).items

    announcements = sqla.session.query(sqlm.Topic) \
        .filter_by(announcement=True, hidden=False) \
        .filter(sqlm.Topic.category.has(sqlm.Category.restricted==False)) \
        .order_by(sqlm.Topic.created.desc()).paginate(1, 5, False).items

    if current_user.is_authenticated():
        blogs = sqla.session.query(sqlm.Blog) \
            .join(sqlm.Blog.recent_entry) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqlm.BlogEntry.draft.isnot(True)) \
            .filter(sqlm.BlogEntry.published.isnot(None)) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all",
                sqlm.Blog.privacy_setting == "members"
            )) \
            .order_by(sqla.desc(sqlm.BlogEntry.published))[0:4]
    else:
        blogs = sqla.session.query(sqlm.Blog) \
            .join(sqlm.Blog.recent_entry) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqlm.BlogEntry.draft.isnot(True)) \
            .filter(sqlm.BlogEntry.published.isnot(None)) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all"
            )) \
            .order_by(sqla.desc(sqlm.BlogEntry.published))[0:4]
    
    tweets = sqla.session.query(sqlm.Tweet).order_by(sqla.desc(sqlm.Tweet.time))[:3]
    
    post_count = 0 #sqla.session.query(sqlm.Post).count()
    topic_count = 0 #sqla.session.query(sqlm.Topic).count()
    blog_entry_count = sqla.session.query(sqlm.BlogEntry).count()
    status_update_count = sqla.session.query(sqlm.StatusUpdate).count()
    status_comments_count = sqla.session.query(sqlm.StatusComment).count()
        
    render = render_template("index.jade", page_title="%%GENERIC SITENAME%%", meta_description="Friendly online community devoted to members of the anime fandom that aren't hardcore otakus.",
        hierarchy=hierarchy,children=children,announcements=announcements,
        status_updates=status_updates, online_users=online_users, blogs=blogs,
        newest_member=newest_member, new_member_intro_topic=new_member_intro_topic, tweets=tweets, birthday_list=birthday_list,
        online_user_count=len(online_users), recently_replied_topics=recently_replied_topics, recently_created_topics=recently_created_topics,
        post_count=post_count, topic_count=topic_count, blog_entry_count=blog_entry_count, status_update_count=status_update_count, status_comments_count=status_comments_count)

    return render
