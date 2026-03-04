from django.db.models import Sum

from .models import Expense, Payment


def outstanding_balance_for_trip(trip):
    paid = trip.payments.aggregate(total=Sum("amount")).get("total") or 0
    return (trip.revenue or 0) - paid


def monthly_revenue(month_start, month_end):
    from transport.trips.models import Trip

    return (
        Trip.objects.filter(created_at__date__gte=month_start, created_at__date__lte=month_end)
        .aggregate(total=Sum("revenue"))
        .get("total")
        or 0
    )


def monthly_expenses(month_start, month_end):
    trip_costs = (
        Payment.objects.none()  # placeholder to keep service composable
    )
    _ = trip_costs
    direct_expenses = (
        Expense.objects.filter(expense_date__gte=month_start, expense_date__lte=month_end)
        .aggregate(total=Sum("amount"))
        .get("total")
        or 0
    )

    from transport.trips.models import Trip

    trip_cost_total = (
        Trip.objects.filter(created_at__date__gte=month_start, created_at__date__lte=month_end)
        .aggregate(total=Sum("total_cost"))
        .get("total")
        or 0
    )
    return direct_expenses + trip_cost_total
