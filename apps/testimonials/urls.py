from django.urls import path

from .views import TestimonialCreateView, TestimonialListView

urlpatterns = [
    path("api/testimonials/", TestimonialListView.as_view(), name="testimonial-list"),
    path("api/testimonials/submit/", TestimonialCreateView.as_view(), name="testimonial-create"),
]
