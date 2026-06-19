from django.db import models


class Appointment(models.Model):
    """A test drive / showroom appointment booking.

    Availability is showroom-wide, not per car — there's one location and
    one staff member handling appointments, so a (date, time) slot can only
    ever be booked once regardless of which car it's for. The unique
    constraint is the actual source of truth against double-booking races;
    application code just translates a collision into a 409.
    """

    class Type(models.TextChoices):
        TEST_DRIVE = "test_drive", "Test Drive"
        APPOINTMENT = "appointment", "Appointment"

    car = models.ForeignKey(
        "cars.Car",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointments",
    )
    type = models.CharField(max_length=20, choices=Type.choices)
    date = models.DateField()
    time = models.TimeField()
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "time"]
        constraints = [
            models.UniqueConstraint(fields=["date", "time"], name="unique_appointment_slot")
        ]

    def __str__(self):
        return f"{self.get_type_display()} — {self.date} {self.time} ({self.name})"
