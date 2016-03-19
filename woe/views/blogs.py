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
def blogs_index(page):
    if current_user.is_authenticated():
        my_blogs = sqla.session.query(sqlm.Blog) \
            .filter_by(author=current_user._get_current_object()) \
            .filter(sqlm.Blog.disabled.isnot(True)).all()
    else:
        my_blogs = []

    page = int(page)
    minimum = (int(page)-1)*int(20)
    maximum = int(page)*int(20)

    if current_user.is_authenticated():
        blogs = sqla.session.query(sqlm.Blog) \
            .join(sqlm.Blog.recent_entry) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all",
                sqlm.Blog.privacy_setting == "members"
            )) \
            .order_by(sqla.desc(sqlm.BlogEntry.created)).all()[minimum:maximum]
        count = sqla.session.query(sqlm.Blog) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all",
                sqlm.Blog.privacy_setting == "members"
            )) \
            .filter(sqlm.Blog.disabled.isnot(True)).count()
    else:
        blogs = sqla.session.query(sqlm.Blog) \
            .join(sqlm.Blog.recent_entry) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all"
            )) \
            .order_by(sqla.desc(sqlm.BlogEntry.created)).all()[minimum:maximum]
        count = sqla.session.query(sqlm.Blog) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all"
            )) \
            .filter(sqlm.Blog.disabled.isnot(True)).count()

    pages = int(count)/20
    if pages > 10:
        pages = 10

    pages = [p+1 for p in range(pages)]

    clean_html_parser = ForumPostParser()

    for blog in blogs:
        blog.preview = unicode(BeautifulSoup(clean_html_parser.parse(blog.recent_entry.html)[:500]))+"..."

    return render_template("blogs/list_of_blogs.jade",
        page_title="Blogs - Scarlet's Web",
        my_blogs=my_blogs,
        blogs=blogs,
        pages=pages,
        page=page
    )

@app.route('/blogs/new-blog', methods=['GET', 'POST'])
@login_required
def new_blog():
    form = BlogSettingsForm(csrf_enabled=False)
    if form.validate_on_submit():
        b = sqlm.Blog()
        b.name = form.title.data
        b.description = form.description.data
        b.privacy_setting = form.privacy_setting.data
        b.slug = sqlm.find_blog_slug(b.name)
        b.author = current_user._get_current_object()
        sqla.session.add(b)
        sqla.session.commit()
        return redirect("/blog/"+unicode(b.slug))

    return render_template("blogs/create_new_blog.jade", form=form, page_title="New Blog - Scarlet's Web")

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
