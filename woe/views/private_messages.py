from woe import app
from woe.models.core import PrivateMessageTopic, PrivateMessageParticipant, User, PrivateMessage, ForumPostParser
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session
from flask.ext.login import login_user, logout_user, current_user, login_required
import arrow, time, math
from woe.utilities import get_top_frequences, scrub_json, humanize_time, ForumHTMLCleaner
from woe.views.dashboard import broadcast

@app.route('/messages/<pk>/edit-post/<post>', methods=['GET'])
@login_required
def get_post_html_in_pm_topic(pk, post):
    try:
        topic = PrivateMessageTopic.objects(pk=pk)[0]
    except IndexError:
        return abort(404)

    try:
        post = PrivateMessage.objects(topic=topic, pk=post)[0]
    except:
        return abort(404)
        
    return json.jsonify(content=post.message)

@app.route('/messages/<pk>/kick-from-topic/<upk>', methods=['POST'])
@login_required
def kick_from_pm_topic(pk, upk):
    try:
        topic = PrivateMessageTopic.objects(pk=pk)[0]
    except IndexError:
        return abort(404)
        
    if not current_user._get_current_object() in topic.participating_users or not current_user._get_current_object() == topic.creator:
        return abort(404)
        
    try:
        target_user = User.objects(pk=upk)[0]
    except:
        return abort(404)
        
    topic.update(add_to_set__users_left_pm=target_user)
    topic.update(add_to_set__blocked_users=target_user)
    
    return json.jsonify(url='/messages/'+str(topic.pk))

@app.route('/messages/<pk>/leave-topic', methods=['POST'])
@login_required
def leave_pm_topic(pk):
    try:
        topic = PrivateMessageTopic.objects(pk=pk)[0]
    except IndexError:
        return abort(404)
        
    if not current_user._get_current_object() in topic.participating_users:
        return abort(404)
        
    topic.update(add_to_set__users_left_pm=current_user._get_current_object())
    
    return json.jsonify(url='/messages')

@app.route('/messages/<pk>/edit-post', methods=['POST'])
@login_required
def edit_post_in_pm_topic(pk):
    try:
        topic = PrivateMessageTopic.objects(pk=pk)[0]
    except IndexError:
        return abort(404)
    
    if not current_user._get_current_object() in topic.participating_users:
        return abort(404)

    request_json = request.get_json(force=True)
    
    try:
        message = PrivateMessage.objects(topic=topic, pk=request_json.get("pk"))[0]
    except IndexError:
        return abort(404)
        
    if current_user._get_current_object() != message.author:
        return abort(404)

    if request_json.get("text", "").strip() == "":
        return app.jsonify(error="Your post is empty.")
        
    cleaner = ForumHTMLCleaner()
    try:
        post_html = cleaner.clean(request_json.get("post", ""))
    except:
        return abort(500)
        
    message.message = post_html
    message.modified = arrow.utcnow().datetime
    message.save()
    
    clean_html_parser = ForumPostParser()    
    return app.jsonify(html=clean_html_parser.parse(message.message), success=True)

@app.route('/messages/<pk>/new-post', methods=['POST'])
@login_required
def new_message_in_pm_topic(pk):
    try:
        topic = PrivateMessageTopic.objects(pk=pk)[0]
    except IndexError:
        return abort(404)
    
    if not current_user._get_current_object() in topic.participating_users:
        return abort(404)

    request_json = request.get_json(force=True)
    
    if request_json.get("text", "").strip() == "":
        return app.jsonify(error="Your post is empty.")
        
    cleaner = ForumHTMLCleaner()
    try:
        post_html = cleaner.clean(request_json.get("post", ""))
    except:
        return abort(500)
        
    topic.last_reply_by = current_user._get_current_object()
    topic.last_reply_name = current_user._get_current_object().display_name
    topic.last_reply_time = arrow.utcnow().datetime
    topic.message_count = topic.message_count + 1
    topic.save()
    
    message = PrivateMessage()
    message.message = post_html
    message.author = current_user._get_current_object()
    message.created = arrow.utcnow().datetime
    message.author_name = current_user._get_current_object().login_name
    message.topic = topic
    message.topic_name = topic.title
    message.topic_creator_name = topic.creator_name
    message.save()
    
    clean_html_parser = ForumPostParser()
    parsed_post = message.to_mongo().to_dict()
    parsed_post["created"] = humanize_time(message.created, "MMM D YYYY")
    parsed_post["modified"] = humanize_time(message.modified, "MMM D YYYY")
    parsed_post["html"] = clean_html_parser.parse(message.message)
    parsed_post["user_avatar"] = message.author.get_avatar_url()
    parsed_post["user_avatar_x"] = message.author.avatar_full_x
    parsed_post["user_avatar_y"] = message.author.avatar_full_y
    parsed_post["user_avatar_60"] = message.author.get_avatar_url("60")
    parsed_post["user_avatar_x_60"] = message.author.avatar_60_x
    parsed_post["user_avatar_y_60"] = message.author.avatar_60_y
    parsed_post["user_title"] = message.author.title
    parsed_post["author_name"] = message.author.display_name
    parsed_post["author_login_name"] = message.author.login_name
    parsed_post["group_pre_html"] = message.author.group_pre_html
    parsed_post["author_group_name"] = message.author.group_name
    parsed_post["group_post_html"] = message.author.group_post_html    
    post_count = PrivateMessage.objects(topic=topic).count()
    
    notify_users = []
    for u in topic.participating_users:
        if u == message.author:
            continue
        notify_users.append(u)
    
    broadcast(
        to=notify_users,
        category="pm", 
        url="/messages/%s/page/1/post/%s" % (str(topic.pk), str(message.pk)),
        title="%s has replied to %s." % (unicode(message.author.display_name), unicode(topic.title)),
        description=message.message, 
        content=topic, 
        author=message.author
        )
    
    return app.jsonify(newest_post=parsed_post, count=post_count, success=True)    

