from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import User


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_roles = []

    def test_func(self):
        return self.request.user.role in self.allowed_roles


class SuperAdminMixin(RoleRequiredMixin):
    allowed_roles = [User.Role.SUPERADMIN]


class AdminMixin(RoleRequiredMixin):
    allowed_roles = [User.Role.SUPERADMIN, User.Role.ADMIN]


class ManagerMixin(RoleRequiredMixin):
    allowed_roles = [User.Role.MANAGER]


class DriverMixin(RoleRequiredMixin):
    allowed_roles = [User.Role.DRIVER]


class ClientMixin(RoleRequiredMixin):
    allowed_roles = [User.Role.CLIENT]
