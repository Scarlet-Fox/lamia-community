from woe import db
from woe import app
from woe import bcrypt
from woe.utilities import ipb_password_check
from wand.image import Image
from urllib import quote
from woe.models.forum import Post
import arrow, re, os, math
from flask.ext.login import current_user

attachment_re = re.compile(r'\[attachment=(.+?):(\d+)\]')
spoiler_re = re.compile(r'\[spoiler\]')
end_spoiler_re = re.compile(r'\[\/spoiler\]')
bold_re = re.compile(r'\[b\]')
end_bold_re = re.compile(r'\[\/b\]')
italic_re = re.compile(r'\[i\]')
end_italic_re = re.compile(r'\[\/i\]')
strike_re = re.compile(r'\[s\]')
end_strike_re = re.compile(r'\[\/s\]')
prefix_re = re.compile(r'(\[prefix=(.+?)\](.+?)\[\/prefix\])')
mention_re = re.compile("\[@(.*?)\]")
reply_re = re.compile(r'\[reply=(.+?):(post|pm)\]')

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
class ForumPostParser(object):
    def __init__(self):
        pass
        
    def parse(self, html):
        # parse attachment tags
        attachment_bbcode_in_post = attachment_re.findall(html)
        
        for attachment_bbcode in attachment_bbcode_in_post:
            try:
                attachment = Attachment.objects(pk=attachment_bbcode[0])[0]
            except:
                pass
            
            try:
                size = attachment_bbcode[1]
                if int(size) < 5:
                    size = "5"
                if int(size) > 700:
                    size = "700"
                if int(size) == attachment.x_size and attachment.size_in_bytes < 1024*1024:
                    url = os.path.join("/static/uploads", attachment.path)
                    show_box = "no"
                
                    image_html = """
                    <img class="attachment-image" src="%s" width="%spx" data-show_box="%s" alt="%s" data-url="/static/uploads/%s" data-size="%s"/>
                    """ % (quote(url), attachment.x_size, show_box, attachment.alt, quote(attachment.path), int(float(attachment.size_in_bytes)/1024))
                    html = html.replace("[attachment=%s:%s]" % (attachment_bbcode[0], attachment_bbcode[1]), image_html, 1)
                else:
                    attachment_path = attachment.path
                    filepath = os.path.join(os.getcwd(), "woe/static/uploads", attachment.path)
                    sizepath = os.path.join(os.getcwd(), "woe/static/uploads", 
                        ".".join(filepath.split(".")[:-1])+".custom_size."+size+"."+filepath.split(".")[-1])
                
                    if not os.path.exists(sizepath):
                        try:
                            image = Image(filename=filepath)
                        except:
                            continue
                        xsize = image.width
                        ysize = image.height
                        if attachment.x_size == 0:
                            attachment.x_size = xsize
                            attachment.y_size = ysize
                            attachment.save()
                        resize_measure = float(size)/float(xsize)
                        image.resize(int(round(xsize*resize_measure)),int(round(ysize*resize_measure)))
                        if attachment.extension == "gif" and len(image.make_blob()) > 1024*1024: # Larger than 1 megabyte.
                            image.save(filename=sizepath.replace(".gif",".animated.gif"))
                            first_frame = image.sequence[0].clone()
                            first_frame.save(filename=sizepath)
                            new_x = image.width
                            new_y = image.height
                        else:
                            image.save(filename=sizepath)
                            new_x = image.width
                            new_y = image.height
                    else:
                        filepath = os.path.join(os.getcwd(), "woe/static/uploads", attachment.path)
                        if attachment.x_size == 0 or attachment.y_size == 0:
                            try:
                                image = Image(filename=filepath)
                            except:
                                continue
                            
                            attachment.x_size = image.width
                            attachment.y_size = image.height
                            attachment.save()
                        
                        resize_measure = float(size)/float(attachment.x_size)
                        new_x = int(round(attachment.x_size*resize_measure))
                        new_y = int(round(attachment.y_size*resize_measure))
            
                    url = os.path.join("/static/uploads", 
                        ".".join(attachment_path.split(".")[:-1])+".custom_size."+size+"."+attachment_path.split(".")[-1])
                
                    if abs(new_x - attachment.x_size) > 100 and new_x < attachment.x_size:
                        show_box = "yes"
                    else:
                        show_box = "no"
                                    
                    if attachment.extension == "gif" and attachment.size_in_bytes > 1024*1024:
                        show_box = "yes"
                        new_size = os.path.getsize(sizepath.replace(".gif",".animated.gif"))
                        image_html = """
                        <div class="click-to-play">
                            <img class="attachment-image" src="%s" width="%spx" data-first_click="yes" data-show_box="%s" alt="%s" data-url="/static/uploads/%s" data-size="%s"/>
                            <p class="text-warning">This file is %sKB large, click to play.</p>
                        </div>
                        """ % (quote(url), new_x, show_box, attachment.alt, quote(attachment.path), int(float(new_size)/1024), int(float(new_size)/1024))
                    else:                
                        image_html = """
                        <img class="attachment-image" src="%s" width="%spx" data-first_click="yes" data-show_box="%s" alt="%s" data-url="/static/uploads/%s" data-size="%s"/>
                        """ % (quote(url), new_x, show_box, attachment.alt, quote(attachment.path), int(float(attachment.size_in_bytes)/1024))
                    html = html.replace("[attachment=%s:%s]" % (attachment_bbcode[0], attachment_bbcode[1]), image_html, 1)
            except:
                continue

        replies = reply_re.findall(html)
        for reply in replies:
            if reply[1] == "post":
                _replying_to = Post.objects(pk=reply[0])[0]
                html = html.replace("[reply=%s:%s]" % (reply[0],reply[1]), """
                <blockquote data-time="%s" data-link="%s" data-author="%s" data-authorlink="%s" class="blockquote-reply">
                %s
                </blockquote> 
                """ % (
                    arrow.get(_replying_to.created).timestamp,
                    "/t/%s/page/1/post/%s" % (_replying_to.topic.slug, _replying_to.pk),
                    _replying_to.author.display_name,
                    "/member/%s" % _replying_to.author.login_name,
                    re.sub(reply_re, "", _replying_to.html.replace("img", "imgdisabled"))
                ))
            if reply[1] == "pm":
                _replying_to = PrivateMessage.objects(pk=reply[0])[0]
                html = html.replace("[reply=%s:%s]" % (reply[0],reply[1]), """
                <blockquote data-time="%s" data-link="%s" data-author="%s" data-authorlink="%s" class="blockquote-reply">
                %s
                </blockquote> 
                """ % (
                    arrow.get(_replying_to.created).timestamp,
                    "/messages/%s/page/1/post/%s" % (_replying_to.topic.pk, _replying_to.pk),
                    _replying_to.author.display_name,
                    "/member/%s" % _replying_to.author.login_name,
                    re.sub(reply_re, "", _replying_to.message.replace("img", "imgdisabled"))
                ))
                    
        mentions = mention_re.findall(html)
        for mention in mentions:
            try:
                user = User.objects(login_name=mention)[0]
                html = html.replace("[@%s]" % unicode(mention), """<a href="/members/%s" class="hover_user">@%s</a>""" % (user.login_name, user.display_name), 1)
            except:
                html = html.replace("[@%s]" % unicode(mention), "", 1) 
        
        html = html.replace("[hr]", "<hr>")
        
        prefix_bbcode_in_post = prefix_re.findall(html)
        for prefix_bbcode in prefix_bbcode_in_post:
            html = html.replace(prefix_bbcode[0], """<span class="badge prefix" style="background:%s; font-size: 10px; font-weight: normal; vertical-align: top; margin-top: 2px;">%s</span>""" % (prefix_bbcode[1], prefix_bbcode[2],))
        
        # parse smileys
        for smiley in emoticon_codes.keys():
            img_html = """<img src="%s" />""" % (os.path.join("/static/emoticons",emoticon_codes[smiley]),)
            html = html.replace(smiley, img_html)

        # parse spoilers
        spoiler_bbcode_in_post = spoiler_re.findall(html)
        for spoiler_bbcode in spoiler_bbcode_in_post:
            if end_spoiler_re.search(html):
                html = html.replace("[spoiler]", """<div class="content-spoiler"><div> <!-- spoiler div -->""", 1)
                html = html.replace("[/spoiler]", """</div></div> <!-- /spoiler div -->""", 1)

        strong_bbcode_in_post = bold_re.findall(html)
        for strong_bbcode in strong_bbcode_in_post:
            if end_bold_re.search(html):
                html = html.replace("[b]", """<strong>""", 1)
                html = html.replace("[/b]", """</strong>""", 1)
        italic_bbcode_in_post = italic_re.findall(html)
        for italic_bbcode in italic_bbcode_in_post:
            if end_italic_re.search(html):
                html = html.replace("[i]", """<em>""", 1)
                html = html.replace("[/i]", """</em>""", 1)
        strike_bbcode_in_post = strike_re.findall(html)
        for strike_bbcode in strike_bbcode_in_post:
            if end_strike_re.search(html):
                html = html.replace("[s]", """<span style="text-decoration: line-through;"><span> <!-- strike span -->""", 1)
                html = html.replace("[/s]", """</span></span> <!-- /strike span -->""", 1)

        return html
