from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
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
    content_html = models.TextField(blank=True)

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
    created = models.DateTimeField(auto_now_add=True, index=True)
    category = models.CharField(index=True, index=True)
    details = models.TextField(blank=True)
    """YAML or JSON containing more details."""

class Prefix(models.Model):
    title = models.CharField(max_length=255, index=True)
    pre_html = models.CharField(max_length=255)
    post_html = models.CharField(max_length=255)

class Topic(DateContentAuthor):
    title = models.CharField(max_length=255)
    category = models.ForeignKey("Category")
    prefix = models.ForeignKey("Prefix", blank=True, null=True)
    
    active_user = models.ForeignKey("User")
    created = models.DateTimeField(blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)

    views = models.IntegerField(default=0)
    post_count = models.IntegerField(default=0)
    recent_post = models.ForeignKey("Post")

    sticky = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)

    participants = models.ManyToManyField() # TODO
    favorites = models.ManyToManyField() # TODO