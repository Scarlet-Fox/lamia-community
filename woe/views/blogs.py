from woe import app
from woe import sqla
from woe.models.core import User
from woe.forms.blogs import BlogSettingsForm
from woe.parsers import ForumPostParser
from woe.models.blogs import *
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session, send_from_directory
from flask.ext.login import login_required, current_user
from woe.utilities import scrub_json, humanize_time, ForumHTMLCleaner, parse_search_string_return_q, parse_search_string
from mongoengine.queryset import Q
import arrow, json
from woe.views.dashboard import broadcast
from BeautifulSoup import BeautifulSoup
import woe.sqlmodels as sqlm

@app.route('/blogs', methods=['GET'], defaults={'page': 1})
@app.route('/blogs/page/<page>', methods=['GET'])
@login_required
def blogs_index(page):
    my_blogs = sqla.session.query(sqlm.Blog) \
        .join(sqlm.Blog.recent_entry) \
        .filter_by(author=current_user._get_current_object()) \
        .filter(sqlm.Blog.disabled.isnot(True)) \
        .order_by(sqla.desc(sqlm.BlogEntry.created)).all()

    page = int(page)
    minimum = (int(page)-1)*int(20)
    maximum = int(page)*int(20)

    blogs = sqla.session.query(sqlm.Blog) \
        .join(sqlm.Blog.recent_entry) \
        .filter(sqlm.Blog.disabled.isnot(True)) \
        .order_by(sqla.desc(sqlm.BlogEntry.created)).all()[minimum:maximum]

    count = sqla.session.query(sqlm.Blog) \
        .filter(sqlm.Blog.disabled.isnot(True)).count()

    pages = int(count)/20
    if pages > 10:
        pages = 10

    pages = [p+1 for p in range(pages)]

    clean_html_parser = ForumPostParser()

    for blog in blogs:
        blog.preview = unicode(BeautifulSoup(clean_html_parser.parse(blog.recent_entry.html)[:500]))+"..."

    return render_template("blogs/list_of_blogs.jade",
        page_title="Blogs - World of Equestria",
        my_blogs=my_blogs,
        blogs=blogs,
        pages=pages,
        page=page
    )

#
#
#
# @app.route('/blogs', methods=['GET', 'POST'])
# @login_required
# def list_of_blogs():
#     count = session.get("count", 10)
#     authors = session.get("authors", [])
#     search = session.get("search", "")
#
#     if request.method == 'POST':
#         request_json = request.get_json(force=True)
#
#         try:
#             count = int(request_json.get("count"), 10)
#             if count > 100:
#                 count = 100
#             session["count"] = count
#         except:
#             pass
#
#         try:
#             users = list(
#                     sqla.session.query(sqlm.User) \
#                         .filter(sqlm.User.id.in_(request_json.get("authors"))) \
#                         .all()
#                 )
#             session["authors"] = authors
#         except:
#             authors = []
#             session["authors"] = []
#
#         try:
#             search = request_json.get("search", "")[0:100]
#             session["search"] = search
#         except:
#             pass
#
#     query = {}
#
#     try:
#         authors = [{"id": unicode(u.id), "text": u.display_name} for u in users]
#     except:
#         users = []
#         authors = []
#
#     query_ = sqla.session.query(sqlm.Blog)
#
#     if len(authors) > 0:
#         query_ = query_.filter(sqlm.Blog.author.id.in_([a.id for a in users]))
#
#     query_ = parse_search_string(search, sqlm.Blog, query_, ["name",])
#
#     blogs = query_.join(sqlm.Blog.recent_entry).order_by(sqla.desc(sqlm.BlogEntry.created)).all()[:count]
#     my_blogs = sqla.session.query(sqlm.Blog).join(sqlm.Blog.recent_entry).filter_by(author=current_user._get_current_object()).order_by(sqla.desc(sqlm.BlogEntry.created)).all()
#
#     print len(blogs)
#
#     clean_html_parser = ForumPostParser()
#
#     if request.method == 'POST':
#         parsed_blogs = []
#         for blog in blogs:
#             parsed_blog = {}
#             parsed_blog["slug"] = blog.slug
#             parsed_blog["recent_entry_content"] = clean_html_parser.parse(blog.recent_entry.html, strip_images=True)
#             parsed_blog["recent_entry_title"] = blog.recent_entry.title
#             parsed_blog["recent_entry_slug"] = blog.recent_entry.slug
#             parsed_blog["recent_entry_time"] = humanize_time(blog.recent_entry.created)
#             parsed_blog["recent_entry_avatar_x"] = blog.recent_entry.author.avatar_60_x
#             parsed_blog["recent_entry_avatar_y"] = blog.recent_entry.author.avatar_60_y
#             parsed_blog["recent_entry_avatar"] = blog.recent_entry.author.get_avatar_url("60")
#             parsed_blogs.append(parsed_blog)
#
#         return app.jsonify(blogs=parsed_blogs)
#     else:
#         return render_template("blogs/list_of_blogs.jade", page_title="Blogs - World of Equestria", my_blogs=my_blogs, count=count, search=search, authors=json.dumps(authors))
#
# @app.route('/blogs/new-blog', methods=['GET', 'POST'])
# @login_required
# def new_blog():
#     form = BlogSettingsForm(csrf_enabled=False)
#     if form.validate_on_submit():
#         b = Blog()
#         b.name = form.title.data
#         b.description = form.description.data
#         b.privacy_setting = form.privacy_setting.data
#         b.slug = get_blog_slug(b.name)
#         b.creator = current_user._get_current_object()
#         b.creator_name = current_user._get_current_object().login_name
#         b.save()
#         return redirect("/blog/"+unicode(b.slug))
#
#     return render_template("blogs/create_new_blog.jade", form=form, page_title="New Blog - World of Equestria")
#
# @app.route('/blog/<slug>', methods=['GET'], defaults={'page': 1})
# @app.route('/blog/<slug>/page/<page>', methods=['GET'])
# def blog_index(slug, page):
#     try:
#         blog = Blog.objects(slug=slug)[0]
#     except:
#         return abort(404)
#
#     try:
#         page = int(page)
#     except:
#         return abort(500)
#
#     entries = BlogEntry.objects(hidden=False, draft=False, blog=blog).order_by("-created")[(page-1)*10:page*10]
#     clean_html_parser = ForumPostParser()
#
#     for entry in entries:
#         entry.parsed = clean_html_parser.parse(entry.html)
#         entry.parsed_truncated = unicode(BeautifulSoup(entry.parsed[:1000]))+"..."
#
#     comments = BlogComment.objects(hidden=False, blog=blog).order_by("-created")[0:10]
#
#     entry_count = BlogEntry.objects(hidden=False, draft=False, blog=blog).count()
#     pages = range(1,int(entry_count / 10)+1)
#
#     return render_template("blogs/blog_entry_listing.jade", blog=blog, entries=entries, comments=comments, page=page, pages=pages, entry_count=entry_count)
