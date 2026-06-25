from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import GymToken


class TokenStatusFilter(admin.SimpleListFilter):
    title = "وضعیت واقعی"
    parameter_name = "real_status"

    def lookups(self, request, model_admin):
        return [
            ("valid", "فعال و معتبر"),
            ("expired_by_time", "منقضی‌شده (زمان)"),
            ("used", "استفاده‌شده"),
        ]

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == "valid":
            return queryset.filter(status="active", valid_until__gt=now)
        if self.value() == "expired_by_time":
            return queryset.filter(status="active", valid_until__lte=now)
        if self.value() == "used":
            return queryset.filter(status="used")
        return queryset


@admin.register(GymToken)
class GymTokenAdmin(admin.ModelAdmin):
    list_display = [
        "token_code_short",
        "user_display",
        "gym",
        "status_badge",
        "issued_at",
        "valid_until",
        "used_at",
    ]
    list_filter = ["status", TokenStatusFilter, "gym"]
    search_fields = [
        "token_code",
        "subscription__user__phone_number",
        "subscription__user__full_name",
        "gym__name",
    ]
    readonly_fields = [
        "token_code",
        "issued_at",
        "valid_until",
        "used_at",
        "subscription",
        "gym",
    ]
    date_hierarchy = "issued_at"

    def token_code_short(self, obj):
        return str(obj.token_code)[:8] + "..."
    token_code_short.short_description = "کد توکن"

    def user_display(self, obj):
        return str(obj.subscription.user)
    user_display.short_description = "کاربر"

    def status_badge(self, obj):
        colors = {
            "active": "green",
            "used": "gray",
            "expired": "red",
        }
        labels = {
            "active": "فعال",
            "used": "استفاده‌شده",
            "expired": "منقضی",
        }
        color = colors.get(obj.status, "black")
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            label,
        )
    status_badge.short_description = "وضعیت"