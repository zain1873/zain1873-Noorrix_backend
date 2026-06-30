from rest_framework import serializers
from .models import DeliveryRequest


class DeliveryRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryRequest
        fields = ["name", "phone", "email", "vehicle", "address", "postcode", "preferred_date", "notes"]

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters.")
        return value.strip()

    def validate_phone(self, value):
        return value.strip()

    def validate_vehicle(self, value):
        return value.strip()

    def validate_address(self, value):
        return value.strip()

    def validate_postcode(self, value):
        return value.strip()
