from django.urls import path

from .views import AppointmentCreateView, AvailabilityView

urlpatterns = [
    path("api/appointments/availability/", AvailabilityView.as_view(), name="appointment-availability"),
    path("api/appointments/", AppointmentCreateView.as_view(), name="appointment-create"),
]
