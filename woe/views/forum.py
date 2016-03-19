from woe import app
from woe import sqla
from woe.models.core import User, DisplayNameHistory, StatusUpdate, Attachment
from woe.parsers import ForumPostParser
from woe.models.forum import Category, Post, Topic, Prefix, get_topic_slug, PostHistory
from woe.models.roleplay import Character
from collections import OrderedDict
from woe.forms.core import LoginForm, RegistrationForm
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session
from flask.ext.login import login_user, logout_user, current_user, login_required
import arrow, time, math
from threading import Thread
from woe.utilities import get_top_frequences, scrub_json, humanize_time, ForumHTMLCleaner, parse_search_string_return_q, parse_search_string
from woe.views.dashboard import broadcast
import re, json
from datetime import datetime
import woe.sqlmodels as sqlm

mention_re = re.compile("\[@(.*?)\]")
reply_re = re.compile(r'\[reply=(.+?):(post)(:.+?)?\]')

@app.route('/category-list-api', methods=['GET'])
@login_required
def category_list_api():
    query = request.args.get("q", "")[0:300]
    if len(query) < 2:
        return app.jsonify(results=[])

    q_ = parse_search_string(query, sqlm.Category, sqla.session.query(sqlm.Category), ["name",])
    categories = q_.all()
    results = [{"text": unicode(c.name), "id": str(c.id)} for c in categories]
    return app.jsonify(results=results)

@app.route('/topic-list-api', methods=['GET'])
@login_required
def topic_list_api():
    query = request.args.get("q", "")[0:300]
    if len(query) < 2:
        return app.jsonify(results=[])

    q_ = parse_search_string(query, sqlm.Topic, sqla.session.query(sqlm.Topic), ["title",])
    topics = q_.all()
    results = [{"text": unicode(t.title), "id": str(t.id)} for t in topics]
    return app.jsonify(results=results)

@app.route('/t/<slug>/toggle-follow', methods=['POST'])
@login_required
def toggle_follow_topic(slug):
    try:
        topic = sqla.session.query(sqlm.Topic).filter_by(slug=slug)[0]
    except IndexError:
        return abort(404)

    if current_user._get_current_object() in topic.banned:
        return abort(404)

    if not current_user._get_current_object() in topic.watchers:
        topic.watchers.append(current_user._get_current_object())
    else:
        try:
            topic.watchers.remove(current_user._get_current_object())
        except:
            pass

    try:
        sqla.session.add(topic)
        sqla.commit()
    except:
        sqla.rollback()

    return app.jsonify(url="/t/"+unicode(topic.slug)+"")

