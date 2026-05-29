from django.contrib import admin
from .models import ContactSubmission


@admin.register(ContactSubmission)
class ContactSubmissionAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "subject", "submitted_at", "is_read"]
    list_filter = ["is_read", "submitted_at"]
    search_fields = ["name", "email", "subject"]
    readonly_fields = ["name", "email", "phone", "subject", "message", "submitted_at"]
