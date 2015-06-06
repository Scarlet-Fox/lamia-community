from woe import app
from woe.models.core import PrivateMessageTopic, PrivateMessageParticipant, User, PrivateMessage
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session
from flask.ext.login import login_user, logout_user, current_user, login_required
import arrow, time
from woe.utilities import get_top_frequences, scrub_json, humanize_time, ForumPostParser, ForumHTMLCleaner



@app.route('/messages/<pk>', methods=['GET'], defaults={'page': 1})
@app.route('/messages/<pk>/page/<page>', methods=['GET'])
def message_index(pk, page):
    try:
        topic = PrivateMessageTopic.objects(pk=pk)[0]
    except IndexError:
        return abort(404)
    
    if not current_user._get_current_object() in topic.participating_users:
        return abort(404)
        
    try:
        page = int(page)
    except:
        page = 1

    return render_template("core/messages_topic.jade", topic=topic, initial_page=page,)

@app.route('/new-message', methods=['POST'])
@login_required
def create_message():
    request_json = request.get_json(force=True)
    print request_json

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

        
@app.route('/new-message', methods=['GET'])
@login_required
def create_message_index():
    return render_template("core/new_message.jade")

@app.route('/message-topics', methods=['POST'])
@login_required
def messages_topics():
    print time.time()
    request_json = request.get_json(force=True)
    page = request_json.get("page", 1)
    pagination = request_json.get("pagination", 20)

    try:
        minimum = (int(page)-1)*int(pagination)
        maximum = int(page)*int(pagination)
    except:
        minimum = 0
        maximum = 20
        
    messages = PrivateMessageTopic.objects(participating_users=current_user._get_current_object()).order_by("-last_reply_time").select_related(0)[minimum:maximum+10]
    print time.time()
    parsed_messages = []
    
    for message in messages:
        participating = False
        for participant in message.participants:
            if participant.user == current_user._get_current_object():
                if not participant.left_pm and not participant.blocked:
                    participating = True
            
        if not participating:
            continue
            
        _parsed = message.to_mongo().to_dict()
        _parsed["creator"] = message.creator.display_name
        _parsed["created"] = humanize_time(message.created, "MMM D YYYY")
        
        _parsed["last_post_date"] = humanize_time(message.last_reply_time)
        _parsed["last_post_by"] = message.last_reply_by.display_name
        _parsed["last_post_x"] = message.last_reply_by.avatar_40_x
        _parsed["last_post_y"] = message.last_reply_by.avatar_40_y
        _parsed["last_post_by_login_name"] = message.last_reply_by.login_name
        _parsed["last_post_author_avatar"] = message.last_reply_by.get_avatar_url("40")
        _parsed["post_count"] = "{:,}".format(message.message_count)
        try:
            _parsed["last_page"] = float(message.message_count)/float(pagination)
        except:
            _parsed["last_page"] = 1
        _parsed["last_pages"] = _parsed["last_page"] > 1
        del _parsed["participants"]
        parsed_messages.append(_parsed)
    print time.time()
        
    return app.jsonify(topics=parsed_messages[minimum:maximum], count=len(parsed_messages))

@app.route('/messages', methods=['GET'])
@login_required
def messages_index():
    return render_template("core/messages.jade")
