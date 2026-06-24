from rest_framework import serializers

from apps.cars.utils import to_browser_safe_image

from .models import Testimonial


class TestimonialCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Testimonial
        fields = ("name", "role", "rating", "review", "photo")

    def validate_photo(self, photo):
        return to_browser_safe_image(photo) if photo else photo


class TestimonialSerializer(serializers.ModelSerializer):
    """Public shape — excludes any testimonial staff have hidden."""

    photo_url = serializers.SerializerMethodField()

    class Meta:
        model  = Testimonial
        fields = ("id", "name", "role", "rating", "review", "photo_url", "submitted_at")

    def get_photo_url(self, obj):
        if not obj.photo:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.photo.url) if request else obj.photo.url
