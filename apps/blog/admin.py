from django.contrib import admin
from .models import BlogPost, BlogCategory


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display  = ("name",)
    search_fields = ("name",)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display        = ("title", "category", "is_featured", "is_published", "published_at", "read_time")
    list_filter         = ("is_published", "is_featured", "category")
    search_fields       = ("title", "excerpt", "body")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields     = ("created_at", "updated_at")
    list_editable       = ("is_published", "is_featured")

    fieldsets = (
        ("Content", {
            "fields": ("title", "slug", "category", "excerpt", "body", "image", "read_time")
        }),
        ("Publishing", {
            "fields": ("is_published", "is_featured", "published_at")
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        }),
    )
