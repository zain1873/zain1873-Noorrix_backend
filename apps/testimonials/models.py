from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Testimonial(models.Model):
    """A customer-submitted review for the public 'What Our Clients Say'
    section. Submitted via the site with no login required; shows up
    immediately. ``is_approved`` defaults to True so it's only a manual
    takedown switch for staff (e.g. spam) — not an approval gate."""

    name      = models.CharField(max_length=100)
    role      = models.CharField(
        max_length=120, blank=True,
        help_text='Optional, e.g. "Verified Customer" or a location',
    )
    rating    = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review    = models.TextField()
    photo     = models.ImageField(upload_to="testimonials/", blank=True, null=True)
    is_approved  = models.BooleanField(default=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.name} ({self.rating}★) — {'visible' if self.is_approved else 'hidden'}"
 