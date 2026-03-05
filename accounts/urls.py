from django.urls import path

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
]
