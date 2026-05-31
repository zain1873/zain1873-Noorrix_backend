from django.contrib.auth import get_user_model
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """Extends the standard JWT login response with name and email."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            try:
                user = User.objects.get(email=request.data.get("email", ""))
                response.data["name"] = user.name
                response.data["email"] = user.email
            except User.DoesNotExist:
                pass
        return response


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        email = serializer.validated_data['email']
        return Response({'detail': f'If this email is registered, an OTP has been sent to {email}.'})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Password has been reset successfully.'})
