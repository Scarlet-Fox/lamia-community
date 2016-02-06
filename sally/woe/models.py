from __future__ import unicode_literals
from django.contrib.postgres.fields import JSONField
from django.db import models
from django.contrib.auth.models import User

############################################################
# Abstract Models
############################################################
class PublicContent(models.Model):
    author = models.ForeignKey(User)
    created = models.DateTimeField()
    
    hidden = models.BooleanField(default=False)
    locked = models.BooleanField(default=False)
    muted = models.BooleanField(default=False)
    
    class Meta:
        abstract = True

############################################################
# Core User Models
############################################################

class Role(models.Model):
    pre_html = models.CharField(max_length=255, blank=True)
    role = models.CharField(max_length=255)
    post_html = models.CharField(max_length=255, blank=True)
    
class IgnoredUser(models.Model):
    user_that_is_ignoring = models.ForeignKey("UserProfile")
    user_that_is_ignored = models.ForeignKey(User)
    
    #block_posts = models.BooleanField(default=False)
    block_sigs = models.BooleanField(default=False)
    block_pms = models.BooleanField(default=False)
    block_blogs = models.BooleanField(default=False)
    block_status = models.BooleanField(default=False)

class Friendship(models.Model):
    friend_requester = models.ForeignKey("UserProfile")
    friend_target = models.ForeignKey(User)
    
    pending = models.BooleanField(default=True)
    blocked = models.BooleanField(default=False)

class UserProfile(models.Model):
    profile_user = models.ForeignKey(User, related_name="profile")
    user_role = models.ForeignKey("Role")
    display_name = models.CharField(max_length=255, blank=True, unique=True)
    how_did_you_find_us = models.TextField(blank=True)
    is_allowed_during_construction = models.BooleanField(default=False)
#    roles =         
    data = JSONField()
    time_zone = models.CharField(max_length=255, default="US/Pacific")

    banned = models.BooleanField(default=False)
    validated = models.BooleanField(default=False)
    over_thirteen = models.BooleanField(default=False)

    emails_muted = models.BooleanField(default=False)
    last_sent_notification_email = models.DateTimeField()

    title = models.CharField(max_length=255, blank=True)
    minecraft = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    about_me = models.TextField()
    anonymous_login = models.BooleanField(default=False)
    
    avatar_extension = models.CharField(max_length=255, blank=True)
    avatar_full_x = models.IntegerField()
    avatar_full_y = models.IntegerField()
    avatar_60_x = models.IntegerField()
    avatar_60_y = models.IntegerField()
    avatar_40_x = models.IntegerField()
    avatar_40_y = models.IntegerField()
    avatar_timestamp = models.IntegerField()
    
    password_forgot_token = models.CharField(max_length=255, blank=True)
    password_forgot_token_date = models.DateTimeField()
    
    ignoring_users = models.ManyToManyField(User, through="IgnoredUser", related_name="ignored_by")
    following_users = models.ManyToManyField(User)
    profile_friends = models.ManyToManyField(User, through="Friendship", related_name="friended_by")
    
    joined = models.DateTimeField()
    posts_count = models.IntegerField(default=0)
    topic_count = models.IntegerField(default=0)
    status_count = models.IntegerField(default=0)
    status_comment_count = models.IntegerField(default=0)
    last_seen = models.DateTimeField()
    hidden_last_seen = models.DateTimeField()
    last_at = models.CharField(max_length=255, blank=True, default="Watching forum index.")
    last_at_url = models.CharField(max_length=255, blank=True, default="/")
    
    is_admin = models.BooleanField(default=False)
    is_mod = models.BooleanField(default=False)
        
    # Migration related
    old_ipb_id = models.IntegerField(default=0)
    old_mongo_hash = models.CharField(max_length=255, blank=True)

class DisplayNameHistory(models.Model):
    user_profile = models.ForeignKey("UserProfile")
    name = models.CharField(max_length=255, blank=True)
    date = models.DateTimeField()
    
