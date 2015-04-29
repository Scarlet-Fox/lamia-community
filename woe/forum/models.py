from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import HStoreField
import reversion

"""This file should go from low level to high level."""

@reversion.register
class Post(models.Model):
    author = models.ForeignKey(User)
    edited_by = models.ForeignKey(User, related_name="+", null=True, blank=True)
    topic = models.ForeignKey("Topic")

    created = models.DateTimeField(auto_now_add=True)
    edited = models.DateTimeField(auto_now=True)
    
    content = models.TextField(blank=True)
    meta = HStoreField(blank=True, null=True)
    moderation_post = models.BooleanField(default=False)

    hidden = models.BooleanField(default=False)
    hide_message = models.CharField(max_length=255, blank=True)
    flag_score = models.IntegerField(default=0)
    ignore_flags = models.DateTimeField() 
    """Ignore any flags older than this date, useful for resets."""

    def __str__(self):
        return "Post #%s by %s : %s" % (self.id, unicode(self.author), self.content[0:20])

class Attachment(models.Model):
    owner = models.ForeignKey(User)
    meta = HStoreField(blank=True, null=True)

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    link_to = GenericForeignKey('content_type', 'object_id')

    upload = models.FileField(upload_to="uploads", max_length=300)
    file_name = models.CharField(max_length=255, blank=True)
    file_type = models.CharField(max_length=255, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    edited = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.file_name

class Report(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content = GenericForeignKey('content_type', 'object_id')
    author = models.ForeignKey(User)

    report = models.TextField(blank=True)
    STATUS_CHOICES = (
        (0, 'Closed'),
        (1, 'Open'),
        (2, 'Feedback Requested'),
        (3, 'Waiting')
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Report by %s on %s" % (unicode(self.author), unicode(self.created))

class ReportComment(models.Model):
    report = models.ForeignKey("Report")
    author = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True)

    def __str__(self):
        return "%s : %s" % (unicode(self.report), self.comment[0:20])

class Flag(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content = GenericForeignKey('content_type', 'object_id')

    flag_user = models.ForeignKey(User)
    flag_score = models.IntegerField(default=1)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return "%s flag on %s, %s" % (unicode(self.flag_user), unicode(self.created), unicode(self.content))

class LogEntry(models.Model):
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user = models.ForeignKey(User, blank=True, null=True, related_name="logs")
    created = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    """YAML or JSON containing more details."""

    def __str__(self):
        return "%s : %s : %s" % (unicode(self.user), self.category, unicode(self.details))

class Prefix(models.Model):
    title = models.CharField(max_length=255)
    pre_html = models.CharField(max_length=255)
    post_html = models.CharField(max_length=255)

    def __str__(self):
        return self.title

class Topic(models.Model):
    author = models.ForeignKey(User, related_name="my_topics")
    title = models.CharField(max_length=255)
    category = models.ForeignKey("Category")
    prefix = models.ForeignKey("Prefix", blank=True, null=True)
    meta = HStoreField(blank=True, null=True)
    
    active_user = models.ForeignKey(User, related_name="+")
    created = models.DateTimeField(blank=True, null=True)
    last_updated = models.DateTimeField(blank=True, null=True)

    views = models.IntegerField(default=0)
    post_count = models.IntegerField(default=0)

    sticky = models.BooleanField(default=False)
    closed = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)
    hide_message = models.CharField(max_length=255, blank=True)

    participants = models.ManyToManyField(User, through="TopicParticipant")
    # TODO : Rate limiting stuff.

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return "%s by %s" % (self.title, unicode(self.author))

class TopicParticipant(models.Model):
    topic = models.ForeignKey("Topic")
    user = models.ForeignKey(User)
    following = models.BooleanField(default=False)
    posts = models.IntegerField(default=0)    
    moderator = models.BooleanField(default=False)
    last_seen = models.DateTimeField(blank=True, null=True)
    # TODO : Add a preference to toggle this.

    def __str__(self):
        return "%s : %s" % (unicode(self.user), unicode(self.topic))

class Category(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    weight = models.IntegerField(default=0)
    parent = models.ForeignKey("Category", blank=True, null=True)
    moderators = models.ManyToManyField(User, through="CategoryParticipant")
    restricted = models.BooleanField(default=False)
    latest_topic = models.ForeignKey("Topic", blank=True, null=True, related_name="+")
    latest_poster = models.ForeignKey("Profile", blank=True, null=True, related_name="+")

    class Meta:
        ordering = ["-parent_id", "weight"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.title

class CategoryParticipant(models.Model):
    category = models.ForeignKey("Category")
    user = models.ForeignKey(User)
    moderator = models.BooleanField(default=False)

    def __str__(self):
        return "%s : %s" % (unicode(self.user), unicode(self.category))

class StatusUpdate(models.Model):
    author = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True)
    message = models.TextField()
    profile = models.ForeignKey(User, blank=True, null=True, related_name="+")
    """If null, then a normal status update. If not, then user-linked."""
    participants = models.ManyToManyField(User, through="StatusParticipant", related_name="+")
    hidden = models.BooleanField(default=False)
    # TODO - comment count
    # TODO - latest activity
    # TODO - velocity (weight of age and comment count)
    
    def __str__(self):
        return "%s by %s" % (self.message, unicode(self.author))

class StatusParticipant(models.Model):
    status = models.ForeignKey("StatusUpdate")
    user = models.ForeignKey(User)
    ignoring = models.BooleanField(default=True)

    def __str__(self):
        return "%s : %s" % (unicode(self.user), unicode(self.status))

class StatusComment(models.Model):
    status = models.ForeignKey("StatusUpdate")
    comment = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User)

    hidden = models.BooleanField(default=False)

    def __str__(self):
        return "%s says %s in %s" % (unicode(self.author), self.comment, unicode(self.status))

class UserIP(models.Model):
    ip_address = models.GenericIPAddressField()
    users = models.ManyToManyField(User, blank=True)
    first_seen = models.DateTimeField()
    last_seen = models.DateTimeField()

    def __str__(self):
        return self.ip_address

class Fingerprint(models.Model):
    identity = models.TextField()
    users = models.ManyToManyField(User, blank=True)
    first_seen = models.DateTimeField()
    last_seen = models.DateTimeField()

    def __str__(self):
        return self.identity

class Ban(models.Model):
    user = models.ForeignKey(User, related_name="bans")
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    mod = models.ForeignKey(User, related_name="banned")

    def __str__(self):
        return "%s on %s" % (unicode(self.user), unicode(self.created))

class ModerationNotes(models.Model):
    user = models.ForeignKey(User)
    author = models.ForeignKey(User, related_name="+")
    created = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True)

    def __str__(self):
        return "%s : %s on %s" % (unicode(self.user), self.comment, unicode(self.created))

class Friend(models.Model):
    user = models.ForeignKey("Profile", related_name="+")
    friend = models.ForeignKey(User, related_name="followers")
    follow_posts = models.BooleanField(default=False)
    follow_status = models.BooleanField(default=False)
    follow_topics = models.BooleanField(default=False)

    def __str__(self):
        return "%s : %s" % (unicode(self.user), unicode(self.friend))

class Profile(models.Model):
    user = models.OneToOneField(User)
    display_name = models.CharField(max_length=255, blank=True)
    status = models.ForeignKey("StatusUpdate", blank=True, null=True, related_name="+")
    title = models.CharField(max_length=255,  blank=True)
    location = models.CharField(max_length=255, blank=True)
    time_zone = models.FloatField(default=0.0)
    about = models.TextField(blank=True)
    friends = models.ManyToManyField(User, through="Friend", related_name="+")

    birthday = models.DateField(blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    hide_age = models.BooleanField(default=True)
    hide_birthday = models.BooleanField(default=True)
    hide_login = models.BooleanField(default=False)

    GENDERS = (
        ('n', ''),
        ('f', 'Female'),
        ('m', 'Male'),
        ('g', 'Genderfluid'),
        ('o', 'Other'),
    )
    gender = models.CharField(max_length=255, choices=GENDERS, default="n")
    hide_gender = models.BooleanField(default=True)
    favorite_color = models.CharField(max_length=255, default="Red", blank=True)
    how_found = models.TextField(blank=True)

    ALLOWED_FIELDS = (
        'Website',
        'DeviantArt'
        'Skype',
        'Steam',
        'Tumblr'
        )
    fields = HStoreField(blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars", blank=True)

    VALIDATION_STATUSES = (
        (0, "Pending"),
        (1, "Reviewing"),
        (2, "Validated"),
        (3, "Banned in Validation"),
    )
    validation_status = models.IntegerField(choices=VALIDATION_STATUSES, default=0)

    MODERATION_STATUSES = (
        (0, "Under Review"),
        (1, "Request Feedback"),
        (2, "Good"),
        (3, "Bad Egg"),
        (4, "KO"),
    )
    moderation_status = models.IntegerField(choices=MODERATION_STATUSES, default=2)

    disable_posts = models.BooleanField(default=False)
    disable_status = models.BooleanField(default=False)
    disable_pm = models.BooleanField(default=False)
    disable_topics = models.BooleanField(default=False)
    hellban = models.BooleanField(default=False)

    posts = models.IntegerField(default=0)
    status_updates = models.IntegerField(default=0)
    status_comments = models.IntegerField(default=0)

    def __str__(self):
        return unicode(self.user)

class Signature(models.Model):
    user = models.ForeignKey(User)
    description = models.CharField(max_length=255)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s : %s" % (unicode(self.user), self.description)

class PrivateMessageLabel(models.Model):
    user = models.ForeignKey(User)
    label = models.CharField(max_length=255)

    def __str__(self):
        return "%s : %s" % (unicode(self.user), label)

class PrivateMessage(models.Model):
    title = models.CharField(max_length=255)
    label = models.ForeignKey("PrivateMessageLabel", blank=True, null=True)
    author = models.ForeignKey(User)
    participants = models.ManyToManyField(User, through="PrivateMessageParticipant", related_name="+")

    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s : %s" % (unicode(self.author), self.title)

class PrivateMessageParticipant(models.Model):
    pm = models.ForeignKey("PrivateMessage")
    user = models.ForeignKey(User)
    ignore = models.BooleanField(default=False)
    blocked = models.BooleanField(default=False)
    left = models.BooleanField(default=False)
    last_viewed = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return "%s :: %s" % (unicode(self.user), unicode(pm))

class PrivateMessageReply(models.Model):
    pm = models.ForeignKey("PrivateMessage")
    author = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True)
    edited = models.DateTimeField(auto_now=True)
    content = models.TextField(blank=True)

    def __str__(self):
        return "%s :: %s" % (unicode(self.author), unicode(pm))

class Notification(models.Model):
    user = models.ForeignKey(User)
    created = models.DateField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content = GenericForeignKey('content_type', 'object_id')

    action = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    author = models.ForeignKey(User, null=True, blank=True, related_name="+")
    meta = HStoreField(blank=True, null=True)

    seen = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)

    def __str__(self):
        return "%s : %s : %s" % (unicode(self.user), unicode(self.created), self.category)

class NotificationPreferences(models.Model):
    user = models.OneToOneField(User)
    
    OPTIONS = (
        (0, "Dashboard"),
        (1, "Email"),
        (2, "All")
    )
    moderation = models.CharField(choices=OPTIONS, default=0, max_length=255)
    topics = models.CharField(choices=OPTIONS, default=0, max_length=255)
    status = models.CharField(choices=OPTIONS, default=0, max_length=255)
    quote = models.CharField(choices=OPTIONS, default=0, max_length=255)
    mention = models.CharField(choices=OPTIONS, default=0, max_length=255)
    followed = models.CharField(choices=OPTIONS, default=0, max_length=255)
    messages = models.CharField(choices=OPTIONS, default=0, max_length=255)
    announcements = models.CharField(choices=OPTIONS, default=0, max_length=255)

    def __str__(self):
        return unicode(self.user)

class MailingListExclude(models.Model):
    user = models.ForeignKey(User)
    exclude = models.BooleanField(default=False)

    def __str__(self):
        return unicode(self.user)