from django.contrib import admin

from .models import Testimonial


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display   = ("name", "rating", "is_approved", "submitted_at")
    list_filter    = ("is_approved", "rating", "submitted_at")
    search_fields  = ("name", "review")
    readonly_fields = ("submitted_at",)
    actions = ("show_testimonials", "hide_testimonials")

    @admin.action(description="Show selected testimonials on the site")
    def show_testimonials(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"Shown {updated} testimonial(s).")

    @admin.action(description="Hide selected testimonials from the site")
    def hide_testimonials(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"Hidden {updated} testimonial(s).")
