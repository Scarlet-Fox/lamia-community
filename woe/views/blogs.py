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

        featured_blog_entries = sqla.session.query(sqlm.BlogEntry) \
            .join(sqlm.BlogEntry.blog) \
            .join(sqlm.BlogEntry.author) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqlm.User.banned.isnot(True)) \
            .filter(sqlm.BlogEntry.featured == True) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all",
                sqlm.Blog.privacy_setting == "members"
            )) \
            .order_by(sqla.desc(sqlm.BlogEntry.created)).all()[0:5]

        random_blogs = sqla.session.query(sqlm.Blog) \
            .join(sqlm.Blog.recent_entry) \
            .join(sqlm.Blog.author) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqlm.User.banned.isnot(True)) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all",
                sqlm.Blog.privacy_setting == "members"
            )) \
            .order_by(sqla.func.random()).all()[0:5]
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

        featured_blog_entries = sqla.session.query(sqlm.BlogEntry) \
            .join(sqlm.BlogEntry.blog) \
            .join(sqlm.BlogEntry.author) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqlm.User.banned.isnot(True)) \
            .filter(sqlm.BlogEntry.featured == True) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all"
            )) \
            .order_by(sqla.desc(sqlm.BlogEntry.created)).all()[0:5]

        random_blogs = qla.session.query(sqlm.Blog) \
            .join(sqlm.Blog.recent_entry) \
            .join(sqlm.Blog.author) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqlm.User.banned.isnot(True)) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all"
            )) \
            .order_by(sqla.func.random()).all()[0:5]

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
        random_blogs=random_blogs,
        featured_blog_entries=featured_blog_entries,
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

@app.route('/blog/<slug>/toggle-follow', methods=['POST'])
@login_required
def toggle_follow_blog(slug):
    try:
        blog = sqla.session.query(sqlm.Blog).filter_by(slug=slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    if not current_user._get_current_object() in blog.subscribers:
        blog.subscribers.append(current_user._get_current_object())
    else:
        try:
            blog.subscribers.remove(current_user._get_current_object())
        except:
            pass

    try:
        sqla.session.add(blog)
        sqla.commit()
    except:
        sqla.rollback()

    return app.jsonify(url="/blog/%s" % (blog.slug))

@app.route('/blog/<slug>/edit-blog', methods=['GET', 'POST'])
@login_required
def edit_blog(slug):
    try:
        blog = sqla.session.query(sqlm.Blog).filter_by(slug=slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    if current_user._get_current_object() != blog.author:
        if not current_user._get_current_object().is_admin and not current_user._get_current_object().is_mod:
            if current_user._get_current_object() not in blog.editors:
                return abort(404)

    form = BlogSettingsForm(csrf_enabled=False)
    if form.validate_on_submit():
        blog.name = form.title.data
        blog.description = form.description.data
        blog.privacy_setting = form.privacy_setting.data
        sqla.session.add(blog)
        sqla.session.commit()
        return redirect("/blog/"+unicode(blog.slug))
    else:
        form.description.data = blog.description
        form.privacy_setting.data = blog.privacy_setting
        form.title.data = blog.name

    return render_template("blogs/edit_blog.jade", form=form, blog=blog, page_title="Edit Blog - Scarlet's Web")

@app.route('/blog/<slug>', methods=['GET'], defaults={'page': 1})
@app.route('/blog/<slug>/page/<page>', methods=['GET'])
def blog_index(slug, page):
    try:
        blog = sqla.session.query(sqlm.Blog).filter_by(slug=slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    try:
        page = int(page)
    except:
        return abort(500)

    if current_user._get_current_object() == blog.author:
        entries = sqla.session.query(sqlm.BlogEntry) \
            .filter_by(hidden=False, blog=blog) \
            .order_by(sqla.desc(sqlm.BlogEntry.published)).all()[(page-1)*10:page*10]
        entry_count = sqla.session.query(sqlm.BlogEntry) \
            .filter_by(hidden=False, blog=blog).count()
    else:
        entries = sqla.session.query(sqlm.BlogEntry) \
            .filter_by(hidden=False, blog=blog) \
            .filter(sqlm.BlogEntry.published.isnot(None)) \
            .filter(sqlm.BlogEntry.draft.isnot(True)) \
            .order_by(sqla.desc(sqlm.BlogEntry.published)).all()[(page-1)*10:page*10]
        entry_count = sqla.session.query(sqlm.BlogEntry) \
            .filter_by(hidden=False, blog=blog) \
            .filter(sqlm.BlogEntry.published.isnot(None)) \
            .filter(sqlm.BlogEntry.draft.isnot(True)).count()

    clean_html_parser = ForumPostParser()

    for entry in entries:
        entry.parsed = clean_html_parser.parse(entry.html)
        entry.parsed_truncated = unicode(BeautifulSoup(entry.parsed[:1000]))+"..."

    # comments = BlogComment.objects(hidden=False, blog=blog).order_by("-created")[0:10]

    comments = []
    pages = range(1,int(entry_count / 10)+1)

    return render_template("blogs/blog_entry_listing.jade", blog=blog, entries=entries, comments=comments, page=page, pages=pages, entry_count=entry_count)
