from django.contrib import admin

from .models import ReportExport


@admin.register(ReportExport)
class ReportExportAdmin(admin.ModelAdmin):
    list_display = ("name", "generated_by", "status", "created_at", "completed_at")
    list_filter = ("status",)
    search_fields = ("name", "generated_by__username")