class Fingerprint(models.Model):
    fingerprint_user = models.ForeignKey(User)
    fingerprint_last_seen = models.IntegerField(default=0)
    fingerprint_json = JSONField()
    fingerprint_hash = models.TextField()
    factor_count = models.IntegerField()
    
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
    user = models.ForeignKey(User)
    ip_address = models.CharField(max_length=255)
    last_seen = models.DateTimeField()
    
############################################################
# Status Update Models
############################################################

class StatusUpdateUser(models.Model):
    user = models.ForeignKey(User)
    status_update = models.ForeignKey("StatusUpdate")
    
    ignoring = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False)
    viewed = models.IntegerField(default=0)
    last_viewed = models.DateTimeField()
    
class StatusComment(PublicContent):
    message = models.CharField(max_length=255)

class StatusUpdate(PublicContent):
    attached_to_profile = models.ForeignKey("UserProfile", blank=True, null=True)    
    message = models.CharField(max_length=255)
    
    last_replied = models.DateTimeField()
    last_viewed = models.DateTimeField()
    replies = models.IntegerField(default=0)
    participants = models.ManyToManyField(User, through="StatusUpdateUser", related_name="participating_in_statuses")
    
    # Migration related
    old_ipb_id = models.IntegerField(default=0)
    old_mongo_hash = models.CharField(max_length=255, blank=True)

############################################################
# Attachment Model
############################################################

class Attachment(models.Model):
    user = models.ForeignKey(User)
    
    path = models.CharField(max_length=255)
    mimetype = models.CharField(max_length=255)
    extension = models.CharField(max_length=255)
    
    size_in_bytes = models.IntegerField(default=0)
    created_date = models.DateTimeField()
    do_not_convert = models.BooleanField(default=False)
    alt = models.CharField(max_length=255, blank=True)
        
    old_ipb_id = models.IntegerField(default=0)
    old_mongo_hash = models.CharField(max_length=255, blank=True)
    
    x_size = models.IntegerField()
    y_size = models.IntegerField()
    
    file_hash = models.CharField(max_length=255, blank=True)
    linked = models.BooleanField(default=False)
    origin_url = models.CharField(max_length=255, blank=True)
    origin_domain = models.CharField(max_length=255, blank=True)
    caption = models.CharField(max_length=255, blank=True)
    
    # RP Specific Stuff
    character = models.ForeignKey("Character", blank=True, null=True)
    character_gallery = models.BooleanField(default=False)
    character_emote = models.BooleanField(default=False)

############################################################
# Notification Model
############################################################

class Notification(models.Model):
    user = models.ForeignKey(User, related_name="user_notifications")
    message = models.CharField(max_length=255)
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
    url = models.CharField(max_length=255)
    originating_user = models.ForeignKey(User, blank=True, null=True)
    acknowledged = models.BooleanField(default=False)
    seen = models.BooleanField(default=False)
    emailed = models.BooleanField(default=False)
    priority = models.IntegerField(default=0)

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
    user = models.ForeignKey(User, blank=True, null=True)
    time = models.DateTimeField()
    error = models.BooleanField()
    error_name = models.CharField(max_length=255, blank=True)
    error_code = models.CharField(max_length=255, blank=True)
    error_description = models.TextField(blank=True)

############################################################
# Private Message Model
############################################################

class PrivateMessageUser(models.Model):
    user = models.ForeignKey(User)
    private_message = models.ForeignKey("PrivateMessage")
    
    ignoring = models.BooleanField(default=False)
    exited = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False)
    viewed = models.IntegerField(default=0)
    last_viewed = models.DateTimeField()

class PrivateMessage(models.Model):
    title = models.CharField(max_length=255, blank=True)
    author = models.ForeignKey(User)
    last_reply = models.ForeignKey("PrivateMessageReply")

    created = models.DateTimeField()
    participants = models.ManyToManyField(User, through="PrivateMessageUser", related_name="participating_in_pms")

    # Migration related
    old_ipb_id = models.IntegerField(default=0)
    old_mongo_hash = models.CharField(max_length=255, blank=True)

