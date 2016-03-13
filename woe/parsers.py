from woe import db
from woe import app
from woe import bcrypt
from woe.utilities import ipb_password_check
from wand.image import Image
from urllib import quote
from woe.models.forum import Post
import arrow, re, os, math
from flask.ext.login import current_user
from threading import Thread
from woe.models.core import Attachment, User, PrivateMessage
from woe.models.forum import Post
from woe.models.roleplay import Character
from woe import sqla
import woe.sqlmodels as sqlm

attachment_re = re.compile(r'\[attachment=(.+?):(\d+)(:wrap)?\]')
spoiler_re = re.compile(r'\[spoiler\](.*?)\[\/spoiler\]', re.DOTALL)
center_re = re.compile(r'\[center\](.*?)\[\/center\]', re.DOTALL)
image_re = re.compile(r'\[img\](.*?)\[\/img\]', re.DOTALL)
quote_re = re.compile(r'\[quote=?(.*?)\](.*?)\[\/quote\]', re.DOTALL)
font_re = re.compile(r'\[font=?(.*?)\](.*?)\[\/font\]', re.DOTALL)
color_re = re.compile(r'\[color=?(.*?)\](.*?)\[\/color\]', re.DOTALL)
size_re = re.compile(r'\[size=?(.*?)\](.*?)\[\/size\]', re.DOTALL)
url_re = re.compile(r'\[url=?("?)(.*?)("?)\](.*?)\[\/url\]', re.DOTALL)
bold_re = re.compile(r'\[b\](.*?)\[\/b\]', re.DOTALL)
italic_re = re.compile(r'\[i\](.*?)\[\/i\]', re.DOTALL)
strike_re = re.compile(r'\[s\](.*?)\[\/s\]', re.DOTALL)
prefix_re = re.compile(r'(\[prefix=(.+?)\](.+?)\[\/prefix\])')
mention_re = re.compile("\[@(.*?)\]")
reply_re = re.compile(r'\[reply=(.+?):(post|pm)(:.+?)?\]')
legacy_postcharacter_re = re.compile(r'\[(post)?character=.*?\]')
list_re = re.compile(r'\[list\](.*?)\[\/list\]', re.DOTALL)
link_re = re.compile(ur'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?\xab\xbb\u201c\u201d\u2018\u2019]))')
bbcode_re = re.compile("(\[(attachment|spoiler|center|img|quote|font|color|size|url|b|i|s|prefix|@|reply|character|postcharacter|list).*?\])")
href_re = re.compile("((href|src)=(.*?)>(.*?)(<|>))")

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
    ";)" : "twilight_wink_by_angelishi.gif"
}

def resize_image_save_custom(image_file_location, new_image_file, new_x_size, attachment):
    try:
        source_image = Image(filename=image_file_location)
    except:
        attachment.update(do_not_convert=True)
        return False

    original_x = source_image.width
    original_y = source_image.height

    if original_x != new_x_size:
        resize_measure = float(new_x_size)/float(original_x)
        try:
            source_image.resize(int(round(original_x*resize_measure)),int(round(original_y*resize_measure)))
        except:
            attachment.update(do_not_convert=True)

    try:
        if attachment.extension == "gif":
            source_image.save(filename=new_image_file.replace(".gif",".animated.gif"))
            first_frame = source_image.sequence[0].clone()
            first_frame.save(filename=new_image_file)
        else:
            source_image.save(filename=new_image_file)
    except:
        attachment.update(do_not_convert=True)

