from django.db import models


class PartExchangeRequest(models.Model):
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    make = models.CharField(max_length=60)
    model = models.CharField(max_length=60)
    year = models.CharField(max_length=10)
    mileage = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    contacted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.make} {self.model} ({self.year})"