@app.route('/t/<slug>/new-post', methods=['POST'])
@login_required
def new_post_in_topic(slug):
    try:
        topic = sqla.session.query(sqlm.Topic).filter_by(slug=slug)[0]
    except IndexError:
        return abort(404)

    if current_user._get_current_object() in topic.banned:
        return abort(404)

    if topic.locked or topic.hidden:
        return app.jsonify(closed_topic=True, closed_message=topic.close_message)

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

    print character
    print request_json.get("avatar")

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

    print avatar

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

    clean_html_parser = ForumPostParser()
    parsed_post = {}
    parsed_post["created"] = humanize_time(new_post.created, "MMM D YYYY")
    parsed_post["modified"] = humanize_time(new_post.modified, "MMM D YYYY")
    parsed_post["html"] = clean_html_parser.parse(new_post.html)
    parsed_post["user_avatar"] = new_post.author.get_avatar_url()
    parsed_post["user_avatar_x"] = new_post.author.avatar_full_x
    parsed_post["user_avatar_y"] = new_post.author.avatar_full_y
    parsed_post["user_avatar_60"] = new_post.author.get_avatar_url("60")
    parsed_post["user_avatar_x_60"] = new_post.author.avatar_60_x
    parsed_post["user_avatar_y_60"] = new_post.author.avatar_60_y
    parsed_post["user_title"] = new_post.author.title
    parsed_post["author_name"] = new_post.author.display_name
    parsed_post["author_login_name"] = new_post.author.login_name

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
      title="%s mentioned you in %s." % (unicode(new_post.author.display_name), unicode(topic.title)),
      description=new_post.html,
      content=new_post,
      author=new_post.author
      )

    replies = reply_re.findall(post_html)
    to_notify = {}
    for reply_ in replies:
        try:
            to_notify[reply_] = sqlm.session.query(sqlm.Post).filter_by(id=reply_[0])[0].author
        except:
            continue

    broadcast(
      to=to_notify.values(),
      category="topic_reply",
      url="/t/%s/page/1/post/%s" % (str(topic.slug), str(new_post.id)),
      title="%s replied to you in %s." % (unicode(new_post.author.display_name), unicode(topic.title)),
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
        title="%s has replied to %s." % (unicode(new_post.author.display_name), unicode(topic.title)),
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

@app.route('/t/<slug>/posts', methods=['POST'])
def topic_posts(slug):
    start = time.time()
    try:
        topic = sqla.session.query(sqlm.Topic).filter_by(slug=slug)[0]
    except IndexError:
        return abort(404)

    if current_user._get_current_object() in topic.banned:
        return abort(404)

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
        [(page-1)*pagination:page*pagination]

    parsed_posts = []

    first_post = sqla.session.query(sqlm.Post).filter_by(topic=topic) \
        .filter(sqla.or_(sqlm.Post.hidden == False, sqlm.Post.hidden == None)) \
        .order_by(sqlm.Post.created)[0]

    for post in posts:
        clean_html_parser = ForumPostParser()
        parsed_post = {}
        parsed_post["_id"] = post.id
        parsed_post["created"] = humanize_time(post.created, "MMM D YYYY")
        parsed_post["modified"] = humanize_time(post.modified, "MMM D YYYY")
        parsed_post["html"] = clean_html_parser.parse(post.html)
        parsed_post["roles"] = post.author.get_roles()
        parsed_post["user_avatar"] = post.author.get_avatar_url()
        parsed_post["user_avatar_x"] = post.author.avatar_full_x
        parsed_post["user_avatar_y"] = post.author.avatar_full_y
        parsed_post["user_avatar_60"] = post.author.get_avatar_url("60")
        parsed_post["user_avatar_x_60"] = post.author.avatar_60_x
        parsed_post["user_avatar_y_60"] = post.author.avatar_60_y
        parsed_post["user_title"] = post.author.title
        parsed_post["author_name"] = post.author.display_name
        if post == first_post:
            parsed_post["topic_leader"] = "/t/"+topic.slug+"/edit-topic"
        parsed_post["author_login_name"] = post.author.login_name
        parsed_post["has_booped"] = current_user._get_current_object() in post.boops
        parsed_post["boop_count"] = len(post.boops)
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

        if post.character is not None:
            try:
                character = post.character
                parsed_post["character_name"] = character.name
                parsed_post["character_slug"] = character.slug
                parsed_post["character_motto"] = character.motto
            except:
                pass
        else:
            character = None

        if post.avatar is not None:
            try:
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
            character_gallery=True, character_avatar=True, id=request_json.get("avatar")) \
            .order_by(character_gallery_weight).first()

        if avatar == None:
            avatar = sqla.session.query(sqlm.Attachment).filter_by(character=character, \
                character_gallery=True, character_avatar=True) \
                .order_by(character_gallery_weight).first()[0]
    except:
        avatar = False

    history = {}
    history["author"] = current_user._get_current_object().id
    history["created"] = str(arrow.utcnow().datetime)
    history["html"] = post.html+""
    history["data"] = post.data
    history["reason"] = request_json.get("edit_reason", "")

    if post.post_history == None:
        post.post_history = []

    post.post_history.append(history)

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
                post.character == None
            except:
                pass
        if avatar:
            post.avatar == avatar
        else:
            try:
                post.avatar == None
            except:
                pass

    sqla.session.add(post)
    sqla.session.commit()

    clean_html_parser = ForumPostParser()
    return app.jsonify(html=clean_html_parser.parse(post.html), success=True)

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
        return abort(404)

    if topic.hidden and not (current_user._get_current_object().is_admin or current_user._get_current_object().is_mod):
        return abort(404)

    try:
        page = int(page)
    except:
        page = 1

    if topic.last_seen_by is None:
        topic.last_seen_by = {}

    if post == "latest_post":
        try:
            post = sqla.session.query(sqlm.Post).filter_by(topic=topic) \
            .filter(sqla.or_(sqlm.Post.hidden == False, sqlm.Post.hidden == None)) \
            .order_by(sqla.desc(sqlm.Post.created))[0]
        except:
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
            try:
                post = sqla.session.query(sqlm.Post).filter_by(topic=topic) \
                    .filter_by(id=post).filter(sqlm.Post.created < last_seen) \
                    .filter(sqla.or_(sqlm.Post.hidden == False, sqlm.Post.hidden == None)) \
                    .order_by(sqlm.Post.created.desc())[0]
            except:
                return redirect("/t/"+unicode(topic.slug))
    else:
        if post != "":
            try:
                post = sqla.session.query(sqlm.Post).filter_by(topic=topic) \
                    .filter_by(id=post).filter(sqlm.Post.created < last_seen) \
                    .filter(sqla.or_(sqlm.Post.hidden == False, sqlm.Post.hidden == None)) \
                    .order_by(sqlm.Post.created.desc())[0]
            except:
                return redirect("/t/"+unicode(topic.slug))
        else:
            post = ""

    if post != "":
        topic.view_count = topic.view_count + 1
        try:
            topic.last_seen_by[str(current_user._get_current_object().id)] = arrow.utcnow().timestamp
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
        return render_template("forum/topic.jade", topic=topic, page_title="%s - Scarlet's Web" % unicode(topic.title), initial_page=page, initial_post=str(post.id), rp_area=rp_topic)

    topic.view_count = topic.view_count + 1
    try:
        topic.last_seen_by[str(current_user._get_current_object().id)] = arrow.utcnow().timestamp
        sqla.session.add(topic)
        sqla.session.commit()
    except:
        sqla.session.rollback()
        pass

    rp_topic = "false"
    if topic.category.slug in ["roleplays", "scenarios"]:
        rp_topic = "true"

    return render_template("forum/topic.jade", topic=topic, page_title="%s - Scarlet's Web" % unicode(topic.title), initial_page=page, rp_area=rp_topic)

