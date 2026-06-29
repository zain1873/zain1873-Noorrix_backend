from django.db import models


class VehicleSourcingRequest(models.Model):
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    make = models.CharField(max_length=60)
    model = models.CharField(max_length=60)
    year = models.CharField(max_length=10)
    mileage = models.CharField(max_length=20)
    budget = models.CharField(max_length=40)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    contacted = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} — {self.make} {self.model} ({self.budget})"
