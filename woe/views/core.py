from woe import login_manager
from woe import app, bcrypt
from woe.models.core import User, DisplayNameHistory, StatusUpdate, StatusComment, StatusViewer, PrivateMessage, PrivateMessageTopic, Attachment, IPAddress, Log, Fingerprint, Report
from woe.models.forum import Category, Post, Topic
from woe.parsers import ForumPostParser
from collections import OrderedDict
from woe.forms.core import LoginForm, RegistrationForm, ForgotPasswordForm, ResetPasswordForm
from flask import abort, redirect, url_for, request, render_template, make_response, json, flash, session, send_from_directory
from flask.ext.login import login_user, logout_user, login_required, current_user
from woe.utilities import get_top_frequences, scrub_json, humanize_time, ForumHTMLCleaner, parse_search_string_return_q
from mongoengine.queryset import Q
from wand.image import Image
from werkzeug import secure_filename
import arrow, mimetypes, json, os, hashlib, time, StringIO
from woe.views.dashboard import broadcast
from ipwhois import IPWhois
import urllib
import mechanize
import HTMLParser
from werkzeug.exceptions import default_exceptions, HTTPException
from  werkzeug.debug import get_current_traceback
login_manager.login_view = "sign_in"

@app.before_request
def make_session_permanent():
    session.permanent = True

@app.errorhandler(500)
def server_error(e):
    traceback = get_current_traceback()
    l = Log(
        method=request.method,
        path=request.path,
        ip_address=request.remote_addr,
        agent_platform=request.user_agent.platform,
        agent_browser=request.user_agent.browser,
        agent_browser_version=request.user_agent.version,
        agent=request.user_agent.string,
        time=arrow.utcnow().datetime
    )
    try:
        if current_user.is_authenticated():
            l.user = current_user._get_current_object()
            l.user_name = current_user.login_name
    except:
        pass
        
    if isinstance(e, HTTPException):
        description = unicode(e.get_description(request.environ))
        code = unicode(e.code)
        name = unicode(e.name)
    else:
        description = "Shit... Something's broken!"
        code = unicode(500)
        name = "Server Error."
        
    l.error = True
    l.error_name = name
    l.error_code = code
    l.error_description = description + "\n\n" + traceback.plaintext
    l.save()
    
    return render_template('500.jade', page_title="SERVER ERROR! - World of Equestria"), 500

@app.errorhandler(403)
def unauthorized_access(e):
    l = Log(
        method=request.method,
        path=request.path,
        ip_address=request.remote_addr,
        agent_platform=request.user_agent.platform,
        agent_browser=request.user_agent.browser,
        agent_browser_version=request.user_agent.version,
        agent=request.user_agent.string,
        time=arrow.utcnow().datetime
    )
    try:
        if current_user.is_authenticated():
            l.user = current_user._get_current_object()
            l.user_name = current_user.login_name
    except:
        pass
        
    if isinstance(e, HTTPException):
        description = unicode(e.get_description(request.environ))
        code = unicode(e.code)
        name = unicode(e.name)
    else:
        description = "Page not found."
        code = unicode(403)
        name = "Page Not Found."
        
    l.error = True
    l.error_name = name
    l.error_code = code
    l.error_description = description
    l.save()
    
    return render_template('403.jade', page_title="Page Not Found - World of Equestria"), 403

@app.errorhandler(404)
def page_not_found(e):
    l = Log(
        method=request.method,
        path=request.path,
        ip_address=request.remote_addr,
        agent_platform=request.user_agent.platform,
        agent_browser=request.user_agent.browser,
        agent_browser_version=request.user_agent.version,
        agent=request.user_agent.string,
        time=arrow.utcnow().datetime
    )
    try:
        if current_user.is_authenticated():
            l.user = current_user._get_current_object()
            l.user_name = current_user.login_name
    except:
        pass
        
    if isinstance(e, HTTPException):
        description = unicode(e.get_description(request.environ))
        code = unicode(e.code)
        name = unicode(e.name)
    else:
        description = "Page not found."
        code = unicode(404)
        name = "Page Not Found."
        
    l.error = True
    l.error_name = name
    l.error_code = code
    l.error_description = description
    l.save()
    
    return render_template('404.jade', page_title="Page Not Found - World of Equestria"), 404

