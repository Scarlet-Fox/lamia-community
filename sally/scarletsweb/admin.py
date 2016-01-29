from django.contrib import admin
from .models import *

@admin.register(SiteTheme)
class SiteThemeAdmin(admin.ModelAdmin):
    list_display = ("theme_name", "created_date")
    search_fields = ("theme_name",)

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("pre_html", "role", "post_html")
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
    pass

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    pass

@admin.register(SiteLog)
class SiteLogAdmin(admin.ModelAdmin):
    pass

@admin.register(PrivateMessageUser)
class PrivateMessageUserAdmin(admin.ModelAdmin):
    pass

@admin.register(PrivateMessage)
class PrivateMessageAdmin(admin.ModelAdmin):
    pass

@admin.register(PrivateMessageReply)
class PrivateMessageReplyAdmin(admin.ModelAdmin):
    pass

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    pass

@admin.register(ReportComment)
class ReportCommentAdmin(admin.ModelAdmin):
    pass

@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    pass

@admin.register(PostHistory)
class PostHistoryAdmin(admin.ModelAdmin):
    pass

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    pass

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    pass

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    pass

@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    pass
