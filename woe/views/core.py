from woe import login_manager
from woe import app
from woe.models.core import User, DisplayNameHistory, StatusUpdate, StatusComment, StatusViewer, PrivateMessage, PrivateMessageTopic
from woe.models.forum import Category, Post, Topic
from collections import OrderedDict
from woe.forms.core import LoginForm, RegistrationForm
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session, send_from_directory
from flask.ext.login import login_user, logout_user, login_required, current_user
from woe.utilities import get_top_frequences, scrub_json, humanize_time, ForumPostParser, ForumHTMLCleaner, parse_search_string_return_q
from mongoengine.queryset import Q
import arrow
import json

    
@app.route('/pm-topic-list-api', methods=['GET'])
@login_required
def pm_topic_list_api():
    query = request.args.get("q", "")[0:300]
    if len(query) < 2:
        return app.jsonify(results=[])
    
    q_ = parse_search_string_return_q(query, ["title",])
    me = current_user._get_current_object()
    topics = PrivateMessageTopic.objects(q_, participating_users=me)
    results = [{"text": unicode(t.title), "id": str(t.pk)} for t in topics]
    return app.jsonify(results=results)
    
@app.route('/search', methods=['POST',])
@login_required
def search_lookup():
    request_json = request.get_json(force=True)
    
    try:
        start_date = arrow.get(request_json.get("start_date",""), ["M/D/YY",]).datetime
    except:
        start_date = False
        
    try: # created
        end_date = arrow.get(request_json.get("start_date",""), ["M/D/YY",]).datetime
    except:
        end_date = False
        
    try: # category
        categories = Category.objects(pk__in=request_json.get("categories",[]))
    except:
        categories = []
        
    try:
        if content_type == "posts":
            topics = Topic.objects(pk__in=request_json.get("topics",[]))
        elif content_type == "messages":
            topics = PrivateMessageTopic.objects(pk__in=request_json.get("topics",[]))
    except:
        topics = []
        
    try:
        authors = User.objects(pk__in=request_json.get("authors",[]))
    except:
        authors = []
        
    query = request.args.get("q", "")[0:300]
    pagination = 20
    try:
        page = int(request_json.get("page", 0))
    except:
        page = 1
        
    content_type = request_json.get("content_type", "topics")
    _q_objects = Q()

    if start_date:
        _q_objects = _q_objects & Q(created__gte=start_date)

    if end_date:
        _q_objects = _q_objects & Q(created__lte=start_date)

    if categories and content_type == "topics":
        _q_objects = _q_objects & Q(category__in=categories)

    if categories and content_type == "posts":
        _q_objects = _q_objects & Q(topic__category__in=categories)
        
    if topics:
        _q_objects = _q_objects & Q(topic__in=topics)
        
    if authors and content_type == "posts":
        _q_objects = _q_objects & Q(author__in=authors)
    if authors and content_type == "topics":
        _q_objects = _q_objects & Q(creator__in=authors)
    if authors and content_type == "messages":
        _q_objects = _q_objects & Q(author__in=authors)
    if authors and content_type == "status":
        _q_objects = _q_objects & Q(author__in=authors)

    parsed_results = []
    if content_type == "posts":
        _q_objects = _q_objects & parse_search_string_return_q(query, ["html",])
        results = Post.objects(_q_objects)[(page-1)*pagination:pagination*page]
        for result in results:
            parsed_result["time"] = humanize_time(result.created)
            parsed_result["title"] = result.topic.title
            parsed_result["url"] = "/topic/"+result.topic.slug # TODO : Direct links to posts.
            parsed_result["description"] = result.html
            parsed_result["author_profile_link"] = result.author.login_name
            parsed_result["author_name"] = result.author.display_name
            parsed_results.append(parsed_result)
    elif content_type == "topics":
        _q_objects = _q_objects &  parse_search_string_return_q(query, ["title",])
        results = Topic.objects(_q_objects)[(page-1)*pagination:pagination*page]
        for result in results:
            parsed_result["time"] = humanize_time(result.created)
            parsed_result["title"] = result.title
            parsed_result["url"] = "/topic/"+result.topic.slug
            parsed_result["description"] = ""
            parsed_result["author_profile_link"] = result.creator.login_name
            parsed_result["author_name"] = result.creator.display_name
            parsed_results.append(parsed_result)
    elif content_type == "status":
        _q_objects = _q_objects &  parse_search_string_return_q(query, ["message",])
        results = StatusUpdate.objects(_q_objects)[(page-1)*pagination:pagination*page]
        for result in results:
            parsed_result["time"] = humanize_time(result.created)
            parsed_result["title"] = result.message
            parsed_result["description"] = ""
            parsed_result["url"] = "/status/"+result.pk
            parsed_result["author_profile_link"] = result.author.login_name
            parsed_result["author_name"] = result.author.display_name
            parsed_results.append(parsed_result)
    elif content_type == "messages":
        _q_objects = _q_objects &  parse_search_string_return_q(query, ["topic_name","message",])
        results = PrivateMessage.objects(_q_objects)[(page-1)*pagination:pagination*page]
        for result in results:
            parsed_result["time"] = humanize_time(result.created)
            parsed_result["title"] = result.topic.title
            parsed_result["description"] = result.message
            parsed_result["url"] = "/messages/"+result.topic.pk
            parsed_result["author_profile_link"] = result.author.login_name
            parsed_result["author_name"] = result.author.display_name
            parsed_results.append(parsed_result)
    
    print parsed_results

