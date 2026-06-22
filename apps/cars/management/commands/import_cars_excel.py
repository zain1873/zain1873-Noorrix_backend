from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import openpyxl
from django.core.management.base import BaseCommand, CommandError

from apps.cars.models import BodyType, Car, CarStatus, Colour, FuelType, Transmission

REQUIRED_COLUMNS = (
    "title", "subtitle", "make", "model", "body_type", "fuel",
    "transmission", "colour", "year", "engine_cc", "mileage", "price",
)

CHOICE_FIELDS = {
    "body_type": BodyType,
    "fuel": FuelType,
    "transmission": Transmission,
    "colour": Colour,
    "status": CarStatus,
}


def match_choice(value, choices_enum):
    """Case/whitespace-insensitive match against a TextChoices' values."""
    if value is None:
        return None
    needle = str(value).strip().casefold()
    for choice_value, _label in choices_enum.choices:
        if choice_value.casefold() == needle:
            return choice_value
    return None


def parse_date(value):
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def parse_decimal(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value).strip())
    except InvalidOperation:
        return None


def parse_int(value):
    if value in (None, ""):
        return None
    try:
        return int(float(str(value).strip()))
    except ValueError:
        return None


class Command(BaseCommand):
    help = "Bulk-create cars from an Excel sheet (.xlsx). Images are added afterwards via the admin."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to the .xlsx file")
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Validate and report without saving anything to the database.",
        )

    def handle(self, *args, **options):
        path = options["path"]
        dry_run = options["dry_run"]

        try:
            wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        except FileNotFoundError:
            raise CommandError(f"File not found: {path}")
        ws = wb.active

        rows = ws.iter_rows(values_only=True)
        header = [str(h).strip().lower() if h else "" for h in next(rows)]
        missing = [c for c in REQUIRED_COLUMNS if c not in header]
        if missing:
            raise CommandError(f"Missing required column(s): {', '.join(missing)}")

        created, errors = 0, []
        for row_num, raw_row in enumerate(rows, start=2):
            if raw_row is None or all(v is None for v in raw_row):
                continue
            row = dict(zip(header, raw_row))
            error = self._import_row(row, dry_run)
            if error:
                errors.append(f"Row {row_num}: {error}")
            else:
                created += 1

        wb.close()

        self.stdout.write(self.style.SUCCESS(
            f"{'Would create' if dry_run else 'Created'} {created} car(s)."
        ))
        if errors:
            self.stdout.write(self.style.WARNING(f"Skipped {len(errors)} row(s):"))
            for e in errors:
                self.stdout.write(f"  - {e}")

    def _import_row(self, row, dry_run):
        for field in REQUIRED_COLUMNS:
            if row.get(field) in (None, ""):
                return f"missing required field '{field}'"

        data = {
            "title": str(row["title"]).strip(),
            "subtitle": str(row["subtitle"]).strip(),
            "make": str(row["make"]).strip(),
            "model": str(row["model"]).strip(),
            "engine": str(row.get("engine") or "").strip(),
            "doors": parse_int(row.get("doors")) or 5,
            "seats": parse_int(row.get("seats")) or 5,
            "monthly": parse_decimal(row.get("monthly")),
            "mot_date": parse_date(row.get("mot_date")),
            "history_check": str(row.get("history_check") or "All passed").strip(),
            "deposit_amount": parse_decimal(row.get("deposit_amount")) or Decimal("200.00"),
            "description": str(row.get("description") or "").strip(),
            "video_url": str(row.get("video_url") or "").strip(),
            "location_name": str(row.get("location_name") or "").strip(),
            "location_address": str(row.get("location_address") or "").strip(),
        }

        for field, enum in CHOICE_FIELDS.items():
            raw_value = row.get(field) or (CarStatus.AVAILABLE if field == "status" else None)
            matched = match_choice(raw_value, enum)
            if matched is None:
                valid = ", ".join(v for v, _ in enum.choices)
                return f"invalid {field} '{raw_value}' — must be one of: {valid}"
            data[field] = matched

        for field in ("year", "engine_cc", "mileage", "price"):
            value = parse_int(row.get(field))
            if value is None:
                return f"'{field}' must be a number"
            data[field] = value

        if not dry_run:
            Car.objects.create(**data)
        return None
