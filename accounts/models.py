import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

from .managers import CustomUserManager


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        SUPERADMIN = "superadmin", "SuperAdmin"
        ADMIN = "admin", "Admin"
        MANAGER = "manager", "Manager"
        DRIVER = "driver", "Driver"
        CLIENT = "client", "Client"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(regex=r"^[0-9+()\-\s]{7,20}$")],
        blank=True,
    )
    full_name = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)
    profile_photo = models.ImageField(upload_to="profiles/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"


class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    address = models.TextField(blank=True)
    national_id = models.CharField(max_length=50, blank=True)
    emergency_contact = models.CharField(max_length=120, blank=True)
    license_number = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"Profile - {self.user.email}"


class ActivityLog(models.Model):
    """Track user activities for audit purposes"""
    class ActionType(models.TextChoices):
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout" 
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        VIEW = "view", "View"
        EXPORT = "export", "Export"
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs')
    action = models.CharField(max_length=20, choices=ActionType.choices)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.full_name} - {self.get_action_display()} - {self.created_at}"


class RolePermission(models.Model):
    """Custom role and permission management"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=[
        ('superadmin', 'SuperAdmin'),
        ('admin', 'Admin'), 
        ('manager', 'Manager'),
        ('driver', 'Driver'),
        ('client', 'Client'),
    ])
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    granted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='permissions_granted')
    granted_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['role', 'permission']
        
    def __str__(self):
        return f"{self.role} - {self.permission.name}"


class SystemSettings(models.Model):
    """System-wide settings for the application"""
    class ColorTheme(models.TextChoices):
        BLUE = "blue", "Blue Theme"
        GREEN = "green", "Green Theme"
        PURPLE = "purple", "Purple Theme"
        RED = "red", "Red Theme"
        ORANGE = "orange", "Orange Theme"
        
    class Currency(models.TextChoices):
        USD = "USD", "US Dollar ($)"
        EUR = "EUR", "Euro (€)"
        GBP = "GBP", "British Pound (£)"
        RWF = "RWF", "Rwandan Franc (Fr)"
        KES = "KES", "Kenyan Shilling (KSh)"
        UGX = "UGX", "Ugandan Shilling (USh)"
        TZS = "TZS", "Tanzanian Shilling (TSh)"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company_name = models.CharField(max_length=255, default="ATMS")
    company_logo = models.ImageField(upload_to="settings/", blank=True, null=True)
    primary_color = models.CharField(
        max_length=20, 
        choices=ColorTheme.choices, 
        default=ColorTheme.BLUE,
        help_text="Primary color theme for the application"
    )
    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.USD,
        help_text="Default currency for financial calculations"
    )
    currency_symbol = models.CharField(max_length=5, default="$")
    exchange_rate_cache = models.TextField(
        blank=True, default="",
        help_text="JSON cache for exchange rates — auto-managed",
    )
    timezone_setting = models.CharField(max_length=50, default="UTC")
    date_format = models.CharField(
        max_length=20,
        choices=[
            ('Y-m-d', 'YYYY-MM-DD'),
            ('d/m/Y', 'DD/MM/YYYY'),
            ('m/d/Y', 'MM/DD/YYYY'),
            ('d-m-Y', 'DD-MM-YYYY'),
        ],
        default='Y-m-d'
    )
    language = models.CharField(
        max_length=10,
        choices=[
            ('en', 'English'),
            ('fr', 'French'),
            ('sw', 'Swahili'),
            ('rw', 'Kinyarwanda'),
        ],
        default='en'
    )
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='settings_updated')
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"
        
    def __str__(self):
        return f"System Settings - {self.company_name}"
        
    @classmethod
    def get_settings(cls):
        """Get the current system settings, create if doesn't exist"""
        settings = cls.objects.first()
        if settings is None:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admin_user = User.objects.filter(
                role__in=['superadmin', 'admin']
            ).first()
            if admin_user is None:
                admin_user = User.objects.first()
            if admin_user:
                settings = cls.objects.create(
                    company_name='ATMS',
                    primary_color=cls.ColorTheme.BLUE,
                    currency=cls.Currency.USD,
                    currency_symbol='$',
                    updated_by=admin_user,
                )
        return settings
