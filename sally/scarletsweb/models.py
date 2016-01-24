from __future__ import unicode_literals
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.contrib.auth.models import User

############################################################
# Abstract Models
############################################################
class PublicContent(models.Model):
    author = models.ForeignKey("UserProfile")
    created = models.DateTimeField()

    hidden = models.BooleanField(default=False)
    locked = models.BooleanField(default=False)
    muted = models.BooleanField(default=False)

    class Meta:
        abstract = True

############################################################
# Site Preference Models
############################################################

class SiteTheme(models.Model):
    css = models.TextField(default="", blank=True)
    theme_name = models.CharField(max_length=255)
    weight = models.IntegerField(default=0)
    created_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['weight']

    def __unicode__(self):
        return self.theme_name

############################################################
# Core User Models
############################################################

class UserRole(models.Model):
    pre_html = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=255)
    post_html = models.CharField(max_length=255, blank=True)
    created_date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.role

class IgnoredUser(models.Model):
    is_ignoring = models.ForeignKey("UserProfile", related_name="ignoring")
    is_ignored = models.ForeignKey("UserProfile", related_name="ignored")
    created_date = models.DateTimeField(auto_now=True)

    distort_posts = models.BooleanField(default=True)
    block_sigs = models.BooleanField(default=True)
    block_pms = models.BooleanField(default=True)
    block_blogs = models.BooleanField(default=True)
    block_status = models.BooleanField(default=True)

    def __unicode__(self):
        return "%s ignoring %s" % (self.is_ignoring.display_name, self.is_ignored.display_name)

class Friendship(models.Model):
    requester = models.ForeignKey("UserProfile", related_name="requested")
    target = models.ForeignKey("UserProfile", related_name="target")
    created_date = models.DateTimeField(auto_now=True)

    pending = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False)

    def __unicode__(self):
        if self.pending == True:
            return "%s friended %s" % (self.requester.display_name, self.target.display_name)
        elif self.pending == False:
            return "%s wants to friend %s" % (self.requester.display_name, self.target.display_name)
        elif self.blocked == True:
            return "%s failed to friend %s" % (self.requester.display_name, self.target.display_name)

class FollowPreferences(models.Model):
    following = models.ForeignKey("UserProfile", related_name="following")
    followed = models.ForeignKey("UserProfile", related_name="followed")
    created_date = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return "%s is following %s" % ()

class UserProfile(models.Model):
    profile_user = models.ForeignKey(User, related_name="user_profile")
    user_role = models.ManyToManyField("UserRole", blank=True)
    display_name = models.CharField(max_length=255, blank=True, unique=True)
    how_did_you_find_us = models.TextField(blank=True)
    is_allowed_during_construction = models.BooleanField(default=False)
    my_url = models.CharField(max_length=255, blank=True, unique=True)
    data = JSONField(blank=True, null=True)
    time_zone = models.CharField(max_length=255, default="US/Pacific")

    banned = models.BooleanField(default=False)
    validated = models.BooleanField(default=False)
    over_thirteen = models.BooleanField(default=False)

    emails_muted = models.BooleanField(default=False)
    last_sent_notification_email = models.DateTimeField(blank=True, null=True)

    title = models.CharField(max_length=255, blank=True)
    minecraft = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    about_me = models.TextField(blank=True)
    anonymous_login = models.BooleanField(default=False)

    avatar_extension = models.CharField(max_length=255, blank=True, null=True)
    avatar_full_x = models.IntegerField(blank=True, null=True)
    avatar_full_y = models.IntegerField(blank=True, null=True)
    avatar_60_x = models.IntegerField(blank=True, null=True)
    avatar_60_y = models.IntegerField(blank=True, null=True)
    avatar_40_x = models.IntegerField(blank=True, null=True)
    avatar_40_y = models.IntegerField(blank=True, null=True)
    avatar_timestamp = models.CharField(max_length=255, blank=True)

    password_forgot_token = models.CharField(max_length=255, blank=True)
    password_forgot_token_date = models.DateTimeField(blank=True, null=True)

    ignoring_users = models.ManyToManyField("UserProfile", through="IgnoredUser", related_name="ignored_by", blank=True)
    following_users = models.ManyToManyField("UserProfile", through="FollowPreferences", related_name="followed_by", blank=True)
    profile_friends = models.ManyToManyField("UserProfile", through="Friendship", related_name="friended_by", blank=True)

    posts_count = models.IntegerField(default=0, null=True)
    topic_count = models.IntegerField(default=0, null=True)
    status_count = models.IntegerField(default=0, null=True)
    status_comment_count = models.IntegerField(default=0, null=True)

    last_seen = models.DateTimeField(blank=True, null=True)
    hidden_last_seen = models.DateTimeField(auto_now=True)
    last_at = models.CharField(max_length=255, blank=True, default="Lurking forum index.")
    last_at_url = models.CharField(max_length=255, blank=True, default="/")

    is_admin = models.BooleanField(default=False)
    is_mod = models.BooleanField(default=False)

    # Migration related
    old_mongo_hash = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return "%s AKA %s" % (self.display_name, self.login_name)