@app.route('/search', methods=['GET',])
@login_required
def search_display():
    return render_template("core/search.jade")

@app.route('/status-updates', methods=['GET', 'POST'])
@login_required
def status_update_index():
    count = session.get("count", 10)
    authors = session.get("authors", [])
    search = session.get("search", "")
    
    if request.method == 'POST':
        request_json = request.get_json(force=True)
        
        try:
            count = int(request_json.get("count"), 10)
            if count > 1000:
                count = 1000
            session["count"] = count
        except:
            pass
            
        try:
            authors = request_json.get("authors", [])
            session["authors"] = authors
        except:
            pass
            
        try:
            search = request_json.get("search", "")[0:100]
            session["search"] = search
        except:
            pass
    
    query = {}
    
    try:
        users = User.objects(pk__in=authors)  
        authors = [{"id": unicode(u.pk), "text": u.display_name} for u in users]
    except:
        users = []
        authors = []
    
    user_q_ = Q()
    if len(users) > 0:
        user_q_ = Q(author__in=list(users))
    
    search_q_ = Q()
    if search != "":
        search_q_ = parse_search_string_return_q(search, ["message",])
        
    status_updates = StatusUpdate.objects(user_q_ & search_q_)[:count]
    
    if request.method == 'POST':
        parsed_statuses = []
        for status in status_updates:
            parsed_status = status.to_mongo().to_dict()
            parsed_status["profile_address"] = url_for('view_profile', login_name=status.author.login_name)
            parsed_status["user_name"] = status.author.display_name
            parsed_status["message"] = status.message
            if status.old_ipb_id != None:
                parsed_status["ipb"] = True
            else:
                parsed_status["ipb"] = False
            parsed_status["user_avatar"] = status.author.get_avatar_url("40")
            if status.attached_to_user != None:
                parsed_status["attached_to_user"] = status.attached_to_user.display_name
                parsed_status["attached_to_user_url"] = url_for('view_profile', login_name=status.attached_to_user.login_name)
            else:
                parsed_status["attached_to_user"] = False
            parsed_status["user_avatar_x"] = status.author.avatar_40_x
            parsed_status["user_avatar_y"] = status.author.avatar_40_y
            parsed_status["created"] = humanize_time(status.created)
            parsed_status["comment_count"] = status.get_comment_count()
            del parsed_status["comments"]
            parsed_statuses.append(parsed_status)
        return app.jsonify(status_updates=parsed_statuses)
    else:
        return render_template("core/status_index.jade", status_updates=status_updates, count=count, search=search, authors=json.dumps(authors))

@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, app.settings_file.get("robots-alt", request.path[1:]))

@app.route('/create-status', methods=['POST'])
@login_required
def create_new_status():
    request_json = request.get_json(force=True)
        
    status = StatusUpdate()
    status.author = current_user._get_current_object()
    status.author_name = current_user._get_current_object().login_name

    if len(request_json.get("message", "")) == 0:
        return app.jsonify(error="Your status update is empty.")
    
    cleaner = ForumHTMLCleaner()
    try:
        _html = cleaner.clean(request_json.get("message", "").strip())
    except:
        return abort(500)
        
    status.message = _html
    status.participants.append(status.author)
    status.created = arrow.utcnow().datetime
    status.save()
    
    return app.jsonify(url="/status/"+unicode(status.pk))

