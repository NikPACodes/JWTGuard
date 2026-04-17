from django.contrib import admin
from apps.content.models import ContentItem

@admin.register(ContentItem)
class ContentItemAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "created_at")
    filter_horizontal = ("allowed_groups",)
    search_fields = ("title",)