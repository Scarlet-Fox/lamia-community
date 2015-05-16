from lxml.html.clean import Cleaner

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
        return text