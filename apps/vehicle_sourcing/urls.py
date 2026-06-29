from django.urls import path
from .views import VehicleSourcingRequestView

urlpatterns = [
    path("vehicle-sourcing/", VehicleSourcingRequestView.as_view(), name="vehicle-sourcing-submit"),
]
