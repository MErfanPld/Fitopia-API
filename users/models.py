from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):

    def create_user(self, phone_number=None, username=None, password=None, **extra_fields):
        if not phone_number and not username:
            raise ValueError("Phone or username required")

        user = self.model(
            phone_number=phone_number,
            username=username,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number=None, username=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(
            phone_number=phone_number,
            username=username,
            password=password,
            **extra_fields
        )


class User(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        verbose_name="شماره موبایل"
    )

    username = models.CharField(
        max_length=150,
        unique=True,
        null=True,
        blank=True,
        verbose_name="نام کاربری"
    )

    full_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="نام کامل"
    )

    is_active = models.BooleanField(default=True, verbose_name="فعال")
    is_staff = models.BooleanField(default=False, verbose_name="کارمند")

    is_staff_user = models.BooleanField(default=False, verbose_name="باشگاه‌دار")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    objects = UserManager()

    USERNAME_FIELD = "phone_number"

    def __str__(self):
        if self.full_name:
            return self.full_name
        return self.phone_number or self.username or f"User-{self.id}"

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"