from woe import app
from woe.models.core import User, DisplayNameHistory, StatusUpdate, ForumPostParser
from woe.models.forum import Category, Post, Topic, Prefix, get_topic_slug, PostHistory
from collections import OrderedDict
from woe.forms.core import LoginForm, RegistrationForm
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session
from flask.ext.login import login_user, logout_user, current_user, login_required
import arrow, time, math
from woe.utilities import get_top_frequences, scrub_json, humanize_time, ForumHTMLCleaner, parse_search_string_return_q
from woe.views.dashboard import broadcast

@app.route('/category-list-api', methods=['GET'])
@login_required
def category_list_api():
    query = request.args.get("q", "")[0:300]
    if len(query) < 2:
        return app.jsonify(results=[])
    
    q_ = parse_search_string_return_q(query, ["name",])
    categories = Category.objects(q_)
    results = [{"text": unicode(c.name), "id": str(c.pk)} for c in categories]
    return app.jsonify(results=results)
    
@app.route('/topic-list-api', methods=['GET'])
@login_required
def topic_list_api():
    query = request.args.get("q", "")[0:300]
    if len(query) < 2:
        return app.jsonify(results=[])
    
    q_ = parse_search_string_return_q(query, ["title",])
    topics = Topic.objects(q_)
    results = [{"text": unicode(t.title), "id": str(t.pk)} for t in topics]
    return app.jsonify(results=results)
    
@app.route('/t/<slug>/new-post', methods=['POST'])
@login_required
def new_post_in_topic(slug):
    try:
        topic = Topic.objects(slug=slug)[0]
    except IndexError:
        return abort(404)
    
    if current_user._get_current_object() in topic.banned_from_topic:
        return abort(404)
    
    if topic.closed:
        return app.jsonify(closed_topic=True, closed_message=topic.close_message)

    request_json = request.get_json(force=True)
    
    if request_json.get("text", "").strip() == "":
        return app.jsonify(no_content=True)
        
    cleaner = ForumHTMLCleaner()
    try:
        post_html = cleaner.clean(request_json.get("post", ""))
    except:
        return abort(500)
    
    try: # TODO : Cannot do this for roleplay topics.
        users_last_post = Post.objects(author=current_user._get_current_object()).order_by("-created")[0]
        difference = (arrow.utcnow().datetime - arrow.get(users_last_post.created).datetime).seconds
        if difference < 30:
            return app.jsonify(error="Please wait %s seconds before posting again." % (30 - difference))
    except:
        pass
        
    new_post = Post()
    new_post.html = post_html
    new_post.author = current_user._get_current_object()
    new_post.author_name = current_user.login_name
    new_post.topic = topic
    new_post.topic_name = topic.title
    new_post.created = arrow.utcnow().datetime
    new_post.save()
    
    topic.last_post_by = current_user._get_current_object()
    topic.last_post_date = new_post.created
    topic.last_post_author_avatar = current_user._get_current_object().get_avatar_url("40")
    topic.post_count = Post.objects(topic=topic, hidden=False).count()
    topic.save()
    
    category = topic.category
    category.last_topic = topic
    category.last_topic_name = topic.title
    category.last_post_by = topic.last_post_by
    category.last_post_date = topic.last_post_date
    category.last_post_author_avatar = topic.last_post_author_avatar
    category.post_count = category.post_count + 1
    category.save()
    
    clean_html_parser = ForumPostParser()
    parsed_post = new_post.to_mongo().to_dict()
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
    parsed_post["group_pre_html"] = new_post.author.group_pre_html
    parsed_post["author_group_name"] = new_post.author.group_name
    parsed_post["group_post_html"] = new_post.author.group_post_html
    
    post_count = Post.objects(hidden=False, topic=topic).count()
    
    notify_users = []
    for u in topic.watchers:
        if u == new_post.author:
            continue
            
        notify_users.append(u)
    
    broadcast(
        to=notify_users,
        category="topic", 
        url="/t/%s/page/1/post/%s" % (str(topic.slug), str(new_post.pk)),
        title="%s has replied to %s." % (new_post.author.display_name, topic.title),
        description=new_post.html, 
        content=topic, 
        author=new_post.author
        )
    
    return app.jsonify(newest_post=parsed_post, count=post_count, success=True)    

