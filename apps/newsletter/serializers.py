from rest_framework import serializers
from .models import NewsletterSubscriber


class NewsletterSubscriberSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.strip().lower()
