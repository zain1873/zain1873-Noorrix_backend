from django.contrib import admin

from .models import Testimonial


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display   = ("name", "rating", "is_approved", "submitted_at")
    list_filter    = ("is_approved", "rating", "submitted_at")
    search_fields  = ("name", "review")
    readonly_fields = ("submitted_at",)
    actions = ("approve_testimonials", "unapprove_testimonials")

    @admin.action(description="Approve selected testimonials")
    def approve_testimonials(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"Approved {updated} testimonial(s).")

    @admin.action(description="Unapprove selected testimonials")
    def unapprove_testimonials(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"Unapproved {updated} testimonial(s).")
