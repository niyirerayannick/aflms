from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, TemplateView

from accounts.decorators import driver_required

from .forms import FuelDocumentForm, FuelRequestForm
from .models import FuelRequest


def _sync_trip_fuel_cost_from_requests(trip):
    approved_total = (
        FuelRequest.objects.filter(trip=trip, is_approved=True)
        .aggregate(total=Sum("amount"))
        .get("total")
        or 0
    )
    trip.fuel_cost = approved_total
    # Use full save so Trip model recalculates dependent financial fields.
    trip.save()


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role in {"superadmin", "admin", "manager"}


class FuelRequestListView(StaffRequiredMixin, ListView):
    model = FuelRequest
    template_name = "transport/fuel/staff_list.html"
    context_object_name = "fuel_requests"
    paginate_by = 20

    def get_queryset(self):
        qs = FuelRequest.objects.select_related("trip", "station", "driver").order_by("-created_at")
        status = self.request.GET.get("status", "").lower()
        search = self.request.GET.get("search", "").strip()

        if status == "approved":
            qs = qs.filter(is_approved=True)
        elif status == "pending":
            qs = qs.filter(is_approved=False)

        if search:
            qs = qs.filter(trip__order_number__icontains=search)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        all_requests = FuelRequest.objects.all()
        ctx["total_requests"] = all_requests.count()
        ctx["approved_requests"] = all_requests.filter(is_approved=True).count()
        ctx["pending_requests"] = all_requests.filter(is_approved=False).count()
        ctx["total_amount"] = all_requests.aggregate(total=Sum("amount"))["total"] or 0
        ctx["selected_status"] = self.request.GET.get("status", "")
        ctx["search_query"] = self.request.GET.get("search", "")
        return ctx


class FuelRequestDetailView(StaffRequiredMixin, DetailView):
    model = FuelRequest
    template_name = "transport/fuel/staff_detail.html"
    context_object_name = "fuel_request"

    def get_queryset(self):
        return FuelRequest.objects.select_related("trip", "station", "driver").prefetch_related("documents")


class FuelRequestAnalyticsView(StaffRequiredMixin, TemplateView):
    template_name = "transport/fuel/staff_analytics.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        requests = FuelRequest.objects.select_related("station", "trip")

        ctx["total_requests"] = requests.count()
        ctx["approved_requests"] = requests.filter(is_approved=True).count()
        ctx["pending_requests"] = requests.filter(is_approved=False).count()
        ctx["total_amount"] = requests.aggregate(total=Sum("amount"))["total"] or 0

        ctx["top_stations"] = (
            requests.values("station__name")
            .annotate(total_amount=Sum("amount"), req_count=Count("id"))
            .order_by("-total_amount")[:5]
        )

        ctx["monthly_requests"] = (
            requests.annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(req_count=Count("id"), total_amount=Sum("amount"))
            .order_by("month")
        )
        return ctx


@login_required
@require_POST
def approve_fuel_request(request, pk):
    if request.user.role not in {"superadmin", "admin", "manager"}:
        messages.error(request, "You do not have permission to approve fuel requests.")
        return redirect("transport:fuel:detail", pk=pk)

    fuel_request = get_object_or_404(FuelRequest, pk=pk)
    if fuel_request.is_approved:
        messages.info(request, "Fuel request is already approved.")
    else:
        fuel_request.is_approved = True
        fuel_request.approved_by = request.user
        fuel_request.approved_at = timezone.now()
        _sync_trip_fuel_cost_from_requests(fuel_request.trip)
        fuel_request.posted_to_trip = True
        fuel_request.posted_at = timezone.now()
        fuel_request.save(
            update_fields=[
                "is_approved",
                "approved_by",
                "approved_at",
                "posted_to_trip",
                "posted_at",
                "updated_at",
            ]
        )
        messages.success(request, f"Fuel request #{fuel_request.pk} approved.")

    return redirect("transport:fuel:detail", pk=pk)


@driver_required
def request_fuel(request):
    if request.method == "POST":
        form = FuelRequestForm(request.POST, driver_user=request.user)
        if form.is_valid():
            fuel_request = form.save(commit=False)
            fuel_request.driver = request.user
            fuel_request.save()
            messages.success(request, "Fuel request submitted successfully.")
            return redirect("transport:driver_fuel")
    else:
        form = FuelRequestForm(driver_user=request.user)

    return render(
        request,
        "transport/fuel/request.html",
        {
            "form": form,
            "initial_tab": "fuel",
            "driver_spa": False,
        },
    )


@driver_required
def upload_fuel_document(request, fuel_request_id):
    fuel_request = get_object_or_404(
        FuelRequest,
        pk=fuel_request_id,
        driver=request.user,
    )

    if request.method == "POST":
        form = FuelDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.fuel_request = fuel_request
            document.save()
            messages.success(request, "Fuel document uploaded successfully.")
            return redirect("transport:driver_fuel")
    else:
        form = FuelDocumentForm()

    return render(
        request,
        "transport/fuel/upload_document.html",
        {
            "form": form,
            "fuel_request": fuel_request,
            "initial_tab": "fuel",
            "driver_spa": False,
        },
    )
