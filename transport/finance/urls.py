from django.urls import path
from . import views

app_name = 'finance'

# Finance management endpoints
urlpatterns = [
    # Overview
    path("", views.FinanceOverviewView.as_view(), name="overview"),
    
    # Payments
    path("payments/", views.PaymentListView.as_view(), name="payment-list"),
    path("payments/create/", views.PaymentCreateView.as_view(), name="payment-create"),
    path("payments/<int:pk>/", views.PaymentDetailView.as_view(), name="payment-detail"),
    path("payments/<int:pk>/edit/", views.PaymentUpdateView.as_view(), name="payment-edit"),
    
    # Expenses
    path("expenses/", views.ExpenseListView.as_view(), name="expense-list"),
    path("expenses/create/", views.ExpenseCreateView.as_view(), name="expense-create"),
    path("expenses/<int:pk>/", views.ExpenseDetailView.as_view(), name="expense-detail"),
    path("expenses/<int:pk>/edit/", views.ExpenseUpdateView.as_view(), name="expense-edit"),
]