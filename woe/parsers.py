from woe import app
from woe import bcrypt
from woe.utilities import ipb_password_check, ForumHTMLCleaner
from wand.image import Image
from urllib import quote
import arrow, os, math
try:
    import regex as re
except:
    import re
from flask.ext.login import current_user
from threading import Thread
from woe import sqla
import woe.sqlmodels as sqlm
from urllib import urlencode
import bbcode

roll_re = re.compile(r'(\[roll=(\d+)d(\d+)(?:\+(\d+)|\-(\d+))?\](.*?)\[\/roll\])', re.DOTALL|re.IGNORECASE)
attachment_re = re.compile(r'\[attachment=(.+?):(\d+)(:wrap)?\]')
center_re = re.compile(r'\[center\](.*?)\[\/center\]', re.DOTALL|re.IGNORECASE)
image_re = re.compile(r'\[img\](.*?)\[\/img\]', re.DOTALL|re.IGNORECASE)
quote_re = re.compile(r'\[quote=?(.*?)\](.*)\[\/quote\]', re.DOTALL|re.IGNORECASE)
font_re = re.compile(r'\[font=?(.*?)\](.*?)\[\/font\]', re.DOTALL|re.IGNORECASE)
url_re = re.compile(r'\[url=?("?)(.*?)("?)\](.*?)\[\/url\]', re.DOTALL|re.IGNORECASE)
img_re = re.compile(r'\[img\](.*?)\[\/img\]', re.DOTALL|re.IGNORECASE)
html_img_re = re.compile(r'<img src=\"(.*?)\">', re.IGNORECASE)
progress_re = re.compile(r'(\[progressbar=(#?[a-zA-Z0-9]+)\](\d+?)\[\/progressbar\])', re.IGNORECASE)
mention_re = re.compile("\[@(.*?)\]")
deluxe_reply_re = re.compile(r'\[reply=(.+?):(post|pm|blogcomment)(:.+?)?\](.*?\[\/reply\])', re.DOTALL|re.IGNORECASE)
reply_re = re.compile(r'\[reply=(.+?):(post|pm|blogcomment)(:.+?)?\]')
legacy_postcharacter_re = re.compile(r'\[(post)?character=.*?\]')
list_re = re.compile(r'\[list\](.*?)\[\/list\]', re.DOTALL|re.IGNORECASE)
link_re = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')
bbcode_re = re.compile("(\[(attachment|spoiler|center|align|img|quote|font|color|size|url|b|i|s|prefix|@|reply|character|postcharacter|list).*?\])")
youtube_re = re.compile("https?://(?:www\.)?youtu(?:be\.com/watch\?v=|\.be/)([\w\-]+)(&(amp;)?[\w\?=]*)?", re.IGNORECASE)
dailymotion_re = re.compile("(?:dailymotion\.com(?:\/video|\/hub)|dai\.ly)\/([0-9a-z]+)(?:[\-_0-9a-zA-Z]+#video=([a-z0-9]+))?", re.IGNORECASE)
vimeo_re = re.compile("(?:https?:\/\/)?(?:www\.)?vimeo.com\/(?:channels\/(?:\w+\/)?|groups\/(?:[^\/]*)\/videos\/|album\/(?:\d+)\/video\/|)(\d+)(?:$|\/|\?)", re.IGNORECASE)
soundcloud_re = re.compile("(?:(?:https:\/\/)|(?:http:\/\/)|(?:www.)|(?:\s))+(?:soundcloud.com\/)+([a-zA-Z0-9\-\.]+)(?:\/)+([a-zA-Z0-9\-\.]+)", re.IGNORECASE)
spotify_re = re.compile("spotify\.com/(album|track|user/[^/]+/playlist)/([a-zA-Z0-9]+)", re.IGNORECASE)
vine_re = re.compile("(?:vine\.co/v/|www\.vine\.co/v/)(.*)", re.IGNORECASE)
giphy_re = re.compile("(?:giphy\.com/gifs/|gph\.is/)(?:.*)-(.*)", re.IGNORECASE)
href_re = re.compile("((href|src)=(.*?)>(.*?)(<|>))")

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