class PrivateMessageReply(models.Model):
    author = models.ForeignKey(User)
    message = models.CharField(max_length=255)
    private_message = models.ForeignKey("PrivateMessage")
    
    created = models.DateTimeField()
    modified = models.DateTimeField()
    
############################################################
# Report Model
############################################################

class Report(models.Model):
    url = models.CharField(max_length=300, blank=True)
    content_type = models.CharField(max_length=255, blank=True)
    content_id = models.IntegerField(blank=True)
    content_author = models.ForeignKey(User)
    
    report = models.TextField(blank=True)
    initiated = models.ForeignKey(User, related_name="started_reports")
    
    STATUS_CHOICES = ( 
        ('ignored', 'Ignored'), 
        ('open', 'Open'), 
        ('feedback', 'Feedback Requested'), 
        ('waiting', 'Waiting'),
        ('action taken', 'Action Taken') 
    )
    report_status = models.CharField(choices=STATUS_CHOICES, max_length=60)
    created = models.DateTimeField()
    handler = models.ForeignKey(User, related_name="handled_reports")
    
############################################################
# Category Model
############################################################

class Prefix(models.Model):
    pre_html = models.CharField(max_length=255, blank=True)
    post_html = models.CharField(max_length=255, blank=True)
    prefix = models.CharField(max_length=255)

class PostHistory(models.Model):
    creator = models.ForeignKey(User)
    html = models.TextField()
    reason = models.CharField(max_length=255, blank=True)
    data = JSONField()

class Category(models.Model):
    name = models.CharField(max_length=255, blank=True)
    slug = models.CharField(max_length=255, blank=True)
    parent = models.ForeignKey("Category", blank=True, null=True)
    root_category = models.BooleanField(default=False)
    
    weight = models.IntegerField(default=0)
    restricted = models.BooleanField(default=False)
    allowed_users = models.ManyToManyField(User)
    allowed_prefixes = models.ManyToManyField("Prefix")
    
    topic_count = models.IntegerField(default=0)
    post_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)
    most_recent_topic = models.ForeignKey("Topic", blank=True, null=True, related_name="recent_topic_in")
    most_recent_post = models.ForeignKey("Post", blank=True, null=True, related_name="recent_post_in")
    
    old_ipb_id = models.IntegerField(blank=True)

class Topic(PublicContent):
    name = models.CharField(max_length=255, blank=True)
    slug = models.CharField(max_length=255, blank=True)
    category = models.ForeignKey("Category")
    sticky = models.BooleanField(default=True)
    announcement = models.BooleanField(default=True)
    prefix = models.ForeignKey("Prefix", blank=True, null=True)
    
    watchers = models.ManyToManyField(User, related_name="watched_content")
    moderators = models.ManyToManyField(User, related_name="moderated_topics")
    banned = models.ManyToManyField(User, related_name="banned_from_topics")
    
    topic_count = models.IntegerField(default=0)
    post_count = models.IntegerField(default=0)
    first_post = models.ForeignKey("Post", related_name="topics_where_first")
    most_recent_post = models.ForeignKey("Post", blank=True, null=True, related_name="most_recent_post_in")
    
    old_ipb_id = models.IntegerField(blank=True)
    old_mongo_hash = models.CharField(max_length=255, blank=True)
    
class Post(PublicContent):
    html = models.TextField()
    topic = models.ForeignKey("Topic")
    history = models.ManyToManyField("PostHistory")
    
    edited = models.DateTimeField()
    editor = models.ForeignKey(User, related_name="edited_posts")
    
    boops = models.ManyToManyField(User, related_name="booped_posts")
    
    old_ipb_id = models.IntegerField(blank=True)
    old_mongo_hash = models.CharField(max_length=255, blank=True)
    character = models.ForeignKey("Character", blank=True, null=True)
    data = JSONField()
    
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
    modified = models.DateTimeField(max_length=255, blank=True)
    