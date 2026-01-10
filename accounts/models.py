from __future__ import annotations
from typing import Any
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
from config.storage_backends import MinioMediaStorageTesting, MinioMediaStoragePrivateTesting

media_storage = MinioMediaStorageTesting()
private_media_storage = MinioMediaStoragePrivateTesting()

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields: Any):
        if not email:
            raise ValueError("Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields: Any):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None, **extra_fields: Any):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    # Auth/identity fields
    email = models.EmailField(unique=True, db_index=True)
    username = models.CharField(max_length=150, unique=True, null=True, blank=True) # optional username
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    # Nice to have on the user itself
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    # Optional verification flag for email workflows
    is_verified = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []  # no username

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self) -> str:
        return self.email

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


def user_avatar_upload_to(instance: "Profile", filename: str) -> str:
    return f"avatars/user_{instance.user_id}/{filename}"

def user_file_upload_to(instance: "Profile", filename: str) -> str:
    return f"invoices/user_{instance.user_id}/{filename}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    timezone = models.CharField(max_length=64, default="Europe/London")
    language = models.CharField(max_length=32, null=True, blank=True, default="")

    avatar = models.ImageField(
        # storage=media_storage - Not needed as default storage is set in storage backend
        upload_to=user_avatar_upload_to,
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "webp"])],
    )
    
    file = models.FileField(
        storage=private_media_storage,
        upload_to=user_file_upload_to,
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "docx", "txt"])],
    )

    website = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    instagram = models.URLField(blank=True)

    # PostgreSQL-friendly flexible preferences
    preferences = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    def __str__(self) -> str:
        return self.display_name or self.user.full_name or self.user.email
