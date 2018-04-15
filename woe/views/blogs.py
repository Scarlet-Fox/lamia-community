from woe import app
from woe import sqla
from woe.parsers import ForumPostParser
from flask import abort, redirect, url_for, request, make_response, json, flash, session, send_from_directory
from flask_login import login_required, current_user
from woe.utilities import scrub_json, humanize_time, ForumHTMLCleaner, parse_search_string_return_q, parse_search_string, get_preview
from mongoengine.queryset import Q
import arrow, json
from woe.views.dashboard import broadcast
from BeautifulSoup import BeautifulSoup
import woe.sqlmodels as sqlm
from woe.forms.blogs import BlogSettingsForm, BlogEntryForm, BlogCommentForm
import math, re
from woe.utilities import render_lamia_template as render_template

mention_re = re.compile("\[@(.*?)\]")
reply_re = re.compile(r'\[reply=(.+?):(post)(:.+?)?\]')

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
    minimum = (int(page)-1)*int(10)
    maximum = int(page)*int(10)
            
    request.canonical = app.config['BASE'] + "/blogs/page/%s" % (page,)

    if current_user.is_authenticated():
        comments = sqla.session.query(sqlm.BlogComment) \
            .join(sqlm.BlogComment.blog) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all",
                sqlm.Blog.privacy_setting == "members"
            )) \
            .order_by(sqla.desc(sqlm.BlogComment.created))[0:10]
        entries = sqla.session.query(sqlm.BlogEntry) \
            .join(sqlm.BlogEntry.blog) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqlm.BlogEntry.draft.isnot(True)) \
            .filter(sqlm.BlogEntry.published.isnot(None)) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all",
                sqlm.Blog.privacy_setting == "members"
            )) \
            .order_by(sqla.desc(sqlm.BlogEntry.published))[minimum:maximum]
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
            .order_by(sqla.desc(sqlm.BlogEntry.published))[0:5]
        random_blogs = sqla.session.query(sqlm.Blog) \
            .join(sqlm.Blog.recent_entry) \
            .join(sqlm.Blog.author) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqlm.User.banned.isnot(True)) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all",
                sqlm.Blog.privacy_setting == "members"
            )) \
            .order_by(sqla.func.random())[0:10]
    else:
        comments = sqla.session.query(sqlm.BlogComment) \
            .join(sqlm.BlogComment.blog) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all"
            )) \
            .order_by(sqla.desc(sqlm.BlogComment.created))[0:10]
        entries = sqla.session.query(sqlm.BlogEntry) \
            .join(sqlm.BlogEntry.blog) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqlm.BlogEntry.draft.isnot(True)) \
            .filter(sqlm.BlogEntry.published.isnot(None)) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all"
            )) \
            .order_by(sqla.desc(sqlm.BlogEntry.published))[minimum:maximum]
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
            .order_by(sqla.desc(sqlm.BlogEntry.published))[0:5]

        random_blogs = sqla.session.query(sqlm.Blog) \
            .join(sqlm.Blog.recent_entry) \
            .join(sqlm.Blog.author) \
            .filter(sqlm.Blog.disabled.isnot(True)) \
            .filter(sqlm.User.banned.isnot(True)) \
            .filter(sqla.or_(
                sqlm.Blog.privacy_setting == "all"
            )) \
            .order_by(sqla.func.random())[0:10]

    pages = int(math.ceil(float(count)/10.0))
    if pages > 10:
        pages = 10

    pages = [p+1 for p in range(pages)]

    clean_html_parser = ForumPostParser()

    for entry in entries:
        entry.preview = unicode(BeautifulSoup(clean_html_parser.parse(entry.html, _object=entry)[:500]))+"..."

    return render_template("blogs/list_of_blogs.jade",
        page_title="Blogs - %%GENERIC SITENAME%%",
        my_blogs=my_blogs,
        random_blogs=random_blogs,
        featured_blog_entries=featured_blog_entries,
        entries=entries,
        pages=pages,
        comments=comments,
        page=page
    )

