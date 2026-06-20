from django.urls import path
from .views import BlogPostListView, BlogPostDetailView, BlogCategoryListView

urlpatterns = [
    path("api/blog-categories/",       BlogCategoryListView.as_view(), name="blog-categories"),
    path("api/blogs/",                 BlogPostListView.as_view(),     name="blog-list"),
    path("api/blogs/<slug:slug>/",     BlogPostDetailView.as_view(),   name="blog-detail"),
]
