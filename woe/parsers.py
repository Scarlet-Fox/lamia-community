from woe import app
from woe import bcrypt
from woe.utilities import ipb_password_check
from wand.image import Image
from urllib import quote
import arrow, os, math
import regex as re
from flask.ext.login import current_user
from threading import Thread
from woe import sqla
import woe.sqlmodels as sqlm
from urllib import urlencode

roll_re = re.compile(r'(\[roll=(\d+)d(\d+)(?:\+(\d+)|\-(\d+))?\](.*?)\[\/roll\])', re.DOTALL|re.IGNORECASE)
attachment_re = re.compile(r'\[attachment=(.+?):(\d+)(:wrap)?\]')
spoiler_re = re.compile(r'\[[sS][pP][oO][iI][lL][eE][rR]\](.*?)\[\/[sS][pP][oO][iI][lL][eE][rR]\]', re.DOTALL|re.IGNORECASE)
adv_spoiler_re = re.compile(r'\[[sS][pP][oO][iI][lL][eE][rR]=(.*?)\](.*?)\[\/[sS][pP][oO][iI][lL][eE][rR]\]', re.DOTALL|re.IGNORECASE)
center_re = re.compile(r'\[center\](.*?)\[\/center\]', re.DOTALL|re.IGNORECASE)
image_re = re.compile(r'\[img\](.*?)\[\/img\]', re.DOTALL|re.IGNORECASE)
quote_re = re.compile(r'\[quote=?(.*?)\](.*?)\[\/quote\]', re.DOTALL|re.IGNORECASE)
font_re = re.compile(r'\[font=?(.*?)\](.*?)\[\/font\]', re.DOTALL|re.IGNORECASE)
color_re = re.compile(r'\[color=?(.*?)\](.*?)\[\/color\]', re.DOTALL|re.IGNORECASE)
size_re = re.compile(r'\[size=?(.*?)\](.*?)\[\/size\]', re.DOTALL|re.IGNORECASE)
url_re = re.compile(r'\[url=?("?)(.*?)("?)\](.*?)\[\/url\]', re.DOTALL|re.IGNORECASE)
bold_re = re.compile(r'\[b\](.*?)\[\/b\]', re.DOTALL|re.IGNORECASE)
italic_re = re.compile(r'\[i\](.*?)\[\/i\]', re.DOTALL|re.IGNORECASE)
strike_re = re.compile(r'\[s\](.*?)\[\/s\]', re.DOTALL|re.IGNORECASE)
img_re = re.compile(r'\[img\](.*?)\[\/img\]', re.DOTALL|re.IGNORECASE)
html_img_re = re.compile(r'<img src=\"(.*?)\">', re.IGNORECASE)
prefix_re = re.compile(r'(\[prefix=(.+?)\](.+?)\[\/prefix\])')
progress_re = re.compile(r'(\[progressbar=(#?[a-zA-Z0-9]+)\](\d+?)\[\/progressbar\])')
mention_re = re.compile("\[@(.*?)\]")
deluxe_reply_re = re.compile(r'\[reply=(.+?):(post|pm|blogcomment)(:.+?)?\](.*?\[\/reply\])', re.DOTALL|re.IGNORECASE)
reply_re = re.compile(r'\[reply=(.+?):(post|pm|blogcomment)(:.+?)?\]')
legacy_postcharacter_re = re.compile(r'\[(post)?character=.*?\]')
list_re = re.compile(r'\[list\](.*?)\[\/list\]', re.DOTALL|re.IGNORECASE)
link_re = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')
bbcode_re = re.compile("(\[(attachment|spoiler|center|img|quote|font|color|size|url|b|i|s|prefix|@|reply|character|postcharacter|list).*?\])")
href_re = re.compile("((href|src)=(.*?)>(.*?)(<|>))")
raw_image_re = re.compile("(<img src=\"(.*?)\"(?:.*)>)")
youtube_re = re.compile("https?://(?:www\.)?youtu(?:be\.com/watch\?v=|\.be/)([\w\-]+)(&(amp;)?[\w\?=]*)?", re.IGNORECASE)
dailymotion_re = re.compile("(?:dailymotion\.com(?:\/video|\/hub)|dai\.ly)\/([0-9a-z]+)(?:[\-_0-9a-zA-Z]+#video=([a-z0-9]+))?", re.IGNORECASE)
vimeo_re = re.compile("(?:https?:\/\/)?(?:www\.)?vimeo.com\/(?:channels\/(?:\w+\/)?|groups\/(?:[^\/]*)\/videos\/|album\/(?:\d+)\/video\/|)(\d+)(?:$|\/|\?)", re.IGNORECASE)
soundcloud_re = re.compile("(?:(?:https:\/\/)|(?:http:\/\/)|(?:www.)|(?:\s))+(?:soundcloud.com\/)+([a-zA-Z0-9\-\.]+)(?:\/)+([a-zA-Z0-9\-\.]+)", re.IGNORECASE)
spotify_re = re.compile("spotify\.com/(album|track|user/[^/]+/playlist)/([a-zA-Z0-9]+)", re.IGNORECASE)
vine_re = re.compile("(?:vine\.co/v/|www\.vine\.co/v/)(.*)", re.IGNORECASE)
giphy_re = re.compile("(?:giphy\.com/gifs/|gph\.is/)(?:.*)-(.*)", re.IGNORECASE)