@app.route('/under-construction')
def under_construction():
    return render_template("under_construction.jade", page_title="We're working on the site!")

if app.settings_file.get("lockout_on", False):
    @app.before_request
    def lockdown_site():
        if not (request.path == "/under-construction" or request.path == "/sign-in" or "/static" in request.path):
            if current_user._get_current_object().is_authenticated() and (current_user._get_current_object().is_admin or current_user._get_current_object().is_allowed_during_construction):
                pass
            else:
                return redirect("/under-construction")

@app.before_request
def intercept_banned():
    if current_user._get_current_object().is_authenticated():
        if current_user._get_current_object().banned and not (request.path == "/banned" or request.path == "/sign-out" or "/static" in request.path):
            return redirect("/banned")

@app.context_processor
def inject_notification_count():
    c = current_user
    try:
        if c._get_current_object().is_authenticated():
            return dict(notification_count=c._get_current_object().get_notification_count())
        else:
            return dict(notification_count=0)
    except:
        return dict(notification_count=0)

@app.before_request
def log_request():
    l = Log(
        method=request.method,
        path=request.path,
        ip_address=request.remote_addr,
        agent_platform=request.user_agent.platform,
        agent_browser=request.user_agent.browser,
        agent_browser_version=request.user_agent.version,
        agent=request.user_agent.string,
        time=arrow.utcnow().datetime
    )
    try:
        if current_user.is_authenticated():
            l.user = current_user._get_current_object()
            l.user_name = current_user.login_name
        l.save()
    except:
        pass

@app.route('/get-user-info-api', methods=['POST',])
def get_user_info_api():
    request_json = request.get_json(force=True)
    user_name = unicode(request_json.get("user"))
    user_name = urllib.unquote(user_name)
    
    try:
        user = User.objects(login_name=user_name)[0]
    except:
        return app.jsonify(data=False)
    
    try:
        last_at = user.last_seen_at
        last_url = user.last_at_url
    except:
        last_at = False
        last_url = ""
    
    return app.jsonify(
        avatar_image=user.get_avatar_url("60"),
        avatar_x=user.avatar_60_x,
        avatar_y=user.avatar_60_y,
        name=user.display_name,
        login_name=user.login_name,
        last_seen=humanize_time(user.last_seen),
        last_seen_at=last_at,
        last_seen_url=last_url,
        joined=humanize_time(user.joined),
        roles=user.get_roles()
    )

@app.route('/make-report', methods=['POST'])
@login_required
def make_report():
    request_json = request.get_json(force=True)
    
    _type = request_json.get("content_type", "post")
    text = request_json.get("reason", "Blank reason.")
    
    if _type == "post":
        try:
            content = Post.objects(pk=request_json.get("pk"))[0]
        except:
            return abort(500)
        content_id = content.pk
        content_html = content.html
        url = "/t/%s/page/1/post/%s" % (content.topic.slug, content.pk)
    elif _type == "pm":
        try:
            content = PrivateMessage.objects(pk=request_json.get("pk"))[0]
        except:
            return abort(500)
        content_id = content.pk
        content_html = content.message
        url = "/messages/%s/page/1/post/%s" % (content.topic.pk, content.pk)
    elif _type == "status":
        try:
            content = StatusUpdate.objects(pk=request_json.get("pk"))[0]
        except:
            return abort(500)
        content_id = content.pk
        content_html = content.message
        url = "/messages/%s/page/1/post/%s" % (content.topic.pk, content.pk)
    elif _type == "profile":
        try:
            content = User.objects(pk=request_json.get("pk"))[0]
        except:
            return abort(500)
        content_id = content.pk
        content_html = content.about_me
        url = "/member/%s" % (content.login_name)
    
    try:
        report = Report.objects(
            content_type=_type, 
            content_pk=str(content_id),
            initiated_by=current_user._get_current_object(), 
            created__gte=arrow.utcnow().replace(hours=-24).datetime
            )[0]
        return app.jsonify(status="reported")
    except:
        pass
    
    report = Report(
        content_type = _type,
        content_pk = str(content_id),
        report = text,
        content_reported = content_html,
        initiated_by = current_user._get_current_object(),
        initiated_by_u = current_user._get_current_object().display_name,
        created = arrow.utcnow().datetime,
        url = url
    )
    report.save()
    
    broadcast(
        to=list(User.objects(is_admin=True)), 
        category="mod", 
        url=url,
        title="A %s was reported by %s." % (_type, unicode(current_user._get_current_object().display_name)),
        description=text, 
        content=report, 
        author=current_user._get_current_object()
        )
    return app.jsonify(status="reported")

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