@app.route('/messages/<pk>/posts', methods=['POST'])
def private_message_posts(pk):
    try:
        topic = PrivateMessageTopic.objects(pk=pk)[0]
    except IndexError:
        return abort(404)
    
    if not current_user._get_current_object() in topic.participating_users:
        return abort(404)

    request_json = request.get_json(force=True)
    
    try:
        pagination = int(request_json.get("pagination", 20))
        page = int(request_json.get("page", 1))
    except:
        pagination = 20
        page = 1
        
    posts = PrivateMessage.objects(topic=topic)[(page-1)*pagination:page*pagination]
    post_count = PrivateMessage.objects(topic=topic).count()
    parsed_posts = []
    
    for post in posts:
        clean_html_parser = ForumPostParser()
        parsed_post = post.to_mongo().to_dict()
        parsed_post["created"] = humanize_time(post.created, "MMM D YYYY")
        parsed_post["modified"] = humanize_time(post.modified, "MMM D YYYY")
        parsed_post["html"] = clean_html_parser.parse(post.message)
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

@app.route('/messages/<pk>', methods=['GET'], defaults={'page': 1, 'post': ""})
@app.route('/messages/<pk>/page/<page>', methods=['GET'], defaults={'post': ""})
@app.route('/messages/<pk>/page/<page>/post/<post>', methods=['GET'])
def message_index(pk, page, post):
    try:
        topic = PrivateMessageTopic.objects(pk=pk)[0]
    except IndexError:
        return abort(404)
    
    if not current_user._get_current_object() in topic.participating_users or current_user._get_current_object() in topic.users_left_pm or current_user._get_current_object() in topic.blocked_users:
        return abort(404)
        
    try:
        page = int(page)
    except:
        page = 1

    if post == "latest_post":
        try:
            post = PrivateMessage.objects(topic=topic).order_by("-created")[0]
        except:
            return abort(404)
    elif post == "last_seen":
        try:
            last_seen = arrow.get(topic.last_seen_by.get(str(current_user._get_current_object().pk), arrow.utcnow().timestamp)).datetime
        except:
            last_seen = arrow.get(arrow.utcnow().timestamp).datetime
        
        try:
            post = PrivateMessage.objects(topic=topic, created__lt=last_seen).order_by("-created")[0]
        except:
            try:
                post = PrivateMessage.objects(topic=topic, pk=post)[0]
            except:
                return abort(404)
    else:
        if post != "":
            try:
                post = PrivateMessage.objects(topic=topic, pk=post)[0]
            except:
                return abort(404)
        else:
            post = ""
     
    pagination = 20
    
    if post != "":
        target_date = post.created
        posts_before_target = PrivateMessage.objects(topic=topic, created__lt=target_date).count()
        page = int(math.floor(float(posts_before_target)/float(pagination)))+1
        return render_template("core/messages_topic.jade", page_title="%s - World of Equestria" % (unicode(topic.title),), topic=topic, initial_page=page, initial_post=str(post.pk))
        
    try:
        topic.last_seen_by[str(current_user._get_current_object().pk)] = arrow.utcnow().timestamp
        topic.save()
    except:
        pass
        
    return render_template("core/messages_topic.jade", page_title="%s - World of Equestria" % (unicode(topic.title),), topic=topic, initial_page=page,)

