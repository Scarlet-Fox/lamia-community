from woe import login_manager
from woe import app
from woe.models.core import User, DisplayNameHistory, StatusUpdate, StatusComment, StatusViewer, PrivateMessage, PrivateMessageTopic, ForumPostParser, Attachment
from woe.models.forum import Category, Post, Topic
from collections import OrderedDict
from woe.forms.core import LoginForm, RegistrationForm
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session, send_from_directory
from flask.ext.login import login_user, logout_user, login_required, current_user
from woe.utilities import get_top_frequences, scrub_json, humanize_time, ForumHTMLCleaner, parse_search_string_return_q
from mongoengine.queryset import Q
from wand.image import Image
from werkzeug import secure_filename
import arrow, mimetypes, json, os, hashlib, time
from woe.views.dashboard import broadcast

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
  
@app.route('/attach', methods=['POST',])
@login_required
def create_attachment():
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        image = Image(file=file)
        img_bin = image.make_blob()
        img_hash = hashlib.sha256(img_bin).hexdigest()
        
        try:
            attach = Attachment.objects(file_hash=img_hash)[0]
            return app.jsonify(attachment=str(attach.pk), xsize=attach.x_size)
        except:
            pass                
        
        attach = Attachment()
        attach.extension = filename.split(".")[-1]
        attach.x_size = image.width
        attach.y_size = image.height
        attach.mimetype = mimetypes.guess_type(filename)[0]
        attach.size_in_bytes = len(img_bin)
        attach.owner_name = current_user._get_current_object().login_name
        attach.owner = current_user._get_current_object()
        attach.alt = filename
        attach.used_in = 0
        attach.created_date = arrow.utcnow().datetime
        attach.file_hash = img_hash
        attach.linked = False
        upload_path = os.path.join(os.getcwd(), "woe/static/uploads", str(time.time())+"_"+str(current_user.pk)+filename)
        attach.path = str(time.time())+"_"+str(current_user.pk)+filename
        attach.save()
        image.save(filename=upload_path)
        return app.jsonify(attachment=str(attach.pk), xsize=attach.x_size)
    else:
        return abort(404)
          
@app.route('/search', methods=['POST',])
@login_required
def search_lookup():
    request_json = request.get_json(force=True)
    content_type = request_json.get("content_type", "topics")
    session["content_type"] = content_type
    
    try:
        start_date = arrow.get(request_json.get("start_date",""), ["M/D/YY",]).datetime
        session["start_date"] = request_json.get("start_date","")
    except:
        start_date = False
        session["start_date"] = ""
        
    try: # created
        end_date = arrow.get(request_json.get("end_date",""), ["M/D/YY",]).datetime
        session["end_date"] = request_json.get("end_date","")
    except:
        end_date = False
        session["end_date"] = ""
        
    try: # category
        categories = list(Category.objects(pk__in=request_json.get("categories")))
        session["categories"] = categories
    except:
        categories = []
        session["categories"] = []
        
    try:
        if content_type == "posts":
            topics = list(Topic.objects(pk__in=request_json.get("topics")))
        elif content_type == "messages":
            topics = list(PrivateMessageTopic.objects(pk__in=request_json.get("topics")))
        session["topics"] = topics
    except:
        topics = []
        session["topics"] = []
        
    try:
        authors = list(User.objects(pk__in=request_json.get("authors",[])))
        session["authors"] = authors
    except:
        authors = []
        session["authors"] = []
        
    query = request_json.get("q", "")[0:300]
    session["query"] = query
    pagination = 20
    try:
        page = int(request_json.get("page", 1))
    except:
        page = 1
        
    _q_objects = Q()

    if start_date:
        _q_objects = _q_objects & Q(created__gte=start_date)

    if end_date:
        _q_objects = _q_objects & Q(created__lte=end_date)

    if categories and content_type == "topics":
        _q_objects = _q_objects & Q(category__in=categories)
        
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
        count = Post.objects(_q_objects).count()
        results = Post.objects(_q_objects, hidden=False).order_by("-created")[(page-1)*pagination:pagination*page]
        for result in results:
            parsed_result = {}
            parsed_result["time"] = humanize_time(result.created)
            parsed_result["title"] = result.topic.title
            parsed_result["url"] = "/t/"+str(result.topic.slug)+"/page/1/post/"+str(result.pk)
            parsed_result["description"] = result.html
            parsed_result["author_profile_link"] = result.author.login_name
            parsed_result["author_name"] = result.author.display_name
            parsed_result["readmore"] = True
            parsed_results.append(parsed_result)
    elif content_type == "topics":
        _q_objects = _q_objects &  parse_search_string_return_q(query, ["title",])
        count = Topic.objects(_q_objects).count()
        results = Topic.objects(_q_objects, hidden=False).order_by("-created")[(page-1)*pagination:pagination*page]
        for result in results:
            parsed_result = {}
            parsed_result["time"] = humanize_time(result.created)
            parsed_result["title"] = result.title
            parsed_result["url"] = "/t/"+result.slug
            parsed_result["description"] = ""
            parsed_result["author_profile_link"] = result.creator.login_name
            parsed_result["author_name"] = result.creator.display_name
            parsed_result["readmore"] = False
            parsed_results.append(parsed_result)
    elif content_type == "status":
        _q_objects = _q_objects &  parse_search_string_return_q(query, ["message",])
        count = StatusUpdate.objects(_q_objects).count()
        results = StatusUpdate.objects(_q_objects, hidden=False).order_by("-created")[(page-1)*pagination:pagination*page]
        for result in results:
            parsed_result = {}
            parsed_result["time"] = humanize_time(result.created)
            parsed_result["title"] = result.message
            parsed_result["description"] = ""
            parsed_result["url"] = "/status/"+str(result.pk)
            parsed_result["author_profile_link"] = result.author.login_name
            parsed_result["author_name"] = result.author.display_name
            parsed_result["readmore"] = False
            parsed_results.append(parsed_result)
    elif content_type == "messages":
        my_message_topics = PrivateMessageTopic.objects(participating_users=current_user._get_current_object())
        _q_objects = _q_objects & (parse_search_string_return_q(query, ["topic_name",]) | parse_search_string_return_q(query, ["message",]))
        _q_objects = _q_objects & Q(topic__in=my_message_topics)
        count = PrivateMessage.objects(_q_objects).count()
        results = PrivateMessage.objects(_q_objects).order_by("-created")[(page-1)*pagination:pagination*page]
        for result in results:
            parsed_result = {}
            parsed_result["time"] = humanize_time(result.created)
            parsed_result["title"] = result.topic.title
            parsed_result["description"] = result.message
            parsed_result["url"] = "/messages/"+str(result.topic.pk)+"/page/1/post/"+str(result.pk)
            parsed_result["author_profile_link"] = result.author.login_name
            parsed_result["author_name"] = result.author.display_name
            parsed_result["readmore"] = True
            parsed_results.append(parsed_result)
    
    # for term in query.split(" "):
    #     term = term.strip()
    #     if term[0] == "-":
    #         continue
    #     term_re = re.compile(re.escape(term), re.IGNORECASE)
    #
    #     for result in parsed_results:
    #         result["description"] = term_re.sub("""<span style="background-color: yellow">"""+term+"</span>", result["description"])
    
    return app.jsonify(results=parsed_results, count=count, pagination=pagination)

