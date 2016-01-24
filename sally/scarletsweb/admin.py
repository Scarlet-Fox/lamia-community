from django.contrib import admin
from .models import *

@admin.register(SiteTheme)
class SiteThemeAdmin(admin.ModelAdmin):
    pass

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    pass

@admin.register(IgnoredUser)
class IgnoredUserAdmin(admin.ModelAdmin):
    pass

@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    pass

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    pass

@admin.register(DisplayNameHistory)
class DisplayNameHistoryAdmin(admin.ModelAdmin):
    pass

@admin.register(Fingerprint)
class FingerprintAdmin(admin.ModelAdmin):
    pass

@admin.register(IPAddress)
class IPAddressAdmin(admin.ModelAdmin):
    pass

@admin.register(StatusUpdateUser)
class StatusUpdateUserAdmin(admin.ModelAdmin):
    pass

@admin.register(StatusComment)
class StatusCommentAdmin(admin.ModelAdmin):
    pass

@admin.register(StatusUpdate)
class StatusUpdateAdmin(admin.ModelAdmin):
    pass

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