emoticon_codes = {
    ":anger:" : "angry.png",
    ":)" : "smile.png",
    ":(" : "sad.png",
    ":heart:" : "heart.png",
    ":surprise:" : "oh.png",
    ":wink:" : "wink.png",
    ":cry:" : "cry.png",
    ":silly:" : "tongue.png",
    ":blushing:" : "embarassed.png",
    ":lol:" : "biggrin.png",
    ":D" : "biggrin.png",
}

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
        # parse images
        images_found = img_re.findall(html)
        skiplink = []
        for image in images_found:
            html = html.replace("[img]%s[/img]" % image, """<img src="%s" style="max-width: 80%%; display: block;">""" % image, 1)
            skiplink.append(image.strip())

        html_images_found = html_img_re.findall(html)
        for image in html_images_found:
            skiplink.append(image.strip())

        url_bbcode_in_post = url_re.findall(html)
        for url_bbcode in url_bbcode_in_post:
            if url_bbcode[1] == "":
                to_replace = "[url]"
            else:
                to_replace = "[url=%s]" % (url_bbcode[0]+url_bbcode[1]+url_bbcode[2])
            to_replace = to_replace + url_bbcode[3]
            to_replace = to_replace + "[/url]"
            if url_bbcode[0] == "":
                html = html.replace(to_replace, """<a href="%s">%s</a>""" % (unicode(url_bbcode[3]), unicode(url_bbcode[3])), 1)
            else:
                html = html.replace(to_replace, """<a href="%s">%s</a>""" % (unicode(url_bbcode[3]), unicode(url_bbcode[1])), 1)

        # parse urls
        all_bbcode = bbcode_re.findall(html)
        all_html_links = href_re.findall(html)
        parse_for_urls = html

        for bbcode in all_bbcode:
            parse_for_urls = parse_for_urls.replace(bbcode[0], "")

        for bbcode in all_html_links:
            parse_for_urls = parse_for_urls.replace(bbcode[0], "")

        links_in_clean_text = link_re.findall(parse_for_urls)
        for i, link in enumerate(links_in_clean_text):
            if link[0].strip() in skiplink:
                continue
            filler = "LINKTEXT+3235763519_"+str(i)

            html = html.replace(link[0], """<a href="%s">%s</a>""" % (filler, filler))

        for i, link in enumerate(links_in_clean_text):
            filler = "LINKTEXT+3235763519_"+str(i)

            if link[0].lower().startswith("www"):
                link_text = "http://"+link[0]
            else:
                link_text = link[0]

            youtube_match = youtube_re.search(link_text)
            dailymotion_match = dailymotion_re.search(link_text)
            vimeo_match = vimeo_re.search(link_text)
            soundcloud_match = soundcloud_re.search(link_text)
            spotify_match = spotify_re.search(link_text)
            vine_match = vine_re.search(link_text)
            giphy_match = giphy_re.search(link_text)

            if youtube_match:
                video = youtube_match.groups()[0]

                if not current_user.no_images:
                    html = html.replace(
                        """<a href="%s">%s</a>""" % (filler, filler),
                        """<iframe style="max-width: 100%%" width="560" height="315" src="https://www.youtube.com/embed/%s" frameborder="0" allowfullscreen></iframe>""" % (video, )
                    )
                else:
                    link_ = """<a href="https://www.youtube.com/watch?v=%s" target="_blank">Youtube Link (Embed)</a>""" % (video,)
                    html = html.replace(
                        """<a href="%s">%s</a>""" % (filler, filler),
                        link_
                    )

            elif dailymotion_match:
                video = dailymotion_match.groups()[0]

                if not current_user.no_images:
                    html = html.replace(
                        """<a href="%s">%s</a>""" % (filler, filler),
                        """<iframe style="max-width: 100%%" frameborder="0" width="480" height="270" src="//www.dailymotion.com/embed/video/%s" allowfullscreen></iframe>""" % (video, )
                    )
                else:
                    link_ = """<a href="http://www.dailymotion.com/video/%s" target="_blank">Dailymotion Link (Embed)</a>""" % (video,)
                    html = html.replace(
                        """<a href="%s">%s</a>""" % (filler, filler),
                        link_
                    )
            elif vimeo_match:
                video = vimeo_match.groups()[0]

                if not current_user.no_images:
                    html = html.replace(
                        """<a href="%s">%s</a>""" % (filler, filler),
                        """<iframe style="max-width: 100%%" src="https://player.vimeo.com/video/%s?color=ffffff&title=0&byline=0&portrait=0" width="500" height="281" frameborder="0" webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>""" % (video, )
                    )
                else:
                    link_ = """<a href="https://vimeo.com/%s" target="_blank">Vimeo Link (Embed)</a>""" % (video,)
                    html = html.replace(
                        """<a href="%s">%s</a>""" % (filler, filler),
                        link_
                    )
            elif soundcloud_match:
                sound_user = soundcloud_match.groups()[0]
                sound_track = soundcloud_match.groups()[1]
                options = urlencode({
                    "url": "https://soundcloud.com/"+sound_user+"/"+sound_track
                    })

                if not current_user.no_images:
                    html = html.replace(
                        """<a href="%s">%s</a>""" % (filler, filler),
                        """<iframe style="max-width: 100%%" width="100%%" height="166" scrolling="no" frameborder="no" src="https://w.soundcloud.com/player/?%s&amp;color=ff5500&amp;auto_play=false&amp;hide_related=false&amp;show_comments=true&amp;show_user=true&amp;show_reposts=false"></iframe>""" % (options,)
                    )
                else:
                    link_ = """<a href="https://soundcloud.com/%s/%s" target="_blank">Soundcloud Link (%s/%s)</a>""" % (sound_user,sound_track,sound_user,sound_track)
                    html = html.replace(
                        """<a href="%s">%s</a>""" % (filler, filler),
                        link_
                    )
            elif spotify_match:
                uri = spotify_match.groups()[0]
                track = spotify_match.groups()[1]
                uri = "spotify:"+uri.replace("/", ":")+":"+track

                if not current_user.no_images:
                    html = html.replace(
                        """<a href="%s">%s</a>""" % (filler, filler),
                        """<iframe style="max-width: 100%%" src="https://embed.spotify.com/?uri=%s" width="300" height="380" frameborder="0" allowtransparency="true"></iframe>""" % (uri,)
                    )
            elif vine_match:
                video = vine_match.groups()[0]

                if not current_user.no_images:
                    html = html.replace(
                        """<a href="%s">%s</a>""" % (filler, filler),
                        """<iframe style="max-width: 100%%" src="https://vine.co/v/%s/embed/simple?autoplay=0" width="400" height="400" frameborder="0"></iframe><script src="https://platform.vine.co/static/scripts/embed.js"></script>""" % (video, )
                    )
                else:
                    link_ = """<a href="https://vine.co/v/%s" target="_blank">Vine Link (Embed)</a>""" % (video,)
                    html = html.replace(
                        """<a href="%s">%s</a>""" % (filler, filler),
                        link_
                    )
            elif giphy_match:
                giph = giphy_match.groups()[0]

                if not current_user.no_images:
                    html = html.replace(
                        """<a href="%s">%s</a>""" % (filler, filler),
                        """<iframe src="//giphy.com/embed/%s" width="480" height="460" frameBorder="0" class="giphy-embed" allowFullScreen></iframe><p><a href="http://giphy.com/gifs/%s">via GIPHY</a></p>""" % (giph, giph)
                    )
                else:
                    link_ = """<a href="http://giphy.com/gifs/%s" target="_blank">Giphy Link (Embed)</a>""" % (giph,)
                    html = html.replace(
                        """<a href="%s">%s</a>""" % (filler, filler),
                        link_
                    )
            else:
                html = html.replace(
                    """<a href="%s">%s</a>""" % (filler, filler),
                    """<a href="%s">%s</a>""" % (link_text, link[0].strip())
                )

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
                except:
                    sqla.session.rollback()

                    try:
                        _replying_to = sqla.session.query(sqlm.PrivateMessageReply).filter_by(old_mongo_hash=reply[0])[0]
                    except:
                        sqla.session.rollback()
                        return

                if container:
                    inner_html = reply[3].replace("[/reply]","")
                else:
                    inner_html = _replying_to.message.replace("[/reply]","")

                return html.replace(string_to_replace, """
                <blockquote data-time="%s" data-link="%s" data-author="%s" data-authorlink="%s" class="blockquote-reply">
                %s
                </blockquote>
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

        html = html.replace("[hr]", "<hr>")

        prefix_bbcode_in_post = prefix_re.findall(html)
        for prefix_bbcode in prefix_bbcode_in_post:
            html = html.replace(prefix_bbcode[0], """<span class="badge prefix" style="background:%s; font-size: 10px; font-weight: normal; vertical-align: top; margin-top: 2px;">%s</span>""" % (prefix_bbcode[1], prefix_bbcode[2],))

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

        size_bbcode_in_post = size_re.findall(html)
        for size_bbcode in size_bbcode_in_post:
            replace_ = "[size="+size_bbcode[0]+"]"+size_bbcode[1]+"[/size]"
            try:
                html = html.replace(replace_, """<span style="font-size: %spx;">%s</span>""" % (str(14+int(size_bbcode[0])), size_bbcode[1],))
            except:
                continue

        color_bbcode_in_post = color_re.findall(html)
        for color_bbcode in color_bbcode_in_post:
            replace_ = "[color="+color_bbcode[0]+"]"+color_bbcode[1]+"[/color]"
            html = html.replace(replace_, """<span style="color: %s;">%s</span>""" % (color_bbcode[0], color_bbcode[1],))

        font_bbcode_in_post = font_re.findall(html)
        for font_bbcode in font_bbcode_in_post:
            replace_ = "[font="+font_bbcode[0]+"]"+font_bbcode[1]+"[/font]"
            html = html.replace(replace_, """%s""" % (font_bbcode[1],))

        font_bbcode_in_post = font_re.findall(html)
        for font_bbcode in font_bbcode_in_post:
            replace_ = "[font="+font_bbcode[0]+"]"+font_bbcode[1]+"[/font]"
            html = html.replace(replace_, """%s""" % (font_bbcode[1],))

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

        # parse spoilers
        spoiler_bbcode_in_post = spoiler_re.findall(html)
        for spoiler_bbcode in spoiler_bbcode_in_post:
            html = spoiler_re.sub("""<div class="content-spoiler"><div> <!-- spoiler div -->%s</div></div>""" % spoiler_bbcode, html, 1)
            
        spoiler_bbcode_in_post = adv_spoiler_re.findall(html)
        for spoiler_bbcode in spoiler_bbcode_in_post:
            html = adv_spoiler_re.sub("""<div class="content-spoiler" data-caption="%s"><div> <!-- spoiler div -->%s</div></div>""" % (spoiler_bbcode[0], spoiler_bbcode[1]), html, 1)

        center_bbcode_in_post = center_re.findall(html)
        for center_bbcode in center_bbcode_in_post:
            html = html.replace("[center]%s[/center]" % center_bbcode, """<center><div> <!-- center div -->%s</div></center>""" % center_bbcode, 1)

        if strip_images:
            image_bbcode_in_post = image_re.findall(html)
            for image_bbcode in image_bbcode_in_post:
                html = html.replace("[img]%s[/img]" % image_bbcode, """<disabledimg src="%s" style="max-width: 100%%;" />""" % image_bbcode, 1)
        else:
            image_bbcode_in_post = image_re.findall(html)
            for image_bbcode in image_bbcode_in_post:
                html = html.replace("[img]%s[/img]" % image_bbcode, """<img src="%s" style="max-width: 100%%;" />""" % image_bbcode, 1)

        strong_bbcode_in_post = bold_re.findall(html)
        for strong_bbcode in strong_bbcode_in_post:
            html = html.replace("[b]%s[/b]" % strong_bbcode, """<strong>%s</strong>""" % strong_bbcode, 1)

        italic_bbcode_in_post = italic_re.findall(html)
        for italic_bbcode in italic_bbcode_in_post:
            html = html.replace("[i]%s[/i]" % italic_bbcode, """<em>%s</em>""" % italic_bbcode, 1)

        strike_bbcode_in_post = strike_re.findall(html)
        for strike_bbcode in strike_bbcode_in_post:
            html = html.replace("[s]%s[/s]" % strike_bbcode, """<div style="text-decoration: line-through; display: inline !important;"><div style="display: inline !important;"><!-- strike span -->%s</div></div> <!-- /strike span -->""" % strike_bbcode, 1)

        list_bbcode_in_post = list_re.findall(html)
        for list_bbcode in list_bbcode_in_post:
            list_contents = ""
            for list_item in list_bbcode.replace("<div>", "").replace("</div>", "").split("[*]"):
                list_item = list_item.strip()
                if list_item == "":
                    continue
                list_contents += """<li>%s</li>""" % list_item
            html = html.replace("[list]%s[/list]" % list_bbcode, """<ul> <!-- list -->%s</ul>""" % list_contents, 1)

        if current_user.no_images:
            for plain_jane_image in raw_image_re.findall(html):
                html = html.replace(
                    "%s" % plain_jane_image[0],
                    """<a href="%s" target="_blank">View External Image : <br>%s.</a>""" % (plain_jane_image[1], plain_jane_image[1])
                )
        return "<div class=\"parsed\">"+html+"</div>"
