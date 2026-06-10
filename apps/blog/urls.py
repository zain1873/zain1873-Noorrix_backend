from django.urls import path
from .views import BlogPostListView, BlogPostDetailView

urlpatterns = [
    path("api/blogs/", BlogPostListView.as_view(), name="blog-list"),
    path("api/blogs/<slug:slug>/", BlogPostDetailView.as_view(), name="blog-detail"),
]
