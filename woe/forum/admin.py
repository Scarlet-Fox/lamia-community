from django.contrib import admin
from forum.models import *

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('parent', 'weight', 'title')

admin.site.register(Category, CategoryAdmin)