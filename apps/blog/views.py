from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import BlogPost
from .serializers import BlogPostListSerializer, BlogPostDetailSerializer


class BlogPostListView(generics.ListAPIView):
    serializer_class   = BlogPostListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = BlogPost.objects.filter(is_published=True).select_related("category")
        featured = self.request.query_params.get("featured")
        category = self.request.query_params.get("category")
        if featured == "true":
            qs = qs.filter(is_featured=True)
        if category:
            qs = qs.filter(category__name__iexact=category)
        return qs


class BlogPostDetailView(generics.RetrieveAPIView):
    serializer_class   = BlogPostDetailSerializer
    permission_classes = [AllowAny]
    queryset           = BlogPost.objects.filter(is_published=True).select_related("category")
    lookup_field       = "slug"
