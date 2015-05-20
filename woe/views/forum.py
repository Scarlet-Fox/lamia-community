from woe import login_manager
from woe import app
from woe.models.core import User, DisplayNameHistory, StatusUpdate
from woe.models.forum import Category, Post, Topic
from collections import OrderedDict
from woe.forms.core import LoginForm, RegistrationForm
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session
from flask.ext.login import login_user, logout_user, current_user
import arrow, time
from woe.utilities import get_top_frequences, scrub_json, humanize_time, ForumPostParser

@app.route('/topic/<slug>/posts', methods=['POST'])
def topic_posts(slug):
    try:
        topic = Topic.objects(slug=slug)[0]
    except IndexError:
        return abort(404)
    # TODO : Check if someone is topic banned.

    request_json = request.get_json(force=True)
    
    try:
        pagination = int(request_json.get("pagination", 20))
        page = int(request_json.get("page", 1))
    except:
        pagination = 20
        page = 1
        
    posts = Post.objects(hidden=False, topic=topic)[(page-1)*pagination:page*pagination]
    post_count = Post.objects(hidden=False, topic=topic).count()
    parsed_posts = []
    
    for post in posts:
        clean_html_parser = ForumPostParser()
        parsed_post = post.to_mongo().to_dict()
        parsed_post["created"] = humanize_time(post.created, "MMM D YYYY")
        parsed_post["modified"] = humanize_time(post.modified, "MMM D YYYY")
        parsed_post["html"] = clean_html_parser.parse(post.html)
        parsed_post["user_avatar"] = post.author.get_avatar_url()
        parsed_post["user_avatar_x"] = post.author.avatar_full_x
        parsed_post["user_avatar_y"] = post.author.avatar_full_y
        parsed_post["user_avatar_60"] = post.author.get_avatar_url("60")
        parsed_post["user_avatar_x_60"] = post.author.avatar_60_x
        parsed_post["user_avatar_y_60"] = post.author.avatar_60_y
        parsed_post["user_title"] = post.author.title
        parsed_post["author_name"] = post.author.display_name
        parsed_post["author_login_name"] = post.author.login_name
        
        if current_user.is_authenticated():
            if post.author.pk == current_user.pk:
                parsed_post["is_author"] = True
            else:
                parsed_post["is_author"] = False   
        else:
            parsed_post["is_author"] = False   
            
        try:
            if post.author.last_seen > arrow.utcnow().replace(minutes=-15).datetime:
                parsed_post["author_online"] = True
            else:
                parsed_post["author_online"] = False
        except:
            parsed_post["author_online"] = False
        parsed_posts.append(parsed_post)
        
    return app.jsonify(posts=parsed_posts, count=post_count)    

@app.route('/topic/<slug>', methods=['GET'], defaults={'page': 1, 'post': ""})
@app.route('/topic/<slug>/page/<page>', methods=['GET'], defaults={'post': ""})
@app.route('/topic/<slug>/page/<page>/post/<post>', methods=['GET'])
def topic_index(slug, page, post):
    try:
        topic = Topic.objects(slug=slug)[0]
    except IndexError:
        return abort(404)
    # TODO : Check if someone is topic banned.
    
    try:
        page = int(page)
    except:
        page = 1
        
    if post != "":
        try:
            post = Post.objects(topic=topic, pk=post)
        except:
            return abort(404)
    else:
        post = ""

    return render_template("forum/topic.jade", topic=topic, initial_page=page, initial_post="")

@app.route('/category/<slug>/filter-preferences', methods=['GET', 'POST'])
def category_filter_preferences(slug):
    try:
        category = Category.objects(slug=slug)[0]
    except IndexError:
        return abort(404)
    if not current_user.is_authenticated():
        return json.jsonify(preferences={})
            
    if request.method == 'POST':
        
        request_json = request.get_json(force=True)
        try:
            if len(request_json.get("preferences")) < 10:
                current_user.data["category_filter_preference_"+str(category.pk)] = request_json.get("preferences")
        except:
            return json.jsonify(preferences={})
        
        current_user.update(data=current_user.data)
        preferences = current_user.data.get("category_filter_preference_"+str(category.pk), {})
        return json.jsonify(preferences=preferences)
    else:        
        preferences = current_user.data.get("category_filter_preference_"+str(category.pk), {})
        return json.jsonify(preferences=preferences)

