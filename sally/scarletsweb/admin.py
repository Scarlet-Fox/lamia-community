from django.contrib import admin
from .models import *

@admin.register(SiteTheme)
class SiteThemeAdmin(admin.ModelAdmin):
    list_display = ("theme_name", "created_date")
    search_fields = ("theme_name",)

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("role",)
    search_fields = ("role",)

@admin.register(IgnoredUser)
class IgnoredUserAdmin(admin.ModelAdmin):
    list_display = ("created_date", "is_ignoring", "is_ignored", "distort_posts", "block_sigs", "block_pms", "block_blogs", "block_status")
    search_fields = ("is_ignoring__display_name", "is_ignored__display_name")

@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ("requester", "target", "created_date", "pending", "blocked")
    search_fields = ("requester__display_name", "target__display_name")

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("profile_user", "display_name", "banned", "validated", "joined")
    search_fields = ("profile_user__username", "display_name")
    list_filter = ("profile_user__is_staff", "banned", "validated")

@admin.register(DisplayNameHistory)
class DisplayNameHistoryAdmin(admin.ModelAdmin):
    list_display = ("user_profile", "name", "date")
    search_fields = ("user_profile__display_name", "user_profile__profile_user__username")

@admin.register(Fingerprint)
class FingerprintAdmin(admin.ModelAdmin):
    list_display = ("fingerprint_user", "factor_count", "fingerprint_last_seen")
    search_fields = ("fingerprint_user__display_name", "fingerprint_user__profile_user__username")

@admin.register(IPAddress)
class IPAddressAdmin(admin.ModelAdmin):
    list_display = ("user", "ip_address", "last_seen")
    search_fields = ("user__display_name", "user__profile_user__username")

class StatusUpdateUserInline(admin.TabularInline):
    model = StatusUpdateUser

@admin.register(StatusComment)
class StatusCommentAdmin(admin.ModelAdmin):
    list_display = ("author", "created", "snippet", "status_update")
    search_fields = ("author__display_name", "author__profile_user__username", "status_update__message", "message")

@admin.register(StatusUpdate)
class StatusUpdateAdmin(admin.ModelAdmin):
    list_display = ("author", "created", "snippet")
    search_fields = ("author__display_name", "author__profile_user__username")

    inlines = [
        StatusUpdateUserInline,
    ]

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("path", "user", "size_in_bytes", "created_date")
    search_fields = ("path", "user__display_name", "user__profile_user__username")

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "created", "message", "category")
    search_fields = ("message", "user__display_name", "user__profile_user__username")
    list_filter = ("category", "acknowledged", "seen")

@admin.register(SiteLog)
class SiteLogAdmin(admin.ModelAdmin):
    list_display = ("user", "time", "ip_address", "method", "path", "error", "error_code")
    search_fields = ("user__display_name", "user__profile_user__username", "path")
    list_filter = ("error", "error_code")

class PrivateMessageUserInline(admin.TabularInline):
    model = PrivateMessageUser

@admin.register(PrivateMessage)
class PrivateMessageAdmin(admin.ModelAdmin):
    list_display = ("author", "id", "title", "message_count", "last_reply", "created")
    search_fields = ("author__display_name", "author__profile_user__username", "title")
    exclude = ("last_reply",)

    inlines = [
        PrivateMessageUserInline,
    ]

@admin.register(PrivateMessageReply)
class PrivateMessageReplyAdmin(admin.ModelAdmin):
    list_display = ("author", "snippet", "private_message", "created",)
    search_fields = ("author__display_name", "author__profile_user__username", "private_message__title")

class ReportCommentInline(admin.TabularInline):
    model = ReportComment

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("created", "initiated", "snippet", "url", "report_status","content_author")
    search_fields = ("content_author__display_name", "content_author__profile_user__username",
        "initiated__display_name", "initiated__profile_user__username", )
    list_filter = ("report_status", )

    inlines = [
        ReportCommentInline,
    ]

@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ("label",)
    search_fields = ("label",)

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("name", "weight", )
    search_fields = ("name",)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "weight", "restricted", "section", "parent",
        "topic_count", "post_count", "view_count", "most_recent_topic")
    search_fields = ("name",)
    list_filter = ("section", )
    exclude = ('most_recent_topic','most_recent_post',)

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "created", "author", "category", "sticky", "announcement", "label", "hidden")
    search_fields = ("name","author__display_name", "author__profile_user__username")
    list_filter = ("category", "sticky", "announcement", "hidden", "locked", "label")
    exclude = ('most_recent_post',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("created", "author", "topic",)
    list_filter = ("hidden",)
    search_fields = ("html","author__display_name", "author__profile_user__username")
    exclude = ('topic','report','editor', 'avatar','character')

@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    list_display = ("created", "author", "name")
    search_fields = ("name","author__display_name", "author__profile_user__username")
    list_filter = ("hidden",)