@app.route('/upload-image', methods=['POST',])
@login_required
def grab_image():
    request_json = request.get_json(force=True)
    image_source = request_json.get("image")
    
    try: 
        br = mechanize.Browser()
        # image_response = requests.get(image_source, verify=False, headers=headers)
        br.set_handle_robots(False)
        resp = br.open(image_source)
        image_response = resp.read()
    except:
        return app.jsonify(error="There was an error linking to your image.")
        
    if resp.code == 404:
        return app.jsonify(error="This image does not exist. Are you sure the URL is right?")
        
    if str(resp.code).startswith("40"):
        return app.jsonify(error="This image is not publicly accessible. Are you sure the URL is right?")
        
    if resp.code == 500:
        return app.jsonify(error="The server hosting this image seems to be down. Try again later?")
    
    image_domain = image_source.split("/")[2]
    filename = image_source.split("/")[-1].split("?")[0]
    destination_path = os.path.join(os.getcwd(),"woe/static/uploads/linked/",hashlib.md5(image_domain).hexdigest())
    destination_filename = os.path.join(os.getcwd(),"woe/static/uploads/linked/",hashlib.md5(image_domain).hexdigest(),filename)
    extension = filename.split(".")[-1]
    
    image_hash = hashlib.sha256(image_response).hexdigest()
    # try:
    #     attach = Attachment.objects(file_hash=image_hash)[0]
    #     return app.jsonify(attachment=str(attach.pk), xsize=attach.x_size)
    # except:
    #     pass
    
    try:
        image = Image(file=StringIO.StringIO(image_response))
        if os.path.exists(destination_filename):
            destination_filename = os.path.join(os.getcwd(),"woe/static/uploads/linked/",hashlib.md5(image_domain).hexdigest(),filename.replace("."+extension, "."+str(time.time())+"."+extension))
            filename = filename.replace("."+extension, "."+str(time.time())+"."+extension)
    except:
        return app.jsonify(error="There was an error processing this attachment, please verify that this file is an image file.")
        
    attach = Attachment()
    attach.x_size = image.width
    attach.y_size = image.height
    attach.mimetype = mimetypes.guess_type(filename)[0]
    attach.extension = extension
    attach.size_in_bytes = len(image_response)
    attach.owner_name = current_user._get_current_object().login_name
    attach.owner = current_user._get_current_object()
    attach.alt = filename
    attach.used_in = 1
    attach.created_date = arrow.utcnow().datetime
    attach.file_hash = image_hash
    attach.linked = True
    attach.origin_url = image_source
    attach.origin_domain = image_domain
    
    if not os.path.exists(destination_path):
        os.makedirs(destination_path)
        
    image.save(filename=destination_filename)
    attach.path = os.path.join("linked/", hashlib.md5(image_domain).hexdigest(), filename)
    attach.save()
    
    return app.jsonify(attachment=str(attach.pk), xsize=attach.x_size)

