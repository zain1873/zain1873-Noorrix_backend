from django.contrib import admin
from .models import NewsletterSubscriber


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ["email", "is_active", "subscribed_at", "unsubscribed_at"]
    list_filter = ["is_active", "subscribed_at"]
    search_fields = ["email"]
    readonly_fields = ["subscribed_at"]