@app.route('/t/<slug>/posts', methods=['POST'])
def topic_posts(slug):
    try:
        topic = Topic.objects(slug=slug)[0]
    except IndexError:
        return abort(404)
    
    if current_user._get_current_object() in topic.banned_from_topic:
        return abort(404)

    request_json = request.get_json(force=True)
    
    try:
        pagination = int(request_json.get("pagination", 20))
        page = int(request_json.get("page", 1))
    except:
        pagination = 20
        page = 1

    post_count = Post.objects(hidden=False, topic=topic).count()
    max_page = math.ceil(float(topic.post_count)/float(pagination))
    if page > max_page:
        page = max_page
    posts = Post.objects(hidden=False, topic=topic)[(page-1)*pagination:page*pagination]
    topic.update(post_count=post_count)
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
        parsed_post["group_pre_html"] = post.author.group_pre_html
        parsed_post["author_group_name"] = post.author.group_name
        parsed_post["group_post_html"] = post.author.group_post_html
        
        if current_user.is_authenticated():
            if post.author.pk == current_user.pk:
                parsed_post["is_author"] = True
            else:
                parsed_post["is_author"] = False   
        else:
            parsed_post["is_author"] = False   
        
        if post.author.last_seen != None:
            if arrow.get(post.author.last_seen) > arrow.utcnow().replace(minutes=-15).datetime:
                parsed_post["author_online"] = True
            else:
                parsed_post["author_online"] = False
        else:
            parsed_post["author_online"] = False

        parsed_posts.append(parsed_post)
        
    return app.jsonify(posts=parsed_posts, count=post_count)    

@app.route('/topic/<slug>/', methods=['GET'],)
def legacy_topic_index(slug):
    ipb_id = slug.split("-")[0]
    try:
        topic = Topic.objects(old_ipb_id=ipb_id)[0]
    except IndexError:
        print "not here"
        return abort(404)
    
    print "/t/"+topic.slug
    return redirect("/t/"+topic.slug)

@app.route('/t/<slug>/edit-post', methods=['POST'])
@login_required
def edit_topic_post_html(slug):
    try:
        topic = Topic.objects(slug=slug)[0]
    except IndexError:
        return abort(404)

    request_json = request.get_json(force=True)

    try:
        post = Post.objects(topic=topic, pk=request_json.get("pk"), hidden=False)[0]
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
    
    history = PostHistory()
    history.creator = current_user._get_current_object()
    history.created = arrow.utcnow().datetime
    history.html = post.html
    history.data = post.data
    history.reason = request_json.get("edit_reason", "")
    
    if request_json.get("edit_reason", "").strip() == "":
        return app.jsonify(error="Please include an edit reason.")
    
    post.history.append(history)
    post.html = post_html
    post.modified = arrow.utcnow().datetime
    post.save()
        
    clean_html_parser = ForumPostParser()    
    return app.jsonify(html=clean_html_parser.parse(post.html), success=True)


@app.route('/t/<slug>/edit-post/<post>', methods=['GET'])
@login_required
def get_post_html_in_topic(slug, post):
    try:
        topic = Topic.objects(slug=slug)[0]
    except IndexError:
        return abort(404)

    try:
        post = Post.objects(topic=topic, pk=post, hidden=False)[0]
    except:
        return abort(404)
        
    return json.jsonify(content=post.html)

@app.route('/t/<slug>', methods=['GET'], defaults={'page': 1, 'post': ""})
@app.route('/t/<slug>/page/<page>', methods=['GET'], defaults={'post': ""})
@app.route('/t/<slug>/page/<page>/post/<post>', methods=['GET'])
def topic_index(slug, page, post):
    try:
        topic = Topic.objects(slug=slug)[0]
    except IndexError:
        return abort(404)
    # TODO : Check if someone is topic banned.
    pagination = 20
    
    if current_user._get_current_object() in topic.banned_from_topic:
        return abort(404)
        
    try:
        page = int(page)
    except:
        page = 1
        
    if post != "":
        try:
            post = Post.objects(topic=topic, pk=post, hidden=False)[0]
        except:
            return abort(404)
    else:
        post = ""
    
    if post != "":
        target_date = post.created
        posts_before_target = Post.objects(hidden=False, topic=topic, created__lt=target_date).count()
        page = int(math.floor(float(posts_before_target)/float(pagination)))+1
        return render_template("forum/topic.jade", topic=topic, initial_page=page, initial_post=str(post.pk))
    
    topic.update(inc__view_count=1)
    return render_template("forum/topic.jade", topic=topic, initial_page=page)

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

