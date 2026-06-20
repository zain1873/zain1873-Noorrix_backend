from django.core.management.base import BaseCommand

from apps.cars.models import Car, CarImage
from apps.cars.utils import HEIC_EXTENSIONS, to_browser_safe_image


def convert_field_file(field_file):
    """Re-save a model's image FileField as JPEG if it's currently HEIC/HEIF."""
    if not field_file or not field_file.name.lower().endswith(HEIC_EXTENSIONS):
        return False

    field_file.open("rb")
    converted = to_browser_safe_image(field_file)
    field_file.close()

    old_name = field_file.name
    field_file.delete(save=False)
    field_file.save(converted.name, converted, save=True)
    return old_name


class Command(BaseCommand):
    help = "Convert any already-uploaded HEIC/HEIF car images on disk to JPEG."

    def handle(self, *args, **options):
        converted = 0

        for car in Car.objects.all():
            old_name = convert_field_file(car.image)
            if old_name:
                self.stdout.write(f"Car #{car.pk}: {old_name} -> {car.image.name}")
                converted += 1

        for img in CarImage.objects.all():
            old_name = convert_field_file(img.image)
            if old_name:
                self.stdout.write(f"CarImage #{img.pk} (car #{img.car_id}): {old_name} -> {img.image.name}")
                converted += 1

        self.stdout.write(self.style.SUCCESS(f"Converted {converted} HEIC image(s)."))