class ForumPostParser(object):
    def __init__(self):
        pass

    def parse(self, html, strip_images=False):
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
            filler = "LINKTEXT+3235763519_"+str(i)

            html = html.replace(link[0], """
                <a href="%s">%s</a>
            """ % (filler, filler))

        for i, link in enumerate(links_in_clean_text):
            filler = "LINKTEXT+3235763519_"+str(i)
            print filler

            if link[0].lower().startswith("www"):
                link_text = "http://"+link[0]
            else:
                link_text = link[0]

            html = html.replace(
                """<a href="%s">%s</a>""" % (filler, filler),
                """
                    <a href="%s">%s</a>
                """ % (link_text, link[0])
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

            size = attachment_bbcode[1]
            if int(size) < 5:
                size = "5"
            if int(size) > 700:
                size = "700"

            if attachment_bbcode[2] == ":wrap":
                image_formatting_class = " image-wrap"
            else:
                image_formatting_class = ""

            if attachment.size_in_bytes < 1024*1024 or attachment.do_not_convert:
                url = os.path.join("/static/uploads", attachment.path)
                show_box = "no"

                image_html = """
                <img class="attachment-image%s" src="%s" width="%spx" data-show_box="%s" alt="%s" data-url="/static/uploads/%s" data-size="%s"/>
                """ % (image_formatting_class, quote(url), size, show_box, attachment.alt, quote(attachment.path), int(float(attachment.size_in_bytes)/1024))
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
                    """ % (image_formatting_class, quote(url), size, show_box, attachment.alt, quote(attachment.path), int(float(new_size)/1024), int(float(new_size)/1024), int(float(new_size)/1024))
                    html = html.replace("[attachment=%s:%s%s]" % (attachment_bbcode[0], attachment_bbcode[1], attachment_bbcode[2]), image_html)
                    continue
                elif attachment.extension != "gif":
                    image_html = """
                    <img class="attachment-image%s" src="%s" width="%spx" data-first_click="yes" data-show_box="%s" alt="%s" data-url="/static/uploads/%s" data-size="%s">
                    """ % (image_formatting_class, quote(url), size, show_box, attachment.alt, quote(attachment.path), int(float(attachment.size_in_bytes)/1024))
                    html = html.replace("[attachment=%s:%s%s]" % (attachment_bbcode[0], attachment_bbcode[1], attachment_bbcode[2]), image_html)
                    continue
            else:
                thread = Thread(target=resize_image_save_custom, args=(filepath, sizepath, size, attachment, ))
                thread.start()
                url = os.path.join("/static/uploads", attachment.path)
                image_html = """
                <img class="attachment-image%s" src="%s" width="%spx" data-first_click="yes" data-show_box="%s" alt="%s" data-url="/static/uploads/%s" data-size="%s">
                """ % (image_formatting_class, quote(url), size, "no", attachment.alt, quote(attachment.path), int(float(attachment.size_in_bytes)/1024))
                html = html.replace("[attachment=%s:%s%s]" % (attachment_bbcode[0], attachment_bbcode[1], attachment_bbcode[2]), image_html)
                continue

        #clean up old char tags
        html = legacy_postcharacter_re.sub("", html)

        replies = reply_re.findall(html)
        for reply in replies:
            if reply[1] == "post":
                try:
                    r_id = int(reply[0])
                    _replying_to = sqla.session.query(sqlm.Post).filter_by(id=r_id)[0]
                except ValueError:
                    sqla.session.rollback()

                    try:
                        _replying_to = sqla.session.query(sqlm.Post).filter_by(old_mongo_hash=reply[0])[0]
                    except:
                        sqla.session.rollback()
                        continue

                try:
                    if _replying_to.character is not None:
                        _replying_to.author.display_name = _replying_to.character.name
                except:
                    continue

                html = html.replace("[reply=%s:%s%s]" % (reply[0],reply[1],reply[2]), """
                <blockquote data-time="%s" data-link="%s" data-author="%s" data-authorlink="%s" class="blockquote-reply"><div>
                %s
                </div></blockquote>
                """ % (
                    arrow.get(_replying_to.created).timestamp,
                    "/t/%s/page/1/post/%s" % (_replying_to.topic.slug, _replying_to.id),
                    _replying_to.author.display_name,
                    "/member/%s" % _replying_to.author.login_name,
                    re.sub(reply_re, "", _replying_to.html.replace("img", "imgdisabled"))
                ))
            if reply[1] == "pm":
                try:
                    _replying_to = sqla.session.query(sqlm.PrivateMessageReply).filter_by(id=reply[0])[0]
                except:
                    sqla.session.rollback()
                html = html.replace("[reply=%s:%s%s]" % (reply[0],reply[1],reply[2]), """
                <blockquote data-time="%s" data-link="%s" data-author="%s" data-authorlink="%s" class="blockquote-reply">
                %s
                </blockquote>
                """ % (
                    arrow.get(_replying_to.created).timestamp,
                    "/messages/%s/page/1/post/%s" % (_replying_to.topic.id, _replying_to.id),
                    _replying_to.author.display_name,
                    "/member/%s" % _replying_to.author.login_name,
                    re.sub(reply_re, "", _replying_to.message.replace("img", "imgdisabled"))
                ))

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
        for smiley in emoticon_codes.keys():
            img_html = """<img src="%s" />""" % (os.path.join("/static/emoticons",emoticon_codes[smiley]),)
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

        # parse spoilers
        spoiler_bbcode_in_post = spoiler_re.findall(html)
        for spoiler_bbcode in spoiler_bbcode_in_post:
            html = html.replace("[spoiler]%s[/spoiler]" % spoiler_bbcode, """<div class="content-spoiler"><div> <!-- spoiler div -->%s</div></div>""" % spoiler_bbcode, 1)

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

        return html