class DisplayNameHistory(models.Model):
    user_profile = models.ForeignKey("UserProfile")
    name = models.CharField(max_length=255, blank=True)
    date = models.DateTimeField()

    def __unicode__(self):
        return "%s AKA %s" % (self.name, self.user_profile.login_name)


class Fingerprint(models.Model):
    fingerprint_user = models.ForeignKey("UserProfile")
    fingerprint_last_seen = models.IntegerField(default=0)
    fingerprint_json = JSONField(blank=True, null=True)
    fingerprint_hash = models.TextField()
    factor_count = models.IntegerField()

    def __unicode__(self):
        return "%s's %s factor fingerprint" % (self.fingerprint_user.display_name, self.factor_count)

    def compute_similarity_score(self, stranger):
        score = 0.0
        attributes = {}

        for key in self.fingerprint_json.keys():
            attributes[key] = 1

        for key in stranger.fingerprint_json.keys():
            attributes[key] = 1

        max_score = float(len(attributes.keys()))
        for attribute in attributes.keys():
            if self.fingerprint_json.get(attribute, None) == stranger.fingerprint_json.get(attribute, None):
                score += 1

        return score/max_score

class IPAddress(models.Model):
    user = models.ForeignKey("UserProfile")
    ip_address = models.CharField(max_length=255)
    last_seen = models.DateTimeField()

    def __unicode__(self):
        return "%s's %s IP" % (self.user.display_name, self.ip_address)

############################################################
# Status Update Models
############################################################

class StatusUpdateUser(models.Model):
    user = models.ForeignKey("UserProfile")
    status_update = models.ForeignKey("StatusUpdate")

    ignoring = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False)
    viewed = models.IntegerField(default=0)
    last_viewed = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return "%s in %s's status update. \'%s...\'" % (self.user.display_name, self.status_update.author.display_name, self.status_update.message[0:50])

class StatusComment(PublicContent):
    message = models.TextField()
    status_update = models.ForeignKey("StatusUpdate")

    def __unicode__(self):
        return "%s in %s's status update. \'%s...\'" % (self.author.display_name, self.status_update.author.display_name, self.message[0:50])

class StatusUpdate(PublicContent):
    attached_to_profile = models.ForeignKey("UserProfile", blank=True, null=True, related_name="profile_status")
    message = models.TextField()

    last_replied = models.DateTimeField(blank=True, null=True)
    last_viewed = models.DateTimeField(blank=True, null=True)
    replies = models.IntegerField(default=0)
    participants = models.ManyToManyField("UserProfile", through="StatusUpdateUser", related_name="participating_in_statuses")

    old_mongo_hash = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return "%s's status update. \'%s...\'" % (self.author.display_name, self.message[0:50])


############################################################
# Attachment Model
############################################################

