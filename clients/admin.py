from django.contrib import admin

from .models import ClientProfile


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "contact_person", "email", "phone_number", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "contact_person", "email", "phone_number")
