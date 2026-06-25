from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Plan, UserSubscription, UserDiscountProfile


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "price",
        "duration_days",
        "token_count",
        "gyms_count",
        "is_active",
        "order",
    ]
    list_editable = ["is_active", "order"]
    list_filter = ["is_active"]
    search_fields = ["name"]
    filter_horizontal = ["gyms"]

    def gyms_count(self, obj):
        return obj.gyms.count()
    gyms_count.short_description = "تعداد باشگاه‌ها"


class SubscriptionStatusFilter(admin.SimpleListFilter):
    title = "وضعیت واقعی"
    parameter_name = "real_status"

    def lookups(self, request, model_admin):
        return [
            ("truly_active", "فعال واقعی"),
            ("expired_by_time", "منقضی‌شده (زمان)"),
            ("expired_by_token", "منقضی‌شده (توکن)"),
        ]

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == "truly_active":
            return queryset.filter(status="active", end_date__gt=now)
        if self.value() == "expired_by_time":
            return queryset.filter(status="active", end_date__lte=now)
        if self.value() == "expired_by_token":
            return queryset.filter(status="active", tokens_used__gte=models.F("tokens_total"))
        return queryset


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "plan",
        "status",
        "tokens_remaining_display",
        "end_date",
        "paid_amount",
        "discount_applied",
        "created_at",
    ]
    list_filter = ["status", SubscriptionStatusFilter, "plan"]
    search_fields = ["user__phone_number", "user__full_name"]
    readonly_fields = [
        "tokens_total",
        "tokens_used",
        "leftover_tokens",
        "paid_amount",
        "discount_applied",
        "start_date",
        "end_date",
        "created_at",
    ]
    date_hierarchy = "created_at"
    actions = ["expire_subscriptions"]

    def tokens_remaining_display(self, obj):
        remaining = obj.tokens_remaining
        total = obj.tokens_total
        color = "green" if remaining > 0 else "red"
        return format_html(
            '<span style="color: {};">{} / {}</span>',
            color,
            remaining,
            total,
        )
    tokens_remaining_display.short_description = "توکن باقیمانده"

    def expire_subscriptions(self, request, queryset):
        count = 0
        for sub in queryset.filter(status="active"):
            sub.expire()
            count += 1
        self.message_user(request, f"{count} اشتراک منقضی شد.")
    expire_subscriptions.short_description = "انقضای اشتراک‌های انتخاب‌شده"


@admin.register(UserDiscountProfile)
class UserDiscountProfileAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "accumulated_leftover_tokens",
        "discount_amount",
        "is_used",
        "updated_at",
    ]
    list_filter = ["is_used"]
    search_fields = ["user__phone_number", "user__full_name"]
    readonly_fields = ["updated_at"]