class Attachment(models.Model):
    user = models.ForeignKey("UserProfile")

    path = models.TextField()
    mimetype = models.CharField(max_length=255)
    extension = models.CharField(max_length=255)

    size_in_bytes = models.IntegerField(default=0)
    created_date = models.DateTimeField()
    do_not_convert = models.BooleanField(default=False)
    alt = models.TextField()

    old_mongo_hash = models.CharField(max_length=255, blank=True)

    x_size = models.IntegerField()
    y_size = models.IntegerField()

    file_hash = models.TextField()
    linked = models.BooleanField(default=False)
    origin_url = models.TextField()
    origin_domain = models.TextField()
    caption = models.TextField()

    # RP Specific Stuff
    character = models.ForeignKey("Character", blank=True, null=True)
    character_gallery = models.BooleanField(default=False)
    character_gallery_weight = models.IntegerField(default=0)
    character_avatar = models.BooleanField(default=False)

    def __unicode__(self):
        return "%s's attachment - %s" % (self.user.display_name, self.path)

############################################################
# Notification Model
############################################################

class Notification(models.Model):
    user = models.ForeignKey("UserProfile", related_name="user_notifications")
    message = models.TextField()
    description = models.TextField(blank=True)

    NOTIFICATION_CATEGORIES = (
        ("topic", "Topics"),
        ("pm", "Private Messages"),
        ("mention", "Mentioned"),
        ("topic_reply", "Topic Replies"),
        ("boop", "Boops"),
        ("mod", "Moderation"),
        ("status", "Status Updates"),
        ("new_member", "New Members"),
        ("announcement", "Announcements"),
        ("profile_comment","Profile Comments"),
        ("rules_updated", "Rule Update"),
        ("faqs", "FAQs Updated"),
        ("user_activity", "Followed User Activity"),
        ("streaming", "Streaming"),
        ("other", "Other")
    )

    category = models.CharField(choices=NOTIFICATION_CATEGORIES, max_length=55)
    created = models.DateTimeField()
    url = models.TextField(blank=True)
    originating_user = models.ForeignKey("UserProfile", blank=True, null=True)
    acknowledged = models.BooleanField(default=False)
    seen = models.BooleanField(default=False)
    emailed = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)

    def __unicode__(self):
        return "%s's notification \'%s...\'" % (self.user.display_name, self.description)

############################################################
# Log Model
############################################################
class SiteLog(models.Model):
    method = models.CharField(max_length=255, blank=True)
    path = models.CharField(max_length=255, blank=True)
    ip_address = models.CharField(max_length=255, blank=True)
    agent_platform = models.CharField(max_length=255, blank=True)
    agent_browser = models.CharField(max_length=255, blank=True)
    agent_browser_version = models.CharField(max_length=255, blank=True)
    agent = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey("UserProfile", blank=True, null=True)
    time = models.DateTimeField()
    error = models.BooleanField()
    error_name = models.CharField(max_length=255, blank=True)
    error_code = models.CharField(max_length=255, blank=True)
    error_description = models.TextField(blank=True)

    def __unicode__(self):
        return "%s %s %s :: %s %s %s %s" % (self.time.isoformat(), self.method, self.ip_address, self.agent, self.agent_browser, self.agent_browser_version, self.agent_platform)

############################################################
# Private Message Model
############################################################

class PrivateMessageUser(models.Model):
    user = models.ForeignKey("UserProfile")
    private_message = models.ForeignKey("PrivateMessage")

    ignoring = models.BooleanField(default=False)
    exited = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False)
    viewed = models.IntegerField(default=0)
    last_viewed = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return "%s in \'%s...\'" % (self.user.display_name, self.private_message.title)

class PrivateMessage(models.Model):
    title = models.CharField(max_length=255, blank=True)
    author = models.ForeignKey("UserProfile")
    last_reply = models.ForeignKey("PrivateMessageReply", null=True, blank=True)
    message_count = models.IntegerField(default=0)

    created = models.DateTimeField()
    participants = models.ManyToManyField("UserProfile", through="PrivateMessageUser", related_name="participating_in_pms", blank=True)

    old_mongo_hash = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return "%s's message \'%s...\'" % (self.author.display_name, self.title)

