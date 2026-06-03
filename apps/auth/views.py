from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import generics, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import RegisterSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer

User = get_user_model()


@extend_schema(
    tags=['Authentication'],
    summary='Obtain JWT token pair',
    responses=inline_serializer(
        name='TokenObtainPairResponse',
        fields={
            'access': serializers.CharField(),
            'refresh': serializers.CharField(),
            'name': serializers.CharField(),
            'email': serializers.EmailField(),
        },
    ),
)
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


@extend_schema(tags=['Authentication'], summary='Register a new user')
class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


@extend_schema(
    tags=['Authentication'],
    summary='Request a password reset OTP',
    request=PasswordResetSerializer,
    responses=inline_serializer(
        name='PasswordResetResponse',
        fields={'detail': serializers.CharField()},
    ),
)
class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        email = serializer.validated_data['email']
        return Response({'detail': f'If this email is registered, an OTP has been sent to {email}.'})


@extend_schema(
    tags=['Authentication'],
    summary='Confirm password reset with OTP',
    request=PasswordResetConfirmSerializer,
    responses=inline_serializer(
        name='PasswordResetConfirmResponse',
        fields={'detail': serializers.CharField()},
    ),
)
class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Password has been reset successfully.'})
