from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "recipient", "channel", "status", "created_at", "sent_at")
    list_filter = ("channel", "status")
    search_fields = ("title", "recipient__username", "recipient__email")
