from lxml.html.clean import Cleaner
import hashlib
import arrow
from lamia import app
import cgi, pytz, os
try:
    import regex as re
except:
    import re
from lamia import sqla
from flask_login import current_user
from BeautifulSoup import BeautifulSoup
from sqlalchemy.sql import text
from datetime import timedelta
from functools import update_wrapper
from flask import request, make_response
from urllib import urlencode
current_app = app

url_rgx = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
spec_characters = re.compile('&[a-z0-9]{2,5};')
twitter_hashtag_re = re.compile(r'(?<=^|(?<=[^a-zA-Z0-9-\.]))#([A-Za-z]+[A-Za-z0-9-]+)')
twitter_user_re = re.compile(r'(?<=^|(?<=[^a-zA-Z0-9-\.]))@([A-Za-z]+[A-Za-z0-9-]+)')
link_re = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')
bbcode_re = re.compile("(\[(attachment|custompostcaracter|postcharacter|spoiler|center|img|quote|font|color|size|url|b|i|s|prefix|@|reply|character|postcharacter|list).*?\])")

from HTMLParser import HTMLParser

class CategoryPermissionCalculator(object):
    def __init__(self, user):
        self.user_is_admin = user.is_admin
        
        raw_user_role_permissions = sqla.engine.execute(
            text("""SELECT category_id, bool_or(can_create_topics), bool_or(can_post_in_topics), bool_or(can_view_topics)
                FROM ( 
                    SELECT c.id AS category_id, cpo.can_create_topics, cpo.can_post_in_topics, cpo.can_view_topics
                	FROM user_roles ur
                	JOIN category_permission_override cpo ON ur.role_id = cpo.role_id
                	JOIN category c ON c.id = cpo.category_id
                    WHERE user_id = :uid
                ) perms
                GROUP BY category_id"""),
                uid=user.id
            )
        
        user_role_permissions = {}
    
        for _category_perm in raw_user_role_permissions:
            user_role_permissions[_category_perm[0]] = {
                    "can_create_topics": _category_perm[1],
                    "can_post_in_topics": _category_perm[2],
                    "can_view_topics": _category_perm[3]
                }
            
        self.user_role_permissions = user_role_permissions
        
    def can_view_topics(self, category_id, category_can_view_topics):
        if self.user_is_admin:
            return True
        
        if not self.user_role_permissions.has_key(category_id):
            if category_can_view_topics != None:
                return category_can_view_topics
            else:
                return True
            
        return self.user_role_permissions[category_id]["can_view_topics"]
        
    def can_post_in_topics(self, category_id, category_can_post_in_topics):
        if self.user_is_admin:
            return True
        
        if not self.user_role_permissions.has_key(category_id):
            if category_can_post_in_topics != None:
                return category_can_post_in_topics
            else:
                return True
            
        return self.user_role_permissions[category_id]["can_post_in_topics"]
        
    def can_create_topics(self, category_id, category_can_create_topics):
        if self.user_is_admin:
            return True
        
        if not self.user_role_permissions.has_key(category_id):
            if category_can_create_topics != None:
                return category_can_create_topics
            else:
                return True
            
        return self.user_role_permissions[category_id]["can_create_topics"]

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

words_re = re.compile("[a-zA-Z0-9']+")

def strip_tags(html):
    spc = spec_characters.findall(html)
    for sp in spc:
        html = html.replace(sp, "")
    links = link_re.findall(html)
    for link in links:
        html = html.replace(link[0], "")
    bbcode = bbcode_re.findall(html)
    for code in bbcode:
        html = html.replace(code[0], "")
    soup = BeautifulSoup(html)
    text = soup.getText()
    words = words_re.findall(text)
    return words

def get_preview_for_email(html):
    spc = spec_characters.findall(html)
    for sp in spc:
        html = html.replace(sp, "")
    links = link_re.findall(html)
    for link in links:
        html = html.replace(link[0], "")
    bbcode = bbcode_re.findall(html)
    for code in bbcode:
        html = html.replace(code[0], "")
    soup = BeautifulSoup(html)
    text = soup.getText()
    if len(text) > 100:
        text = text[:100] + "..."
    return text

def get_preview(html, characters):
    spc = spec_characters.findall(html)
    for sp in spc:
        html = html.replace(sp, "")
    links = link_re.findall(html)
    for link in links:
        html = html.replace(link[0], "")
    bbcode = bbcode_re.findall(html)
    for code in bbcode:
        html = html.replace(code[0], "")
    soup = BeautifulSoup(html)
    text = soup.getText()
    if len(text) > characters:
        text = text[:characters] + "..."
    return text

