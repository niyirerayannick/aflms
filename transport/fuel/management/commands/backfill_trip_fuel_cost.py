from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db.models import Sum

from transport.fuel.models import FuelRequest
from transport.trips.models import Trip


class Command(BaseCommand):
    help = "Backfill Trip.fuel_cost from approved FuelRequest.amount totals."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without saving.",
        )
        parser.add_argument(
            "--trip-id",
            type=int,
            nargs="+",
            help="Optional list of Trip IDs to backfill.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        trip_ids = options.get("trip_id")

        trips = Trip.objects.all().only("id", "order_number", "fuel_cost")
        if trip_ids:
            trips = trips.filter(id__in=trip_ids)

        approved_totals = {
            row["trip"]: (row["total"] or Decimal("0"))
            for row in FuelRequest.objects.filter(is_approved=True)
            .values("trip")
            .annotate(total=Sum("amount"))
        }

        scanned = 0
        changed = 0

        for trip in trips.iterator():
            scanned += 1
            target_fuel_cost = approved_totals.get(trip.id, Decimal("0"))
            current_fuel_cost = trip.fuel_cost or Decimal("0")

            if current_fuel_cost == target_fuel_cost:
                continue

            changed += 1
            self.stdout.write(
                f"Trip #{trip.id} ({trip.order_number}): "
                f"{current_fuel_cost} -> {target_fuel_cost}"
            )

            if dry_run:
                continue

            # Use model save so derived totals/profit/cost_per_km are recalculated.
            trip.fuel_cost = target_fuel_cost
            trip.save()

        mode = "DRY-RUN" if dry_run else "APPLIED"
        self.stdout.write(
            self.style.SUCCESS(
                f"[{mode}] Scanned: {scanned}, Updated: {changed}"
            )
        )

