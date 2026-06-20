from datetime import datetime

from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cars.models import Car

from .emails import send_admin_appointment_notification, send_appointment_confirmation
from .models import Appointment
from .serializers import AppointmentCreateSerializer, AppointmentSerializer


class AvailabilityView(APIView):
    """GET /api/appointments/availability/?date=YYYY-MM-DD

    Booked slots for that date across all cars — one showroom, one
    appointment at a time, regardless of which car it's for.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        date_str = request.query_params.get("date")
        if not date_str:
            return Response(
                {"error": "date query param is required."}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "date must be in YYYY-MM-DD format."}, status=status.HTTP_400_BAD_REQUEST
            )

        booked_times = [
            t.strftime("%H:%M")
            for t in Appointment.objects.filter(date=date_obj)
            .order_by("time")
            .values_list("time", flat=True)
        ]
        return Response({"date": date_str, "booked_times": booked_times})


class AppointmentCreateView(APIView):
    """POST /api/appointments/ — book a test drive / appointment slot.

    The (date, time) unique constraint on the model is the actual source of
    truth against double-booking races; this view just translates the
    resulting IntegrityError into a 409.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        car = get_object_or_404(Car, pk=request.data.get("car"))

        serializer = AppointmentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            with transaction.atomic():
                appointment = Appointment.objects.create(car=car, **serializer.validated_data)
        except IntegrityError:
            return Response(
                {"error": "This time slot has just been booked. Please pick another."},
                status=status.HTTP_409_CONFLICT,
            )

        send_appointment_confirmation(appointment)
        send_admin_appointment_notification(appointment)

        return Response(AppointmentSerializer(appointment).data, status=status.HTTP_201_CREATED)
