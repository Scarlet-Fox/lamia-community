from woe.models.core import User, Attachment
from woe.models.forum import Post
import re, time, hashlib, mimetypes, os, json
from urllib2 import urlopen, HTTPError, URLError
from multiprocessing.pool import ThreadPool
from wand.image import Image

posts_with_images = Post.objects(html__icontains="<img")
img_tag_re = re.compile("(<img.*?src=\")(.*?)(\".*?>)")
settings_file = json.loads(open("config.json").read())

def process_post(post):
    post_html = post.html
    image_tags_in_post = img_tag_re.findall(post_html)

    for image_html in image_tags_in_post:
        image_source = image_html[1]
        try:
            attachment_exists = Attachment(origin_url=image_source)[0]
            attachment_exists.update(inc__used_in=1)
            post_html = post_html.replace("".join(image_html), "[attachment=%s:%s]" % (str(attachment_exists.pk), attachment_exists.x_size),1)
            post.update(html=post_html)
        except:
            pass

        print "Processing %s" % str(image_html)
        try:
            if image_source.startswith("data"):
                continue
            image_domain = image_source.split("/")[2]
            filename = image_source.split("/")[-1].split("?")[0]
            destination_pathname = os.path.join(os.getcwd(),"woe/static/uploads/linked/",image_domain)
            destination_filename = os.path.join(os.getcwd(),"woe/static/uploads/linked/",image_domain,filename)
            extension = filename.split(".")[-1]

            if not os.path.exists(destination_filename):
                image_response = urlopen(image_source, timeout=8)
                try:
                    image = Image(file=image_response)
                except:
                    continue
            else:
                image = Image(filename=destination_filename)

            attach = Attachment()
            attach.x_size = image.width
            attach.y_size = image.height
            attach.mimetype = mimetypes.guess_type(filename)[0]
            attach.extension = extension

            image_bin = image.make_blob()
            attach.size_in_bytes = len(image_bin)
            attach.owner_name = post.author.login_name
            attach.owner = post.author
            attach.alt = filename
            attach.used_in = 1
            attach.created_date = post.created
            image_bin = image.make_blob()
            attach.file_hash = hashlib.sha256(image_bin).hexdigest()
            attach.linked = True
            attach.origin_url = image_source
            attach.origin_domain = image_domain

            if not os.path.exists(destination_pathname):
                try:
                    os.makedirs(destination_pathname)
                except:
                    print "OS Makedirs error : %s" % str(destination_pathname)

            image.save(filename=destination_filename)

            attach.path = os.path.join("linked/", image_domain, filename)
            attach.save()
            post_html = post_html.replace("".join(image_html), "[attachment=%s:%s]" % (str(attach.pk), attach.x_size),1)
            post.update(html=post_html)
            try:
                image_response.close()
            except:
                pass
        except HTTPError:
            print "Skipping %s" % str(image_html)
            continue
        except URLError:
            print "Skipping %s" % str(image_html)
            continue
        except:
            print "Skipping %s" % str(image_html)
            continue

for post in posts_with_images:
    process_post(post)