@app.route('/category/<slug>/filter-preferences', methods=['GET', 'POST'])
def category_filter_preferences(slug):
    try:
        category = sqla.session.query(sqlm.Category).filter_by(slug=slug)[0]
    except IndexError:
        return abort(404)
    if not current_user.is_authenticated():
        return app.jsonify(preferences={})

    if current_user.data is None:
        current_user.data = {}

    if request.method == 'POST':
        request_json = request.get_json(force=True)
        try:
            if len(request_json.get("preferences")) < 10:
                current_user.data["category_filter_preference_"+str(category.id)] = request_json.get("preferences")
        except:
            return app.jsonify(preferences={})

        sqla.session.add(current_user)
        sqla.session.commit()
        preferences = current_user.data.get("category_filter_preference_"+str(category.id), {})
        return app.jsonify(preferences=preferences)
    else:
        preferences = current_user.data.get("category_filter_preference_"+str(category.id), {})
        return app.jsonify(preferences=preferences)

@app.route('/t/<slug>/edit-topic', methods=['GET', 'POST'])
@login_required
def edit_topic(slug):
    try:
        topic = sqla.session.query(sqlm.Topic).filter_by(slug=slug)[0]
    except IndexError:
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

        if len(category.allowed_prefixes) > 0:
            if request_json.get("prefix", "").strip() == "":
                return app.jsonify(error="Please choose a label.")

            if not request_json.get("prefix", "").strip() in category.allowed_prefixes:
                return app.jsonify(error="Please choose a valid label.")

        cleaner = ForumHTMLCleaner()
        try:
            post_html = cleaner.clean(request_json.get("html", ""))
        except:
            return abort(500)

        try:
            label = sqla.session.query(sqlm.Label).filter_by(label=request_json.get("prefix", "").strip())[0]
        except IndexError:
            prefix = ""

        history = {}
        history["author"] = current_user._get_current_object().id
        history["created"] = str(arrow.utcnow().datetime)
        history["html"] = first_post.html+""
        history["data"] = first_post.data
        history["reason"] = request_json.get("edit_reason", "")

        if post.post_history == None:
            post.post_history = []

        post.post_history.append(history)

        if current_user._get_current_object() != topic.author:
            if request_json.get("edit_reason", "").strip() == "":
                return app.jsonify(error="Please include an edit reason for editing someone else's topic.")

        topic.title = request_json.get("title")
        if prefix != "":
            topic.label = label

        first_post = topic.first_post
        first_post.modified = arrow.utcnow().datetime
        first_post.html = post_html

        sqla.session.add(topic)
        sqla.session.add(first_post)
        sqla.session.commit()
        return app.jsonify(url="/t/"+topic.slug)
    else:
        return render_template("forum/edit_topic.jade", page_title="Edit Topic", category=category, topic=topic)

