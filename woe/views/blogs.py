from woe import app
from woe.models.core import User
from woe.parsers import ForumPostParser
from woe.models.blogs import *
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session, send_from_directory
from flask.ext.login import login_required, current_user
from woe.utilities import scrub_json, humanize_time, ForumHTMLCleaner, parse_search_string_return_q
from mongoengine.queryset import Q
import arrow, json
from woe.views.dashboard import broadcast

@app.route('/blogs', methods=['GET', 'POST'])
@login_required
def list_of_blogs():
    count = session.get("count", 10)
    authors = session.get("authors", [])
    search = session.get("search", "")
    
    if request.method == 'POST':
        request_json = request.get_json(force=True)
        
        try:
            count = int(request_json.get("count"), 10)
            if count > 100:
                count = 100
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
        user_q_ = Q(creator__in=list(users))
        
    hidden_q_ = Q(disabled=False)
    
    search_q_ = Q()
    if search != "":
        search_q_ = parse_search_string_return_q(search, ["name",])
        
    blogs = Blog.objects(user_q_ & search_q_ & hidden_q_).order_by("-last_entry_date")[:count]
    my_blogs = Blog.objects(creator=current_user._get_current_object()).order_by("-last_entry_date")
    
    clean_html_parser = ForumPostParser()
    
    if request.method == 'POST':
        parsed_blogs = []
        for blog in blogs:
            parsed_blog = blog.to_mongo().to_dict()
            parsed_blog["recent_entry_content"] = clean_html_parser.parse(blog.last_entry.html, strip_images=True)
            parsed_blog["recent_entry_title"] = blog.last_entry.title
            parsed_blog["recent_entry_slug"] = blog.last_entry.slug
            parsed_blog["recent_entry_time"] = humanize_time(blog.last_entry.created)
            parsed_blog["recent_entry_avatar_x"] = blog.last_entry.author.avatar_60_x
            parsed_blog["recent_entry_avatar_y"] = blog.last_entry.author.avatar_60_y
            parsed_blog["recent_entry_avatar"] = blog.last_entry.author.get_avatar_url("60")
            parsed_blogs.append(parsed_blog)
                        
        return app.jsonify(blogs=parsed_blogs)
    else:
        return render_template("blogs/list_of_blogs.jade", page_title="Blogs - World of Equestria", my_blogs=my_blogs, count=count, search=search, authors=json.dumps(authors))
