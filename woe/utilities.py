from lxml.html.clean import Cleaner
import hashlib

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
        return self.cleaner.clean_html(dirty_html)
        
class ForumPostParser(object):
    def __init__(self):
        pass
        
    def parse(self, text):
        text = text.replace("[hr]", "<hr>")
        return text