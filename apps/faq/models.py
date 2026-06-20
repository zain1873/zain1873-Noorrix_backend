from django.db import models


class FAQ(models.Model):
    question   = models.CharField(max_length=500)
    answer     = models.TextField()
    order      = models.PositiveSmallIntegerField(
        default=0,
        help_text="Lower number appears first."
    )
    is_active  = models.BooleanField(
        default=True,
        help_text="Uncheck to hide this FAQ without deleting it."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created_at"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question[:80]
