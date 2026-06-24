from django.urls import path
from .views import PartExchangeRequestView

urlpatterns = [
    path("part-exchange/", PartExchangeRequestView.as_view(), name="part-exchange-submit"),
]
