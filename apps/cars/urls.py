from django.urls import path

from .views import (
    CarDetailView,
    CarListView,
    FavouriteDeleteView,
    FavouriteListCreateView,
    FiltersView,
    SimilarCarsView,
)

urlpatterns = [
    path("api/cars/",                  CarListView.as_view(),    name="car-list"),
    path("api/cars/<int:pk>/",         CarDetailView.as_view(),  name="car-detail"),
    path("api/cars/<int:pk>/similar/", SimilarCarsView.as_view(), name="car-similar"),
    path("api/filters/",               FiltersView.as_view(),    name="car-filters"),
    path("api/favourites/",            FavouriteListCreateView.as_view(), name="favourite-list-create"),
    path("api/favourites/<int:car_id>/", FavouriteDeleteView.as_view(),   name="favourite-delete"),
]
