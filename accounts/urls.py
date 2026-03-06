from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from .views import (
    AdminDashboardView,
    ClientDashboardView,
    DashboardView,
    DriverDashboardView,
    LoginView,
    LogoutView,
    ManagerDashboardView,
    ProfileView,
    SuperAdminDashboardView,
    UserCreateView,
    UserDeleteView,
    UserListView,
    UserUpdateView,
    RoleManagementView,
    UserRoleUpdateView,
    ActivityLogView,
    PermissionManagementView,
    SystemSettingsView,
    exchange_rates_api,
)

app_name = "accounts"

urlpatterns = [
    path("", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("dashboard/superadmin/", SuperAdminDashboardView.as_view(), name="dashboard-superadmin"),
    path("dashboard/admin/", AdminDashboardView.as_view(), name="dashboard-admin"),
    path("dashboard/manager/", ManagerDashboardView.as_view(), name="dashboard-manager"),
    path("dashboard/driver/", DriverDashboardView.as_view(), name="dashboard-driver"),
    path("dashboard/client/", ClientDashboardView.as_view(), name="dashboard-client"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/create/", UserCreateView.as_view(), name="user-create"),
    path("users/<uuid:pk>/edit/", UserUpdateView.as_view(), name="user-update"),
    path("users/<uuid:pk>/delete/", UserDeleteView.as_view(), name="user-delete"),
    
    # Role and Permission Management
    path("roles/", RoleManagementView.as_view(), name="role-management"),
    path("users/<uuid:pk>/role/", UserRoleUpdateView.as_view(), name="user-role-update"),
    path("permissions/", PermissionManagementView.as_view(), name="permission-management"),
    
    # Activity Logs
    path("activity-logs/", ActivityLogView.as_view(), name="activity-logs"),
    
    # System Settings
    path("settings/", SystemSettingsView.as_view(), name="system-settings"),
    
    # API
    path("exchange-rates/", exchange_rates_api, name="exchange-rates"),
    
    path('password/reset/',
    auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        success_url=reverse_lazy('accounts:password_reset_done'),
        html_email_template_name='registration/password_reset_email_html.html'
    ),
    name='password_reset'),
    path('password/reset/done/',
    auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ),
    name='password_reset_done'),
    
    path('password/reset/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password/reset/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), name='password_reset_complete'),
]
