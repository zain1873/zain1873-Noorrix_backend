from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .serializers import RegisterSerializer


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


class PasswordResetView(APIView):
    pass


class PasswordResetConfirmView(APIView):
    pass
