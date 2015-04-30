from lxml.html.clean import Cleaner
from django import template
register = template.Library()

def clean_html(value):
    cleaner = Cleaner(style=False, links=True, add_nofollow=True,
        page_structure=False, safe_attrs_only=False)
        
    return cleaner.clean_html(value)

@register.filter(name='clean_html', is_safe=True)
def clean_html_filter(value):
    return clean_html(value)