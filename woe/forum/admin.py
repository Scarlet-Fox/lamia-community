from django.contrib import admin
from forum.models import *

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('parent', 'weight', 'title')

admin.site.register(Category, CategoryAdmin)

class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created', 'category')

    fieldsets = (
        (None, {
            'fields': ('category', 'title', 'author', 'prefix'),
        }),
        ("Recent Status", {
            'fields': ('active_user','created','last_updated'),
        }),
        ("Tracking", {
            'fields': ('views','post_count'),
        }),
        ("Moderation", {
            'fields': ('sticky','closed','hidden','hide_message'),
        }),
    )

    list_filter = ('category',)
admin.site.register(Topic, TopicAdmin)

class PostAdmin(admin.ModelAdmin):
    list_display = ('topic', 'author', 'created')

    fieldsets = (
        (None, {
            'fields': ('topic', 'author', 'content', 'edited_by', 'meta'),
        }),
        ("Moderation", {
            'fields': ('hidden','hide_message','flag_score','ignore_flags'),
        }),
    )

    search_fields = ('topic__title', 'author__username')
admin.site.register(Post, PostAdmin)

class FlagAdmin(admin.ModelAdmin):
    list_display = ('content', 'flag_user', 'created')
    search_fields = ('flag_user__username',)
admin.site.register(Flag, FlagAdmin)

class BanAdmin(admin.ModelAdmin):
    list_display = ('user', 'ip_address', 'created', 'mod')
    search_fields = ('user__username', 'ip_address')
admin.site.register(Ban, BanAdmin)

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'created', 'action', 'category')
    list_filter = ('category',)
admin.site.register(Notification, NotificationAdmin)

class LogAdmin(admin.ModelAdmin):
    list_display = ('user', 'created', 'category', 'details')
    search_fields = ('details',)
    list_filter = ('category',)
admin.site.register(LogEntry, LogAdmin)

class StatusUpdateAdmin(admin.ModelAdmin):
    list_display = ('author', 'created', 'message')
    list_filter = ('author__username',)
    search_fields = ('message',)
admin.site.register(StatusUpdate, StatusUpdateAdmin)

class ReportCommentInline(admin.TabularInline):
    model = ReportComment

class ReportAdmin(admin.ModelAdmin):
    list_display = ('author', 'status', 'created', 'report')
    list_filter = ('status',)
    search_fields = ('report',)

    inlines = [
        ReportCommentInline,
    ]
admin.site.register(Report, ReportAdmin)

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'title',)
    search_fields = ('about',)
admin.site.register(Profile, ProfileAdmin)

class PrivateMessageParticipantInline(admin.TabularInline):
    model = PrivateMessageParticipant

class PrivateMessageReplyInline(admin.TabularInline):
    model = PrivateMessageReply

class PrivateMessageAdmin(admin.ModelAdmin):
    list_display = ('author', 'title', 'created')
    inlines = [
        PrivateMessageParticipantInline,
        PrivateMessageReplyInline
    ]
admin.site.register(PrivateMessage, PrivateMessageAdmin)

class IPAddressAdmin(admin.ModelAdmin):
    list_display = ('ip_address',)
    search_fields = ('ip_address',)
admin.site.register(UserIP, IPAddressAdmin)