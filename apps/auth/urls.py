from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import RegisterView, PasswordResetView, PasswordResetConfirmView, CustomTokenObtainPairView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('token/', CustomTokenObtainPairView.as_view(), name='auth-token'),
    path('token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),
    path('password-reset/', PasswordResetView.as_view(), name='auth-password-reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='auth-password-reset-confirm'),
]
