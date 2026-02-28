from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import User


def role_required(roles_list):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if request.user.role not in roles_list:
                raise PermissionDenied("You do not have permission to access this resource.")
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    return decorator


def superadmin_required(view_func):
    return role_required([User.Role.SUPERADMIN])(view_func)


def admin_required(view_func):
    return role_required([User.Role.SUPERADMIN, User.Role.ADMIN])(view_func)


def manager_required(view_func):
    return role_required([User.Role.MANAGER])(view_func)


def driver_required(view_func):
    return role_required([User.Role.DRIVER])(view_func)


def client_required(view_func):
    return role_required([User.Role.CLIENT])(view_func)


def staff_required(view_func):
    return role_required([User.Role.SUPERADMIN, User.Role.ADMIN, User.Role.MANAGER])(view_func)
