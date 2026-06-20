from rest_framework import serializers

from .models import Appointment


class AppointmentCreateSerializer(serializers.Serializer):
    """Validates a booking request.

    ``car`` is deliberately not a field here — the view resolves it via
    ``get_object_or_404`` so an unknown id returns 404 (per spec), not the
    400 a PrimaryKeyRelatedField would give.
    """

    type = serializers.ChoiceField(choices=Appointment.Type.choices)
    date = serializers.DateField()
    time = serializers.TimeField()
    name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=30)


class AppointmentSerializer(serializers.ModelSerializer):
    time = serializers.TimeField(format="%H:%M")

    class Meta:
        model = Appointment
        fields = ["id", "car", "type", "date", "time", "name", "email", "phone", "created_at"]
        read_only_fields = fields