@app.route('/category/<slug>/new-topic', methods=['GET', 'POST'])
@login_required
def new_topic(slug):
    if request.method == 'POST':
        try:
            category = sqla.session.query(sqlm.Category).filter_by(slug=slug)[0]
        except IndexError:
            return abort(404)

        request_json = request.get_json(force=True)

        if request_json.get("title", "").strip() == "":
            return app.jsonify(error="Please enter a title.")

        if request_json.get("text", "").strip() == "":
            return app.jsonify(error="Please enter actual text for your post.")

        if len(category.allowed_labels) > 0:
            if request_json.get("prefix", "").strip() == "":
                return app.jsonify(error="Please choose a label.")

            if not current_user._get_current_object().is_admin and not current_user._get_current_object().is_mod:
                try:
                    label = sqla.session.query(sqlm.Label).filter_by(label=request_json.get("prefix", "").strip())[0]

                    if not label in category.allowed_labels:
                        return app.jsonify(error="Please choose a valid label.")
                except:
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
        new_topic.title = request_json.get("title")
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

        sqla.session.add(category)
        sqla.session.add(new_topic)
        sqla.session.commit()

        send_notify_to_users = []
        # TODO:
        # for user in new_post.author.followed_by:
        #     if user not in new_post.author.ignored_users:
        #         send_notify_to_users.append(user)

        broadcast(
          to=send_notify_to_users,
          category="user_activity",
          url="/t/"+unicode(new_topic.slug),
          title="%s created a new topic. %s." % (unicode(new_post.author.display_name), unicode(new_topic.title)),
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
          title="%s mentioned you in new topic %s." % (unicode(new_post.author.display_name), unicode(new_topic.title)),
          description=new_post.html,
          content=new_topic,
          author=new_post.author
          )

        return app.jsonify(url="/t/"+new_topic.slug)
    else:
        try:
            category = sqla.session.query(sqlm.Category).filter_by(slug=slug)[0]
        except IndexError:
            return abort(404)

        return render_template("forum/new_topic.jade", page_title="Create New Topic", category=category)