class PrivateMessageReply(models.Model):
    author = models.ForeignKey("UserProfile")
    message = models.TextField()
    private_message = models.ForeignKey("PrivateMessage")
    old_mongo_hash = models.CharField(max_length=255, blank=True)

    created = models.DateTimeField()
    modified = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        return "%s's reply to \'%s...\'" % (self.author.display_name, self.private_message.title)

############################################################
# Report Model
############################################################

class Report(models.Model):
    url = models.CharField(max_length=300, blank=True)
    content_type = models.CharField(max_length=255, blank=True)
    content_id = models.IntegerField(blank=True)
    content_author = models.ForeignKey("UserProfile")

    report = models.TextField(blank=True)
    initiated = models.ForeignKey("UserProfile", related_name="started_reports")

    STATUS_CHOICES = (
        ('ignored', 'Ignored'),
        ('open', 'Open'),
        ('feedback', 'Feedback Requested'),
        ('waiting', 'Waiting'),
        ('action taken', 'Action Taken')
    )
    report_status = models.CharField(choices=STATUS_CHOICES, max_length=60)
    created = models.DateTimeField()
    handler = models.ForeignKey("UserProfile", related_name="handled_reports")

    def __unicode__(self):
        return "%s on %s - STATUS " % (self.created.isoformat(), self.content_author.display_name, self.report_status)

class ReportComment(models.Model):
    author = models.ForeignKey("UserProfile")
    created = models.DateTimeField(auto_now=True)
    text = models.TextField()
    report = models.ForeignKey("Report")

    def __unicode__(self):
        return "%s %s" % (self.created.isoformat(), self.author.display_name)

############################################################
# Category Model
############################################################

class Label(models.Model):
    pre_html = models.CharField(max_length=255, blank=True)
    post_html = models.CharField(max_length=255, blank=True)
    label = models.CharField(max_length=255, unique=True)

    def __unicode__(self):
        return self.label

class PostHistory(models.Model):
    creator = models.ForeignKey("UserProfile")
    post = models.ForeignKey("Post", related_name="past_versions")
    created = models.DateTimeField(auto_now=True)
    html = models.TextField()
    reason = models.CharField(max_length=255, blank=True)
    data = JSONField()

    def __unicode__(self):
        return "%s %s" % (self.created.isoformat(), self.creator.display_name)

class Section(models.Model):
    name = models.CharField(max_length=255, blank=True, unique=True)
    weight = models.IntegerField(default=0)

    def __unicode__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=255, blank=True, unique=True)
    slug = models.CharField(max_length=255, blank=True, unique=True)
    parent = models.ForeignKey("Category", blank=True, null=True, related_name="category_children")
    section = models.ForeignKey("Section", blank=True, null=True, related_name="section_children")

    weight = models.IntegerField(default=0)
    restricted = models.BooleanField(default=False)
    allowed_users = models.ManyToManyField("UserProfile")
    allowed_labels = models.ManyToManyField("Label")

    topic_count = models.IntegerField(default=0)
    post_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    most_recent_topic = models.ForeignKey("Topic", blank=True, null=True, related_name="recent_topic_in")
    most_recent_post = models.ForeignKey("Post", blank=True, null=True, related_name="recent_post_in")

    def __unicode__(self):
        return self.name

class Topic(PublicContent):
    name = models.CharField(max_length=255, blank=True)
    slug = models.CharField(max_length=255, blank=True, unique=True)
    category = models.ForeignKey("Category")
    sticky = models.BooleanField(default=True)
    announcement = models.BooleanField(default=True)
    label = models.ForeignKey("Label", blank=True, null=True)

    watchers = models.ManyToManyField("UserProfile", related_name="watched_content")
    moderators = models.ManyToManyField("UserProfile", related_name="moderated_topics")
    banned = models.ManyToManyField("UserProfile", related_name="banned_from_topics")

    post_count = models.IntegerField(default=0)
    first_post = models.ForeignKey("Post", related_name="topics_where_first", blank=True, null=True)
    most_recent_post = models.ForeignKey("Post", blank=True, null=True, related_name="most_recent_post_in")

    def __unicode__(self):
        return self.name

