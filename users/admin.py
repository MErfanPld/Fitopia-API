from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "phone_number",
        "username",
        "full_name",
        "gender",
        "birth_date",
        "is_staff_user",
        "is_staff",
        "is_active",
        "created_at",
    )

    list_filter = (
        "gender",
        "is_staff_user",
        "is_staff",
        "is_active",
        "created_at",
    )

    search_fields = (
        "phone_number",
        "username",
        "full_name",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "created_at",
        "last_login",
    )

    fieldsets = (
        ("اطلاعات اصلی", {
            "fields": (
                "phone_number",
                "username",
                "full_name",
                "gender",
                "birth_date",
                "avatar",
                "password",
            )
        }),
        ("سطوح دسترسی", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "is_staff_user",
            )
        }),
        ("زمان‌ها", {
            "fields": (
                "created_at",
                "last_login",
            )
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "phone_number",
                "username",
                "full_name",
                "gender",
                "birth_date",
                "password1",
                "password2",
                "is_staff_user",
                "is_active",
            ),
        }),
    )