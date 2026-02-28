from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UserCreationForm, UserUpdateForm
from .models import User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    form = UserUpdateForm
    model = User

    list_display = (
        "email",
        "full_name",
        "role",
        "phone",
        "is_active",
        "is_staff",
        "created_at",
    )
    list_filter = ("role", "is_active", "is_staff", "is_superuser", "created_at")
    search_fields = ("email", "full_name", "phone")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "last_login")

    fieldsets = (
        (
            "Authentication",
            {
                "fields": ("email", "password"),
            },
        ),
        (
            "Personal Info",
            {
                "fields": ("full_name", "phone", "role", "profile_photo"),
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Important Dates", {"fields": ("last_login", "created_at")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "full_name",
                    "phone",
                    "role",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "national_id", "license_number", "emergency_contact")
    search_fields = ("user__email", "user__full_name", "national_id", "license_number")
    list_select_related = ("user",)