@app.route('/category/<slug>/new-topic', methods=['GET', 'POST'])
@login_required
def new_topic(slug):
    if request.method == 'POST':
        try:
            category = Category.objects(slug=slug)[0]
        except IndexError:
            print "Error?"
            return abort(404)
        
        request_json = request.get_json(force=True)
    
        if request_json.get("title", "").strip() == "":
            return app.jsonify(error="Please enter a title.")
    
        if request_json.get("text", "").strip() == "":
            return app.jsonify(error="Please enter actual text for your post.")
    
        if len(category.allowed_prefixes) > 0:
            if request_json.get("prefix", "").strip() == "":
                return app.jsonify(error="Please choose a prefix.")
        
            if not request_json.get("prefix", "").strip() in category.allowed_prefixes:
                return app.jsonify(error="Please choose a valid prefix.")
        
        cleaner = ForumHTMLCleaner()
        try:
            post_html = cleaner.clean(request_json.get("html", ""))
        except:
            return abort(500)
            
        try:
            prefix = Prefix.objects(prefix=request_json.get("prefix", "").strip())[0]
        except IndexError:
            prefix = ""

        try:
            users_last_topic = Topic.objects(creator=current_user._get_current_object()).order_by("-created")[0]
            difference = (arrow.utcnow().datetime - arrow.get(users_last_topic.created).datetime).seconds
            if difference < 360:
                return app.jsonify(error="Please wait %s seconds before you create another topic." % (360 - difference))
        except:
            pass

        new_topic = Topic()
        new_topic.category = category
        new_topic.title = request_json.get("title")
        new_topic.slug = get_topic_slug(new_topic.title)
        new_topic.creator = current_user._get_current_object()
        new_topic.created = arrow.utcnow().datetime
        if prefix != "":
            new_topic.pre_html = prefix.pre_html
            new_topic.prefix = prefix.prefix
            new_topic.post_html = prefix.post_html
            new_topic.prefix_reference = prefix
        new_topic.last_post_by = current_user._get_current_object()
        new_topic.last_post_date = new_topic.created
        new_topic.last_post_author_avatar = current_user._get_current_object().get_avatar_url("40")
        new_topic.post_count = 1
        new_topic.save()
        
        category.last_topic = new_topic
        category.last_topic_name = new_topic.title
        category.last_post_by = new_topic.last_post_by
        category.last_post_date = new_topic.last_post_date
        category.last_post_author_avatar = new_topic.last_post_author_avatar
        category.post_count = category.post_count + 1
        category.save()
        
        new_post = Post()
        new_post.html = post_html
        new_post.author = current_user._get_current_object()
        new_post.author_name = current_user.login_name
        new_post.topic = new_topic
        new_post.topic_name = new_topic.title
        new_post.created = arrow.utcnow().datetime
        new_post.save()
        new_topic.update(first_post=new_post)
    
        send_notify_to_users = []
        for user in new_post.author.followed_by:
            if user not in new_post.author.ignored_users:
                send_notify_to_users.append(user)

        broadcast(
          to=send_notify_to_users,
          category="user_activity", 
          url="/t/"+unicode(new_topic.slug),
          title="%s created a new topic. %s." % (new_post.author.display_name, new_topic.title),
          description=new_post.html, 
          content=new_topic, 
          author=new_post.author
          )
        
        return app.jsonify(url="/t/"+new_topic.slug)
    else:
        try:
            category = Category.objects(slug=slug)[0]
        except IndexError:
            return abort(404)
        
        return render_template("forum/new_topic.jade", category=category)

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
        topics = Topic.objects(category=category, prefix__in=prefixes, hidden=False, post_count__gt=0).order_by("-sticky", "-last_post_date")[minimum:maximum]
        topic_count = Topic.objects(category=category, prefix__in=prefixes, hidden=False, post_count__gt=0).count()
    else:
        topics = Topic.objects(category=category, post_count__gt=0).order_by("-sticky", "-last_post_date")[minimum:maximum]
        topic_count = Topic.objects(category=category, post_count__gt=0).count()
    
    parsed_topics = []
    for topic in topics:
        if current_user._get_current_object() in topic.banned_from_topic:
            continue
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
    
    status_updates = StatusUpdate.objects(attached_to_user=None)[:30]
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
