import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserRole(models.TextChoices):
    CITIZEN = "CITIZEN", "Citizen"
    LAWYER = "LAWYER", "Lawyer"
    LEGAL_AID_USER = "LEGAL_AID_USER", "Legal Aid User"
    ADMIN = "ADMIN", "Admin"


class LanguageChoice(models.TextChoices):
    HINDI = "hi", "Hindi"
    ENGLISH = "en", "English"


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        extra_fields.setdefault("role", UserRole.CITIZEN)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields["is_staff"] = True
        extra_fields["is_superuser"] = True
        extra_fields["role"] = UserRole.ADMIN
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    name = models.CharField(max_length=255)
    preferred_language = models.CharField(max_length=5, choices=LanguageChoice.choices, default=LanguageChoice.HINDI)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.CITIZEN)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]
    objects = UserManager()

    class Meta:
        db_table = "users"
        indexes = [models.Index(fields=["email"]), models.Index(fields=["role"])]

    def __str__(self):
        return f"{self.name} <{self.email}>"

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def is_citizen(self):
        return self.role == UserRole.CITIZEN
