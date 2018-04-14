from woe import app
from flask import request, session, redirect
from flask.ext.login import current_user, login_required
from woe.utilities import humanize_time, parse_search_string_return_q, parse_search_string
from mongoengine.queryset import Q
import arrow, json, pytz
import woe.sqlmodels as sqlm
from woe import sqla
from sqlalchemy_searchable import search
import HTMLParser
from woe.utilities import render_lamia_template as render_template

@app.route('/search', methods=['GET',])
@login_required
def search_display():
    start_date = session.get("start_date","")
    end_date = session.get("end_date", "")
    categories = [{"id": unicode(c["id"]), "text": c["name"]} for c in session.get("categories", [])]
    topics = [{"id": unicode(t["id"]), "text": t["title"]} for t in session.get("topics", [])]
    if session.get("search_authors"):
        authors = [{"id": unicode(a["id"]), "text": a["display_name"]} for a in session.get("search_authors", [])]
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
        page_title="Search - %%GENERIC SITENAME%%"
        )

@app.route('/clear-search', methods=['POST',])
@login_required
def clear_search_lookup():
    session["start_date"] = ""
    session["end_date"] = ""
    session["categories"] = []
    session["topics"] = []
    session["content_type"] = "posts"
    session["search_authors"] = []
    session["query"] = ""

    return app.jsonify(url="/search")