@app.route('/search', methods=['GET',])
@login_required
def search_display():
    start_date = session.get("start_date","")
    end_date = session.get("end_date", "")
    categories = [{"id": unicode(c.pk), "text": c.name} for c in session.get("categories", [])]
    topics = [{"id": unicode(t.pk), "text": t.title} for t in session.get("topics", [])]
    if session.get("authors"):
        authors = [{"id": unicode(a.pk), "text": a.display_name} for a in session.get("authors", [])]
    else:
        authors = []
    query = session.get("query","")
    content_type = session.get("content_type","posts")
    return render_template("core/search.jade", 
        query=query, 
        content_type=content_type,
        start_date=start_date,
        end_date=end_date,
        categories=json.dumps(categories),
        topics=json.dumps(topics),
        authors=json.dumps(authors),
        page_title="Search - World of Equestria"
        )

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
        return render_template("core/status_index.jade", page_title="Status Updates - World of Equestria", status_updates=status_updates, count=count, search=search, authors=json.dumps(authors))

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
        _html = cleaner.escape(request_json.get("message", "").strip())
    except:
        return abort(500)
    
    try:
        users_last_status = StatusUpdate.objects(author=current_user._get_current_object()).order_by("-created")[0]
        difference = (arrow.utcnow().datetime - arrow.get(users_last_status.created).datetime).seconds
        if difference < 360:
            return app.jsonify(error="Please wait %s seconds before you create another status update." % (360 - difference))
    except:
        pass
        
    status.message = _html
    status.participants.append(status.author)
    status.created = arrow.utcnow().datetime
    status.save()
    
    send_notify_to_users = []
    for user in status.author.followed_by:
        if user not in status.author.ignored_users:
            send_notify_to_users.append(user)

    broadcast(
      to=send_notify_to_users,
      category="user_activity", 
      url="/status/"+unicode(status.pk),
      title="%s created a status update." % (unicode(status.author.display_name),),
      description=status.message, 
      content=status, 
      author=status.author
      )
    
    return app.jsonify(url="/status/"+unicode(status.pk))

