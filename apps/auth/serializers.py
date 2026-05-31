import secrets

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from rest_framework import serializers

from .models import PasswordResetOTP

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'confirm_password']
        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True},
            'name': {'min_length': 1},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        try:
            validate_password(attrs['password'])
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        return User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name'],
        )


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self):
        email = self.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return

        PasswordResetOTP.objects.filter(user=user, is_used=False).delete()

        otp = f'{secrets.randbelow(1000000):06d}'
        PasswordResetOTP.objects.create(user=user, otp=otp)

        send_mail(
            subject='Password Reset OTP',
            message=(
                f'Your password reset OTP is: {otp}\n\n'
                f'This OTP expires in {PasswordResetOTP.OTP_EXPIRY_MINUTES} minutes.\n\n'
                'If you did not request a password reset, please ignore this email.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError({'otp': ['Invalid or expired OTP.']})

        otp_obj = PasswordResetOTP.objects.filter(
            user=user, otp=attrs['otp'], is_used=False
        ).last()

        if not otp_obj or not otp_obj.is_valid():
            raise serializers.ValidationError({'otp': ['Invalid or expired OTP.']})

        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': ['Passwords do not match.']})

        try:
            validate_password(attrs['new_password'], user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'new_password': list(e.messages)})

        attrs['user'] = user
        attrs['otp_obj'] = otp_obj
        return attrs

    def save(self):
        otp_obj = self.validated_data['otp_obj']
        otp_obj.is_used = True
        otp_obj.save()
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
