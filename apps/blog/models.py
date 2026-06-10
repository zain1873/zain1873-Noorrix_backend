from django.db import models
from django.utils.text import slugify


class BlogPost(models.Model):
    title        = models.CharField(max_length=255)
    slug         = models.SlugField(max_length=255, unique=True, blank=True)
    excerpt      = models.TextField(help_text="Short summary shown on the card (1–3 sentences)")
    body         = models.TextField(help_text="Full article content (Markdown or HTML)")
    image        = models.ImageField(upload_to="blogs/", help_text="Cover image — recommended 1200×630px")
    is_featured  = models.BooleanField(default=False, help_text="Show as the featured/editor's pick post")
    is_published = models.BooleanField(default=False, help_text="Only published posts appear on the site")
    read_time    = models.PositiveSmallIntegerField(help_text="Estimated read time in minutes")
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
