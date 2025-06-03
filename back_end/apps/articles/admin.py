from django.contrib import admin
from .models import Article

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "created_at", "updated_at")
    list_filter = ("status", "created_at", "updated_at")
    search_fields = ("title", "content", "author__username", "author__email")
    raw_id_fields = ("author",)
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
