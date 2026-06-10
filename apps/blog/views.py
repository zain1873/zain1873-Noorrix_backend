from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import BlogPost
from .serializers import BlogPostListSerializer, BlogPostDetailSerializer


class BlogPostListView(generics.ListAPIView):
    serializer_class   = BlogPostListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = BlogPost.objects.filter(is_published=True)
        if self.request.query_params.get("featured") == "true":
            qs = qs.filter(is_featured=True)
        return qs


class BlogPostDetailView(generics.RetrieveAPIView):
    serializer_class   = BlogPostDetailSerializer
    permission_classes = [AllowAny]
    queryset           = BlogPost.objects.filter(is_published=True)
    lookup_field       = "slug"
