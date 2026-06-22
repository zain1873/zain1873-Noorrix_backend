from rest_framework import serializers
from .models import Car, Favourite


def _abs(request, image_field):
    """Absolute URL for an ImageField, or None — mirrors the blog app."""
    if image_field and request:
        return request.build_absolute_uri(image_field.url)
    return image_field.url if image_field else None


class CarListSerializer(serializers.ModelSerializer):
    """Card fields for the stock grid / brand list. Numbers are sent raw —
    the front-end formats them (£14,495 / 42,300 Miles / 1,995 CC)."""

    image_url    = serializers.SerializerMethodField()
    is_favourite = serializers.SerializerMethodField()

    class Meta:
        model  = Car
        fields = (
            "id", "title", "subtitle",
            "make", "model", "body_type", "fuel", "transmission", "colour",
            "year", "engine_cc", "mileage", "price", "monthly", "mot_date",
            "image_url", "status", "is_favourite", "deposit_amount",
        )

    def get_image_url(self, obj):
        return _abs(self.context.get("request"), obj.image)

    def get_is_favourite(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        # Cached per-request in the shared serializer context so a list of
        # cars only costs one favourites query, not one per row.
        favourite_ids = self.context.get("favourite_ids")
        if favourite_ids is None:
            favourite_ids = set(
                Favourite.objects.filter(user=request.user).values_list("car_id", flat=True)
            )
            self.context["favourite_ids"] = favourite_ids
        return obj.id in favourite_ids


class CarDetailSerializer(CarListSerializer):
    """Full detail-page payload — everything that used to be hardcoded."""

    images   = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()

    class Meta(CarListSerializer.Meta):
        fields = CarListSerializer.Meta.fields + (
            "engine", "doors", "seats", "history_check",
            "images", "features", "description",
            "video_url", "location",
            "created_at", "updated_at",
        )

    def get_images(self, obj):
        request = self.context.get("request")
        gallery = [_abs(request, img.image) for img in obj.gallery.all()]
        # Fall back to the main image so the slider always has at least one.
        return gallery or ([_abs(request, obj.image)] if obj.image else [])

    def get_features(self, obj):
        return [{"category": f.category, "text": f.text} for f in obj.features.all()]

    def get_location(self, obj):
        if not (obj.location_name or obj.location_address):
            return None
        return {"name": obj.location_name, "address": obj.location_address}
