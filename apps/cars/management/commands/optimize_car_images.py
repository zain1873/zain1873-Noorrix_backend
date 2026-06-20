from django.core.management.base import BaseCommand

from apps.cars.models import Car, CarImage
from apps.cars.utils import to_browser_safe_image


def convert_field_file(field_file):
    """Re-save a model's image FileField if to_browser_safe_image would change it
    (HEIC/HEIF -> JPEG, or downscaled if oversized)."""
    if not field_file or not field_file.name:
        return False

    field_file.open("rb")
    result = to_browser_safe_image(field_file)
    changed = result is not field_file
    field_file.close()
    if not changed:
        return False

    old_name = field_file.name
    field_file.delete(save=False)
    field_file.save(result.name, result, save=True)
    return old_name


class Command(BaseCommand):
    help = "Convert HEIC/HEIF and downscale oversized car images already on disk."

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

        self.stdout.write(self.style.SUCCESS(f"Optimized {converted} image(s)."))
