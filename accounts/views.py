from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, TemplateView, UpdateView

from .forms import LoginForm, UserCreationForm, UserProfileForm, UserUpdateForm
from .mixins import AdminMixin, ClientMixin, DriverMixin, ManagerMixin, SuperAdminMixin
from .models import User


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
            return redirect('/transport/analytics/driver-dashboard/')
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
        return redirect('/transport/analytics/driver-dashboard/')


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
        user.delete()
        messages.success(request, "User deleted successfully.")
        return redirect("accounts:user-list")

