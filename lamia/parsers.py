from lamia import app
from lamia import bcrypt
from lamia.utilities import ipb_password_check, ForumHTMLCleaner
from wand.image import Image
from urllib.parse import quote
import arrow, os, math
try:
    import regex as re
except:
    import re
from flask_login import current_user
from threading import Thread
from lamia import sqla
from bs4 import BeautifulSoup
import lamia.sqlmodels as sqlm
from urllib.parse import urlencode
import bbcode

#quote_re = re.compile(r'\[quote=?(.*?)\](.*)\[\/quote\]', re.DOTALL|re.IGNORECASE)
mention_re = re.compile("\[@(.*?)\]")

youtube_re = re.compile("https?://(?:www\.)?youtu(?:be\.com/watch\?v=|\.be/)([\w\-]+)(&(amp;)?[\w\?=]*)?", re.IGNORECASE)
dailymotion_re = re.compile("(?:dailymotion\.com(?:\/video|\/hub)|dai\.ly)\/([0-9a-z]+)(?:[\-_0-9a-zA-Z]+#video=([a-z0-9]+))?", re.IGNORECASE)
vimeo_re = re.compile("(?:https?:\/\/)?(?:www\.)?vimeo.com\/(?:channels\/(?:\w+\/)?|groups\/(?:[^\/]*)\/videos\/|album\/(?:\d+)\/video\/|)(\d+)(?:$|\/|\?)", re.IGNORECASE)
soundcloud_re = re.compile("(?:(?:https:\/\/)|(?:http:\/\/)|(?:www.)|(?:\s))+(?:soundcloud.com\/)+([a-zA-Z0-9\-\.]+)(?:\/)+([a-zA-Z0-9\-\.]+)", re.IGNORECASE)
spotify_re = re.compile("spotify\.com/(album|track|user/[^/]+/playlist)/([a-zA-Z0-9]+)", re.IGNORECASE)
vine_re = re.compile("(?:vine\.co/v/|www\.vine\.co/v/)(.*)", re.IGNORECASE)
giphy_re = re.compile("(?:giphy\.com/gifs/|gph\.is/)(?:.*)-(.*)", re.IGNORECASE)
_domain_re = re.compile(r'(?im)(?:www\d{0,3}[.]|[a-z0-9.\-]+[.](?:com|net|org|edu|biz|gov|mil|info|io|name|me|tv|us|uk|mobi))')

raw_image_re = re.compile("(<img src=\"(.*?)\"(?:.*)>)")
html_img_re = re.compile(r'<img src=\"(.*?)\">', re.IGNORECASE)
href_re = re.compile("((href|src)=(.*?)>(.*?)(<|>))")

