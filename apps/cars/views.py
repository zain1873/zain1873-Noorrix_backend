from collections import defaultdict

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Car, CarStatus, Favourite
from .serializers import CarDetailSerializer, CarListSerializer

# Static range options (kept server-side so the front-end and /filters agree).
PRICE_RANGES = [
    {"label": "Under £10,000",      "min": 0,     "max": 10000},
    {"label": "£10,000 – £15,000",  "min": 10000, "max": 15000},
    {"label": "£15,000 – £20,000",  "min": 15000, "max": 20000},
    {"label": "£20,000 – £30,000",  "min": 20000, "max": 30000},
    {"label": "£30,000+",           "min": 30000, "max": None},
]
MILEAGE_RANGES = [
    {"label": "Under 20,000",        "min": 0,      "max": 20000},
    {"label": "20,000 – 50,000",     "min": 20000,  "max": 50000},
    {"label": "50,000 – 100,000",    "min": 50000,  "max": 100000},
    {"label": "100,000+",            "min": 100000, "max": None},
]


def _resolve_make(brand_slug):
    """Map a brand slug (e.g. 'mercedes-benz') back to its stored make name."""
    for make in Car.objects.order_by().values_list("make", flat=True).distinct():
        if slugify(make) == brand_slug:
            return make
    return None


class CarListView(generics.ListAPIView):
    """GET /api/cars/ — all stock (available, reserved, sold) as a plain array.

    Reserved/sold cars are included so their detail/checkout links keep working
    and the front-end shows a "Reserved"/"Sold" badge instead of hiding them.
    Optional ``?make=BMW`` (exact) or ``?brand=bmw`` (slug) for the brand page.
    All other filtering happens client-side on this list.
    """

    serializer_class   = CarListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Car.objects.all()

        make = self.request.query_params.get("make")
        if make:
            qs = qs.filter(make__iexact=make)

        brand = self.request.query_params.get("brand")
        if brand:
            resolved = _resolve_make(brand)
            qs = qs.filter(make=resolved) if resolved else qs.none()

        return qs


class CarDetailView(generics.RetrieveAPIView):
    """GET /api/cars/:id/ — full detail (any status, so reserved/sold links work)."""

    serializer_class   = CarDetailSerializer
    permission_classes = [AllowAny]
    queryset           = Car.objects.prefetch_related("gallery", "features")


class SimilarCarsView(generics.ListAPIView):
    """GET /api/cars/:id/similar/ — same body type or make, excluding this car."""

    serializer_class   = CarListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        car = get_object_or_404(Car, pk=self.kwargs["pk"])
        try:
            limit = max(1, min(int(self.request.query_params.get("limit", 6)), 24))
        except (TypeError, ValueError):
            limit = 6
        return (
            Car.objects.filter(status=CarStatus.AVAILABLE)
            .filter(Q(body_type=car.body_type) | Q(make=car.make))
            .exclude(pk=car.pk)[:limit]
        )


class FiltersView(APIView):
    """GET /api/filters/ — dynamic filter options built from all stock.

    Make/Model/body/fuel/transmission/colour are derived from every car
    (not just "available" ones) so a make/model doesn't vanish from the
    dropdowns just because its only car got reserved/sold — same reasoning
    as why CarListView no longer filters by status. Price/mileage ranges
    are static.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        cars = Car.objects.all()

        make_models = defaultdict(set)
        for make, model in cars.values_list("make", "model"):
            make_models[make].add(model)

        def distinct(field):
            # .order_by() clears the model's default ordering, otherwise the
            # order field leaks into SELECT and breaks DISTINCT.
            values = cars.order_by().values_list(field, flat=True).distinct()
            return sorted(v for v in values if v)

        return Response({
            "makes":         sorted(make_models.keys()),
            "makeModels":    {m: sorted(models) for m, models in sorted(make_models.items())},
            "bodyTypes":     distinct("body_type"),
            "fuelTypes":     distinct("fuel"),
            "transmissions": distinct("transmission"),
            "colours":       distinct("colour"),
            "priceRanges":   PRICE_RANGES,
            "mileageRanges": MILEAGE_RANGES,
        })


class FavouriteListCreateView(APIView):
    """GET /api/favourites/ — the current user's saved cars (card shape).
    POST /api/favourites/ — save a car, idempotent."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        car_ids = Favourite.objects.filter(user=request.user).values_list("car_id", flat=True)
        cars = Car.objects.filter(pk__in=car_ids)
        serializer = CarListSerializer(cars, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request):
        car = get_object_or_404(Car, pk=request.data.get("car"))
        Favourite.objects.get_or_create(user=request.user, car=car)
        return Response({"success": True, "car": car.id}, status=status.HTTP_201_CREATED)


class FavouriteDeleteView(APIView):
    """DELETE /api/favourites/:car_id/ — unsave a car, idempotent."""

    permission_classes = [IsAuthenticated]

    def delete(self, request, car_id):
        Favourite.objects.filter(user=request.user, car_id=car_id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