@app.route('/robots.txt')
def static_from_root():
    return send_from_directory(app.static_folder, app.settings_file.get("robots-alt", request.path[1:]))

@login_manager.user_loader
def load_user(login_name):
    try:
        user = User.objects(login_name=login_name)[0]
        user.update(last_seen=arrow.utcnow().datetime)
        if request.path.startswith("/message"):
            user.update(last_seen_at="Private messages")
            user.update(last_at_url="/messages")
        elif request.path == "/":
            user.update(last_seen_at="Forum index")
            user.update(last_at_url="/")
        elif request.path.startswith("/admin"):
            user.update(last_seen_at="Forum index")
            user.update(last_at_url="/")
        elif request.path.startswith("/t/"):
            try:
                topic = Topic.objects(slug=request.path.split("/")[2])[0]
                user.update(last_seen_at=unicode(topic.title))
                user.update(last_at_url="/t/"+unicode(topic.slug))
            except:
                pass
        elif request.path.startswith("/status-updates"):
            user.update(last_seen_at="Viewing status updates")
            user.update(last_at_url="/status-updates")            
        elif request.path.startswith("/status/"):
            try:
                status = StatusUpdate.objects(pk=request.path.split("/")[2])[0]
                user.update(last_seen_at=unicode(status.author.display_name)+"\'s status update")
                user.update(last_at_url="/status/"+unicode(status.pk))
            except:
                pass
        elif request.path.startswith("/category/"):
            try:
                category = Category.objects(slug=request.path.split("/")[2])[0]
                user.update(last_seen_at=category.name)
                user.update(last_at_url="/category/"+unicode(category.slug))
            except:
                pass
        elif request.path.startswith("/search"):
            user.update(last_seen_at="Searching...")
            user.update(last_at_url="/search")
            
        try:
            ip_address = IPAddress.objects(ip_address=request.remote_addr, user=user)[0]
        except:
            ip_address = IPAddress(ip_address=request.remote_addr, user=user, user_name=user.login_name)
            ip_address.save()
        ip_address.update(last_seen=arrow.utcnow().datetime)
            
        if user.validated:
            return user
        else:
            return None
    except IndexError:
        return None

@app.route('/password-reset/<token>', methods=['GET', 'POST'])
def password_reset(token):
    if current_user.is_authenticated():
        return abort(404)
    
    try:
        user = User.objects(password_forgot_token=token)[0]
    except:
        return abort(404)
    
    form = ResetPasswordForm(csrf_enabled=False)
    form.user = user
    if form.validate_on_submit():
        user.password_forgot_token = None
        user.password_forgot_token_date = None
        user.set_password(form.password.data.strip())
        user.save()
        login_user(user)
        broadcast(
            to=[user,],
            category="other", 
            url="/member/"+unicode(user.login_name),
            title="Password reset successful! Welcome back %s!" % (unicode(user.display_name),),
            description="",
            content=user, 
            author=user
            )
        return redirect("/")
        
    return render_template("new_password.jade", page_title="Forgot Password - World of Equestria", form=form, token=token)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated():
        return abort(404)
    
    form = ForgotPasswordForm(csrf_enabled=False)
    if form.validate_on_submit():
        time = str(arrow.utcnow().timestamp)+"THIS IS A POINTLESS BIT OF TEXT LOL"
        token = bcrypt.generate_password_hash(time,10).encode('utf-8').replace("/","_")
        form.user.password_forgot_token = token
        form.user.password_forgot_token_date = arrow.utcnow().datetime
        form.user.save()
        return render_template("forgot_password_confirm.jade", page_title="Forgot Password - World of Equestria", profile=form.user)
    
    return render_template("forgot_password.jade", page_title="Forgot Password - World of Equestria", form=form)

