from django.core.management.base import BaseCommand

from apps.cars.models import CarFeature, FeatureCategory

# Best-effort keyword guess for existing free-text features, same idea as the
# front-end's old heuristic. Checked in order — first match wins. Anything
# unmatched falls back to Interior; dealers correct it in the admin afterwards.
KEYWORD_CATEGORIES = [
    (FeatureCategory.AUDIO_AND_COMMUNICATIONS, (
        "bluetooth", "speaker", "radio", "usb", "aux", "navigation", "sat nav",
        "satnav", "hands-free", "hands free", "voice control", "audio",
        "carplay", "android auto", "infotainment", "dab", "stereo",
    )),
    (FeatureCategory.PERFORMANCE, (
        "engine", "traction", "abs", "suspension", "turbo", "horsepower",
        "torque", "drive mode", "cruise control", "brake", "4wd", "awd",
        "eco mode", "gearbox", "transmission", "stability control",
    )),
    (FeatureCategory.EXTERIOR, (
        "alloy", "wheel", "paint", "roof", "window", "mirror", "headlight",
        "taillight", "bumper", "spoiler", "tint", "sunroof", "bodywork",
        "wiper", "grille", "parking sensor", "tow bar", "roof rail", "led",
    )),
    (FeatureCategory.INTERIOR, (
        "seat", "leather", "cabin", "dashboard", "steering wheel", "climate",
        "air conditioning", "legroom", "storage", "cup holder", "boot space",
        "trim", "upholstery", "interior",
    )),
]


def guess_category(text):
    lowered = text.lower()
    for category, keywords in KEYWORD_CATEGORIES:
        if any(kw in lowered for kw in keywords):
            return category
    return FeatureCategory.INTERIOR


class Command(BaseCommand):
    help = (
        "Best-effort categorize existing free-text CarFeature rows by keyword. "
        "Run once after the category field is added — dealers should review/"
        "correct the results in the admin afterwards."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Show what would change without saving.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        updated = 0

        for feature in CarFeature.objects.all():
            guessed = guess_category(feature.text)
            if guessed != feature.category:
                self.stdout.write(f"#{feature.pk} '{feature.text}': {feature.category} -> {guessed}")
                if not dry_run:
                    feature.category = guessed
                    feature.save(update_fields=["category"])
                updated += 1

        verb = "Would update" if dry_run else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{verb} {updated} feature(s)."))
