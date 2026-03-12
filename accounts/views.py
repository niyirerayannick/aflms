from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta

from .forms import LoginForm, UserCreationForm, UserProfileForm, UserUpdateForm, SystemSettingsForm
from .mixins import AdminMixin, ClientMixin, DriverMixin, ManagerMixin, SuperAdminMixin
from .models import User, ActivityLog, RolePermission, SystemSettings
from django.contrib.auth.decorators import login_required as login_required_fn


def role_dashboard_name(role):
    mapping = {
        User.Role.SUPERADMIN: "accounts:dashboard-superadmin",
        User.Role.ADMIN: "accounts:dashboard-admin",
        User.Role.MANAGER: "accounts:dashboard-manager",
        User.Role.DRIVER: "accounts:dashboard-driver",
        User.Role.CLIENT: "accounts:dashboard-client",
    }
    return mapping.get(role, "accounts:dashboard-client")


class LoginView(View):
    form_class = LoginForm
    template_name = "accounts/login.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("accounts:dashboard")
        return render(request, self.template_name, {"form": self.form_class()})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form}, status=400)

        email = form.cleaned_data["email"].lower()
        password = form.cleaned_data["password"]
        user = authenticate(request, email=email, password=password)

        if user is None:
            form.add_error(None, "Invalid email or password.")
            return render(request, self.template_name, {"form": form}, status=401)

        if not user.is_active:
            form.add_error(None, "Your account is inactive.")
            return render(request, self.template_name, {"form": form}, status=403)

        login(request, user)
        return redirect(role_dashboard_name(user.role))


class LogoutView(LoginRequiredMixin, View):
    template_name = "accounts/logout_confirm.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, "You have been logged out.")
        return redirect("accounts:login")


class DashboardView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # Route users to appropriate transport dashboards
        role = request.user.role
        if role in ['superadmin', 'admin', 'manager']:
            return redirect('/transport/analytics/dashboard/')
        elif role == 'driver':
            return redirect('/transport/driver/dashboard/')
        elif role == 'client':
            return redirect('/transport/analytics/client-dashboard/')
        else:
            return redirect(role_dashboard_name(request.user.role))


class SuperAdminDashboardView(SuperAdminMixin, View):
    def get(self, request, *args, **kwargs):
        return redirect('/transport/analytics/dashboard/')


class AdminDashboardView(AdminMixin, View):
    def get(self, request, *args, **kwargs):
        return redirect('/transport/analytics/dashboard/')


class ManagerDashboardView(ManagerMixin, View):
    def get(self, request, *args, **kwargs):
        return redirect('/transport/analytics/dashboard/')


class DriverDashboardView(DriverMixin, View):
    def get(self, request, *args, **kwargs):
        return redirect('/transport/driver/dashboard/')