class Post(PublicContent):
    html = models.TextField()
    topic = models.ForeignKey("Topic")
    report = models.ManyToManyField("Report", blank=True, null=True)
    modified = models.DateTimeField(blank=True, null=True)

    editor = models.ForeignKey("UserProfile", related_name="edited_posts", blank=True)

    boops = models.ManyToManyField("UserProfile", related_name="booped_posts", blank=True)

    old_mongo_hash = models.CharField(max_length=255, blank=True)
    character = models.ForeignKey("Character", blank=True, null=True)
    avatar = models.ForeignKey("Attachment", blank=True, null=True)
    data = JSONField(null=True, blank=True)

    def __unicode__(self):
        return "%s in %s" % (self.author.display_name, self.topic.name)

############################################################
# Characters Model
############################################################

class Character(PublicContent):
    name = models.CharField(max_length=255, blank=True)
    slug = models.CharField(max_length=255, blank=True)

    age = models.CharField(max_length=255, blank=True)
    species = models.CharField(max_length=255, blank=True)
    appearance = models.TextField(blank=True)
    personality = models.TextField(blank=True)
    backstory = models.TextField(blank=True)
    other = models.TextField(blank=True)
    motto = models.CharField(max_length=255, blank=True)
    modified = models.DateTimeField(max_length=255, blank=True, null=True)

    character_history = JSONField(blank=True, null=True)
    old_mongo_hash = models.CharField(max_length=255, blank=True)

    def __unicode__(self):
        return "%s by %s" % (self.name, self.author.display_name)

############################################################
# Blog Models TODO
############################################################

class BlogCategory(models.Model):
    name = models.CharField(max_length=255)

class Blog(PublicContent):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)

    description = models.TextField()
    editors = models.ManyToManyField("UserProfile", related_name="blog_editors")
    categories = models.ManyToManyField("BlogCategory")

    entries = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    last_entry_date = models.DateTimeField()
    last_comment_date = models.DateTimeField()

    PRIVACY_LEVELS = (
        ("all", "Everyone"),
        ("members", "Only Members"),
        ("friends", "Only Friends"),
        ("editors", "Only Editors"),
        ("you", "Only You")
    )
    privacy_setting = models.CharField(choices=PRIVACY_LEVELS, default="all", max_length=255)
    mod_locked = models.BooleanField(default=False)
    old_ipb_id = models.IntegerField(blank=True)

class BlogEntry(PublicContent):
    html = models.TextField()
    blog = models.ForeignKey("Blog")
    history = models.ManyToManyField("PostHistory")
    report = models.ForeignKey("Report", blank=True, null=True)

    edited = models.DateTimeField()
    editor = models.ForeignKey("UserProfile", related_name="edited_blog_entries")

    boops = models.ManyToManyField("UserProfile", related_name="booped_blog_entries")

    old_ipb_id = models.IntegerField(blank=True)
    character = models.ForeignKey("Character", blank=True, null=True)
    data = JSONField()

class BlogComment(PublicContent):
    html = models.TextField()
    blog = models.ForeignKey("Blog")
    blog_entry = models.ForeignKey("BlogEntry")
    history = models.ManyToManyField("PostHistory")
    report = models.ForeignKey("Report", blank=True, null=True)

    edited = models.DateTimeField()
    editor = models.ForeignKey("UserProfile", related_name="edited_blog_comments")

    boops = models.ManyToManyField("UserProfile", related_name="booped_blog_comments")

    old_ipb_id = models.IntegerField(blank=True)
    character = models.ForeignKey("Character", blank=True, null=True)
    data = JSONField()
