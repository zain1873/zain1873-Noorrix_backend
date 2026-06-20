from django.contrib import admin, messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path

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
    change_form_template = "admin/cars/car/change_form.html"

    def response_add(self, request, obj, post_url_continue=None):
        # After creating a new car, land on its edit page (not the changelist)
        # so the "Bulk upload images" button is right there — no second open.
        if "_addanother" not in request.POST and "_continue" not in request.POST:
            request.POST = request.POST.copy()
            request.POST["_continue"] = "1"
        return super().response_add(request, obj, post_url_continue)

    def get_urls(self):
        return [
            path(
                "<int:car_id>/bulk-upload-images/",
                self.admin_site.admin_view(self.bulk_upload_images_view),
                name="cars_car_bulk_upload_images",
            ),
        ] + super().get_urls()

    def bulk_upload_images_view(self, request, car_id):
        car = get_object_or_404(Car, pk=car_id)

        if request.method == "POST":
            files = request.FILES.getlist("images")
            if not files:
                messages.error(request, "No files were selected.")
            else:
                next_order = (
                    car.gallery.order_by("-sort_order").values_list("sort_order", flat=True).first() or 0
                ) + 1
                created = 0
                skipped = 0
                for offset, f in enumerate(files):
                    if not f.content_type or not f.content_type.startswith("image/"):
                        skipped += 1
                        continue
                    CarImage.objects.create(car=car, image=f, sort_order=next_order + offset)
                    created += 1
                if created:
                    messages.success(request, f"Uploaded {created} image(s) to {car.title}.")
                if skipped:
                    messages.warning(request, f"Skipped {skipped} non-image file(s).")
            return redirect("admin:cars_car_change", car_id)

        return render(request, "admin/cars/car/bulk_upload_images.html", {
            "car": car,
            "opts": self.model._meta,
            "title": f"Bulk upload images — {car.title}",
        })

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
