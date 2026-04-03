from django.contrib import admin
from .models import Category, Post, VisitorLog


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "created_at", "is_secret")
    list_filter = ("category", "is_secret")
    search_fields = ("title", "content")


admin.site.register(Category)
admin.site.register(VisitorLog)