def parse_search_string(search_text, model, query_object, fields_to_search):
    if search_text.strip() == "":
        return query_object

    and_terms = []
    not_terms = []

    search_tokens = search_text.split(" ")

    token_buffer = ""
    quote_active = False
    negative = False
    for i, token in enumerate(search_tokens):
        if token.strip() == "":
            continue
        if token == "-":
            continue
        if token == "\"":
            continue

        if token[0] == "-":
            negative = True
            token = token[1:]
        else:
            if not quote_active:
                negative = False

        if token[0] == "\"":
            for look_forward_token in search_tokens[i:]:
                if look_forward_token[len(look_forward_token)-1] == "\"":
                    quote_active = True
            token = token[1:]

        if token[len(token)-1] == "\"":
            token_buffer = token_buffer.strip() + " " + token[:len(token)-1]
            quote_active = False

        if quote_active:
            token_buffer = token_buffer.strip() + " " + token + " "
        else:
            if token_buffer == "":
                token_buffer = token

            if negative:
                not_terms.append(token_buffer)
            else:
                and_terms.append(token_buffer)
            token_buffer = ""

    or_groups = []

    for term in and_terms:
        and_query = []
        for field in fields_to_search:
            if type(field) is str:
                and_query.append(getattr(model, field).ilike("%%%s%%" % term.strip()))
            else:
                and_query.append(field.ilike("%%%s%%" % term.strip()))
        or_groups.append(and_query)

    for term in not_terms:
        and_query = []
        for field in fields_to_search:
            if type(field) is str:
                and_query.append(~getattr(model, field).ilike("%%%s%%" % term.strip()))
            else:
                and_query.append(~field.ilike("%%%s%%" % term.strip()))
        or_groups.append(and_query)

    for or_group in or_groups:
        query_object = query_object.filter(sqla.or_(*or_group))

    return query_object

def scrub_json(list_of_json, fields_to_scrub=[]):
    for o in list_of_json:
        for f in fields_to_scrub:
            try:
                del o[f]
            except KeyError:
                continue

def get_top_frequences(frequencies, trim, floor=1):
    inside_out = {}

    for key, value in frequencies.items():
        if value > floor:
            inside_out[value] = key

    values = inside_out.keys()
    values.sort()
    values.reverse()
    keys = [inside_out[v] for v in values]

    return ([keys[:trim], values[:trim]])

def md5(txt):
    return unicode(txt) #hashlib.md5(txt).hexdigest()

def ipb_password_check(salt, old_hash, password):
    password = password.replace("&", "&amp;") \
            .replace("\\", "&#092;") \
            .replace("!", "&#33;") \
            .replace("$", "&#036;") \
            .replace("\"", "&quot;") \
            .replace("<", "&lt;") \
            .replace(">", "&gt;") \
            .replace("\'", "&#39;")
    new_hash = md5( md5(salt) + md5(password) )

    return new_hash == old_hash

emoticon_codes = {
    ":anger:" : "angry.png",
    ":)" : "smile.png",
    ":(" : "sad.png",
    ":heart:" : "heart.png",
    ":O" : "oh.png",
    ":o" : "oh.png",
    ":surprise:" : "oh.png",
    ":wink:" : "wink.png",
    ";)" : "wink.png",
    ":cry:" : "cry.png",
    ":P" : "tongue.png",
    ":silly:" : "tongue.png",
    ":blushing:" : "embarassed.png",
    ":lol:" : "biggrin.png",
    ":D" : "biggrin.png",
}

class ForumHTMLCleaner(object):
    def __init__(self):
        self.cleaner = Cleaner(
            style=False,
            links=True,
            add_nofollow=True,
            page_structure=False,
            safe_attrs_only=False
        )

    def basic_escape(self, dirty_text):
        text = cgi.escape(dirty_text)
        return text
        
    def tweet_clear(self, dirty_text):
        text = cgi.escape(dirty_text)

        urls = url_rgx.findall(text)
        for url in urls:
            text = text.replace(url, """<a href="%s" target="_blank">%s</a>""" % (unicode(url), unicode(url),), 1)

        hashtags = twitter_hashtag_re.findall(text)
        for hashtag in hashtags:
            text = text.replace("#"+hashtag, """<a href="%s" target="_blank">%s</a>""" % (unicode("https://twitter.com/hashtag/")+unicode(hashtag), unicode("#")+unicode(hashtag),), 1)

        users = twitter_user_re.findall(text)
        for user in users:
            text = text.replace("@"+user, """<a href="%s" target="_blank">%s</a>""" % (unicode("https://twitter.com/")+unicode(user), unicode("@")+unicode(user),), 1)

        return text

    def escape(self, dirty_text):
        text = cgi.escape(dirty_text)

        urls = url_rgx.findall(text)
        for url in urls:
            text = text.replace(url, """<a href="%s" target="_blank">%s</a>""" % (unicode(url), unicode(url),), 1)

        for smiley in emoticon_codes.keys():
            img_html = """<img src="%s" />""" % (os.path.join("/static/emotes",emoticon_codes[smiley]),)
            text = text.replace(smiley, img_html)

        return text

    def clean(self, dirty_html):
        try:
            html = self.cleaner.clean_html(dirty_html)
        except:
            html = dirty_html # WARNING - POTENTIALLY STUPID

        if html[0:5] == "<div>":
            html = html[5:]
        if html[-6:] == "</div>":
            html = html[:-6]

        return html

