from django.urls import path
from .views import DeliveryRequestView

urlpatterns = [
    path("delivery/", DeliveryRequestView.as_view(), name="delivery-submit"),
]
