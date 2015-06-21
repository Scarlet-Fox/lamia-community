from lxml.html.clean import Cleaner
import hashlib
import arrow
from woe import app
import cgi, re, pytz
from flask.ext.login import current_user
from mongoengine.queryset import Q

url_rgx = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

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

def get_top_frequences(frequencies, trim, floor=10):
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

class ForumHTMLCleaner(object):
    def __init__(self):
        self.cleaner = Cleaner(
            style=False,
            links=True,
            add_nofollow=True,
            page_structure=False,
            safe_attrs_only=False
        )
        
    def escape(self, dirty_text):
        text = cgi.escape(dirty_text)
            
        urls = url_rgx.findall(text)
        for url in urls:
            text = text.replace(url, """<a href="%s" target="_blank">%s</a>""" % (unicode(url), unicode(url),), 1)
            
        return text    
    
    def clean(self, dirty_html):
        html = self.cleaner.clean_html(dirty_html)
        if html[0:5] == "<div>":
            html = html[5:]
        if html[-6:] == "</div>":
            html = html[:-6]
        
        return html
        
@app.template_filter('humanize_time')
def humanize(time):
    if time == None:
        return ""
        
    try:
        timezone = current_user._get_current_object().time_zone
    except:
        timezone = "US/Pacific"
    
    try:        
        a = arrow.get(time)
        b = arrow.utcnow().replace(hours=-1)
        if a > b:
            return a.humanize()
        else:
            return a.to(timezone).format("MMM D YYYY, hh:mm a")
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
        a = arrow.get(time)
        b = arrow.utcnow().replace(hours=-1)
        if a > b:
            return a.humanize()
        else:
            return a.to(timezone).format(format_str)
    except:
        return ""