@app.route('/new-message', methods=['POST'])
@login_required
def create_message():
    request_json = request.get_json(force=True)

    if len(request_json.get("title", "").strip()) == 0:
        return app.jsonify(error="Please enter a title.")

    if request_json.get("text", "").strip() == "":
        return app.jsonify(error="Please enter actual text for your message.")
    
    if request_json.get("to") == None or not len(request_json.get("to", [""])) > 0:
        return app.jsonify(error="Choose who should receive your message.")
    
    participant_users = []
    for user_pk in request_json.get("to"):
        if user_pk == current_user._get_current_object().pk:
            continue 
            
        try:
            u = User.objects(pk=user_pk)[0]
            
            if current_user._get_current_object() in u.ignored_users:
                return app.jsonify(error="You can not send a message to %s." % (u.display_name,))
            
            participant_users.append(u)
        except IndexError:
            continue
            
    if len(participant_users) == 0:
        return app.jsonify(error="Your member list is invalid.")
        
    topic = PrivateMessageTopic()
        
    participant = PrivateMessageParticipant()
    participant.user = current_user._get_current_object()
    participant.last_read = arrow.utcnow().datetime
    topic.participants.append(participant)
    topic.participating_users.append(participant.user)
    
    topic.participating_users.extend(participant_users)
    for _p in participant_users:
        participant = PrivateMessageParticipant()
        participant.user = _p
        topic.participants.append(participant)
    
    topic.title = request_json.get("title", "").strip()
    topic.creator = current_user._get_current_object()
    topic.creator_name = current_user._get_current_object().display_name
    topic.created = arrow.utcnow().datetime
    topic.participant_count = len(topic.participants)
    topic.last_reply_by = current_user._get_current_object()
    topic.last_reply_name = current_user._get_current_object().display_name
    topic.last_reply_time = arrow.utcnow().datetime
    topic.message_count = 1
    topic.save()
    
    message = PrivateMessage()
    message.message = request_json.get("html", "").strip()
    message.author = current_user._get_current_object()
    message.created = arrow.utcnow().datetime
    message.author_name = current_user._get_current_object().login_name
    message.topic = topic
    message.topic_name = topic.title
    message.topic_creator_name = topic.creator_name
    message.save()
    
    broadcast(
        to=topic.participating_users,
        category="pm", 
        url="/messages/"+str(topic.pk),
        title="New Message: "+unicode(topic.title),
        description=message.message, 
        content=topic, 
        author=message.author
        )
    
    return app.jsonify(url="/messages/"+str(topic.pk))
        
@app.route('/new-message', methods=['GET'])
@login_required
def create_message_index():
    return render_template("core/new_message.jade", page_title="New Private Message - World of Equestria")

@app.route('/message-topics', methods=['POST'])
@login_required
def messages_topics():
    request_json = request.get_json(force=True)
    page = request_json.get("page", 1)
    pagination = request_json.get("pagination", 20)

    try:
        minimum = (int(page)-1)*int(pagination)
        maximum = int(page)*int(pagination)
    except:
        minimum = 0
        maximum = 20
        
    messages = PrivateMessageTopic.objects(participating_users=current_user._get_current_object(), 
        users_left_pm__ne=current_user._get_current_object()
        ).order_by("-last_reply_time").select_related(0)[minimum:maximum+10]
    parsed_messages = []
    
    for message in messages:
        participating = False
        for participant in message.participants:
            if participant.user == current_user._get_current_object():
                if not participant.left_pm and not participant.blocked:
                    participating = True
            
        if not participating:
            continue
            
        try:
            _parsed = message.to_mongo().to_dict()
        except:
            _parsed = {}
        print message
        _parsed["creator"] = message.creator.display_name
        _parsed["created"] = humanize_time(message.created, "MMM D YYYY")
        
        _parsed["last_post_date"] = humanize_time(message.last_reply_time)
        _parsed["last_post_by"] = message.last_reply_by.display_name
        _parsed["last_post_x"] = message.last_reply_by.avatar_40_x
        _parsed["last_post_y"] = message.last_reply_by.avatar_40_y
        _parsed["last_post_by_login_name"] = message.last_reply_by.login_name
        _parsed["last_post_author_avatar"] = message.last_reply_by.get_avatar_url("40")
        _parsed["post_count"] = "{:,}".format(message.message_count)
        _parsed["pk"] = message.pk
        try:
            _parsed["last_page"] = float(message.message_count)/float(pagination)
        except:
            _parsed["last_page"] = 1
        _parsed["last_pages"] = _parsed["last_page"] > 1
        
        try:
            del _parsed["participants"]
        except:
            pass
        parsed_messages.append(_parsed)
        
    return app.jsonify(topics=parsed_messages[minimum:maximum], count=len(parsed_messages))

@app.route('/messages', methods=['GET'])
@login_required
def messages_index():
    return render_template("core/messages.jade", page_title="Your Private Messages - World of Equestria")
