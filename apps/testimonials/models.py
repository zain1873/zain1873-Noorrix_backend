from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Testimonial(models.Model):
    """A customer-submitted review for the public 'What Our Clients Say'
    section. Submitted via the site with no login required; held back from
    the public API until a staff member approves it."""

    name      = models.CharField(max_length=100)
    role      = models.CharField(
        max_length=120, blank=True,
        help_text='Optional, e.g. "Verified Customer" or a location',
    )
    rating    = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review    = models.TextField()
    photo     = models.ImageField(upload_to="testimonials/", blank=True, null=True)
    is_approved  = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.name} ({self.rating}★) — {'approved' if self.is_approved else 'pending'}"
