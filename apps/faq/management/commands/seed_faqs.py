from django.core.management.base import BaseCommand
from django.core.management import call_command
from apps.faq.models import FAQ


class Command(BaseCommand):
    help = "Load FAQ fixtures only if the table is empty"

    def handle(self, *args, **kwargs):
        if FAQ.objects.exists():
            self.stdout.write("FAQs already exist — skipping seed.")
            return
        call_command("loaddata", "apps/faq/fixtures/faqs.json")
        self.stdout.write(self.style.SUCCESS("FAQs seeded successfully."))
