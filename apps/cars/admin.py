from django.contrib import admin

from .models import Car, CarFeature, CarImage, Favourite


class CarImageInline(admin.TabularInline):
    model = CarImage
    extra = 3
    fields = ("image", "sort_order")


class CarFeatureInline(admin.TabularInline):
    model = CarFeature
    extra = 5
    fields = ("text",)


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display  = ("title", "subtitle", "make", "model", "year", "price", "mileage", "status")
    list_filter   = ("status", "make", "body_type", "fuel", "transmission", "colour")
    list_editable = ("status",)
    search_fields = ("title", "subtitle", "make", "model")
    readonly_fields = ("created_at", "updated_at")
    inlines = (CarImageInline, CarFeatureInline)

    fieldsets = (
        ("Identity", {
            "fields": ("title", "subtitle", "image", "status")
        }),
        ("Classification (filters)", {
            "fields": ("make", "model", "body_type", "fuel", "transmission", "colour")
        }),
        ("Specs", {
            "fields": (
                "year", "engine_cc", "engine", "doors", "seats",
                "mileage", "price", "monthly", "mot_date", "history_check",
                "deposit_amount",
            )
        }),
        ("Detail copy", {
            "fields": ("description", "summary", "performance", "interior", "safety", "video_url")
        }),
        ("Location (leave blank for site default)", {
            "fields": ("location_name", "location_address"),
            "classes": ("collapse",),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )


@admin.register(Favourite)
class FavouriteAdmin(admin.ModelAdmin):
    list_display   = ("user", "car", "created_at")
    list_filter    = ("created_at",)
    search_fields  = ("user__email", "car__title", "car__make", "car__model")
    list_select_related = ("user", "car")