@app.route('/status/<status>/hide-reply/<idx>', methods=['POST'])
@login_required
def status_hide_reply(status, idx):
    try:
        status = StatusUpdate.objects(id=status)[0]
    except:
        return abort(404)
        
    if current_user._get_current_object() != status.author and (current_user._get_current_object().is_admin != True or current_user._get_current_object().is_mod != True):
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
        
    if not status.hidden:
        if current_user._get_current_object() != status.author:
            broadcast(
                to=[status.author,], 
                category="status", 
                url="/status/"+str(status.pk),
                title="Status update hidden.",
                description=status.message, 
                content=status, 
                author=current_user._get_current_object()
                )
            
        broadcast(
            to=list(User.objects(is_admin=True)), 
            category="mod", 
            url="/status/"+str(status.pk),
            title="%s's status update hidden." % (unicode(status.author.display_name),),
            description=status.message, 
            content=status, 
            author=current_user._get_current_object()
            )
        
    status.update(hidden=not status.hidden)
    return app.jsonify(url="/status/"+unicode(status.pk))
    
@app.route('/status/<status>/toggle-mute', methods=['POST'])
@login_required
def toggle_status_mute(status):
    try:
        status = StatusUpdate.objects(id=status)[0]
    except:
        return abort(404)
                
    if current_user._get_current_object() != status.author and (current_user._get_current_object().is_admin != True or current_user._get_current_object().is_mod != True):
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
        _html = cleaner.escape(request_json.get("reply", ""))
    except:
        return abort(500)
    
    user_last_comment = False
    for comment in status.comments:
        if comment.author == current_user._get_current_object():
            user_last_comment = comment
    if user_last_comment:
        difference = (arrow.utcnow().datetime - arrow.get(user_last_comment.created).datetime).seconds
        if difference < 5:
            return app.jsonify(error="Please wait %s seconds before you can reply again." % (5 - difference))
    
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
    
    send_notify_to_users = []
    for user in status.participants:
        if user == current_user._get_current_object():
            continue
            
        if user in status.ignoring:
            continue
            
        if user == status.author:
            continue
            
        send_notify_to_users.append(user)
        
    broadcast(
        to=send_notify_to_users, 
        category="status", 
        url="/status/"+str(status.pk),
        title="Reply to %s's Status Update" % (unicode(status.author.display_name),),
        description=status.message, 
        content=status, 
        author=current_user._get_current_object()
        )
        
    if current_user._get_current_object() != status.author and current_user._get_current_object() not in status.ignoring:
        broadcast(
            to=[status.author], 
            category="status", 
            url="/status/"+str(status.pk),
            title="Reply to Your Status Update",
            description=status.message, 
            content=status, 
            author=current_user._get_current_object()
            )    
            
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
            
    return render_template("status_update.jade", page_title="%s - World of Equestria" % unicode(status.message), status=status, mod=mod)

@login_manager.user_loader
def load_user(login_name):
    try:
        user = User.objects(login_name=login_name)[0]
        user.update(last_seen=arrow.utcnow().datetime)
        if user.validated and not user.banned:
            return user
        else:
            return None
    except IndexError:
        return None

@app.route('/hello/<pk>')
def confirm_register(pk):
    user = User.objects(pk=pk)[0]
    return render_template("welcome_new_user.jade", page_title="Welcome! - World of Equestria", profile=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated():
        return abort(404)
    
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
        
        broadcast(
            to=User.objects(is_admin=True),
            category="mod", 
            url="/member/"+unicode(new_user.login_name),
            title="%s has joined the forum. Please review and approve/ban (go to /admin/)." % (unicode(new_user.display_name),),
            description="", 
            content=new_user, 
            author=new_user
            )
            
        broadcast(
            to=User.objects(banned=False, login_name__ne=new_user.login_name, last_seen__gte=arrow.utcnow().replace(hours=-24).datetime),
            category="new_member", 
            url="/member/"+unicode(new_user.login_name),
            title="%s has joined the forum! Greet them!" % (unicode(new_user.display_name),),
            description="", 
            content=new_user, 
            author=new_user
            )

        broadcast(
            to=[new_user,],
            category="new_member", 
            url="/category/welcome-mat",
            title="Welcome to World of Equestria! Click here to introduce yourself!",
            description="", 
            content=new_user, 
            author=new_user
            )

        broadcast(
            to=[new_user,],
            category="new_member", 
            url="/t/community-rules-and-terms",
            title="Make sure to read the rules.",
            description="", 
            content=new_user, 
            author=new_user
            )

        return redirect('/hello/'+str(new_user.pk))
    
    return render_template("register.jade", page_title="Become One of Us - World of Equestria", form=form)

@app.route('/sign-in', methods=['GET', 'POST'])
def sign_in():
    if current_user.is_authenticated():
        return abort(404)
        
    form = LoginForm(csrf_enabled=False)
    if form.validate_on_submit():
        login_user(form.user)
        # TODO - get fingerprint
        return redirect('/')
        
    return render_template("sign_in.jade", page_title="Sign In - World of Equestria", form=form)
    
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