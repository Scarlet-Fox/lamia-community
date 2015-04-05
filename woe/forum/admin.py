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