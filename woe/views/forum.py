from woe import login_manager
from woe import app
from woe.models.core import User, DisplayNameHistory, StatusUpdate
from woe.models.forum import Category, Post, Topic
from collections import OrderedDict
from woe.forms.core import LoginForm, RegistrationForm
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session
from flask.ext.login import login_user, logout_user
import arrow, time
from woe.utilities import get_top_frequences, scrub_json

@app.route('/category/<slug>/filter-preferences', methods=['GET', 'POST'])
def category_filter_preferences(slug):
    try:
        category = Category.objects(slug=slug)[0]
    except IndexError:
        return abort(404)
            
    if request.method == 'POST':
        if not current_user.is_authenticated:
            return json.jsonify(preferences={})
        
        if len(request.form.get("preferences")) < 10:
            current_user.data["category_filter_preference_"+str(category.pk)] = request.form.get("preferences")
            
        preferences = current_user.data.get("category_filter_preference_"+str(category.pk), {})
        return json.jsonify(preferences)
    else:        
        if not current_user.is_authenticated:
            return json.jsonify(preferences={})
    
        preferences = current_user.data.get("category_filter_preference_"+str(category.pk), {})
        return json.jsonify(preferences)

@app.route('/category/<slug>/topics', methods=['POST'])
def category_topics(slug):
    try:
        category = Category.objects(slug=slug)[0]
    except IndexError:
        return abort(404)
    
    if current_user.is_authenticated:
        preferences = current_user.data.get("category_filter_preference_"+str(category.pk), {})
        prefixes = preferences.keys()
    else:
        prefixes = []
    
    page = request.form.get("page")
    pagination = request.form.get("pagination")
    
    try:
        minimum = (int(page)-1)*int(pagination)
        maximum = int(page)*int(pagination)
    except TypeError:
        minimum = 0
        maximum = 20
    
    if prefixes:
        topics = Topic.objects(category=category, prefix__in=prefixes)[minimum:maximum].to_json()
    else:
        topics = Topic.objects(category=category)[minimum:maximum].to_json()
        
    return json.jsonify(topics=topics)

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