from django.urls import path
from .views import ContactSubmissionView

urlpatterns = [
    path("contact/", ContactSubmissionView.as_view(), name="contact-submit"),
]