@app.route('/search', methods=['POST',])
@login_required
def search_lookup():
    request_json = request.get_json(force=True)
    content_type = request_json.get("content_type", "posts")
    session["content_type"] = content_type

    try:
        timezone = pytz.timezone(current_user._get_current_object().time_zone)
    except:
        timezone = pytz.timezone("US/Pacific")

    try:
        start_date = arrow.get(request_json.get("start_date",""), ["M/D/YY",])
        offset = timezone.utcoffset(start_date.naive).total_seconds()
        start_date = start_date.replace(seconds=-offset).datetime.replace(tzinfo=None)
        session["start_date"] = request_json.get("start_date","")
    except:
        start_date = False
        session["start_date"] = ""

    try: # created
        end_date = arrow.get(request_json.get("end_date",""), ["M/D/YY",])
        offset = timezone.utcoffset(end_date.naive).total_seconds()
        end_date = end_date.replace(seconds=-offset).replace(hours=24).datetime.replace(tzinfo=None)
        session["end_date"] = request_json.get("end_date","")
    except:
        end_date = False
        session["end_date"] = ""

    try: # category
        categories = list(
                sqla.session.query(sqlm.Category) \
                    .filter(sqlm.Category.id.in_(request_json.get("categories"))) \
                    .all()
            )
        session["categories"] = [{"id": c.id, "name": c.name} for c in categories]
    except:
        categories = []
        session["categories"] = []

    try: # category
        blogs = list(
                sqla.session.query(sqlm.Blog) \
                    .filter(sqlm.Blog.id.in_(request_json.get("blogs"))) \
                    .all()
            )
        # session["categories"] = [{"id": c.id, "name": c.name} for c in categories]
    except:
        blogs = []
        # session["categories"] = []

    try:
        if content_type == "posts":
            topics = list(
                sqla.session.query(sqlm.Topic) \
                    .filter(sqlm.Topic.id.in_(request_json.get("topics"))) \
                    .all()
            )
        elif content_type == "messages":
            topics = list(
                sqla.session.query(sqlm.PrivateMessage) \
                    .filter(sqlm.PrivateMessage.id.in_(request_json.get("topics"))) \
                    .all()
            )
        session["topics"] = [{"id": t.id, "title": t.title} for t in topics]
    except:
        topics = []
        session["topics"] = []

    try:
        authors = list(
                sqla.session.query(sqlm.User) \
                    .filter(sqlm.User.id.in_(request_json.get("authors"))) \
                    .all()
            )
        session["search_authors"] = [{"id": a.id, "display_name": a.display_name} for a in authors]
    except:
        authors = []
        session["search_authors"] = []

    query = request_json.get("q", "")[0:300]
    try:
        session["query"] = query
    except:
        pass

    pagination = 20
    try:
        page = int(request_json.get("page", 1))
    except:
        page = 1

    if content_type == "posts":
        query_ = sqla.session.query(sqlm.Post)
        model_ = sqlm.Post
    elif content_type == "topics":
        query_ = sqla.session.query(sqlm.Topic)
        model_ = sqlm.Topic
    elif content_type == "status":
        query_ = sqla.session.query(sqlm.StatusUpdate)
        model_ = sqlm.StatusUpdate
    elif content_type == "messages":
        query_ = sqla.session.query(sqlm.PrivateMessageReply)
        model_ = sqlm.PrivateMessageReply
    elif content_type == "blogs":
        query_ = sqla.session.query(sqlm.BlogEntry)
        model_ = sqlm.BlogEntry

    if start_date:
        query_ = query_.filter(model_.created >= start_date)

    if end_date:
        query_ = query_.filter(model_.created <= end_date)

    if categories and content_type == "topics":
        query_ = query_.filter(model_.category_id.in_([c.id for c in categories]))

    if blogs and content_type == "blogs":
        query_ = query_.filter(model_.blog_id.in_([b.id for b in blogs]))

    if topics and content_type == "posts":
        query_ = query_.filter(model_.topic_id.in_([t.id for t in topics]))
    if topics and content_type == "messages":
        query_ = query_.filter(model_.pm_id.in_([t.id for t in topics]))

    if authors:
        query_ = query_.filter(model_.author_id.in_([a.id for a in authors]))

    parsed_results = []
    if content_type == "posts":
        if current_user.is_admin:
            query_ = search(query_, query) \
                .join(sqlm.Post.topic) \
                .filter(model_.hidden==False)
        else:
            _cat_perms = current_user.get_category_permission_subquery()
            
            query_ = search(query_, query) \
                .join(sqlm.Post.topic) \
                .join(_cat_perms, _cat_perms.c.category_id == sqlm.Topic.category_id) \
                .filter(_cat_perms.c.category_can_view_topics == True) \
                .filter(model_.hidden==False)
        
        results = query_.order_by(sqla.desc(model_.created)).paginate(page, pagination, False)
        has_next = len(query_.order_by(sqla.desc(model_.created)).paginate(pagination+1, 1, False).items) > 0
        if has_next:
            count = 21
        elif len(results.items) == 0:
            count = 0
        else:
            count = 20
        for result in results.items:
            parsed_result = {}
            parsed_result["time"] = humanize_time(result.created)
            parsed_result["title"] = result.topic.title
            parsed_result["url"] = "/t/"+str(result.topic.slug)+"/page/1/post/"+str(result.id)
            parsed_result["description"] = result.html
            parsed_result["author_profile_link"] = result.author.my_url
            parsed_result["author_name"] = result.author.display_name
            parsed_result["readmore"] = True
            parsed_results.append(parsed_result)
    elif content_type == "topics":
        query_ = parse_search_string(query, model_, query_, ["title",]) \
            .filter(model_.hidden==False)
            
        if not current_user.is_admin:
            _cat_perms = current_user.get_category_permission_subquery()

            query_ = query_ \
                .join(_cat_perms, _cat_perms.c.category_id == sqlm.Topic.category_id) \
                .filter(_cat_perms.c.category_can_view_topics == True)
        
        count = query_.count()
        
        if current_user.is_admin:
            results = query_ \
                .join(sqlm.Topic.recent_post) \
                .order_by(sqla.desc(sqlm.Post.created)).paginate(page, pagination, False)
        else:
            results = query_ \
                .join(sqlm.Topic.recent_post) \
                .order_by(sqla.desc(sqlm.Post.created)).paginate(page, pagination, False)

        for result in results.items:
            parsed_result = {}
            parsed_result["time"] = humanize_time(result.created)
            parsed_result["title"] = result.title
            parsed_result["url"] = "/t/"+result.slug
            parsed_result["description"] = ""
            parsed_result["author_profile_link"] = result.author.my_url
            parsed_result["author_name"] = result.author.display_name
            parsed_result["readmore"] = False
            parsed_results.append(parsed_result)
    elif content_type == "blogs":
        query_ = parse_search_string(query, model_, query_, ["html","title"])
        count = query_.count()

        results = query_ \
            .join(sqlm.BlogEntry.blog) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqlm.BlogEntry.draft.isnot(True)) \
            .filter(sqlm.BlogEntry.published.isnot(None)) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all",
                sqlm.Blog.privacy_setting == "members"
            )) \
            .order_by(sqla.desc(sqlm.BlogEntry.published))[(page-1)*pagination:pagination*page]

        for result in results:
            parsed_result = {}
            parsed_result["time"] = humanize_time(result.created)
            parsed_result["title"] = result.title
            parsed_result["url"] = "/blog/"+unicode(result.blog.slug)+"/e/"+unicode(result.slug)
            parsed_result["description"] = result.html
            parsed_result["author_profile_link"] = result.author.my_url
            parsed_result["author_name"] = result.author.display_name
            parsed_result["readmore"] = True
            parsed_results.append(parsed_result)

    elif content_type == "status":
        query_ = parse_search_string(query, model_, query_, ["message",]).filter(model_.hidden==False)
        count = query_.count()

        results = query_ \
            .order_by(sqla.desc(sqlm.StatusUpdate.created))[(page-1)*pagination:pagination*page]

        for result in results:
            parsed_result = {}
            parsed_result["time"] = humanize_time(result.created)
            parsed_result["title"] = result.message
            parsed_result["description"] = ""
            parsed_result["url"] = "/status/"+str(result.id)
            parsed_result["author_profile_link"] = result.author.my_url
            parsed_result["author_name"] = result.author.display_name
            parsed_result["readmore"] = False
            parsed_results.append(parsed_result)

    elif content_type == "messages":
        query_ = query_.join(sqlm.PrivateMessageUser, sqlm.PrivateMessageUser.pm_id == sqlm.PrivateMessageReply.pm_id) \
            .filter(
                sqlm.PrivateMessageUser.author == current_user._get_current_object(),
                sqlm.PrivateMessageUser.blocked == False,
                sqlm.PrivateMessageUser.exited == False
            ).order_by(sqlm.PrivateMessageReply.created.desc())
        query_ = parse_search_string(query, model_, query_, [sqlm.PrivateMessageReply.message])
        count = query_.count()
        results = query_[(page-1)*pagination:pagination*page]

        for result in results:
            parsed_result = {}
            parsed_result["time"] = humanize_time(result.created)
            parsed_result["title"] = result.pm.title
            parsed_result["description"] = result.message
            parsed_result["url"] = "/messages/"+str(result.pm.id)+"/page/1/post/"+str(result.id)
            parsed_result["author_profile_link"] = result.author.my_url
            parsed_result["author_name"] = result.author.display_name
            parsed_result["readmore"] = True
            parsed_results.append(parsed_result)

    return app.jsonify(results=parsed_results, count=count, pagination=pagination)
