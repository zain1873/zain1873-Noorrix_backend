from django import forms
from django.contrib import admin, messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path

from .models import Car, CarFeature, CarImage, Favourite


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """A FileField that accepts and validates a list of uploaded files."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if isinstance(data, (list, tuple)):
            return [super(MultipleFileField, self).clean(d, initial) for d in data]
        return super().clean(data, initial)


class CarAdminForm(forms.ModelForm):
    gallery_images = MultipleFileField(
        required=False,
        help_text="Select all gallery images at once (e.g. 50-100 files) — added after Save.",
    )

    class Meta:
        model = Car
        fields = "__all__"


class CarImageInline(admin.TabularInline):
    """Shows already-added gallery images for reorder/delete.
    New images are added via the "Gallery (bulk upload)" field above instead,
    so adding through this inline is disabled."""

    model = CarImage
    extra = 0
    fields = ("image", "sort_order")

    def has_add_permission(self, request, obj=None):
        return False


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
    form = CarAdminForm

    def get_inline_instances(self, request, obj=None):
        instances = super().get_inline_instances(request, obj)
        if obj is None:
            # Nothing to manage yet on the Add Car page — images come via gallery_images.
            instances = [i for i in instances if not isinstance(i, CarImageInline)]
        return instances

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        files = form.cleaned_data.get("gallery_images") or []
        if files:
            next_order = (
                obj.gallery.order_by("-sort_order").values_list("sort_order", flat=True).first() or 0
            ) + 1
            for offset, f in enumerate(files):
                CarImage.objects.create(car=obj, image=f, sort_order=next_order + offset)
            messages.success(request, f"Uploaded {len(files)} gallery image(s).")

    def response_add(self, request, obj, post_url_continue=None):
        # After creating a new car, land on its edit page (not the changelist)
        # so the gallery (and "Bulk upload images" button) are right there.
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
        ("Gallery (bulk upload)", {
            "fields": ("gallery_images",),
            "description": "Select 20, 50, 100+ images here — they're added as gallery images on Save.",
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
