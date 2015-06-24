from woe import app
from woe.models.core import User, PrivateMessage, PrivateMessageTopic, StatusUpdate
from woe.models.forum import Category, Post, Topic
from flask import request, render_template, session
from flask.ext.login import current_user, login_required
from woe.utilities import humanize_time, parse_search_string_return_q
from mongoengine.queryset import Q
import arrow, json
import HTMLParser

@app.route('/search', methods=['GET',])
@login_required
def search_display():
    start_date = session.get("start_date","")
    end_date = session.get("end_date", "")
    categories = [{"id": unicode(c.pk), "text": c.name} for c in session.get("categories", [])]
    topics = [{"id": unicode(t.pk), "text": t.title} for t in session.get("topics", [])]
    if session.get("search_authors"):
        authors = [{"id": unicode(a.pk), "text": a.display_name} for a in session.get("search_authors", [])]
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
        session["search_authors"] = authors
    except:
        authors = []
        session["search_authors"] = []
        
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