@app.route('/blogs/new-blog', methods=['GET', 'POST'])
@login_required
def new_blog():
    form = BlogSettingsForm(csrf_enabled=False)
    if form.validate_on_submit():
        b = sqlm.Blog()
        b.name = form.title.data
        cleaner = ForumHTMLCleaner()
        try:
            b.description = cleaner.clean(form.description.data)
        except:
            return abort(500)
        b.privacy_setting = form.privacy_setting.data
        b.slug = sqlm.find_blog_slug(b.name)
        b.author = current_user._get_current_object()
        sqla.session.add(b)
        sqla.session.commit()
        return redirect("/blog/"+unicode(b.slug))

    return render_template("blogs/create_new_blog.jade", form=form, page_title="New Blog - %%GENERIC SITENAME%%")

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
        broadcast(
          to=[blog.author,],
          category="followed",
          url="/blog/%s" % (str(blog.slug),),
          title="followed blog %s" % (unicode(blog.name)),
          description="",
          content=blog,
          author=current_user
          )
    else:
        try:
            blog.subscribers.remove(current_user._get_current_object())
        except:
            pass

    try:
        sqla.session.add(blog)
        sqla.session.commit()
    except:
        sqla.session.rollback()

    return app.jsonify(url="/blog/%s" % (blog.slug))

