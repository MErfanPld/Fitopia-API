"""ادمین عملیات باشگاه: حضور، دوره، مالی، مجوز، لاگ."""
from django.contrib import admin
from django.utils.html import format_html

from .models import GymVisit
from .expansion_models import (
    GymOffering,
    GymOfferingSchedule,
    Course,
    CourseEnrollment,
    SingleSessionPurchase,
    StaffPermission,
    FinanceTransaction,
    CustomerPayment,
    Refund,
    AuditLog,
)


class GymOfferingScheduleInline(admin.TabularInline):
    model = GymOfferingSchedule
    extra = 1


@admin.register(GymOffering)
class GymOfferingAdmin(admin.ModelAdmin):
    list_display = (
        "sport",
        "gym",
        "single_session_price",
        "course_price",
        "monthly_price",
        "capacity",
        "skill_level",
        "gender_restriction",
        "is_active",
    )
    list_filter = ("is_active", "skill_level", "gender_restriction", "gym")
    search_fields = ("sport__name", "gym__name", "description")
    autocomplete_fields = ("gym", "sport")
    filter_horizontal = ("coaches",)
    inlines = [GymOfferingScheduleInline]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "gym",
        "sport",
        "coach",
        "start_date",
        "end_date",
        "capacity",
        "price",
        "status",
        "is_active",
    )
    list_filter = ("status", "is_active", "gym", "start_date")
    search_fields = ("title", "gym__name", "sport__name")
    autocomplete_fields = ("gym", "sport", "offering", "coach")
    date_hierarchy = "start_date"


@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ("customer", "course", "status", "price_paid", "enrolled_at")
    list_filter = ("status", "enrolled_at")
    search_fields = ("customer__full_name", "customer__phone", "course__title")
    autocomplete_fields = ("course", "customer")
    date_hierarchy = "enrolled_at"


@admin.register(SingleSessionPurchase)
class SingleSessionPurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "customer",
        "gym",
        "sport",
        "price_paid",
        "purchased_at",
        "used_at",
        "expires_at",
    )
    list_filter = ("gym", "purchased_at")
    search_fields = ("customer__full_name", "customer__phone")
    autocomplete_fields = ("gym", "sport", "customer", "transaction")
    date_hierarchy = "purchased_at"


@admin.register(GymVisit)
class GymVisitAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "gym",
        "who",
        "sport",
        "source",
        "method",
        "is_open",
        "check_in_at",
        "check_out_at",
        "price",
        "created_at",
    )
    list_filter = ("source", "method", "is_open", "gym", "created_at")
    search_fields = (
        "guest_name",
        "guest_phone",
        "customer__full_name",
        "customer__phone",
        "gym__name",
    )
    autocomplete_fields = ("gym", "sport", "token", "customer", "registered_by")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at",)

    @admin.display(description="مراجعه‌کننده")
    def who(self, obj):
        if obj.customer_id:
            return obj.customer.full_name
        if obj.guest_name:
            return obj.guest_name
        if obj.token_id:
            try:
                return str(obj.token.subscription.user)
            except Exception:
                return f"token#{obj.token_id}"
        return "—"


@admin.register(StaffPermission)
class StaffPermissionAdmin(admin.ModelAdmin):
    list_display = ("staff_access", "code")
    list_filter = ("code",)
    search_fields = (
        "staff_access__user__username",
        "staff_access__user__phone_number",
    )
    autocomplete_fields = ("staff_access",)


@admin.register(FinanceTransaction)
class FinanceTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "gym",
        "type_badge",
        "category",
        "amount_display",
        "date",
        "payment_method",
        "status",
        "customer",
    )
    list_filter = ("type", "category", "status", "payment_method", "gym", "date")
    search_fields = (
        "description",
        "reference_number",
        "customer__full_name",
        "gym__name",
    )
    autocomplete_fields = ("gym", "customer", "created_by")
    date_hierarchy = "date"
    readonly_fields = ("created_at",)

    @admin.display(description="نوع")
    def type_badge(self, obj):
        color = "#0a7" if obj.type == "income" else "#c33"
        label = obj.get_type_display() if hasattr(obj, "get_type_display") else obj.type
        return format_html(
            '<span style="color:{};font-weight:bold">{}</span>', color, label
        )

    @admin.display(description="مبلغ (تومان)")
    def amount_display(self, obj):
        return f"{obj.amount:,}"


@admin.register(CustomerPayment)
class CustomerPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "customer",
        "gym",
        "total_price",
        "amount_paid",
        "discount",
        "payment_method",
        "created_at",
    )
    list_filter = ("payment_method", "gym", "created_at")
    search_fields = ("customer__full_name", "customer__phone", "reference_number")
    autocomplete_fields = (
        "customer",
        "gym",
        "related_course",
        "related_transaction",
        "created_by",
    )
    date_hierarchy = "created_at"


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "gym",
        "original_transaction",
        "amount",
        "status",
        "operator",
        "created_at",
        "completed_at",
    )
    list_filter = ("status", "gym", "created_at")
    search_fields = ("reason",)
    autocomplete_fields = ("gym", "original_transaction", "operator")
    readonly_fields = ("created_at",)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "gym",
        "user",
        "action",
        "object_type",
        "object_id",
        "created_at",
    )
    list_filter = ("action", "gym", "created_at")
    search_fields = (
        "action",
        "object_type",
        "object_id",
        "user__username",
        "user__phone_number",
    )
    autocomplete_fields = ("gym", "user")
    date_hierarchy = "created_at"
    readonly_fields = (
        "gym",
        "user",
        "action",
        "object_type",
        "object_id",
        "metadata",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