class ClientDashboardView(ClientMixin, View):
    def get(self, request, *args, **kwargs):
        return redirect('/transport/analytics/client-dashboard/')


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_user"] = self.request.user
        context["profile_form"] = UserProfileForm(instance=getattr(self.request.user, "profile", None))
        context["user_form"] = UserUpdateForm(instance=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        profile = getattr(request.user, "profile", None)
        profile_form = UserProfileForm(request.POST, instance=profile)

        user = request.user
        user.full_name = request.POST.get("full_name", user.full_name)
        user.phone = request.POST.get("phone", user.phone)
        if "profile_photo" in request.FILES:
            user.profile_photo = request.FILES["profile_photo"]

        if profile_form.is_valid():
            user.save(update_fields=["full_name", "phone", "profile_photo"])
            profile_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("accounts:profile")

        messages.error(request, "Please correct the errors below.")
        return render(
            request,
            self.template_name,
            {
                "profile_user": request.user,
                "profile_form": profile_form,
                "user_form": UserUpdateForm(instance=request.user),
            },
            status=400,
        )

    from django.views.generic import TemplateView

    # Custom password reset confirmation view
    class CustomPasswordResetDoneView(TemplateView):
        template_name = "accounts/password_reset_done.html"



class UserListView(AdminMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 25

    def get_queryset(self):
        return User.objects.all().order_by("-created_at")


class UserCreateView(AdminMixin, CreateView):
    model = User
    form_class = UserCreationForm
    template_name = "accounts/user_create.html"
    success_url = reverse_lazy("accounts:user-list")


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "accounts/user_edit.html"
    success_url = reverse_lazy("accounts:user-list")

    def dispatch(self, request, *args, **kwargs):
        target_user = self.get_object()
        privileged = request.user.role in {User.Role.SUPERADMIN, User.Role.ADMIN}
        if not privileged and request.user != target_user:
            return HttpResponseRedirect(reverse("accounts:dashboard"))
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        if self.request.user.role in {User.Role.SUPERADMIN, User.Role.ADMIN}:
            return reverse("accounts:user-list")
        return reverse("accounts:profile")


class UserDeleteView(SuperAdminMixin, View):
    def post(self, request, *args, **kwargs):
        user = User.objects.filter(pk=kwargs["pk"]).first()
        if user is None:
            messages.error(request, "User not found.")
            return redirect("accounts:user-list")
        if user == request.user:
            messages.error(request, "You cannot delete your own account.")
            return redirect("accounts:user-list")
        
        # Log the deletion activity
        ActivityLog.objects.create(
            user=request.user,
            action=ActivityLog.ActionType.DELETE,
            description=f"Deleted user: {user.full_name} ({user.email})",
            ip_address=self.get_client_ip(request)
        )
        
        user.delete()
        messages.success(request, "User deleted successfully.")
        return redirect("accounts:user-list")
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RoleManagementView(SuperAdminMixin, TemplateView):
    """Role and permission management interface"""
    template_name = 'accounts/role_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # User role statistics
        role_stats = []
        for role_choice in User.Role.choices:
            role_code, role_name = role_choice
            count = User.objects.filter(role=role_code).count()
            role_stats.append({
                'code': role_code,
                'name': role_name,
                'count': count
            })
        
        context.update({
            'role_stats': role_stats,
            'total_users': User.objects.count(),
            'permissions': Permission.objects.all()[:20],  # Show first 20 permissions
            'recent_role_changes': self.get_recent_role_changes(),
        })
        
        return context
    
    def get_recent_role_changes(self):
        """Get recent role/permission changes"""
        return ActivityLog.objects.filter(
            action__in=['create', 'update'], 
            description__icontains='role'
        )[:10]


class UserRoleUpdateView(SuperAdminMixin, View):
    """Update user role"""
    
    def post(self, request, *args, **kwargs):
        user_id = kwargs.get('pk')
        new_role = request.POST.get('role')
        
        user = get_object_or_404(User, pk=user_id)
        old_role = user.role
        
        if new_role in dict(User.Role.choices):
            user.role = new_role
            user.save()
            
            # Log the role change
            ActivityLog.objects.create(
                user=request.user,
                action=ActivityLog.ActionType.UPDATE,
                description=f"Changed role of {user.full_name} from {old_role} to {new_role}",
                ip_address=self.get_client_ip(request)
            )
            
            messages.success(request, f"Successfully updated {user.full_name}'s role to {new_role}")
        else:
            messages.error(request, "Invalid role selected")
        
        return redirect('accounts:role-management')
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class ActivityLogView(AdminMixin, ListView):
    """Display user activity logs"""
    model = ActivityLog
    template_name = 'accounts/activity_logs.html'
    context_object_name = 'logs'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = ActivityLog.objects.select_related('user').all()
        
        # Filtering
        user_filter = self.request.GET.get('user')
        action_filter = self.request.GET.get('action')
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        search = self.request.GET.get('search')
        
        if user_filter:
            queryset = queryset.filter(user__id=user_filter)
        if action_filter:
            queryset = queryset.filter(action=action_filter)
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(user__full_name__icontains=search) |
                Q(user__email__icontains=search)
            )
            
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistics for the page
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        context.update({
            'users': User.objects.all(),
            'action_choices': ActivityLog.ActionType.choices,
            'total_activities': ActivityLog.objects.count(),
            'activities_today': ActivityLog.objects.filter(created_at__date=today).count(),
            'activities_this_week': ActivityLog.objects.filter(created_at__date__gte=week_ago).count(),
            
            # Current filter values
            'current_user': self.request.GET.get('user'),
            'current_action': self.request.GET.get('action'),
            'current_date_from': self.request.GET.get('date_from'),
            'current_date_to': self.request.GET.get('date_to'),
            'current_search': self.request.GET.get('search'),
        })
        
        return context


class PermissionManagementView(SuperAdminMixin, TemplateView):
    """Manage permissions for different roles"""
    template_name = 'accounts/permission_management.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Group permissions by content type for better organization
        permissions_by_app = {}
        for permission in Permission.objects.select_related('content_type').all():
            app_label = permission.content_type.app_label
            if app_label not in permissions_by_app:
                permissions_by_app[app_label] = []
            permissions_by_app[app_label].append(permission)
        
        context.update({
            'permissions_by_app': permissions_by_app,
            'role_choices': User.Role.choices,
            'role_permissions': RolePermission.objects.select_related('permission', 'granted_by').all()
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle permission assignment"""
        role = request.POST.get('role')
        permission_id = request.POST.get('permission_id')
        action = request.POST.get('action')  # 'grant' or 'revoke'
        
        if not all([role, permission_id, action]):
            messages.error(request, "Missing required parameters")
            return self.get(request, *args, **kwargs)
        
        try:
            permission = Permission.objects.get(id=permission_id)
            
            if action == 'grant':
                role_perm, created = RolePermission.objects.get_or_create(
                    role=role,
                    permission=permission,
                    defaults={'granted_by': request.user}
                )
                if created:
                    ActivityLog.objects.create(
                        user=request.user,
                        action=ActivityLog.ActionType.CREATE,
                        description=f"Granted permission '{permission.name}' to role '{role}'",
                        ip_address=self.get_client_ip(request)
                    )
                    messages.success(request, f"Permission granted successfully")
                else:
                    messages.info(request, f"Permission already granted to this role")
                    
            elif action == 'revoke':
                deleted_count = RolePermission.objects.filter(
                    role=role, 
                    permission=permission
                ).delete()[0]
                
                if deleted_count > 0:
                    ActivityLog.objects.create(
                        user=request.user,
                        action=ActivityLog.ActionType.DELETE,
                        description=f"Revoked permission '{permission.name}' from role '{role}'",
                        ip_address=self.get_client_ip(request)
                    )
                    messages.success(request, f"Permission revoked successfully")
                else:
                    messages.warning(request, f"Permission was not assigned to this role")
                    
        except Permission.DoesNotExist:
            messages.error(request, "Permission not found")
        
        return self.get(request, *args, **kwargs)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SystemSettingsView(AdminMixin, View):
    """Manage system settings like colors, currency, etc."""
    template_name = 'accounts/system_settings.html'
    
    def get(self, request):
        """Display settings form"""
        settings = SystemSettings.get_settings()
        form = SystemSettingsForm(instance=settings)
        
        context = {
            'form': form,
            'settings': settings,
            'page_title': 'System Settings'
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Handle settings update"""
        settings = SystemSettings.get_settings()
        form = SystemSettingsForm(request.POST, request.FILES, instance=settings)
        
        if form.is_valid():
            updated_settings = form.save(commit=False)
            updated_settings.updated_by = request.user
            updated_settings.save()
            
            # Log the activity
            ActivityLog.objects.create(
                user=request.user,
                action=ActivityLog.ActionType.UPDATE,
                description=f"Updated system settings",
                ip_address=self.get_client_ip(request)
            )
            
            messages.success(request, "System settings updated successfully!")
            return redirect('accounts:system-settings')
        
        context = {
            'form': form,
            'settings': settings,
            'page_title': 'System Settings'
        }
        return render(request, self.template_name, context)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


# ── Currency exchange-rate API ──────────────────────────────────
@login_required_fn
def exchange_rates_api(request):
    """
    AJAX endpoint returning live exchange rates.
    GET /accounts/exchange-rates/
    GET /accounts/exchange-rates/?base=RWF
    """
    from .currency import get_exchange_rates, CURRENCY_SYMBOLS, CURRENCY_DECIMALS

    base = request.GET.get('base', '').upper()
    if not base:
        settings_obj = SystemSettings.get_settings()
        base = settings_obj.currency if settings_obj else 'USD'

    rates = get_exchange_rates(base)

    supported = ['USD', 'RWF', 'EUR', 'GBP', 'KES', 'UGX', 'TZS']
    result = {}
    for code in supported:
        if code in rates:
            result[code] = {
                'rate': rates[code],
                'symbol': CURRENCY_SYMBOLS.get(code, code),
                'decimals': CURRENCY_DECIMALS.get(code, 2),
            }

    return JsonResponse({
        'success': True,
        'base': base,
        'rates': result,
    })