@app.route('/hello/<pk>')
def confirm_register(pk):
    try:
        user = User.objects(pk=pk)[0]
    except:
        return abort(404)
    return render_template("welcome_new_user.jade", page_title="Welcome! - World of Equestria", profile=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated():
        return abort(404)
    
    form = RegistrationForm(csrf_enabled=False)
    form.ip = request.remote_addr
    if form.validate_on_submit():
        new_user = User(
            login_name = form.username.data.strip().lower(),
            display_name = form.username.data.strip(),
            email_address = form.email.data.strip().lower()
        )
        new_user.set_password(form.password.data.strip())
        new_user.joined = arrow.utcnow().datetime
        new_user.over_thirteeen = True
        new_user.how_did_you_find_us = form.how_did_you_find_us.data
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
        if form.user.banned:
            return redirect("/banned")
            
        login_user(form.user)
        
        try:
            fingerprint__info_from_browser = json.loads(request.form.get("log_in_token"))
        except:
            fingerprint__info_from_browser = {"pl": []}
        
        fingerprint_data = {}
        fingerprint_data["current_user"] = form.user.login_name
        fingerprint_data["screen_width"] = fingerprint__info_from_browser.get("sw", 0)
        fingerprint_data["screen_height"] = fingerprint__info_from_browser.get("sh", 0)
        fingerprint_data["screen_colors"] = fingerprint__info_from_browser.get("cd", 0)
        fingerprint_data["timezone"] = fingerprint__info_from_browser.get("tz", 0)
        
        for browser_plugin in fingerprint__info_from_browser.get("pl", []):
            try:
                fingerprint_data[browser_plugin["name"].replace(".", "dt").replace("$", "dl")] = browser_plugin["description"]
            except:
                pass
                
        for browser_plugin in fingerprint__info_from_browser.get("pl", []):
            try:
                for browser_plugin_object in browser_plugin.keys():
                    fingerprint_data[browser_plugin_object] = browser_plugin[browser_plugin_object]
            except:
                pass
            
        fingerprint_data["agent_platform"] = request.user_agent.platform
        fingerprint_data["agent_browser"] = request.user_agent.browser
        fingerprint_data["agent_browser_version"] = request.user_agent.version
        fingerprint_data["agent"] = request.user_agent.string
        
        try:
            for element in request.user_agent.platform.split(" "):
                fingerprint_data[element] = element
        except:
            pass
        
        try:
            for element in request.user_agent.browser.split(" "):
                fingerprint_data[element] = element
        except:
            pass
        
        try:
            for element in request.user_agent.version.split(" "):
                fingerprint_data[element] = element
        except:
            pass
        
        try:
            for element in request.user_agent.string.split(" "):
                fingerprint_data[element] = element
        except:
            pass
        
        try:
            obj = IPWhois(request.remote_addr)
            results=obj.lookup(get_referral=True)
            fingerprint_data["ip_owner"] = results["nets"][0]["name"]
        except:
            pass
        
        clean_fingerprint_data = {}
        fingerprint_hash = ""
        for key, value in sorted(fingerprint_data.items()):
            fingerprint_hash += unicode(key) + " "
            fingerprint_hash += unicode(value) + " "
            clean_fingerprint_data[key.replace(".", "dt").replace("$", "dl")]=value
        
        _fingerprint_hash = hashlib.sha256(fingerprint_hash.encode('utf-8')).hexdigest()
        
        try:
            f = Fingerprint.objects(fingerprint_hash=_fingerprint_hash)[0]
            f.update(last_seen=arrow.utcnow().datetime)
        except:
            f = Fingerprint()
            f.user = form.user
            f.user_name = form.user.login_name
            f.last_seen = arrow.utcnow().datetime
            f.fingerprint = clean_fingerprint_data
            f.fingerprint_hash = _fingerprint_hash
            f.fingerprint_factors = len(clean_fingerprint_data)
            try:
                f.save()
            except:
                pass
            
        try:
            return redirect(form.redirect_to.data)
        except:
            return redirect("/")
    else:
        form.redirect_to.data = request.args.get('next', "/")
        
    return render_template("sign_in.jade", page_title="Sign In - World of Equestria", form=form)

@app.route('/banned')
def banned_user():
    image_dir = os.path.join(os.getcwd(),"woe/static/banned_images/")
    images = ["/static/banned_images/"+unicode(i) for i in os.listdir(image_dir)]
    return render_template("banned.jade", page_title="You Are Banned.", images=images)

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
    
    results_starting_ = []
    results_other_ = []
    
    for result in results:
        if result["text"].lower().startswith(query.lower()[0]):
            results_starting_.append(result)
        else:
            results_other_.append(result)
            
    results_starting_.extend(results_other_)
    return app.jsonify(results=results_starting_)
    
@app.route('/user-list-api-variant', methods=['GET'])
@login_required
def user_list_api_variant():
    query = request.args.get("q", "")[0:100]
    if len(query) < 2:
        return app.jsonify(results=[])
    results = [{"text": unicode(u.display_name), "id": unicode(u.login_name)} for u in User.objects(Q(display_name__icontains=query) | Q(login_name__icontains=query))]
    
    results_starting_ = []
    results_other_ = []
    
    for result in results:
        if result["text"].lower().startswith(query.lower()[0]):
            results_starting_.append(result)
        else:
            results_other_.append(result)
            
    results_starting_.extend(results_other_)
    return app.jsonify(results=results_starting_)

@app.route('/members', methods=["GET",])
@login_required
def show_memeber_listing():
    return render_template("members.jade", page_title="Members - World of Equestria")
    
@app.route('/member-list-api', methods=["GET",])
@login_required
def member_list_api():    
    try:
        current = int(request.args.get("start"))
    except:
        current = 0
        
    try:
        draw = int(request.args.get("draw"))
    except:
        draw = 0
        
    try:
        length = int(request.args.get("length"))
    except:
        length = 10
    
    try:
        order = int(request.args.get("order[0][column]"))
    except:
        order = 4
        
    if order == 4:
        order = "joined"
    elif order == 5:
        order = "last_seen"
    elif order == 3:
        order = "roles"
    elif order == 0:
        order = "display_name"
    else:
        order = "joined"
    
    try:
        direction = request.args.get("order[0][dir]")
    except:
        direction = "desc"
        
    if direction == "desc":
        order = "-"+order
    
    query = request.args.get("search[value]", "")[0:100]
    
    member_count = User.objects(Q(display_name__icontains=query) | Q(login_name__icontains=query), banned=False).count()
    users = User.objects(Q(display_name__icontains=query) | Q(login_name__icontains=query), banned=False).order_by(order)[current:current+length]
    table_data = []
    for i, user in enumerate(users):
        my_roles = [" <b>"+role+"</b>" for role in user.get_roles()]
        roles_template = """"""
        if len(my_roles) > 0:
            roles_template += """<a class="btn btn-default toggle-show-roles-button btn-xs" style="margin-top: 5px;">Community Roles</a>
            <div class="roles-div" style="display: none;">
            """
            for r in my_roles:
                roles_template += r + "<br>"
            roles_template += """</div>"""
        
        extra = ""
        if i > 7:
            extra = """data-hplacement=\"top\""""
        
        table_data.append(
            [
                """<a href="/member/%s"><img src="%s" width="%spx" height="%spx" class="avatar-mini" style="margin-right: 15px;"/></a>
                <a class="hover_user" %s href="/member/%s">%s</a>""" % (unicode(user.login_name), 
                                                                        user.get_avatar_url("60"), 
                                                                        user.avatar_60_x, 
                                                                        user.avatar_60_y, 
                                                                        extra,
                                                                        unicode(user.login_name), 
                                                                        unicode(user.display_name)),
                humanize_time(user.joined),
                humanize_time(user.last_seen),
                roles_template,
                arrow.get(user.joined).timestamp,
                arrow.get(user.last_seen).timestamp
            ]
        )
    data = {
        "draw": draw,
        "recordsTotal": member_count,
        "recordsFiltered": member_count,
        "data": table_data
    }
    return app.jsonify(data)
