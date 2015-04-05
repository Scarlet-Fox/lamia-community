from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import HStoreField
import reversion

"""This file should go from low level to high level."""

@reversion.register
class Post(models.Model):
    author = models.ForeignKey("User", index=True)
    edited_by = models.ForeignKey("User")
    topic = models.ForeignKey("Topic", index=True)

    created = models.DateTimeField(auto_now_add=True, index=True)
    edited = models.DateTimeField(auto_now=True, index=True)
    
    content = models.TextField(blank=True)
    meta = models.HStoreField()

    hidden = models.BooleanField(default=False, index=True)
    hide_message = models.CharField(max_length=255, blank=True)
    flag_score = models.IntegerField(default=0)
    ignore_flags = models.DateTimeField(auto_now=True) 
    """Ignore any flags older than this date, useful for resets."""

class Report(models.Model):
    content_type = models.ForeignKey("ContentType")
    object_id = models.PositiveIntegerField()
    content = GenericForeignKey('content_type', 'object_id')

    report = models.TextField(blank=True)
    STATUS_CHOICES = (
        (0, 'Closed'),
        (1, 'Open'),
        (2, 'Feedback Requested'),
        (3, 'Waiting')
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=1, index=True)
    created = models.DateTimeField(auto_now_add=True, index=True)

class ReportComments(models.Model):
    report = models.ForeignKey("Report", index=True)
    author = models.ForeignKey("User")
    created = models.DateTimeField(auto_now_add=True, index=True)
    comment = models.TextField(blank=True)

class Flag(models.Model):
    content_type = models.ForeignKey("ContentType")
    object_id = models.PositiveIntegerField()
    content = GenericForeignKey('content_type', 'object_id')

    flag_user = models.ForeignKey("User")
    flag_score = models.IntegerField(default=1)
    created = models.DateTimeField(auto_now_add=True, index=True)

class LogEntry(models.Model):
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user = models.ForeignKey(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, index=True)
    category = models.CharField(index=True, index=True)
    details = models.TextField(blank=True)
    """YAML or JSON containing more details."""

class Prefix(models.Model):
    title = models.CharField(max_length=255, index=True)
    pre_html = models.CharField(max_length=255)
    post_html = models.CharField(max_length=255)

class Topic(models.Model):
    author = models.ForeignKey("User")
    title = models.CharField(max_length=255)
    category = models.ForeignKey("Category")
    prefix = models.ForeignKey("Prefix", blank=True, null=True)
    meta = models.HStoreField()
    
    active_user = models.ForeignKey("User")
    created = models.DateTimeField(blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)

    views = models.IntegerField(default=0)
    post_count = models.IntegerField(default=0)
    recent_post = models.ForeignKey("Post")

    sticky = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)
    hide_message = models.CharField(max_length=255)

    participants = models.ManyToManyField() # TODO
    favorites = models.ManyToManyField() # TODO
    moderators = models.ManyToManyField() # TODO

    # TODO : Rate limiting.

class Category(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    weight = models.IntegerField(default=0, index=True)
    category = models.ForeignKey("Category", index=True)

    groups = models.ManyToManyField() # TODO
    moderators = models.ManyToManyField() # TODO

class StatusUpdate(models.Model):
    author = models.ForeignKey("User")
    created = models.DateTimeField(auto_now_add=True, index=True)
    message = models.TextField()
    profile = models.ForeignKey("User", blank=True, null=True)
    """If null, then a normal status update. If not, then user-linked."""

    participants = models.ManyToManyField() # TODO

class StatusComments(models.Model):
    status = models.ForeignKey("StatusUpdate")
    comment = models.TextField()
    created = models.DateTimeField(auto_now_add=True, index=True)
    author = models.ForeignKey("User")

    hidden = models.BooleanField(default=False)

class Ban(models.Model):
    user = models.ForeignKey("User")
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True, index=True)
    mod = models.ForeignKey("User")

class Profile(models.Model):
    user = models.ForeignKey("User")
    status = models.ForeignKey("StatusUpdate", blank=True, null=True)
    title = models.CharField(max_length=255)
    location = models.CharField(blank=True)
    time_zone = models.FloatField(default=0.0)
    about = models.TextField(blank=True)

    birthday = models.DateField(blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    hide_age = models.BooleanField(default=True)
    hide_birthday = models.BooleanField(default=True)

    GENDERS = (
        ('n', ''),
        ('f', 'Female'),
        ('m', 'Male'),
        ('g', 'Genderfluid'),
        ('o', 'Other'),
    )
    gender = models.CharField(choices=GENDERS, default="n")
    hide_gender = models.BooleanField(default=True)
    favorite_color = models.CharField(default="Red", blank=True)
    how_found = models.TextField(blank=True)

    ALLOWED_FIELDS = (
        'Website',
        'DeviantArt'
        'Skype',
        'Steam',
        'Tumblr'
        )
    fields = models.HStoreField()
    avatar = models.ImageField(upload_to="avatars", blank=True)

    disable_posts = models.BooleanField(default=False)
    disable_status = models.BooleanField(default=False)
    disable_pm = models.BooleanField(default=False)
    disable_topics = models.BooleanField(default=False)
    hellban = models.BooleanField(default=False)

    posts = models.IntegerField(default=0)
    status_updates = models.IntegerField(default=0)
    status_comments = models.IntegerField(default=0)

class Signature(models.Model):
    user = models.ForeignKey("User")
    description = models.CharField(max_length=255)
    content = models.TextField()

class PrivateMessageLabel(models.Model):
    user = models.ForeignKey("User")
    label = models.CharField(max_length=255)

class PrivateMessage(models.Model):
    title = models.CharField(max_length=255)
    label = models.ForeignKey("PrivateMessageLabel", blank=True, null=True)
    user = models.ForeignKey("User")
    participants = models.ManyToManyField() # TODO

    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True, index=True)
    last_updated = models.DateTimeField(auto_now=True, index=True)

class PrivateMessageReply(models.Model):
    pm = models.ForeignKey("PrivateMessage")
    author = models.ForeignKey("User", index=True)
    created = models.DateTimeField(auto_now_add=True, index=True)
    edited = models.DateTimeField(auto_now=True, index=True)
    content = models.TextField(blank=True)