@app.route('/blog/<slug>/e/<entry_slug>/toggle-follow', methods=['POST'])
@login_required
def toggle_follow_blog_entry(slug, entry_slug):
    try:
        blog = sqla.session.query(sqlm.Blog).filter_by(slug=slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    try:
        entry = sqla.session.query(sqlm.BlogEntry).filter_by(blog=blog, slug=entry_slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    if blog.privacy_setting == "you" and current_user._get_current_object() != blog.author:
        return abort(404)
    elif blog.privacy_setting == "editors" and (current_user._get_current_object() != blog.author and current_user._get_current_object() not in blog.editors):
        return abort(404)
    elif blog.privacy_setting == "members" and not current_user.is_authenticated():
        return abort(404)

    if not current_user._get_current_object() in entry.subscribers:
        entry.subscribers.append(current_user._get_current_object())
        broadcast(
          to=[entry.author,],
          category="followed",
          url="/blog/%s/e/%s" % (str(blog.slug),str(entry.slug)),
          title="followed blog entry %s" % (unicode(entry.title)),
          description="",
          content=entry,
          author=current_user
          )
    else:
        try:
            entry.subscribers.remove(current_user._get_current_object())
        except:
            pass

    try:
        sqla.session.add(entry)
        sqla.session.commit()
    except:
        sqla.session.rollback()

    return app.jsonify(url="/blog/%s/e/%s" % (blog.slug, entry.slug))

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
        cleaner = ForumHTMLCleaner()
        try:
            blog.description = cleaner.clean(form.description.data)
        except:
            return abort(500)
        blog.privacy_setting = form.privacy_setting.data
        sqla.session.add(blog)
        sqla.session.commit()
        return redirect("/blog/"+unicode(blog.slug))
    else:
        form.description.data = blog.description
        form.privacy_setting.data = blog.privacy_setting
        form.title.data = blog.name

    return render_template("blogs/edit_blog.jade", form=form, blog=blog, page_title="Edit Blog - %%GENERIC SITENAME%%")

@app.route('/blog/<slug>/new-entry', methods=['GET', 'POST'])
@login_required
def new_blog_entry(slug):
    try:
        blog = sqla.session.query(sqlm.Blog).filter_by(slug=slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    if current_user._get_current_object() != blog.author:
        if current_user._get_current_object() not in blog.editors:
            return abort(404)

    form = BlogEntryForm(csrf_enabled=False)
    if form.validate_on_submit():
        e = sqlm.BlogEntry()
        e.blog = blog
        e.title = form.title.data
        e.author = current_user._get_current_object()
        e.slug = sqlm.find_blog_entry_slug(e.title, blog)
        e.draft = form.draft.data
        cleaner = ForumHTMLCleaner()
        try:
            e.html = cleaner.clean(form.entry.data)
        except:
            return abort(500)
        e.created = arrow.utcnow().datetime.replace(tzinfo=None)
        if e.draft == False:
            e.published = arrow.utcnow().datetime.replace(tzinfo=None)
        e.b_title = blog.name
        sqla.session.add(e)
        sqla.session.commit()
        entry = e

        if e.draft == False:
            blog.recent_entry = e
            sqla.session.add(blog)
            sqla.session.commit()

            for subscriber in blog.subscribers:
                e.subscribers.append(subscriber)
            sqla.session.add(e)
            sqla.session.commit()

            if entry.author != blog.author:
                broadcast(
                    to=[blog.author,],
                    category="blog",
                    url="""/blog/%s/e/%s""" % (slug, entry.slug),
                    title="posted %s on blog %s" % (unicode(entry.title), unicode(blog.name)),
                    description=entry.html,
                    content=entry,
                    author=current_user._get_current_object()
                    )

            _to_notify = []
            for u in blog.subscribers:
                if u.id != current_user._get_current_object().id:
                    _to_notify.append(u)
                    
            mentions = mention_re.findall(e.html)
            to_notify_m = {}
            for mention in mentions:
                try:
                    to_notify_m[mention] = sqla.session.query(sqlm.User).filter_by(login_name=mention)[0]
                except:
                    continue

            broadcast(
              to=to_notify_m.values(),
              category="mention",
              url="""/blog/%s/e/%s""" % (slug, entry.slug),
              title="mentioned you in blog %s" % (unicode(entry.title)),
              description=e.html,
              content=e,
              author=e.author
              )

            if len(_to_notify) > 0:
                broadcast(
                    to=_to_notify,
                    category="blog",
                    url="""/blog/%s/e/%s""" % (slug, entry.slug),
                    title="posted %s on blog %s" % (unicode(entry.title), unicode(blog.name)),
                    description=entry.html,
                    content=entry,
                    author=current_user._get_current_object()
                    )
        return redirect("/blog/"+unicode(blog.slug))

    return render_template("blogs/new_blog_entry.jade", form=form, blog=blog, page_title="New Blog Entry - %%GENERIC SITENAME%%")

@app.route('/blog/<slug>/e/<entry_slug>/remove-entry', methods=['GET', 'POST'])
@login_required
def remove_blog_entry(slug, entry_slug):
    try:
        blog = sqla.session.query(sqlm.Blog).filter_by(slug=slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    if current_user._get_current_object() != blog.author:
        if current_user._get_current_object() not in blog.editors:
            return abort(404)

    try:
        e = sqla.session.query(sqlm.BlogEntry).filter_by(blog=blog, slug=entry_slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    e.hidden = True
    sqla.session.add(e)
    sqla.session.commit()
    return app.jsonify(success=True, url="/blog/"+unicode(blog.slug))

@app.route('/blog/<slug>/e/<entry_slug>/edit-entry', methods=['GET', 'POST'])
@login_required
def edit_blog_entry(slug, entry_slug):
    try:
        blog = sqla.session.query(sqlm.Blog).filter_by(slug=slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    if current_user._get_current_object() != blog.author:
        if current_user._get_current_object() not in blog.editors:
            return abort(404)

    try:
        e = sqla.session.query(sqlm.BlogEntry).filter_by(blog=blog, slug=entry_slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    already_published = not e.draft

    form = BlogEntryForm(csrf_enabled=False)
    if form.validate_on_submit():
        e.title = form.title.data
        if current_user._get_current_object() != e.author:
            e.editor = current_user._get_current_object()
        e.draft = form.draft.data
        cleaner = ForumHTMLCleaner()
        try:
            e.html = cleaner.clean(form.entry.data)
        except:
            return abort(500)
        e.created = arrow.utcnow().datetime.replace(tzinfo=None)
        if e.draft == False and already_published == False:
            e.published = arrow.utcnow().datetime.replace(tzinfo=None)
            recent_entry = True

            for subscriber in blog.subscribers:
                e.subscribers.append(subscriber)
            sqla.session.add(e)
            sqla.session.commit()
        else:
            recent_entry = False
        e.b_title = blog.name
        sqla.session.add(e)
        sqla.session.commit()

        if recent_entry:
            blog.recent_entry = e
            sqla.session.add(blog)
            sqla.session.commit()
        return redirect("/blog/"+unicode(blog.slug))
    else:
        form.draft.data = e.draft
        form.title.data = e.title
        form.entry.data = e.html

    return render_template("blogs/edit_blog_entry.jade", form=form, blog=blog, entry=e, page_title="Edit Blog Entry - %%GENERIC SITENAME%%")

@app.route('/blog/<slug>/e/<entry_slug>/c/<comment_id>/edit-comment', methods=['GET', 'POST'])
@login_required
def edit_blog_comment(slug, entry_slug, comment_id):
    try:
        blog = sqla.session.query(sqlm.Blog).filter_by(slug=slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    try:
        entry = sqla.session.query(sqlm.BlogEntry).filter_by(blog=blog, slug=entry_slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    try:
        comment = sqla.session.query(sqlm.BlogComment).filter_by(blog=blog, id=comment_id, blog_entry=entry)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    if current_user._get_current_object() != comment.author:
        return abort(404)

    form = BlogCommentForm(csrf_enabled=False)
    if form.validate_on_submit():
        cleaner = ForumHTMLCleaner()
        try:
            comment.html = cleaner.clean(form.comment.data)
        except:
            return abort(500)
        sqla.session.add(comment)
        sqla.session.commit()
        return redirect("/blog/"+unicode(blog.slug)+"/e/"+unicode(entry_slug))
    else:
        form.comment.data = comment.html

    return render_template("blogs/edit_blog_entry_comment.jade", form=form, blog=blog, entry=entry, comment=comment, page_title="Edit Blog Comment - %%GENERIC SITENAME%%")

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
        page = 1
            
    request.canonical = app.config['BASE'] + "/blog/%s/page/%s" % (slug,page,)

    if blog.privacy_setting == "you" and current_user._get_current_object() != blog.author:
        return abort(404)
    elif blog.privacy_setting == "editors" and (current_user._get_current_object() != blog.author and current_user._get_current_object() not in blog.editors):
        return abort(404)
    elif blog.privacy_setting == "members" and not current_user.is_authenticated():
        return abort(404)

    if current_user._get_current_object() == blog.author or current_user.is_admin:
        entries = sqla.session.query(sqlm.BlogEntry) \
            .filter_by(hidden=False, blog=blog) \
            .order_by(sqla.desc(sqlm.BlogEntry.published))[(page-1)*10:page*10]
        entry_count = sqla.session.query(sqlm.BlogEntry) \
            .filter_by(hidden=False, blog=blog).count()
        drafts = sqla.session.query(sqlm.BlogEntry) \
            .filter_by(hidden=False, blog=blog, draft=True) \
            .order_by(sqla.desc(sqlm.BlogEntry.created)).all()
    else:
        entries = sqla.session.query(sqlm.BlogEntry) \
            .filter_by(hidden=False, blog=blog) \
            .filter(sqlm.BlogEntry.published.isnot(None)) \
            .filter(sqlm.BlogEntry.draft.isnot(True)) \
            .order_by(sqla.desc(sqlm.BlogEntry.published))[(page-1)*10:page*10]
        entry_count = sqla.session.query(sqlm.BlogEntry) \
            .filter_by(hidden=False, blog=blog) \
            .filter(sqlm.BlogEntry.published.isnot(None)) \
            .filter(sqlm.BlogEntry.draft.isnot(True)).count()
        drafts = []

    clean_html_parser = ForumPostParser()

    for entry in entries:
        entry.parsed = clean_html_parser.parse(entry.html, _object=entry)
        entry.parsed_truncated = unicode(BeautifulSoup(entry.parsed[:1000]))+"..."

    description = clean_html_parser.parse(blog.description, _object=blog)

    comments = sqla.session.query(sqlm.BlogComment) \
        .filter_by(hidden=False, blog=blog) \
        .order_by(sqla.desc(sqlm.BlogComment.created))[0:10]

    pages = int(math.ceil(float(entry_count)/10.0))
    if pages > 10:
        pages = 10

    pages = [p+1 for p in range(pages)]

    return render_template("blogs/blog_entry_listing.jade", blog=blog, drafts=drafts, entries=entries, description=description, comments=comments, page=page, pages=pages, entry_count=entry_count, page_title=blog.name+" - %%GENERIC SITENAME%%")

@app.route('/blog/<slug>/e/<entry_slug>/toggle-boop', methods=['POST'])
def boop_blog_entry(slug, entry_slug):
    try:
        blog = sqla.session.query(sqlm.Blog).filter_by(slug=slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    if blog.privacy_setting == "you" and current_user._get_current_object() != blog.author:
        return abort(404)
    elif blog.privacy_setting == "editors" and (current_user._get_current_object() != blog.author and current_user._get_current_object() not in blog.editors):
        return abort(404)
    elif blog.privacy_setting == "members" and not current_user.is_authenticated():
        return abort(404)

    try:
        entry = sqla.session.query(sqlm.BlogEntry).filter_by(blog=blog, slug=entry_slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    if current_user._get_current_object() in entry.boops:
        entry.boops.remove(current_user._get_current_object())
    else:
        entry.boops.append(current_user._get_current_object())
        broadcast(
            to=[entry.author,],
            category="boop",
            url="/blog/%s/e/%s" % (str(blog.slug), str(entry.slug)),
            title="booped your blog entry %s" % (unicode(entry.title)),
            description=entry.html,
            content=entry,
            author=current_user._get_current_object()
            )

    sqla.session.add(entry)
    sqla.session.commit()
    return app.jsonify(success=True)

@app.route('/blog/<slug>/e/<entry_slug>/c/<comment_id>/toggle-boop', methods=['POST'])
def boop_blog_entry_comment(slug, entry_slug, comment_id):
    try:
        blog = sqla.session.query(sqlm.Blog).filter_by(slug=slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    if blog.privacy_setting == "you" and current_user._get_current_object() != blog.author:
        return abort(404)
    elif blog.privacy_setting == "editors" and (current_user._get_current_object() != blog.author and current_user._get_current_object() not in blog.editors):
        return abort(404)
    elif blog.privacy_setting == "members" and not current_user.is_authenticated():
        return abort(404)

    try:
        entry = sqla.session.query(sqlm.BlogEntry).filter_by(blog=blog, slug=entry_slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    try:
        comment = sqla.session.query(sqlm.BlogComment).filter_by(blog=blog, id=comment_id, blog_entry=entry)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    if current_user._get_current_object() in comment.boops:
        comment.boops.remove(current_user._get_current_object())
    else:
        comment.boops.append(current_user._get_current_object())
        broadcast(
            to=[comment.author,],
            category="boop",
            url="/blog/%s/e/%s" % (str(blog.slug), str(entry.slug)),
            title="booped your blog comment on %s" % (unicode(entry.title)),
            description=comment.html,
            content=comment,
            author=current_user._get_current_object()
            )

    sqla.session.add(comment)
    sqla.session.commit()
    return app.jsonify(success=True)

@app.route('/blog/<slug>/e/<entry_slug>', methods=['GET'], defaults={'page': 1})
@app.route('/blog/<slug>/e/<entry_slug>/page/<page>', methods=['GET'])
def blog_entry_index(slug, entry_slug, page):
    try:
        blog = sqla.session.query(sqlm.Blog).filter_by(slug=slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    try:
        page = int(page)
    except:
        page = 1

            
    request.canonical = app.config['BASE'] + "/blog/%s/e/%s/page/%s" % (slug, entry_slug, page)

    if not current_user.is_admin:
        if blog.privacy_setting == "you" and current_user._get_current_object() != blog.author:
            return abort(404)
        elif blog.privacy_setting == "editors" and (current_user._get_current_object() != blog.author and current_user._get_current_object() not in blog.editors):
            return abort(404)
        elif blog.privacy_setting == "members" and not current_user.is_authenticated():
            return abort(404)

    try:
        entry = sqla.session.query(sqlm.BlogEntry).filter_by(blog=blog, slug=entry_slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    if entry.draft == True and (current_user._get_current_object() != blog.author and current_user._get_current_object() not in blog.editors and not current_user.is_admin):
        return abort(404)

    clean_html_parser = ForumPostParser()
    entry.parsed = clean_html_parser.parse(entry.html, _object=entry)

    page = int(page)
    minimum = (int(page)-1)*int(10)
    maximum = int(page)*int(10)

    comments = sqla.session.query(sqlm.BlogComment).filter_by(blog_entry=entry, hidden=False).order_by(sqlm.BlogComment.created)[minimum:maximum]
    count = sqla.session.query(sqlm.BlogComment).filter_by(blog_entry=entry, hidden=False).count()

    for comment in comments:
        comment.parsed = clean_html_parser.parse(comment.html, _object=comment)

    pages = int(math.ceil(float(count)/10.0))
    if pages > 10:
        pages = 10

    pages = [p+1 for p in range(pages)]

    return render_template("blogs/blog_entry_view.jade", blog=blog, meta_description=get_preview(entry.html, 140),
    entry=entry, comments=comments, page=page, pages=pages, page_title=entry.title+" - %%GENERIC SITENAME%%")

@app.route('/blog/<slug>/e/<entry_slug>/new-comment', methods=['POST'], defaults={'page': 1})
@app.route('/blog/<slug>/e/<entry_slug>/page/<page>/new-comment', methods=['POST'])
@login_required
def create_blog_comment(slug, entry_slug, page):
    try:
        blog = sqla.session.query(sqlm.Blog).filter_by(slug=slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    try:
        page = int(page)
    except:
        return abort(500)

    if blog.privacy_setting == "you" and current_user._get_current_object() != blog.author:
        return abort(404)
    elif blog.privacy_setting == "editors" and (current_user._get_current_object() != blog.author and current_user._get_current_object() not in blog.editors):
        return abort(404)
    elif blog.privacy_setting == "members" and not current_user.is_authenticated():
        return abort(404)

    try:
        entry = sqla.session.query(sqlm.BlogEntry).filter_by(slug=entry_slug)[0]
    except IndexError:
        sqla.session.rollback()
        return abort(404)

    if (current_user in [u.ignoring for u in entry.author.ignored_users]) and not current_user.is_admin:
        return app.jsonify(error="You cannot comment on this entry.")

    request_json = request.get_json(force=True)

    if request_json.get("text", "").strip() == "":
        return app.jsonify(no_content=True)

    cleaner = ForumHTMLCleaner()
    try:
        post_html = cleaner.clean(request_json.get("post", ""))
    except:
        return abort(500)

    new_blog_comment = sqlm.BlogComment()
    new_blog_comment.blog_entry = entry
    new_blog_comment.blog = blog
    new_blog_comment.author = current_user
    new_blog_comment.html = post_html
    new_blog_comment.created = arrow.utcnow().datetime.replace(tzinfo=None)
    new_blog_comment.hidden = False
    new_blog_comment.b_e_title = entry.title
    sqla.session.add(new_blog_comment)
    sqla.session.commit()

    max_pages = int(math.ceil(float(entry.comment_count())/10.0))
    e = entry
    
    replies = reply_re.findall(new_blog_comment.html)
    to_notify = {}
    for reply_ in replies:
        try:
            to_notify[reply_] = sqla.session.query(sqlm.BlogComment).filter_by(id=reply_[0])[0].author
        except:
            continue

    broadcast(
      to=to_notify.values(),
      category="topic_reply",
      url="""/blog/%s/e/%s""" % (slug, entry.slug),
      title="replied to you in %s" % (unicode(entry.title)),
      description=new_blog_comment.html,
      content=new_blog_comment,
      author=new_blog_comment.author
      )

    mentions = mention_re.findall(new_blog_comment.html)
    to_notify_m = {}
    for mention in mentions:
        try:
            to_notify_m[mention] = sqla.session.query(sqlm.User).filter_by(login_name=mention)[0]
        except:
            continue

    broadcast(
      to=to_notify_m.values(),
      category="mention",
      url="""/blog/%s/e/%s""" % (slug, entry.slug),
      title="mentioned you in a comment on %s" % (unicode(entry.title)),
      description=new_blog_comment.html,
      content=new_blog_comment,
      author=new_blog_comment.author
      )

    broadcast(
        to=[entry.author,],
        category="blogcomments",
        url="""/blog/%s/e/%s/page/%s#comments""" % (slug, entry_slug, max_pages),
        title="commented on your blog entry %s" % (unicode(entry.title)),
        description=new_blog_comment.html,
        content=new_blog_comment,
        author=current_user._get_current_object()
        )

    if entry.author != blog.author:
        broadcast(
            to=[blog.author,],
            category="blogcomments",
            url="""/blog/%s/e/%s/page/%s#comments""" % (slug, entry_slug, max_pages),
            title="commented on blog entry %s" % (unicode(entry.title)),
            description=new_blog_comment.html,
            content=new_blog_comment,
            author=current_user._get_current_object()
            )

    _to_notify = []
    for u in entry.subscribers:
        if u.id != current_user._get_current_object().id:
            _to_notify.append(u)

    if len(_to_notify) > 0:
        broadcast(
            to=_to_notify,
            category="blogcomments",
            url="""/blog/%s/e/%s/page/%s#comments""" % (slug, entry_slug, max_pages),
            title="commented on %s's blog entry %s" % (unicode(entry.author.display_name),unicode(entry.title)),
            description=new_blog_comment.html,
            content=new_blog_comment,
            author=current_user._get_current_object()
            )

    return app.jsonify(success=True, url="""/blog/%s/e/%s/page/%s""" % (slug, entry_slug, max_pages))

@app.route('/blog-list-api', methods=['GET'])
@login_required
def blog_list_api():
    query = request.args.get("q", "")[0:300]
    if len(query) < 2:
        return app.jsonify(results=[])

    q_ = parse_search_string(query, sqlm.Blog, sqla.session.query(sqlm.Blog), ["name",])
    blogs = q_.all()
    results = [{"text": unicode(b.name), "id": str(b.id)} for b in blogs]
    return app.jsonify(results=results)