@app.route('/status/<status>/hide-reply/<idx>', methods=['POST'])
@login_required
def status_hide_reply(status, idx):
    try:
        status = StatusUpdate.objects(id=status)[0]
    except:
        return abort(404)
        
    if current_user._get_current_object() != status.author:
        return abort(404)
    
    try:
        status.comments[int(idx)].hidden = True
        status.save()
    except:
        pass
        
    return app.jsonify(success=True)
    
@app.route('/status/<status>/toggle-silence/<user>', methods=['POST'])
@login_required
def toggle_status_blocking(status, user):
    try:
        status = StatusUpdate.objects(id=status)[0]
        user = User.objects(id=user)[0]
    except:
        return abort(404)
         
    if current_user._get_current_object() != status.author:
        if (current_user._get_current_object().is_admin != True or current_user._get_current_object().is_mod != True):
            return abort(404)
        
    if user == current_user._get_current_object():
        return abort(404)
        
    if not user in status.blocked:
        status.update(add_to_set__blocked=user)
    else:
        try:
            status.blocked.remove(user)
        except:
            pass
        status.save()
    
    return app.jsonify(url="/status/"+unicode(status.pk))

@app.route('/status/<status>/toggle-ignore', methods=['POST'])
@login_required
def toggle_status_ignoring(status):
    try:
        status = StatusUpdate.objects(id=status)[0]
    except:
        return abort(404)
    
    if not current_user._get_current_object() in status.ignoring:
        status.update(add_to_set__ignoring=current_user._get_current_object())
    else:
        try:
            status.ignoring.remove(current_user._get_current_object())
        except:
            pass
        status.save()
    
    return app.jsonify(url="/status/"+unicode(status.pk))

@app.route('/status/<status>/toggle-hidden', methods=['POST'])
@login_required
def toggle_status_hide(status):
    try:
        status = StatusUpdate.objects(id=status)[0]
    except:
        return abort(404)
        
    if current_user._get_current_object().is_admin != True or current_user._get_current_object().is_mod != True:
        return abort(404)
        
    status.update(hidden=not status.hidden)
    return app.jsonify(url="/status/"+unicode(status.pk))
    
@app.route('/status/<status>/toggle-mute', methods=['POST'])
@login_required
def toggle_status_mute(status):
    try:
        status = StatusUpdate.objects(id=status)[0]
    except:
        return abort(404)
                
    if current_user._get_current_object() != status.author or current_user._get_current_object().is_admin != True or current_user._get_current_object().is_mod != True:
        return abort(404)
        
    status.update(muted=not status.muted)
    return app.jsonify(url="/status/"+unicode(status.pk))

@app.route('/status/<status>/toggle-lock', methods=['POST'])
@login_required
def toggle_status_lock(status):
    try:
        status = StatusUpdate.objects(id=status)[0]
    except:
        return abort(404)
        
    if current_user._get_current_object().is_admin != True or current_user._get_current_object().is_mod != True:
        return abort(404)
        
    status.update(locked=not status.locked)
    return app.jsonify(url="/status/"+unicode(status.pk))

@app.route('/status/<status>/reply', methods=['POST'])
@login_required
def make_status_update_reply(status):
    try:
        status = StatusUpdate.objects(id=status)[0]
    except:
        return abort(404)
        
    if status.hidden == True and (current_user._get_current_object().is_admin != True or current_user._get_current_object().is_mod != True):
        return abort(404)
        
    if status.muted and current_user._get_current_object() != status.author:
        return app.jsonify(error="This status update is silenced. Shhh!")
    
    if not (current_user._get_current_object().is_admin or current_user._get_current_object().is_mod) and (current_user._get_current_object() in status.blocked):
        return app.jsonify(error="You have been blocked from this status update.")
        
    if status.locked:
        return app.jsonify(error="This status update is locked.")
        
    if status.get_comment_count() > 99:
        return app.jsonify(error="This status update is full!")
        
    request_json = request.get_json(force=True)

    cleaner = ForumHTMLCleaner()
    try:
        _html = cleaner.clean(request_json.get("reply", ""))
    except:
        return abort(500)
        
    sc = StatusComment()
    sc.text = _html
    sc.author = current_user._get_current_object()
    sc.created = arrow.utcnow().datetime
    status.comments.append(sc)
    status.replies = status.get_comment_count()
    status.last_replied = arrow.utcnow().datetime
    status.save()
    
    if not current_user._get_current_object() in status.participants:
        status.update(add_to_set__participants=current_user._get_current_object())
        
    clean_html_parser = ForumPostParser()
    parsed_reply = sc.to_mongo().to_dict()
    parsed_reply["user_name"] = sc.author.display_name
    parsed_reply["user_avatar"] = sc.author.get_avatar_url("40")
    parsed_reply["user_avatar_x"] = sc.author.avatar_40_x
    parsed_reply["user_avatar_y"] = sc.author.avatar_40_y
    parsed_reply["time"] = humanize_time(sc.created)
    
    return app.jsonify(newest_reply=parsed_reply, count=status.get_comment_count(), success=True)

