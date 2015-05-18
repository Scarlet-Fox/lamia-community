from woe import login_manager
from woe import app
from woe.models.core import User, DisplayNameHistory, StatusUpdate
from woe.models.forum import Category, Post, Topic
from collections import OrderedDict
from woe.forms.core import LoginForm, RegistrationForm
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session
from flask.ext.login import login_user, logout_user, current_user
import arrow, time
from woe.utilities import get_top_frequences, scrub_json, humanize_time

@app.route('/category/<slug>/filter-preferences', methods=['GET', 'POST'])
def category_filter_preferences(slug):
    try:
        category = Category.objects(slug=slug)[0]
    except IndexError:
        return abort(404)
            
    if request.method == 'POST':
        if not current_user.is_authenticated:
            return json.jsonify(preferences={})
        
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
        if not current_user.is_authenticated:
            return json.jsonify(preferences={})
    
        preferences = current_user.data.get("category_filter_preference_"+str(category.pk), {})
        return json.jsonify(preferences=preferences)

@app.route('/category/<slug>/topics', methods=['POST'])
def category_topics(slug):
    t = time.time()
    try:
        category = Category.objects(slug=slug)[0]
    except IndexError:
        return abort(404)
    
    if current_user.is_authenticated:
        preferences = current_user.data.get("category_filter_preference_"+str(category.pk), {})
        prefixes = preferences.keys()
    else:
        prefixes = []
    
    request_json = request.get_json(force=True)
    page = request_json.get("page", 1)
    pagination = request_json.get("pagination", 20)
    print request_json
    
    try:
        minimum = (int(page)-1)*int(pagination)
        maximum = int(page)*int(pagination)
    except:
        minimum = 0
        maximum = 20
    
    if prefixes:
        topics = Topic.objects(category=category, prefix__in=prefixes, hidden=False, post_count__gt=0).order_by("-last_post_date")[minimum:maximum]
        topic_count = Topic.objects(category=category, prefix__in=prefixes, hidden=False, post_count__gt=0).count()
    else:
        topics = Topic.objects(category=category, post_count__gt=0)[minimum:maximum]
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
    
    print time.time()-t
    return app.jsonify(topics=parsed_topics, count=topic_count)

@app.route('/category/<slug>')
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