@app.route('/category/<slug>/topics', methods=['POST'])
def category_topics(slug):
    try:
        category = Category.objects(slug=slug)[0]
    except IndexError:
        return abort(404)
    
    if current_user.is_authenticated():
        preferences = current_user.data.get("category_filter_preference_"+str(category.pk), {})
        prefixes = preferences.keys()
    else:
        prefixes = []
    
    request_json = request.get_json(force=True)
    page = request_json.get("page", 1)
    pagination = request_json.get("pagination", 20)
    
    try:
        minimum = (int(page)-1)*int(pagination)
        maximum = int(page)*int(pagination)
    except:
        minimum = 0
        maximum = 20
    
    if len(prefixes) > 0:
        topics = Topic.objects(category=category, prefix__in=prefixes, hidden=False, post_count__gt=0).order_by("-last_post_date")[minimum:maximum]
        topic_count = Topic.objects(category=category, prefix__in=prefixes, hidden=False, post_count__gt=0).count()
    else:
        topics = Topic.objects(category=category, post_count__gt=0).order_by("-last_post_date")[minimum:maximum]
        topic_count = Topic.objects(category=category, post_count__gt=0).count()
    
    parsed_topics = []
    for topic in topics:
        parsed_topic = topic.to_mongo().to_dict()
        parsed_topic["creator"] = topic.creator.display_name
        parsed_topic["created"] = humanize_time(topic.created, "MMM D YYYY")
        if topic.last_post_date:
            parsed_topic["last_post_date"] = humanize_time(topic.last_post_date)
            parsed_topic["last_post_by"] = topic.last_post_by.display_name
            parsed_topic["last_post_x"] = topic.last_post_by.avatar_40_x
            parsed_topic["last_post_y"] = topic.last_post_by.avatar_40_y
            parsed_topic["last_post_by_login_name"] = topic.last_post_by.login_name
        parsed_topic["post_count"] = "{:,}".format(topic.post_count)
        parsed_topic["view_count"] = "{:,}".format(topic.view_count)
        try:
            parsed_topic["last_page"] = float(topic.post_count)/float(pagination)
        except:
            parsed_topic["last_page"] = 1
        parsed_topic["last_pages"] = parsed_topic["last_page"] > 1
            
        parsed_topics.append(parsed_topic)
    
    return app.jsonify(topics=parsed_topics, count=topic_count)

@app.route('/category/<slug>', methods=['GET'])
def category_index(slug):
    try:
        category = Category.objects(slug=slug)[0]
    except IndexError:
        return abort(404)
    
    subcategories = Category.objects(parent=category)
    prefixes = get_top_frequences(Topic.objects(category=category, prefix__ne=None).item_frequencies("prefix"),10) 
    
    return render_template("forum/category.jade", category=category, subcategories=subcategories, prefixes=prefixes)

@app.route('/')
def index():
    start = time.time()
    categories = OrderedDict()
    
    for category in Category.objects(root_category=True):
        categories[category.name] = [category,]
        for subcategory in Category.objects(parent=category):
            categories[category.name].append(subcategory)
    
    status_updates = StatusUpdate.objects(attached_to_user=None)[:10]
    cleaned_statuses = []
    user_already_posted = []
    for status in status_updates:
        if status.author_name in user_already_posted:
            continue
        
        user_already_posted.append(status.author_name)
        cleaned_statuses.append(status)
    
    online_users = User.objects(last_seen__gte=arrow.utcnow().replace(minutes=-15).datetime)
    post_count = Post.objects().count()
    member_count = User.objects(banned=False).count()
    newest_member = User.objects().order_by("-joined")[0]
    
    return render_template("index.jade", 
        categories=categories, status_updates=cleaned_statuses[:5], online_users=online_users,
        post_count=post_count, member_count=member_count, newest_member=newest_member, 
        online_user_count=online_users.count())