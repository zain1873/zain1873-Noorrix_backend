from rest_framework import serializers
from .models import VehicleSourcingRequest


class VehicleSourcingRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleSourcingRequest
        fields = ["name", "phone", "email", "make", "model", "year", "mileage", "budget", "notes"]

    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters.")
        return value.strip()

    def validate_phone(self, value):
        return value.strip()

    def validate_make(self, value):
        return value.strip()

    def validate_model(self, value):
        return value.strip()
