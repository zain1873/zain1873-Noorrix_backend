from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .emails import send_admin_testimonial_notification
from .models import Testimonial
from .serializers import TestimonialCreateSerializer, TestimonialSerializer


class TestimonialListView(generics.ListAPIView):
    """GET /api/testimonials/ — visible reviews, for the public site.
    Excludes any a staff member has manually hidden (e.g. spam)."""

    serializer_class   = TestimonialSerializer
    permission_classes = [AllowAny]
    queryset            = Testimonial.objects.filter(is_approved=True)


class TestimonialCreateView(generics.CreateAPIView):
    """POST /api/testimonials/submit/ — anyone can submit a review.
    It appears on the site immediately; staff can hide it later if needed."""

    serializer_class   = TestimonialCreateSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        testimonial = serializer.save()

        send_admin_testimonial_notification(testimonial)

        return Response(
            {"success": True, "message": "Thanks for your review!"},
            status=status.HTTP_201_CREATED,
        )
