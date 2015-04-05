# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django.contrib.postgres.fields.hstore


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Ban',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ip_address', models.GenericIPAddressField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('mod', models.ForeignKey(related_name='banned', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(related_name='bans', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('weight', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='CategoryParticipant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('moderator', models.BooleanField(default=False)),
                ('category', models.ForeignKey(to='forum.Category')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Flag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('flag_score', models.IntegerField(default=1)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('flag_user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Friend',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('follow_posts', models.BooleanField(default=False)),
                ('follow_status', models.BooleanField(default=False)),
                ('follow_topics', models.BooleanField(default=False)),
                ('friend', models.ForeignKey(related_name='followers', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='LogEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ip_address', models.GenericIPAddressField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('category', models.CharField(max_length=255)),
                ('details', models.TextField(blank=True)),
                ('user', models.ForeignKey(related_name='logs', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='MailingListExclude',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('exclude', models.BooleanField(default=False)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ModerationNotes',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('comment', models.TextField(blank=True)),
                ('author', models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='NotificationPreferences',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('moderation', models.CharField(default=0, max_length=255, choices=[(0, b'Dashboard'), (1, b'Email'), (2, b'All')])),
                ('topics', models.CharField(default=0, max_length=255, choices=[(0, b'Dashboard'), (1, b'Email'), (2, b'All')])),
                ('status', models.CharField(default=0, max_length=255, choices=[(0, b'Dashboard'), (1, b'Email'), (2, b'All')])),
                ('quote', models.CharField(default=0, max_length=255, choices=[(0, b'Dashboard'), (1, b'Email'), (2, b'All')])),
                ('mention', models.CharField(default=0, max_length=255, choices=[(0, b'Dashboard'), (1, b'Email'), (2, b'All')])),
                ('followed', models.CharField(default=0, max_length=255, choices=[(0, b'Dashboard'), (1, b'Email'), (2, b'All')])),
                ('messages', models.CharField(default=0, max_length=255, choices=[(0, b'Dashboard'), (1, b'Email'), (2, b'All')])),
                ('announcements', models.CharField(default=0, max_length=255, choices=[(0, b'Dashboard'), (1, b'Email'), (2, b'All')])),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Notifications',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateField(auto_now_add=True)),
                ('object_id', models.PositiveIntegerField()),
                ('action', models.CharField(max_length=255)),
                ('category', models.CharField(max_length=255)),
                ('meta', django.contrib.postgres.fields.hstore.HStoreField()),
                ('seen', models.BooleanField(default=False)),
                ('hidden', models.BooleanField(default=False)),
                ('author', models.ForeignKey(related_name='+', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('edited', models.DateTimeField(auto_now=True)),
                ('content', models.TextField(blank=True)),
                ('meta', django.contrib.postgres.fields.hstore.HStoreField()),
                ('hidden', models.BooleanField(default=False)),
                ('hide_message', models.CharField(max_length=255, blank=True)),
                ('flag_score', models.IntegerField(default=0)),
                ('ignore_flags', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('edited_by', models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Prefix',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('pre_html', models.CharField(max_length=255)),
                ('post_html', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='PrivateMessage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PrivateMessageLabel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(max_length=255)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PrivateMessageParticipant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ignore', models.BooleanField(default=False)),
                ('blocked', models.BooleanField(default=False)),
                ('left', models.BooleanField(default=False)),
                ('last_viewed', models.DateTimeField(null=True, blank=True)),
                ('pm', models.ForeignKey(to='forum.PrivateMessage')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PrivateMessageReply',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('edited', models.DateTimeField(auto_now=True)),
                ('content', models.TextField(blank=True)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('pm', models.ForeignKey(to='forum.PrivateMessage')),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('location', models.CharField(max_length=255, blank=True)),
                ('time_zone', models.FloatField(default=0.0)),
                ('about', models.TextField(blank=True)),
                ('birthday', models.DateField(null=True, blank=True)),
                ('age', models.IntegerField(null=True, blank=True)),
                ('hide_age', models.BooleanField(default=True)),
                ('hide_birthday', models.BooleanField(default=True)),
                ('gender', models.CharField(default=b'n', max_length=255, choices=[(b'n', b''), (b'f', b'Female'), (b'm', b'Male'), (b'g', b'Genderfluid'), (b'o', b'Other')])),
                ('hide_gender', models.BooleanField(default=True)),
                ('favorite_color', models.CharField(default=b'Red', max_length=255, blank=True)),
                ('how_found', models.TextField(blank=True)),
                ('fields', django.contrib.postgres.fields.hstore.HStoreField()),
                ('avatar', models.ImageField(upload_to=b'avatars', blank=True)),
                ('validation_status', models.IntegerField(default=0, choices=[(0, b'Pending'), (1, b'Reviewing'), (2, b'Validated'), (3, b'Banned in Validation')])),
                ('moderation_status', models.IntegerField(default=2, choices=[(0, b'Under Review'), (1, b'Request Feedback'), (2, b'Good'), (3, b'Bad Egg'), (4, b'KO')])),
                ('disable_posts', models.BooleanField(default=False)),
                ('disable_status', models.BooleanField(default=False)),
                ('disable_pm', models.BooleanField(default=False)),
                ('disable_topics', models.BooleanField(default=False)),
                ('hellban', models.BooleanField(default=False)),
                ('posts', models.IntegerField(default=0)),
                ('status_updates', models.IntegerField(default=0)),
                ('status_comments', models.IntegerField(default=0)),
                ('friends', models.ManyToManyField(related_name='+', through='forum.Friend', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('report', models.TextField(blank=True)),
                ('status', models.IntegerField(default=1, choices=[(0, b'Closed'), (1, b'Open'), (2, b'Feedback Requested'), (3, b'Waiting')])),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='ReportComments',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('comment', models.TextField(blank=True)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('report', models.ForeignKey(to='forum.Report')),
            ],
        ),
        migrations.CreateModel(
            name='Signature',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('description', models.CharField(max_length=255)),
                ('content', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='StatusComments',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('comment', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('hidden', models.BooleanField(default=False)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='StatusParticipant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('following', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='StatusUpdate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('message', models.TextField()),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('participants', models.ManyToManyField(related_name='+', through='forum.StatusParticipant', to=settings.AUTH_USER_MODEL)),
                ('profile', models.ForeignKey(related_name='+', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Topic',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('meta', django.contrib.postgres.fields.hstore.HStoreField()),
                ('created', models.DateTimeField(null=True, blank=True)),
                ('last_updated', models.DateTimeField(null=True, blank=True)),
                ('views', models.IntegerField(default=0)),
                ('post_count', models.IntegerField(default=0)),
                ('sticky', models.BooleanField(default=False)),
                ('closed', models.BooleanField(default=False)),
                ('hidden', models.BooleanField(default=False)),
                ('hide_message', models.CharField(max_length=255)),
                ('active_user', models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL)),
                ('author', models.ForeignKey(related_name='my_topics', to=settings.AUTH_USER_MODEL)),
                ('category', models.ForeignKey(to='forum.Category')),
            ],
        ),
        migrations.CreateModel(
            name='TopicParticipant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('following', models.BooleanField(default=False)),
                ('posts', models.IntegerField(default=0)),
                ('moderator', models.BooleanField(default=False)),
                ('last_seen', models.DateTimeField(null=True, blank=True)),
                ('topic', models.ForeignKey(to='forum.Topic')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='topic',
            name='participants',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='forum.TopicParticipant'),
        ),
        migrations.AddField(
            model_name='topic',
            name='prefix',
            field=models.ForeignKey(blank=True, to='forum.Prefix', null=True),
        ),
        migrations.AddField(
            model_name='topic',
            name='recent_post',
            field=models.ForeignKey(related_name='+', to='forum.Post'),
        ),
        migrations.AddField(
            model_name='statusparticipant',
            name='status',
            field=models.ForeignKey(to='forum.StatusUpdate'),
        ),
        migrations.AddField(
            model_name='statusparticipant',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='statuscomments',
            name='status',
            field=models.ForeignKey(to='forum.StatusUpdate'),
        ),
        migrations.AddField(
            model_name='profile',
            name='status',
            field=models.ForeignKey(related_name='+', blank=True, to='forum.StatusUpdate', null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='user',
            field=models.OneToOneField(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='privatemessage',
            name='label',
            field=models.ForeignKey(blank=True, to='forum.PrivateMessageLabel', null=True),
        ),
        migrations.AddField(
            model_name='privatemessage',
            name='participants',
            field=models.ManyToManyField(related_name='+', through='forum.PrivateMessageParticipant', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='post',
            name='topic',
            field=models.ForeignKey(to='forum.Topic'),
        ),
        migrations.AddField(
            model_name='friend',
            name='user',
            field=models.ForeignKey(related_name='+', to='forum.Profile'),
        ),
        migrations.AddField(
            model_name='category',
            name='moderators',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='forum.CategoryParticipant'),
        ),
        migrations.AddField(
            model_name='category',
            name='parent',
            field=models.ForeignKey(blank=True, to='forum.Category', null=True),
        ),
    ]