def lamia_linker(url):
    href = url
    
    youtube_match = youtube_re.search(href)
    dailymotion_match = dailymotion_re.search(href)
    vimeo_match = vimeo_re.search(href)
    soundcloud_match = soundcloud_re.search(href)
    spotify_match = spotify_re.search(href)
    vine_match = vine_re.search(href)
    giphy_match = giphy_re.search(href)
    
    if youtube_match:
        video = youtube_match.groups()[0]

        if not current_user.no_images:
            return """<iframe style="max-width: 100%%" width="560" height="315" src="https://www.youtube.com/embed/%s" frameborder="0" allowfullscreen></iframe>""" % (video, )
        else:
            return """<a href="https://www.youtube.com/watch?v=%s" target="_blank">Youtube Link (Embed)</a>""" % (video,)
    elif dailymotion_match:
        video = dailymotion_match.groups()[0]

        if not current_user.no_images:
            return """<iframe style="max-width: 100%%" frameborder="0" width="480" height="270" src="//www.dailymotion.com/embed/video/%s" allowfullscreen></iframe>""" % (video, )
        else:
            return """<a href="http://www.dailymotion.com/video/%s" target="_blank">Dailymotion Link (Embed)</a>""" % (video,)
    elif vimeo_match:
        video = vimeo_match.groups()[0]

        if not current_user.no_images:
            return """<iframe style="max-width: 100%%" src="https://player.vimeo.com/video/%s?color=ffffff&title=0&byline=0&portrait=0" width="500" height="281" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>""" % (video, )
        else:
            return """<a href="https://vimeo.com/%s" target="_blank">Vimeo Link (Embed)</a>""" % (video,)
    elif soundcloud_match:
        sound_user = soundcloud_match.groups()[0]
        sound_track = soundcloud_match.groups()[1]
        options = urlencode({
            "url": "https://soundcloud.com/"+sound_user+"/"+sound_track
            })

        if not current_user.no_images:
            return """<iframe style="max-width: 100%%" width="100%%" height="166" scrolling="no" frameborder="no" src="https://w.soundcloud.com/player/?%s&amp;color=ff5500&amp;auto_play=false&amp;hide_related=false&amp;show_comments=true&amp;show_user=true&amp;show_reposts=false"></iframe>""" % (options,)
        else:
            return """<a href="https://soundcloud.com/%s/%s" target="_blank">Soundcloud Link (%s/%s)</a>""" % (sound_user,sound_track,sound_user,sound_track)
    elif spotify_match:
        uri = spotify_match.groups()[0]
        track = spotify_match.groups()[1]
        uri = "spotify:"+uri.replace("/", ":")+":"+track

        if not current_user.no_images:
            return """<iframe style="max-width: 100%%" src="https://embed.spotify.com/?uri=%s" width="300" height="380" frameborder="0" allowtransparency="true"></iframe>""" % (uri,)
    elif vine_match:
        video = vine_match.groups()[0]

        if not current_user.no_images:
            return """<iframe style="max-width: 100%%" src="https://vine.co/v/%s/embed/simple?autoplay=0" width="400" height="400" frameborder="0"></iframe><script src="https://platform.vine.co/static/scripts/embed.js"></script>""" % (video, )
        else:
            return """<a href="https://vine.co/v/%s" target="_blank">Vine Link (Embed)</a>""" % (video,)
    elif giphy_match:
        giph = giphy_match.groups()[0]

        if not current_user.no_images:
            return """<iframe src="//giphy.com/embed/%s" width="480" height="460" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><p><a href="http://giphy.com/gifs/%s">via GIPHY</a></p>""" % (giph, giph)
        else:
            return """<a href="http://giphy.com/gifs/%s" target="_blank">Giphy Link (Embed)</a>""" % (giph,)
    else:        
        if '://' not in href:
            href = 'http://' + href
        return '<a href="%s">%s</a>' % (href, url)

bbcode_parser = bbcode.Parser(install_defaults=False, escape_html=False, replace_links=True, linker=lamia_linker)
bbcode_parser.add_simple_formatter('hr', '<hr />', standalone=True)
bbcode_parser.add_simple_formatter('b', '<strong>%(value)s</strong>', escape_html=False)
bbcode_parser.add_simple_formatter('i', '<em>%(value)s</em>', escape_html=False)
bbcode_parser.add_simple_formatter('indent', '<div class="well"><div>%(value)s</div></div>', escape_html=False)

bbcode_parser.add_simple_formatter('media', '%(value)s', escape_html=False)
bbcode_parser.add_simple_formatter('roll', '', escape_html=False)
bbcode_parser.add_simple_formatter('s', '<span style="text-decoration: line-through;">%(value)s</span>', escape_html=False)
bbcode_parser.add_simple_formatter('center', '<center>%(value)s</center>', escape_html=False)
bbcode_parser.add_simple_formatter("right", '<div style="text-align: right;"><div>%(value)s</div></div>', escape_html=False)
bbcode_parser.add_simple_formatter("truespoiler", """
        <span class="truespoiler">%(value)s</span>
    """, escape_html=False)

def _render_list(name, value, options, parent, context):
            list_type = options['list'] if (options and 'list' in options) else '*'
            css_opts = {
                '1': 'decimal', '01': 'decimal-leading-zero',
                'a': 'lower-alpha', 'A': 'upper-alpha',
                'i': 'lower-roman', 'I': 'upper-roman',
            }
            tag = 'ol' if list_type in css_opts else 'ul'
            css = ' style="list-style-type:%s;"' % css_opts[list_type] if list_type in css_opts else ''
            return '<%s%s><div>%s</div></%s>' % (tag, css, value, tag)
bbcode_parser.add_formatter('list', _render_list, transform_newlines=False, strip=True, swallow_trailing_newline=True, escape_html=False)
# Make sure transform_newlines = False for [*], so [code] tags can be embedded without transformation.
bbcode_parser.add_simple_formatter('*', '<li>%(value)s</li>', newline_closes=True, transform_newlines=False,
    same_tag_closes=True, strip=True, escape_html=False)

