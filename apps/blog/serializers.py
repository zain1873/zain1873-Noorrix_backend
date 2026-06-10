from rest_framework import serializers
from .models import BlogPost


class BlogPostListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model  = BlogPost
        fields = (
            "id", "title", "slug",
            "excerpt", "image_url", "read_time",
            "is_featured", "published_at",
        )

    def get_image_url(self, obj):
        request = self.context.get("request")
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class BlogPostDetailSerializer(BlogPostListSerializer):
    class Meta(BlogPostListSerializer.Meta):
        fields = BlogPostListSerializer.Meta.fields + ("body",)
