from django.urls import path
from .views import NewsletterSubscribeView, NewsletterUnsubscribeView

urlpatterns = [
    path("newsletter/subscribe/", NewsletterSubscribeView.as_view(), name="newsletter-subscribe"),
    path("newsletter/unsubscribe/", NewsletterUnsubscribeView.as_view(), name="newsletter-unsubscribe"),
]
