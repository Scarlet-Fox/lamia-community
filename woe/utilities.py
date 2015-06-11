from lxml.html.clean import Cleaner
import hashlib
import arrow
from woe import app

def parse_search_string_return_q(search_text, fields_to_search):
    and_terms = []
    not_terms = []
    
    search_tokens = search_text.split(" ")
    
    for token in search_tokens:
        current_value_of_token = ""
        negative = False
        quote_active = True
        
        if token[0] == "-":
            negative = True
            token = token[1:]    
        
        if token[0] == "\"":
            print
    

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
        
    def clean(self, dirty_html):
        html = self.cleaner.clean_html(dirty_html)
        if html[0:5] == "<div>":
            html = html[5:]
        if html[-6:] == "</div>":
            html = html[:-6]
        return html
        
class ForumPostParser(object):
    def __init__(self):
        pass
        
    def parse(self, html):
        html = html.replace("[hr]", "<hr>")
        return html

@app.template_filter('humanize_time')
def humanize(time):
    a = arrow.get(time)
    b = arrow.utcnow().replace(hours=-24)
    if a > b:
        return a.humanize()
    else:
        return a.format("MMM D, hh:mm a")
        
def humanize_time(time, format_str="MMM D YYYY, hh:mm a"):
    a = arrow.get(time)
    b = arrow.utcnow().replace(hours=-24)
    if a > b:
        return a.humanize()
    else:
        return a.format(format_str)