def lamia_linker(url):
    href = url
    if '://' not in href:
        href = 'http://' + href
    return '<a href="%s">%s</a>' % (href, url)

bbcode_parser = bbcode.Parser(escape_html=False, replace_links=True, linker=lamia_linker)
bbcode_parser.add_simple_formatter('hr', '<hr />', standalone=True)
bbcode_parser.add_simple_formatter('b', '<strong>%(value)s</strong>', escape_html=False)
bbcode_parser.add_simple_formatter('i', '<em>%(value)s</em>', escape_html=False)
bbcode_parser.add_simple_formatter('indent', '<div class="well"><div>%(value)s</div></div>', escape_html=False)
bbcode_parser.add_simple_formatter('media', '%(value)s', escape_html=False)
bbcode_parser.add_simple_formatter('s', '<span style="text-decoration: line-through;">%(value)s</span>', escape_html=False)
bbcode_parser.add_simple_formatter('center', '<center>%(value)s</center>', escape_html=False)
bbcode_parser.add_simple_formatter("right", '<div style="text-align: right;"><div>%(value)s</div></div>', escape_html=False)
bbcode_parser.add_simple_formatter("truespoiler", """
        <span style='color:#000000; background:#000000' onmouseover="style.color='#ffffff'" onmouseout="style.color='#000000'">%(value)s</span>
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

bbcode_parser.add_simple_formatter('u', '<u>%(value)s</u>', escape_html=False)

# TODO : [quote]

def render_code_bbcode(tag_name, value, options, parent, context):
    print value
    return """<code> <!-- code div -->%s</code>""" % (value,)
bbcode_parser.add_formatter('code', render_code_bbcode, render_embedded=False, replace_cosmetic=False, escape_html=False)    
            
def render_spoiler_bbcode(tag_name, value, options, parent, context):
    if options.get("spoiler", False):
        return """<div class="content-spoiler" data-caption="%s"><div> <!-- spoiler div -->%s</div></div>""" % (options.get("spoiler"), value,)
    else:
        return """<div class="content-spoiler"><div> <!-- spoiler div -->%s</div></div>""" % (value,)

bbcode_parser.add_formatter("spoiler", render_spoiler_bbcode, escape_html=False)
bbcode_parser.add_formatter("espoiler", render_spoiler_bbcode, escape_html=False)

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

def resize_image_save_custom(image_file_location, new_image_file, new_x_size, _id):
    from woe import sqla
    import woe.sqlmodels as sqlm

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
        
        # parse attachment tags
        attachment_bbcode_in_post = attachment_re.findall(html)
        for attachment_bbcode in attachment_bbcode_in_post:
            try:
                attachment = sqla.session.query(sqlm.Attachment).filter_by(id=attachment_bbcode[0])[0]
            except:
                sqla.session.rollback()
                try:
                    attachment = sqla.session.query(sqlm.Attachment).filter_by(old_mongo_hash=attachment_bbcode[0])[0]
                except:
                    sqla.session.rollback()
                    continue
            
            if attachment.owner != _content_owner and _content_owner != False:
                continue

            if current_user.no_images:
                link_html = """<a href="/static/uploads/%s" target="_blank">View Attachment.%s (%sKB)</a>""" % (quote(attachment.path.encode('utf-8')), attachment.extension, int(float(attachment.size_in_bytes)/1024))
                html = html.replace("[attachment=%s:%s%s]" % (attachment_bbcode[0], attachment_bbcode[1], attachment_bbcode[2]), link_html, 1)
                continue

            try:
                size = attachment_bbcode[1]
                if int(size) == int(attachment.x_size):
                    ignore_size = True
                else:
                    ignore_size = False
                    if int(size) < 5:
                        size = "5"
                    if int(size) > 700:
                        size = "700"
            except:
                ignore_size = True

            if attachment_bbcode[2] == ":wrap":
                image_formatting_class = " image-wrap"
            else:
                image_formatting_class = ""

            if attachment.size_in_bytes < 1024*1024*10 or attachment.do_not_convert:
                url = os.path.join("/static/uploads", attachment.path)
                show_box = "no"

                if ignore_size:
                    image_html = """
                    <img class="attachment-image%s" src="%s" data-show_box="%s" alt="%s" data-url="/static/uploads/%s" data-size="%s"/>
                    """ % (image_formatting_class, quote(url.encode('utf-8')), show_box, attachment.alt, quote(attachment.path.encode('utf-8')), int(float(attachment.size_in_bytes)/1024))
                    html = html.replace("[attachment=%s:%s%s]" % (attachment_bbcode[0], attachment_bbcode[1], attachment_bbcode[2]), image_html, 1)
                    continue
                else:
                    image_html = """
                    <img class="attachment-image%s" src="%s" width="%spx" data-show_box="%s" alt="%s" data-url="/static/uploads/%s" data-size="%s"/>
                    """ % (image_formatting_class, quote(url.encode('utf-8')), size, show_box, attachment.alt, quote(attachment.path.encode('utf-8')), int(float(attachment.size_in_bytes)/1024))
                    html = html.replace("[attachment=%s:%s%s]" % (attachment_bbcode[0], attachment_bbcode[1], attachment_bbcode[2]), image_html, 1)
                    continue

            filepath = os.path.join(os.getcwd(), "woe/static/uploads", attachment.path)
            sizepath = os.path.join(os.getcwd(), "woe/static/uploads",
                ".".join(filepath.split(".")[:-1])+".custom_size."+size+"."+filepath.split(".")[-1])

            show_box = "yes"

            if os.path.exists(sizepath):
                url = os.path.join("/static/uploads",
                    ".".join(attachment.path.split(".")[:-1])+".custom_size."+size+"."+attachment.path.split(".")[-1])
                try:
                    new_size = os.path.getsize(sizepath.replace(".gif", ".animated.gif"))
                except:
                    new_size = attachment.size_in_bytes
                if attachment.extension == "gif":
                    image_html = """
                    <div class="click-to-play">
                        <img class="attachment-image%s" src="%s" width="%spx" data-first_click="yes" data-show_box="%s" alt="%s" data-url="/static/uploads/%s" data-size="%s" data-resized-size="%s">
                        <p class="text-warning">This file is %sKB large, click to play.</p>
                    </div>
                    """ % (image_formatting_class, quote(url.encode('utf-8')), size, show_box, attachment.alt, quote(attachment.path.encode('utf-8')), int(float(new_size)/1024), int(float(new_size)/1024), int(float(new_size)/1024))
                    html = html.replace("[attachment=%s:%s%s]" % (attachment_bbcode[0], attachment_bbcode[1], attachment_bbcode[2]), image_html)
                    continue
                elif attachment.extension != "gif":
                    image_html = """
                    <img class="attachment-image%s" src="%s" width="%spx" data-first_click="yes" data-show_box="%s" alt="%s" data-url="/static/uploads/%s" data-size="%s">
                    """ % (image_formatting_class, quote(url.encode('utf-8')), size, show_box, attachment.alt, quote(attachment.path.encode('utf-8')), int(float(attachment.size_in_bytes)/1024))
                    html = html.replace("[attachment=%s:%s%s]" % (attachment_bbcode[0], attachment_bbcode[1], attachment_bbcode[2]), image_html)
                    continue
            else:
                thread = Thread(target=resize_image_save_custom, args=(filepath, sizepath, size, attachment.id, ))
                thread.start()
                url = os.path.join("/static/uploads", attachment.path)
                image_html = """
                <img class="attachment-image%s" src="%s" width="%spx" data-first_click="yes" data-show_box="%s" alt="%s" data-url="/static/uploads/%s" data-size="%s">
                """ % (image_formatting_class, quote(url.encode('utf-8')), size, "no", attachment.alt, quote(attachment.path.encode('utf-8')), int(float(attachment.size_in_bytes)/1024))
                html = html.replace("[attachment=%s:%s%s]" % (attachment_bbcode[0], attachment_bbcode[1], attachment_bbcode[2]), image_html)
                continue

        #clean up old char tags
        html = legacy_postcharacter_re.sub("", html)

        def process_reply(reply, html, container=False):
            if container:
                string_to_replace = "[reply=%s:%s%s]%s" % (reply[0],reply[1],reply[2], reply[3])
            else:
                string_to_replace = "[reply=%s:%s%s]" % (reply[0],reply[1],reply[2])

            if reply[1] == "post":
                try:
                    r_id = int(reply[0])
                    _replying_to = sqla.session.query(sqlm.Post).filter_by(id=r_id)[0]
                except:
                    sqla.session.rollback()

                    try:
                        _replying_to = sqla.session.query(sqlm.Post).filter_by(old_mongo_hash=reply[0])[0]
                    except:
                        sqla.session.rollback()
                        return

                _display_name = _replying_to.author.display_name
                try:
                    if _replying_to.character is not None:
                        _display_name = _replying_to.character.name
                except:
                    pass

                if container:
                    inner_html = reply[3].replace("[spoiler]", "").replace("[/spoiler]", "")
                else:
                    inner_html = _replying_to.html.replace("[spoiler]", "").replace("[/spoiler]", "")

                return html.replace(string_to_replace, """
                <blockquote data-time="%s" data-link="%s" data-author="%s" data-authorlink="%s" class="blockquote-reply"><div>
                %s
                </div></blockquote>
                """ % (
                    arrow.get(_replying_to.created).timestamp,
                    "/t/%s/page/1/post/%s" % (_replying_to.topic.slug, _replying_to.id),
                    _display_name,
                    "/member/%s" % _replying_to.author.login_name,
                    re.sub(reply_re, "", re.sub(deluxe_reply_re, "", inner_html))
                ))
                
            if reply[1] == "blogcomment":
                try:
                    r_id = int(reply[0])
                    _replying_to = sqla.session.query(sqlm.BlogComment).filter_by(id=r_id)[0]
                except:
                    sqla.session.rollback()

                _display_name = _replying_to.author.display_name

                if container:
                    inner_html = reply[3].replace("[spoiler]", "").replace("[/spoiler]", "")
                else:
                    inner_html = _replying_to.html.replace("[spoiler]", "").replace("[/spoiler]", "")
                    
                return html.replace(string_to_replace, """
                <blockquote data-time="%s" data-link="%s" data-author="%s" data-authorlink="%s" class="blockquote-reply"><div>
                %s
                </div></blockquote>
                """ % (
                    arrow.get(_replying_to.created).timestamp,
                    "/blog/test/e/%s/page/1" % (_replying_to.blog_entry.slug),
                    _display_name,
                    "/member/%s" % _replying_to.author.login_name,
                    re.sub(reply_re, "", re.sub(deluxe_reply_re, "", inner_html))
                ))
                
            if reply[1] == "pm":
                try:
                    r_id = int(reply[0])
                    _replying_to = sqla.session.query(sqlm.PrivateMessageReply).filter_by(id=reply[0])[0]
                    pm_user = sqla.session.query(sqlm.PrivateMessageUser).filter_by(
                        pm = _replying_to.pm,
                        author = current_user._get_current_object()
                    )[0]
                except:
                    sqla.session.rollback()

                    try:
                        _replying_to = sqla.session.query(sqlm.PrivateMessageReply).filter_by(old_mongo_hash=reply[0])[0]
                        pm_user = sqla.session.query(sqlm.PrivateMessageUser).filter_by(
                            pm = _replying_to.pm,
                            author = current_user._get_current_object()
                        )[0]
                    except:
                        sqla.session.rollback()
                        return html

                if container:
                    inner_html = reply[3].replace("[/reply]","")
                else:
                    inner_html = _replying_to.message.replace("[/reply]","")

                return html.replace(string_to_replace, """
                <blockquote data-time="%s" data-link="%s" data-author="%s" data-authorlink="%s" class="blockquote-reply"><div>
                %s
                </div></blockquote>
                """ % (
                    arrow.get(_replying_to.created).timestamp,
                    "/messages/%s/page/1/post/%s" % (_replying_to.pm.id, _replying_to.id),
                    _replying_to.author.display_name,
                    "/member/%s" % _replying_to.author.login_name,
                    re.sub(reply_re, "", inner_html)
                ))

        def _look_for_quote_replies(reply, html):
            interior_replies = deluxe_reply_re.findall(reply)

            if len(interior_replies) > 0:
                for reply in interior_replies:
                    _interior_interior_replies = deluxe_reply_re.findall(reply[3])
                    if len(_interior_interior_replies) > 0:
                        html = _look_for_quote_replies(reply[3], html)
                    else:
                        html = process_reply(reply, html, container=True)
            return html

        html = _look_for_quote_replies(html, html)

        replies = reply_re.findall(html)
        for reply in replies:
            html = process_reply(reply, html)

        mentions = mention_re.findall(html)
        for mention in mentions:
            try:
                user = sqla.session.query(sqlm.User).filter_by(login_name=mention)[0]
                html = html.replace("[@%s]" % unicode(mention), """<a href="/member/%s" class="hover_user">@%s</a>""" % (user.login_name, user.display_name), 1)
            except:
                sqla.session.rollback()
                html = html.replace("[@%s]" % unicode(mention), "", 1)

        rolls = roll_re.findall(html)
        for roll in rolls:
            html = html.replace(roll[0], "")

        progress_bar_bbcode_in_post = progress_re.findall(html)
        for progress_bar_bbcode in progress_bar_bbcode_in_post:
            html = html.replace(
                progress_bar_bbcode[0],
                """
                    <div class="progress" style="border-radius: 0px; max-width: 75%;">
                      <div class="progress-bar" role="progressbar"
                      aria-valuenow="VALUEHERE" aria-valuemin="0"
                      aria-valuemax="100"
                      style="width: VALUEHERE%; background-color: COLORHERE; border-radius: 0px;">
                        VALUEHERE%
                      </div>
                    </div>
                """.replace("VALUEHERE", progress_bar_bbcode[2]).replace("COLORHERE", progress_bar_bbcode[1]))

        # parse smileys
        if not current_user.no_images:
            for smiley in emoticon_codes.keys():
                img_html = """<img src="%s" />""" % (os.path.join("/static/emotes",emoticon_codes[smiley]),)
                html = html.replace(smiley, img_html)

        quote_bbcode_in_post = quote_re.findall(html)
        for quote_bbcode in quote_bbcode_in_post:
            if quote_bbcode[0] == "":
                to_replace = "[quote]"
            else:
                to_replace = "[quote=%s]" % quote_bbcode[0]
            to_replace = to_replace + quote_bbcode[1]
            to_replace = to_replace + "[/quote]"
            html = html.replace(to_replace, """<blockquote data-author="%s" class="blockquote-reply"><div>%s</div></blockquote>""" % (unicode(quote_bbcode[0]), unicode(quote_bbcode[1])), 1)

                
        html = bbcode_parser.format(html, strip_images=strip_images)
        
        for _code, _html in _mangled_html_links:
            html = html.replace(_code, _html, 1)

        if current_user.no_images:
            for plain_jane_image in raw_image_re.findall(html):
                html = html.replace(
                    "%s" % plain_jane_image[0],
                    """<a href="%s" target="_blank">View External Image : <br>%s.</a>""" % (plain_jane_image[1], plain_jane_image[1])
                )
            
        return "<div class=\"parsed\">"+html+"</div>"
        
@app.template_filter('post_parse')
def post_parse(_html):
    clean_html_parser = ForumPostParser()
    return clean_html_parser.parse(_html)