from collections import defaultdict

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Car, CarStatus, Favourite
from .pagination import OptionalPagePagination
from .serializers import CarDetailSerializer, CarListSerializer

# Static range options (kept server-side so the front-end and /filters agree).
PRICE_RANGES = [
    {"label": "Under £1,500",       "min": 0,     "max": 1500},
    {"label": "£1,500 – £3,000",    "min": 1500,  "max": 3000},
    {"label": "£3,000 – £5,000",    "min": 3000,  "max": 5000},
    {"label": "£5,000 – £10,000",   "min": 5000,  "max": 10000},
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

# Statuses the shopper can filter by. "reserved" is deliberately absent: those
# cars stay visible in the unfiltered list but aren't a browsing category.
FILTERABLE_STATUSES = [CarStatus.AVAILABLE, CarStatus.SOLD]


EXACT_FILTERS = ("model", "body_type", "fuel", "transmission", "colour")
RANGE_FILTERS = ("price", "mileage")
ORDERINGS     = ("price", "-price", "mileage", "-mileage", "year", "-year", "-created_at")
DEFAULT_ORDERING = "-created_at"


def _makes_for_brand(brand_slug):
    """Stored make names whose slug starts with the brand slug at a word
    boundary: 'mini' → 'MINI' and 'MINI Hatch', but not 'Minix'."""
    brand_slug = slugify(brand_slug)
    makes = Car.objects.order_by().values_list("make", flat=True).distinct()
    return [
        make for make in makes
        if slugify(make) == brand_slug or slugify(make).startswith(brand_slug + "-")
    ]


class CarListView(generics.ListAPIView):
    """GET /api/cars/ — all stock (available, reserved, sold).

    Reserved/sold cars are included so their detail/checkout links keep working
    and the front-end shows a "Reserved"/"Sold" badge instead of hiding them.

    Without ``?page=`` the response is the plain array it has always been; with
    it, see ``OptionalPagePagination``. Filters (all optional, combinable, and
    applied before paginating):

    - ``make`` (case-insensitive exact), ``model``, ``body_type``, ``fuel``,
      ``transmission``, ``colour`` (exact)
    - ``status=available`` / ``status=sold`` (reserved cars fall into neither)
    - ``price_min``/``price_max``, ``mileage_min``/``mileage_max`` (inclusive;
      non-numeric values are ignored)
    - ``brand`` (slug prefix on make, for the brand page)

    ``?ordering=`` is one of ``ORDERINGS`` (default newest first); ``id`` is
    always the final tiebreaker so a car can't land on two pages.
    """

    serializer_class   = CarListSerializer
    permission_classes = [AllowAny]
    pagination_class   = OptionalPagePagination

    def get_queryset(self):
        params = self.request.query_params
        qs = Car.objects.all()

        make = params.get("make")
        if make:
            qs = qs.filter(make__iexact=make)

        for field in EXACT_FILTERS:
            value = params.get(field)
            if value:
                qs = qs.filter(**{field: value})

        for field in RANGE_FILTERS:
            for suffix, lookup in (("min", "gte"), ("max", "lte")):
                try:
                    bound = int(params.get(f"{field}_{suffix}", ""))
                except ValueError:
                    continue
                qs = qs.filter(**{f"{field}__{lookup}": bound})

        brand = params.get("brand")
        if brand:
            qs = qs.filter(make__in=_makes_for_brand(brand))

        car_status = params.get("status")
        if car_status:
            wanted = car_status.strip().lower()
            qs = qs.filter(status=wanted) if wanted in FILTERABLE_STATUSES else qs.none()

        ordering = params.get("ordering")
        if ordering not in ORDERINGS:
            ordering = DEFAULT_ORDERING
        return qs.order_by(ordering, "id")


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
    as why CarListView no longer filters by status. "statuses" lists only the
    filterable statuses actually present in stock. Price/mileage ranges
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

        present = set(cars.order_by().values_list("status", flat=True).distinct())

        return Response({
            "makes":         sorted(make_models.keys()),
            "makeModels":    {m: sorted(models) for m, models in sorted(make_models.items())},
            "bodyTypes":     distinct("body_type"),
            "fuelTypes":     distinct("fuel"),
            "transmissions": distinct("transmission"),
            "colours":       distinct("colour"),
            "statuses":      [s.value for s in FILTERABLE_STATUSES if s in present],
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