def _render_url(name, value, options, parent, context):
    if options and 'url' in options:
        # Option values are not escaped for HTML output.
        href = bbcode_parser._replace(options['url'], bbcode_parser.REPLACE_ESCAPE)
    else:
        href = value
    # Completely ignore javascript: and data: "links".
    if re.sub(r'[^a-z0-9+]', '', href.lower().split(':', 1)[0]) in ('javascript', 'data', 'vbscript'):
        return ''
    # Only add the missing http:// if it looks like it starts with a domain name.
    if '://' not in href and _domain_re.match(href):
        href = 'http://' + href
    return '<a href="%s">%s</a>' % (href, value)
bbcode_parser.add_formatter('url', _render_url, replace_links=False, replace_cosmetic=False)

bbcode_parser.add_simple_formatter('u', '<u>%(value)s</u>', escape_html=False)
        
bbcode_parser.add_simple_formatter('quote', '<blockquote><div>%(value)s</div></blockquote>', strip=True,
            swallow_trailing_newline=True, escape_html=False)

def render_code_bbcode(tag_name, value, options, parent, context):
    return """<code> <!-- code div -->%s</code>""" % (value,)
bbcode_parser.add_formatter('code', render_code_bbcode, render_embedded=False, replace_cosmetic=False, escape_html=False)    
            
def render_spoiler_bbcode(tag_name, value, options, parent, context):
    if options.get("spoiler", False):
        return """<div class="content-spoiler" data-caption="%s"><div><div> <!-- spoiler div -->%s</div></div></div>""" % (options.get("spoiler"), value,)
    else:
        return """<div class="content-spoiler"><div><div> <!-- spoiler div -->%s</div></div></div>""" % (value,)

bbcode_parser.add_formatter("spoiler", render_spoiler_bbcode, escape_html=False)
bbcode_parser.add_formatter("espoiler", render_spoiler_bbcode, escape_html=False)

def render_button_bbcode(tag_name, value, options, parent, context):
    if options and options.get("button", False):
        return """<a class="btn btn-default" href="%s" target="_blank" role="button">%s</a>""" % (value, options.get("button"))
    else:
        return """<a class="btn btn-default" href="%s" target="_blank" role="button">%s</a>""" % (value, value)
        
bbcode_parser.add_formatter("button", render_button_bbcode, replace_links=False, replace_cosmetic=False)

def render_image_bbcode(tag_name, value, options, parent, context):
    if context.get("strip_images", False):
        return ""
    else:
        if options.get("img", False):
            return """<img src="%s" style="max-width: 100%%;" />""" % options.get("img")
        else:
            return """<img src="%s" style="max-width: 100%%;" />""" % value
    
bbcode_parser.add_formatter("img", render_image_bbcode, escape_html=True, replace_links=False)

def render_prefix_bbcode(tag_name, value, options, parent, context):
    return """
        <span class="badge prefix" style="background:%s; font-size: 10px; font-weight: normal; vertical-align: top; margin-top: 2px;">%s</span>
    """ % (options.get("color","grey"), value)

bbcode_parser.add_formatter("prefix", render_prefix_bbcode, escape_html=True)

def render_align_bbcode(tag_name, value, options, parent, context):
    return """
        <div style="text-align: %s;"><div>%s</div></div>
    """ % (options.get("align","left"), value)

bbcode_parser.add_formatter("align", render_align_bbcode, escape_html=False)
bbcode_parser.add_formatter("left", render_align_bbcode, escape_html=False)

def render_color_bbcode(tag_name, value, options, parent, context):
    return """
        <span style="color: %s;"><span>%s</span></span>
    """ % (options.get("color","blue"), value)

bbcode_parser.add_formatter("color", render_color_bbcode, escape_html=False)

def render_size_bbcode(tag_name, value, options, parent, context):
    return """
        <span style="font-size: %spt;"><span>%s</span></span>
    """ % (options.get("size","12"), value)

bbcode_parser.add_formatter("size", render_size_bbcode, escape_html=False)

def render_font_bbcode(tag_name, value, options, parent, context):
    return """
        <span style="font-family: %s;"><span>%s</span></span>
    """ % (options.get("font",""), value)

bbcode_parser.add_formatter("font", render_font_bbcode, escape_html=False)

def render_progressbar_bbcode(tag_name, value, options, parent, context):
    try:
        _color = options.get("color", "red")
        _value = int(options.get("value", "0"))
    except:
        return ""
        
    return """
            <div class="progress" style="border-radius: 0px; max-width: 75%;">
              <div class="progress-bar" role="progressbar"
              aria-valuenow="VALUEHERE" aria-valuemin="0"
              aria-valuemax="100"
              style="width: VALUEHERE%; background-color: COLORHERE; border-radius: 0px;">
                VALUEHERE%
              </div>
            </div>
        """.replace("VALUEHERE", str(_value)).replace("COLORHERE", _color)
bbcode_parser.add_formatter("progressbar", render_progressbar_bbcode, standalone=True)

def resize_image_save_custom(image_file_location, new_image_file, new_x_size, _id):
    from lamia import sqla
    import lamia.sqlmodels as sqlm

    attachment = sqla.session.query(sqlm.Attachment).filter_by(id=_id)[0]

    try:
        source_image = Image(filename=image_file_location)
    except:
        attachment.do_not_convert=True
        sqla.session.add(attachment)
        sqla.session.commit()
        return False

    original_x = source_image.width
    original_y = source_image.height

    if original_x != new_x_size:
        resize_measure = float(new_x_size)/float(original_x)
        try:
            source_image.resize(int(round(original_x*resize_measure)),int(round(original_y*resize_measure)))
        except:
            attachment.do_not_convert=True
            sqla.session.add(attachment)
            sqla.session.commit()
            return False

    try:
        if attachment.extension == "gif":
            source_image.save(filename=new_image_file.replace(".gif",".animated.gif"))
            first_frame = source_image.sequence[0].clone()
            first_frame.save(filename=new_image_file)
        else:
            source_image.save(filename=new_image_file)
    except:
        attachment.do_not_convert=True
        sqla.session.add(attachment)
        sqla.session.commit()
        return False

def render_attachment_bbcode(tag_name, value, options, parent, context):
    _options = options.get("attachment","").split(":")
    _content_owner = context.get("content_owner", False)
    
    if context.get("strip_images", False):
        return ""
    
    try:
        _attachment_id = _options[0]
    except:
        return ""
        
    try:
        _attachment_size = int(_options[1])
    except:
        ignore_size = True
        
    try:
        _attachment_wrap = _options[2]
    except:
        _attachment_wrap = "wrap"
        
    try:
        attachment = sqla.session.query(sqlm.Attachment).filter_by(id=_attachment_id)[0]
    except:
        sqla.session.rollback()
        return ""
        
    if current_user.no_images:
        return """<a href="/static/uploads/%s" target="_blank">View Attachment.%s (%sKB)</a>""" % (quote(attachment.path.encode('utf-8')), attachment.extension, int(float(attachment.size_in_bytes)/1024))

    if _attachment_size == attachment.x_size:
        ignore_size = True
    else:
        ignore_size = False
        if _attachment_size < 5:
            _attachment_size = 5
        if _attachment_size > 700:
            _attachment_size = 700 # TODO: Max attachment width should be configurable

    if _attachment_wrap == "wrap":
        image_formatting_class = " image-wrap"
    else:
        image_formatting_class = ""

    if attachment.size_in_bytes < 1024*1024*10 or attachment.do_not_convert:
        url = os.path.join("/static/uploads", attachment.path)
        show_box = "no"

        if ignore_size:
            return """
            <img class="attachment-image%s" src="%s" data-show_box="%s" alt="%s" data-url="/static/uploads/%s" data-size="%s"/>
            """ % (image_formatting_class, quote(url.encode('utf-8')), show_box, attachment.alt, quote(attachment.path.encode('utf-8')), int(float(attachment.size_in_bytes)/1024))
        else:
            return """
            <img class="attachment-image%s" src="%s" width="%spx" data-show_box="%s" alt="%s" data-url="/static/uploads/%s" data-size="%s"/>
            """ % (image_formatting_class, quote(url.encode('utf-8')), _attachment_size, show_box, attachment.alt, quote(attachment.path.encode('utf-8')), int(float(attachment.size_in_bytes)/1024))
    else:
        filepath = os.path.join(os.getcwd(), "lamia/static/uploads", attachment.path)
        sizepath = os.path.join(os.getcwd(), "lamia/static/uploads",
            ".".join(filepath.split(".")[:-1])+".custom_size."+_attachment_size+"."+filepath.split(".")[-1])
        
        show_box = "yes"

        if os.path.exists(sizepath):
            url = os.path.join("/static/uploads",
                ".".join(attachment.path.split(".")[:-1])+".custom_size."+_attachment_size+"."+attachment.path.split(".")[-1])
            try:
                new_size = os.path.getsize(sizepath.replace(".gif", ".animated.gif"))
            except:
                new_size = attachment.size_in_bytes
            if attachment.extension == "gif":
                return """
                <div class="click-to-play">
                    <img class="attachment-image%s" src="%s" width="%spx" data-first_click="yes" data-show_box="%s" alt="%s" data-url="/static/uploads/%s" data-size="%s" data-resized-size="%s">
                    <p class="text-warning">This file is %sKB large, click to play.</p>
                </div>
                """ % (image_formatting_class, quote(url.encode('utf-8')), _attachment_size, show_box, attachment.alt, quote(attachment.path.encode('utf-8')), int(float(new_size)/1024), int(float(new_size)/1024), int(float(new_size)/1024))
            elif attachment.extension != "gif":
                return """
                <img class="attachment-image%s" src="%s" width="%spx" data-first_click="yes" data-show_box="%s" alt="%s" data-url="/static/uploads/%s" data-size="%s">
                """ % (image_formatting_class, quote(url.encode('utf-8')), _attachment_size, show_box, attachment.alt, quote(attachment.path.encode('utf-8')), int(float(attachment.size_in_bytes)/1024))
        else:
            thread = Thread(target=resize_image_save_custom, args=(filepath, sizepath, size, attachment.id, ))
            thread.start()
            url = os.path.join("/static/uploads", attachment.path)
            return """
            <img class="attachment-image%s" src="%s" width="%spx" data-first_click="yes" data-show_box="%s" alt="%s" data-url="/static/uploads/%s" data-size="%s">
            """ % (image_formatting_class, quote(url.encode('utf-8')), _attachment_size, "no", attachment.alt, quote(attachment.path.encode('utf-8')), int(float(attachment.size_in_bytes)/1024))

bbcode_parser.add_formatter("attachment", render_attachment_bbcode, standalone=True)

deluxe_reply_re = re.compile(r'\[reply=(.+?):(post|pm|blogcomment)(:.+?)?\](.*?\[\/reply\])', re.DOTALL|re.IGNORECASE)
reply_re = re.compile(r'\[reply=(.+?):(post|pm|blogcomment)(:.+?)?\]')
def render_reply_bbcode(tag_name, value, options, parent, context):
    _options = options.get("reply","").split(":")
    inner_html = value
    
    try:
        _content_id = int(_options[0])
    except:
        return ""
        
    try:
        _content_type = _options[1]
    except:
        return ""
    
    if _content_type == "post":
        try:
            _replying_to = sqla.session.query(sqlm.Post).filter_by(id=_content_id)[0]
        except:
            sqla.session.rollback()
            return ""
        
        # TODO : Validate permissions
        
        _display_name = _replying_to.author.display_name
        try:
            if _replying_to.character is not None:
                _display_name = _replying_to.character.name
        except:
            pass
            
        if inner_html == "":
            inner_html = bbcode_parser.format(_replying_to.html, strip_images=True, content_owner=context.get("content_owner"))

        return """
        <blockquote data-time="%s" data-link="%s" data-author="%s" data-authorlink="%s" class="blockquote-reply"><div>
        %s
        </div></blockquote>
        """ % (
            arrow.get(_replying_to.created).timestamp,
            "/t/%s/page/1/post/%s" % (_replying_to.topic.slug, _replying_to.id),
            _display_name,
            "/member/%s" % _replying_to.author.my_url,
            re.sub(reply_re, "", re.sub(deluxe_reply_re, "", inner_html))
        )
        
    if reply[1] == "blogcomment":
        try:
            _replying_to = sqla.session.query(sqlm.BlogComment).filter_by(id=_content_id)[0]
        except:
            sqla.session.rollback()
            return ""
        
        # TODO : Validate permissions
        
        _display_name = _replying_to.author.display_name
        if inner_html == "":
            inner_html = bbcode_parser.format(_replying_to.html, strip_images=True, content_owner=context.get("content_owner"))
            
        return """
        <blockquote data-time="%s" data-link="%s" data-author="%s" data-authorlink="%s" class="blockquote-reply"><div>
        %s
        </div></blockquote>
        """ % (
            arrow.get(_replying_to.created).timestamp,
            "/blog/test/e/%s/page/1" % (_replying_to.blog_entry.slug),
            _display_name,
            "/member/%s" % _replying_to.author.my_url,
            re.sub(reply_re, "", re.sub(deluxe_reply_re, "", inner_html))
        )
        
    if reply[1] == "pm":
        try:
            _replying_to = sqla.session.query(sqlm.PrivateMessageReply).filter_by(id=_content_id)[0]
            pm_user = sqla.session.query(sqlm.PrivateMessageUser).filter_by(
                pm = _replying_to.pm,
                author = current_user
            )[0]
        except:
            sqla.session.rollback()
            return ""
            
        if inner_html == "":
            inner_html = bbcode_parser.format(_replying_to.html, strip_images=True, content_owner=context.get("content_owner"))
            
        return """
        <blockquote data-time="%s" data-link="%s" data-author="%s" data-authorlink="%s" class="blockquote-reply"><div>
        %s
        </div></blockquote>
        """ % (
            arrow.get(_replying_to.created).timestamp,
            "/messages/%s/page/1/post/%s" % (_replying_to.pm.id, _replying_to.id),
            _replying_to.author.display_name,
            "/member/%s" % _replying_to.author.my_url,
            re.sub(reply_re, "", inner_html)
        )
bbcode_parser.add_formatter("reply", render_reply_bbcode, escape_html=False)

class ForumPostParser(object):
    def __init__(self):
        pass

    def parse(self, html, strip_images=False, _object=False):
        cleaner = ForumHTMLCleaner()
        
        try:
            _content_owner = _object.author
        except AttributeError:
            try:
                _content_owner = _object.owner
            except AttributeError:
                if type(_object) == sqlm.User:
                    _content_owner = _object
                else:
                    _content_owner = False

        _mangled_html_links = []
        all_html_links = href_re.findall(html)
        for i, _html_link in enumerate(all_html_links):
            _mangled_html_links.append(["mangled-%s" % i, _html_link[0]])
            html = html.replace(_html_link[0], "mangled-%s" % i, 1)
        
        mentions = mention_re.findall(html)
        for mention in mentions:
            try:
                user = sqla.session.query(sqlm.User).filter_by(my_url=mention)[0]
                html = html.replace("[@%s]" % str(mention), """<a href="/member/%s" class="hover_user">@%s</a>""" % (user.my_url, user.display_name), 1)
            except:
                sqla.session.rollback()
                html = html.replace("[@%s]" % str(mention), "", 1)

        if not current_user.no_images:
            emoticon_codes = sqlm.get_local_smilies()
            for smiley in emoticon_codes:
                img_html = """<img src="%s" />""" % (os.path.join("/static/smilies", smiley["filename"]),)
                html = html.replace(":"+smiley["code"]+":", img_html)
            
        html = bbcode_parser.format(html, strip_images=strip_images, content_owner=_content_owner)
        
        for _code, _html in _mangled_html_links:
            html = html.replace(_code, _html, 1)

        if current_user.no_images:
            for plain_jane_image in raw_image_re.findall(html):
                html = html.replace(
                    "%s" % plain_jane_image[0],
                    """<a href="%s" target="_blank">View External Image : <br>%s.</a>""" % (plain_jane_image[1], plain_jane_image[1])
                )
           
        if (app.get_site_config("core.swear-filter-default") == "yes" and not current_user.is_authenticated) or (current_user.is_authenticated and current_user.swear_filter == True):
            swear_words_to_filter = sqlm.get_swear_filters()
            for w in swear_words_to_filter:
                html = re.subn(re.escape(w), "****", html, count=0, flags=re.IGNORECASE)[0]
            
        return "<div class=\"parsed\">"+html+"</div>"
        
@app.template_filter('post_parse')
def post_parse(_html):
    clean_html_parser = ForumPostParser()
    return clean_html_parser.parse(_html)