@app.template_filter('twittercleaner')
def twitter_cleaner(twitter):
    cleaner = ForumHTMLCleaner()
    try:
        _html = cleaner.tweet_clear(twitter)
    except:
        return ""
        
    return _html

@app.template_filter('datetimeformat')
def date_time_format(time, format_str="YYYY"):
    if time == None:
        return ""

    try:
        timezone = current_user.time_zone
    except:
        timezone = "US/Pacific"

    try:
        a = arrow.get(time).to(timezone)
        return a.format(format_str)
    except:
        a = arrow.utcnow().to(timezone)
        return a.format(format_str)
        
@app.template_filter()
def number_format(value, tsep=',', dsep='.'):
    s = unicode(value)
    cnt = 0
    numchars = dsep + '0123456789'
    ls = len(s)
    while cnt < ls and s[cnt] not in numchars:
        cnt += 1

    lhs = s[:cnt]
    s = s[cnt:]
    if not dsep:
        cnt = -1
    else:
        cnt = s.rfind(dsep)
    if cnt > 0:
        rhs = dsep + s[cnt+1:]
        s = s[:cnt]
    else:
        rhs = ''

    splt = ''
    while s != '':
        splt = s[-3:] + tsep + splt
        s = s[:-3]

    return lhs + splt[:-1] + rhs

@app.context_processor
def inject_debug():
    return dict(debug=app.debug)

@app.template_filter('next_url_arg')
def url_arg(url):
    return urlencode({"next": url})

@app.template_filter('humanize_time')
def humanize(time, format_str="MMM D YYYY, hh:mm a"):
    if time == None:
        return ""

    try:
        timezone = current_user.time_zone
    except:
        timezone = "US/Pacific"

    try:
        a = arrow.get(time)
        now = arrow.utcnow()
        b = arrow.utcnow().replace(hours=-48)
        c = arrow.utcnow().replace(hours=-24)
        d = arrow.utcnow().replace(hours=-4)
        if a > d:
            return a.to(timezone).humanize()
        elif a > c and now.day == a.day:
            return "Today " + a.to(timezone).format("hh:mma")
        elif a > b and (now.day-1) == a.day:
            return "Yesterday " + a.to(timezone).format("hh:mma")
        else:
            return a.to(timezone).format(format_str)
    except:
        return ""

def humanize_time(time, format_str="MMM D YYYY, hh:mma"):
    if time == None:
        return ""

    try:
        timezone = current_user.time_zone
    except:
        timezone = "US/Pacific"

    try:
        a = arrow.get(time).to(timezone)
        now = arrow.utcnow().to(timezone)
        b = arrow.utcnow().replace(hours=-48).to(timezone)
        c = arrow.utcnow().replace(hours=-24).to(timezone)
        d = arrow.utcnow().replace(hours=-4).to(timezone)
        if a > d:
            return a.humanize()
        elif a > c and now.day == a.day:
            return "Today " + a.format("hh:mma")
        elif a > b and (now.day-1) == a.day:
            return "Yesterday " + a.format("hh:mma")
        else:
            return a.format(format_str)
    except:
        return ""


from flask import render_template
def render_lamia_template(template_name_or_list, **context):    
    return render_template(template_name_or_list, **context)

# Code from https://stackoverflow.com/questions/22181384/javascript-no-access-control-allow-origin-header-is-present-on-the-requested?utm_medium=organic&utm_source=google_rich_qa&utm_campaign=google_rich_qa
def crossdomain(origin=None, methods=None, headers=None, max_age=21600,
                attach_to_all=True, automatic_options=True):
    """Decorator function that allows crossdomain requests.
      Courtesy of
      https://blog.skyred.fi/articles/better-crossdomain-snippet-for-flask.html
    """
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, list):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        """ Determines which methods are allowed
        """
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        """The decorator function
        """
        def wrapped_function(*args, **kwargs):
            """Caries out the actual cross domain code
            """
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers
            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            h['Access-Control-Allow-Credentials'] = 'true'
            h['Access-Control-Allow-Headers'] = \
                "Origin, X-Requested-With, Content-Type, Accept, Authorization"
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator
