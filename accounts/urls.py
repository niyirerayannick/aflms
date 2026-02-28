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
)

app_name = "accounts"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
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
]