@app.route('/status/<status>/replies', methods=['GET'])
@login_required
def status_update_replies(status):
    try:
        status = StatusUpdate.objects(id=status)[0]
    except:
        return abort(404)
        
    if status.hidden == True and (current_user._get_current_object().is_admin != True or current_user._get_current_object().is_mod != True):
        return abort(404)
        
    replies = []
    idx = 0
    for reply in status.comments:
        parsed_reply = reply.to_mongo().to_dict()
        parsed_reply["user_name"] = reply.author.display_name
        parsed_reply["user_avatar"] = reply.author.get_avatar_url("40")
        parsed_reply["user_avatar_x"] = reply.author.avatar_40_x
        parsed_reply["user_avatar_y"] = reply.author.avatar_40_y
        parsed_reply["time"] = humanize_time(reply.created)
        parsed_reply["idx"] = idx
        replies.append(parsed_reply)
        idx+=1
        
    return app.jsonify(replies=replies, count=status.get_comment_count())

@app.route('/status/<status>', methods=['GET'])
@login_required
def display_status_update(status):
    print status
    
    try:
        status = StatusUpdate.objects(id=status)[0]
    except:
        return abort(404)
        
    if status.hidden == True and (current_user._get_current_object().is_admin != True or current_user._get_current_object().is_mod != True):
        return abort(404)
        
    if current_user._get_current_object().is_admin == True:
        mod = True
    else:
        mod = False
        
    status.update(last_viewed=arrow.utcnow().datetime)
    
    # has_viewed = False
    # for viewer in status.viewing:
    #     if viewer.user == current_user._get_current_object():
    #         viewer.last_seen = arrow.utcnow().datetime
    #         has_viewed = True
    #
    # if has_viewed == False:
    #     status.viewing.append(StatusViewer(user=current_user._get_current_object(), last_seen=arrow.utcnow().datetime))
        
    status.save()
            
    return render_template("status_update.jade", status=status, mod=mod)


@login_manager.user_loader
def load_user(login_name):
    try:
        user = User.objects(login_name=login_name)[0]
        user.update(last_seen=arrow.utcnow().datetime)
        return user
    except IndexError:
        return None

@app.route('/hello/<pk>')
def confirm_register(pk):
    user = User.objects(pk=pk)[0]
    return render_template("welcome_new_user.jade", profile=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(csrf_enabled=False)
    if form.validate_on_submit():
        new_user = User(
            login_name = form.username.data.strip().lower(),
            display_name = form.username.data.strip(),
            email_address = form.email.data.strip().lower()
        )
        new_user.set_password(form.password.data.strip())
        new_user.joined = arrow.utcnow().datetime
        new_user.save()
        
        # Todo : Notify Admin Users
        
        return redirect('/hello/'+str(new_user.pk))
    
    return render_template("register.jade", form=form)

@app.route('/sign-in', methods=['GET', 'POST'])
def sign_in():
    form = LoginForm(csrf_enabled=False)
    if form.validate_on_submit():
        login_user(form.user)
        # TODO - get fingerprint
        return redirect('/')
        
    return render_template("sign_in.jade", form=form)
    
@app.route('/sign-out', methods=['POST'])
def sign_out():
    logout_user()
    return redirect('/')
    
@app.route('/user-list-api', methods=['GET'])
@login_required
def user_list_api():
    query = request.args.get("q", "")[0:100]
    if len(query) < 2:
        return app.jsonify(results=[])
    results = [{"text": unicode(u.display_name), "id": str(u.pk)} for u in User.objects(Q(display_name__icontains=query) | Q(login_name__icontains=query))]
    return app.jsonify(results=results)