from lxml.html.clean import Cleaner
import hashlib
import arrow
from woe import app
import cgi, pytz, os
import regex as re
from woe import sqla
from flask.ext.login import current_user
from mongoengine.queryset import Q
from BeautifulSoup import BeautifulSoup

url_rgx = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
spec_characters = re.compile('&[a-z]{2,5};')
link_re = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')
bbcode_re = re.compile("(\[(attachment|custompostcaracter|postcharacter|spoiler|center|img|quote|font|color|size|url|b|i|s|prefix|@|reply|character|postcharacter|list).*?\])")

from HTMLParser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

words_re = re.compile("[a-zA-Z]+")

def strip_tags(html):
    spc = spec_characters.findall(html)
    for sp in spc:
        html = html.replace(sp[0], "")
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

def parse_search_string_return_q(search_text, fields_to_search):
    if search_text.strip() == "":
        return Q()

    and_terms = []
    not_terms = []

    search_tokens = search_text.split(" ")

    token_buffer = ""
    quote_active = False
    negative = False
    for i, token in enumerate(search_tokens):
        if token.strip() == "":
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

    q_params = []

    for term in and_terms:
        for field in fields_to_search:
            field_name_mongoengine = field + "__icontains"
            q_param = {field_name_mongoengine: term}
            q_params.append(q_param)

    for term in not_terms:
        for field in fields_to_search:
            field_name_mongoengine = field + "__not__icontains"
            q_param = {field_name_mongoengine: term}
            q_params.append(q_param)

    if len(q_params) == 0:
        return Q()

    q_to_return = Q(**q_params[0])

    for q_parameter in q_params[1:]:
        q_to_return = q_to_return & Q(**q_parameter)

    return q_to_return

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
    return hashlib.md5(txt).hexdigest()

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
    ":wat:" : "applejack_confused_by_angelishi-d6wk2ew.gif",
    ":hoofbump:" : "brohoof_by_angelishi-d6wk2et.gif",
    ":derp:" : "derpy_by_angelishi-d7amv0j.gif",
    ":)" : "fluttershy_happy_by_angelishi.gif",
    ":(" : "fluttershy_sad_by_angelishi.gif",
    ":liarjack:" : "liar_applejack_by_angelishi-d7aglwl.gif",
    ":love:" : "love_spike_by_angelishi-d7amv0g.gif",
    ":moonjoy:" : "moon_by_angelishi-d7amv0a.gif",
    ":S" : "nervous_aj_by_angelishi-d7ahd5y.gif",
    ":pinkamena:" : "pinkamena_by_angelishi-d6wk2er.gif",
    ":D" : "pinkie_laugh_by_angelishi-d6wk2ek.gif",
    ":mustache:" : "pinkie_mustache_by_angelishi-d6wk2eh.gif",
    ":P" : "pinkie_silly_by_angelishi-d6wk2ef.gif",
    ":cool:" : "rainbowdash_cool_by_angelishi.gif",
    ":pleased:" : "rarity_happy_by_angelishi.gif",
    ":shocked:" : "rarity_shock_2_by_angelishi-d6wk2eb.gif",
    ":rofl:" : "rd_laugh_by_angelishi-d7aharw.gif",
    ":sing:" : "singing_rarity_by_angelishi-d7agp33.gif",
    ":sunjoy:" : "sun_happy_by_angelishi-d6wlo5g.gif",
    ":twitch:" : "twilight___twitch_by_angelishi.gif",
    ":?" : "twilight_think_by_angelishi.gif",
    ":yawn:" : "rd_yawn_by_angelishi-d9cwc1o.gif",
    ":want:" : "scootaloo_want_face_by_angelishi-d7xyd7g.gif",
    ":unamused:" : "celestia_noapproval_by_angelishi-d9cwc1c.png",
    ":playful:" : "celestia_playful_by_angelishi-d9cwc1g.gif",
    ":jester:" : "head_wobble_by_angelishi-d9cwc16.gif",
    ":plz:" : "luna_please_by_angelishi-d9cwc1l.gif",
    ":troll:" : "discord_troll_laugh_by_angelishi-d7xyd7m.gif",
    ":shy:" : "embarrassed_fluttershy_by_angelishi-d7xyd7k.gif",
    ":horror:" : "shocked_fluttershy_by_angelishi-d7xyd7j.gif",
    ";)" : "twilight_wink_by_angelishi.gif"
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

    def escape(self, dirty_text):
        text = cgi.escape(dirty_text)

        urls = url_rgx.findall(text)
        for url in urls:
            text = text.replace(url, """<a href="%s" target="_blank">%s</a>""" % (unicode(url), unicode(url),), 1)

        for smiley in emoticon_codes.keys():
            img_html = """<img src="%s" />""" % (os.path.join("/static/emoticons",emoticon_codes[smiley]),)
            text = text.replace(smiley, img_html)

        return text

    def clean(self, dirty_html):
        html = self.cleaner.clean_html(dirty_html)
        if html[0:5] == "<div>":
            html = html[5:]
        if html[-6:] == "</div>":
            html = html[:-6]

        return html

@app.template_filter('humanize_time')
def humanize(time, format_str="MMM D YYYY, hh:mm a"):
    if time == None:
        return ""

    try:
        timezone = current_user._get_current_object().time_zone
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
            return "Today " + a.format("hh:mm a")
        elif a > b and (now.day-1) == a.day:
            return "Yesterday " + a.format("hh:mm a")
        else:
            return a.format(format_str)
    except:
        return ""

def humanize_time(time, format_str="MMM D YYYY, hh:mm a"):
    if time == None:
        return ""

    try:
        timezone = current_user._get_current_object().time_zone
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
            return "Today " + a.format("hh:mm a")
        elif a > b and (now.day-1) == a.day:
            return "Yesterday " + a.format("hh:mm a")
        else:
            return a.format(format_str)
    except:
        return ""
