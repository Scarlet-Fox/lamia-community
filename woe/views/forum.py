from woe import login_manager
from woe import app
from woe.models.core import User, DisplayNameHistory, StatusUpdate
from woe.models.forum import Category, Post, Topic
from collections import OrderedDict
from woe.forms.core import LoginForm, RegistrationForm
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session
from flask.ext.login import login_user, logout_user
import arrow, time
from woe.utilities import get_top_frequences

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