from django.contrib import admin

from .models import Expense, Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("trip", "amount", "payment_date", "reference")
    list_filter = ("payment_date",)
    search_fields = ("trip__order_number", "reference")
    autocomplete_fields = ("trip",)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("category", "trip", "amount", "expense_date")
    list_filter = ("category", "expense_date")
    search_fields = ("category", "description", "trip__order_number")
    autocomplete_fields = ("trip",)
