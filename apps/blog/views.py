from rest_framework import generics
from rest_framework.permissions import AllowAny
from .models import BlogPost, BlogCategory
from .serializers import BlogPostListSerializer, BlogPostDetailSerializer, BlogCategorySerializer


class BlogCategoryListView(generics.ListAPIView):
    serializer_class   = BlogCategorySerializer
    permission_classes = [AllowAny]
    queryset           = BlogCategory.objects.all()


class BlogPostListView(generics.ListAPIView):
    serializer_class   = BlogPostListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = BlogPost.objects.filter(is_published=True).select_related("category")
        if self.request.query_params.get("featured") == "true":
            qs = qs.filter(is_featured=True)
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category__name__iexact=category)
        return qs


class BlogPostDetailView(generics.RetrieveAPIView):
    serializer_class   = BlogPostDetailSerializer
    permission_classes = [AllowAny]
    queryset           = BlogPost.objects.filter(is_published=True).select_related("category")
    lookup_field       = "slug"
