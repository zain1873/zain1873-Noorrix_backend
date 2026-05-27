from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import RegisterView, PasswordResetView, PasswordResetConfirmView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('token/', TokenObtainPairView.as_view(), name='auth-token'),
    path('token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),
    path('password-reset/', PasswordResetView.as_view(), name='auth-password-reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='auth-password-reset-confirm'),
]
