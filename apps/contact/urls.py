from django.urls import path
from .views import ContactSubmissionView, EmailTestView

urlpatterns = [
    path("contact/", ContactSubmissionView.as_view(), name="contact-submit"),
    path("email-test/", EmailTestView.as_view(), name="email-test"),
]
