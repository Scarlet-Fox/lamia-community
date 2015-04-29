from lxml.html.clean import Cleaner

cleaner = Cleaner(style=False, links=True, add_nofollow=True,
    page_structure=False, safe_attrs_only=False)
    
test = open("test.txt", "r").read()

open("test.html", "w").write(cleaner.clean_html(test))