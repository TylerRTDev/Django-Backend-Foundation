from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    fk_name = "user"
    verbose_name_plural = "Profile"

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    # Add username to the admin display and search fields (Optional)
    list_display = ("email", "first_name", "last_name", "is_staff", "is_superuser", "is_verified")
    list_filter = ("is_staff", "is_superuser", "is_verified", "is_active")
    ordering = ("email",)
    search_fields = ("email", "first_name", "last_name")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        # Add username fieldset if username is used (optional)
        (_("Personal info"), {"fields": ("first_name", "last_name", "is_verified")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            # Add username to the add user form fields (Optional)
            "fields": ("email", "password1", "password2", "is_staff", "is_superuser"),
        }),
    )

    inlines = [ProfileInline]

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "timezone", "language")
    search_fields = ("user__email", "display_name")
