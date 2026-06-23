from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .emails import send_admin_testimonial_notification
from .models import Testimonial
from .serializers import TestimonialCreateSerializer, TestimonialSerializer


class TestimonialListView(generics.ListAPIView):
    """GET /api/testimonials/ — approved reviews only, for the public site."""

    serializer_class   = TestimonialSerializer
    permission_classes = [AllowAny]
    queryset            = Testimonial.objects.filter(is_approved=True)


class TestimonialCreateView(generics.CreateAPIView):
    """POST /api/testimonials/submit/ — anyone can submit a review.
    It's held back (is_approved=False) until a staff member approves it."""

    serializer_class   = TestimonialCreateSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        testimonial = serializer.save()

        send_admin_testimonial_notification(testimonial)

        return Response(
            {"success": True, "message": "Thanks for your review! It'll appear once approved."},
            status=status.HTTP_201_CREATED,
        )
