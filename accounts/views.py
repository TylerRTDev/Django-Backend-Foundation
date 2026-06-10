from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from .forms import EmailLoginForm


def _safe_next_url(request: HttpRequest) -> str:
    """
    Validate ?next=... to prevent open redirects.
    Defaults to the account page.
    """
    next_url = request.GET.get("next") or request.POST.get("next") or ""
    if next_url and url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return reverse("accounts:account")


@never_cache
@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("accounts:account")

    form = EmailLoginForm(request.POST or None)
    next_url = _safe_next_url(request)

    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        password = form.cleaned_data["password"]

        # IMPORTANT: with USERNAME_FIELD="email", Django expects the identifier
        # in the `username` parameter (confusing name, correct behavior).
        user = authenticate(request, username=email, password=password)

        if user is not None:
            auth_login(request, user)
            return redirect(next_url)

        # Avoid leaking which part failed (email vs password)
        form.add_error(None, "Invalid email or password.")

    return render(
        request,
        "accounts/login.html",
        {"form": form, "next": next_url},
    )


@never_cache
def logout_view(request: HttpRequest) -> HttpResponse:
    auth_logout(request)
    return redirect("accounts:login")


@never_cache
@login_required(login_url="accounts:login")
def account_view(request: HttpRequest) -> HttpResponse:
    return render(request, "accounts/account.html")
