from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import FAQ
from .serializers import FAQSerializer


class FAQListView(generics.ListAPIView):
    serializer_class   = FAQSerializer
    permission_classes = [AllowAny]
    queryset           = FAQ.objects.filter(is_active=True)
