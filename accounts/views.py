from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView

from .forms import LoginForm, UserCreationForm, UserProfileForm, UserUpdateForm
from .mixins import AdminMixin, SuperAdminMixin
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
        from django.shortcuts import render

        if request.user.is_authenticated:
            return redirect("accounts:dashboard")
        return render(request, self.template_name, {"form": self.form_class()})

    def post(self, request, *args, **kwargs):
        from django.shortcuts import render

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
    def post(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, "You have been logged out.")
        return redirect("accounts:login")

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class DashboardView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return redirect(role_dashboard_name(request.user.role))


class SuperAdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/dashboards/superadmin.html"


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/dashboards/admin.html"


class ManagerDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/dashboards/manager.html"


class DriverDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/dashboards/driver.html"


class ClientDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/dashboards/client.html"


class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "accounts/profile.html"
    context_object_name = "profile_user"

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_form"] = UserProfileForm(instance=getattr(self.request.user, "profile", None))
        return context


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
    template_name = "accounts/user_form.html"
    success_url = reverse_lazy("accounts:user-list")


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "accounts/user_form.html"
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