@app.route('/category/<slug>/topics', methods=['POST'])
def category_topics(slug):
    try:
        category = sqla.session.query(sqlm.Category).filter_by(slug=slug)[0]
    except IndexError:
        return abort(404)

    if current_user.is_authenticated():
        preferences = current_user.data.get("category_filter_preference_"+str(category.id), {})
        prefixes = preferences.keys()
    else:
        prefixes = []

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
            sqlm.Label.label.in_(prefixes)).join(sqlm.Topic.label).join(sqlm.Topic.recent_post).order_by(sqlm.Topic.announcement, \
            sqlm.Topic.sticky, sqla.desc(sqlm.Post.created))[minimum:maximum]
        topic_count = sqla.session.query(sqlm.Topic).filter(sqlm.Topic.category==category, sqlm.Topic.hidden==False, \
            sqlm.Label.label.in_(prefixes)).join(sqlm.Topic.label).count()
    else:
        topics = sqla.session.query(sqlm.Topic).filter(sqlm.Topic.category==category, sqlm.Topic.hidden==False) \
            .join(sqlm.Topic.recent_post).order_by(sqlm.Topic.announcement, \
            sqlm.Topic.sticky, sqla.desc(sqlm.Post.created))[minimum:maximum]
        topic_count = sqla.session.query(sqlm.Topic).filter(sqlm.Topic.category==category, sqlm.Topic.hidden==False).count()

    parsed_topics = []
    for topic in topics:
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
            parsed_topic["last_post_by_login_name"] = topic.recent_post.author.login_name
            parsed_topic["last_post_author_avatar"] = topic.recent_post.author.get_avatar_url("40")
        parsed_topic["post_count"] = "{:,}".format(topic.post_count)
        parsed_topic["view_count"] = "{:,}".format(topic.view_count)
        try:
            parsed_topic["last_page"] = float(topic.post_count)/float(pagination)
        except:
            parsed_topic["last_page"] = 1
        parsed_topic["last_pages"] = parsed_topic["last_page"] > 1
        parsed_topic["closed"] = topic.locked
        parsed_topic["title"] = topic.title
        parsed_topic["slug"] = topic.slug

        parsed_topics.append(parsed_topic)

    return app.jsonify(topics=parsed_topics, count=topic_count)

@app.route('/category/<slug>', methods=['GET'])
def category_index(slug):
    try:
        category = sqla.session.query(sqlm.Category).filter_by(slug=slug)[0]
    except IndexError:
        return abort(404)

    subcategories = sqla.session.query(sqlm.Category).filter_by(parent=category).all()
    prefixes = sqla.session.query(sqlm.Label.label, sqla.func.count(sqlm.Topic.id)).filter(sqlm.Topic.category==category) \
            .join(sqlm.Topic.label).group_by(sqlm.Label.label).order_by(sqla.desc(sqla.func.count(sqlm.Topic.id))).all()

    print prefixes

    return render_template("forum/category.jade", page_title="%s - Scarlet's Web" % unicode(category.name), category=category, subcategories=subcategories, prefixes=prefixes)

@app.route('/')
def index():
    sections = []
    categories = {}
    sub_categories = {}

    for section in sqla.session.query(sqlm.Section).order_by(sqlm.Section.weight).all():
        sections.append(section)

        categories[section] = []

        for category in sqla.session.query(sqlm.Category) \
            .filter_by(section=section).filter_by(parent=None).order_by(sqlm.Category.weight).all():
            categories[section].append(category)
            if len(category.children) > 0:
                sub_categories[category] = category.children

    online_users = sqla.session.query(sqlm.User) \
        .filter(sqlm.User.hidden_last_seen > arrow.utcnow() \
        .replace(minutes=-15).datetime).all()

    # post_count = sqla.session.query(sqlm.Post) \
    #     .filter_by(hidden=False).count()
    #
    # member_count = sqla.session.query(sqlm.User) \
    #     .filter_by(banned=False).count()
    #
    # newest_member = sqla.session.query(sqlm.User) \
    #     .order_by(sqla.desc(sqlm.User.joined))[0]

    recently_replied_topics = sqla.session.query(sqlm.Topic) \
        .filter(sqla.or_(sqlm.Topic.hidden == False, sqlm.Topic.hidden == None)) \
        .join(sqlm.Topic.recent_post).order_by(sqlm.Post.created.desc())[:5]

    recently_created_topics = sqla.session.query(sqlm.Topic) \
        .filter(sqla.or_(sqlm.Topic.hidden == False, sqlm.Topic.hidden == None)) \
        .order_by(sqlm.Topic.created.desc())[:5]

    status_updates = [result[1] for result in sqla.session.query(sqla.distinct(sqlm.StatusUpdate.author_id), sqlm.StatusUpdate) \
        .order_by(sqla.desc(sqlm.StatusUpdate.created)).limit(5)]

    return render_template("index.jade", page_title="Scarlet's Web",
        sections=sections, sub_categories=sub_categories,
        categories=categories, status_updates=status_updates, online_users=online_users,
        # post_count=post_count, member_count=member_count, newest_member=newest_member,
        online_user_count=len(online_users), recently_replied_topics=recently_replied_topics, recently_created_topics=recently_created_topics)
