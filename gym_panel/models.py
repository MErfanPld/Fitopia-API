from django.db import models
from django.conf import settings



class GymStaffAccess(models.Model):
    ROLE_CHOICES = [
        ("owner", "مالک"),
        ("manager", "مدیر"),
        ("receptionist", "پذیرش"),
        ("accountant", "حسابدار"),
        ("coach", "مربی"),
        ("staff", "کارمند"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="gym_accesses",
        verbose_name="کاربر",
    )
    gym = models.ForeignKey(
        "gym.Gym",
        on_delete=models.CASCADE,
        related_name="staff_accesses",
        verbose_name="باشگاه",
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="owner",
        verbose_name="نقش",
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    start_date = models.DateField(null=True, blank=True, verbose_name="تاریخ شروع")
    end_date = models.DateField(null=True, blank=True, verbose_name="تاریخ پایان")
    employee_number = models.CharField(max_length=50, blank=True, verbose_name="کد پرسنلی")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ایجاد")

    class Meta:
        verbose_name = "دسترسی باشگاه‌دار"
        verbose_name_plural = "دسترسی‌های باشگاه‌دار"
        unique_together = ("user", "gym")

    def __str__(self):
        return f"{self.user} → {self.gym} ({self.role})"
    


class GymVisit(models.Model):
    SOURCE_CHOICES = [
        ("token", "توکن فیتوپیا"),
        ("direct", "ثبت مستقیم باشگاه"),
        ("qr", "QR"),
        ("manual", "دستی"),
        ("membership", "عضویت"),
        ("single_session", "جلسه تکی"),
    ]
    METHOD_CHOICES = [
        ("qr", "QR"),
        ("token", "توکن"),
        ("manual", "دستی"),
        ("membership", "عضویت"),
    ]

    gym = models.ForeignKey(
        "gym.Gym",
        on_delete=models.CASCADE,
        related_name="visits",
        verbose_name="باشگاه",
    )
    sport = models.ForeignKey(
        "gym.Sport",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visits",
        verbose_name="رشته ورزشی",
    )
    price = models.IntegerField(
        default=0,
        verbose_name="قیمت (تومان) - در لحظه ثبت",
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        verbose_name="منبع",
    )
    token = models.ForeignKey(
        "tokens.GymToken",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visit",
        verbose_name="توکن مرتبط",
    )
    guest_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="نام مراجعه‌کننده (ثبت مستقیم)",
    )
    guest_phone = models.CharField(
        max_length=15,
        blank=True,
        verbose_name="شماره مراجعه‌کننده (ثبت مستقیم)",
    )
    registered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="registered_visits",
        verbose_name="ثبت‌شده توسط",
    )
    customer = models.ForeignKey(
        "GymCustomer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visits",
        verbose_name="مشتری",
    )
    check_in_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان ورود")
    check_out_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان خروج")
    method = models.CharField(
        max_length=20, choices=METHOD_CHOICES, blank=True, default="manual",
        verbose_name="روش ثبت",
    )
    is_open = models.BooleanField(default=False, verbose_name="حضور فعال")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    class Meta:
        verbose_name = "ورود به باشگاه"
        verbose_name_plural = "ورودهای باشگاه"
        ordering = ["-created_at"]

    def __str__(self):
        who = self.token.subscription.user if self.token_id else (self.guest_name or self.customer_id)
        return f"{self.gym.name} - {who} - {self.created_at:%Y-%m-%d %H:%M}"
    
    
class GymChangeRequest(models.Model):
    TYPE_CHOICES = [
        ("field_edit", "ویرایش فیلد محدود"),
        ("new_sport", "پیشنهاد رشته ورزشی جدید"),
    ]
    STATUS_CHOICES = [
        ("pending", "در انتظار بررسی"),
        ("approved", "تایید شده"),
        ("rejected", "رد شده"),
    ]

    gym = models.ForeignKey(
        "gym.Gym", on_delete=models.CASCADE,
        related_name="change_requests", verbose_name="باشگاه"
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name="gym_change_requests", verbose_name="درخواست‌دهنده"
    )
    request_type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name="نوع درخواست")
    payload = models.JSONField(verbose_name="داده‌های درخواست")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending", verbose_name="وضعیت")
    admin_note = models.CharField(max_length=255, blank=True, verbose_name="یادداشت ادمین")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ بررسی")

    class Meta:
        verbose_name = "درخواست تغییر باشگاه"
        verbose_name_plural = "درخواست‌های تغییر باشگاه"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.gym.name} - {self.get_request_type_display()} - {self.status}"
    
    
class GymTicketMessage(models.Model):
    SENDER_CHOICES = [
        ("gym", "باشگاه‌دار"),
        ("admin", "ادمین"),
        ("system", "سیستم"),
    ]

    ticket = models.ForeignKey(
        GymChangeRequest, on_delete=models.CASCADE,
        related_name="messages", verbose_name="تیکت"
    )
    sender_role = models.CharField(max_length=10, choices=SENDER_CHOICES, verbose_name="فرستنده")
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="gym_ticket_messages", verbose_name="کاربر"
    )
    message = models.TextField(verbose_name="پیام")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان")

    class Meta:
        verbose_name = "پیام تیکت"
        verbose_name_plural = "پیام‌های تیکت"
        ordering = ["created_at"]

    def __str__(self):
        return f"#{self.ticket_id} - {self.get_sender_role_display()} - {self.created_at:%Y-%m-%d %H:%M}"
    
    
    

class GymCustomer(models.Model):
    SOURCE_CHOICES = [
        ("token", "توکن/اشتراک فیتوپیا"),
        ("manual", "ثبت دستی توسط باشگاه"),
    ]

    gym = models.ForeignKey(
        "gym.Gym", on_delete=models.CASCADE,
        related_name="customers", verbose_name="باشگاه"
    )
    fitopia_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="gym_customer_profiles",
        verbose_name="کاربر فیتوپیا (در صورت وجود)"
    )
    full_name = models.CharField(max_length=150, verbose_name="نام و نام خانوادگی")
    phone = models.CharField(max_length=15, verbose_name="شماره تماس")
    sport = models.ForeignKey(
        "gym.Sport", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="gym_customers", verbose_name="رشته ورزشی"
    )

    source = models.CharField(
        max_length=10, choices=SOURCE_CHOICES, default="manual",
        verbose_name="منبع"
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="added_gym_customers",
        verbose_name="ثبت‌شده توسط (کارمند/باشگاه‌دار)"
    )
    sessions_total = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="تعداد کل جلسات (بسته)"
    )
    sessions_remaining = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="جلسات باقی‌مانده"
    )
    price_paid = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="مبلغ پرداختی (تومان)"
    )

    join_date = models.DateField(verbose_name="تاریخ عضویت")
    photo = models.ImageField(
        upload_to="uploads/gym/customers/", null=True, blank=True, verbose_name="عکس"
    )
    membership_status = models.CharField(
        max_length=20,
        choices=[
            ("active", "فعال"),
            ("expired", "منقضی"),
            ("suspended", "معلق"),
            ("inactive", "غیرفعال"),
        ],
        default="active",
        verbose_name="وضعیت عضویت",
    )
    membership_type = models.CharField(
        max_length=30,
        choices=[
            ("session_pack", "بسته جلسه"),
            ("monthly", "ماهانه"),
            ("course", "دوره"),
            ("single", "تکی"),
            ("other", "سایر"),
        ],
        default="session_pack",
        blank=True,
        verbose_name="نوع عضویت",
    )
    membership_start = models.DateField(null=True, blank=True, verbose_name="شروع عضویت")
    membership_end = models.DateField(null=True, blank=True, verbose_name="پایان عضویت")
    coach = models.ForeignKey(
        "gym.GymCoach", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="customers", verbose_name="مربی"
    )
    sessions_used = models.PositiveIntegerField(default=0, verbose_name="جلسات مصرف‌شده")
    notes = models.TextField(blank=True, verbose_name="یادداشت")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    last_visit_at = models.DateTimeField(null=True, blank=True, verbose_name="آخرین حضور")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین ویرایش")

    class Meta:
        verbose_name = "مشتری باشگاه"
        verbose_name_plural = "مشتریان باشگاه"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} - {self.gym.name}"

# Expansion domain models (offerings, courses, finance, ACL, audit)
from .expansion_models import (  # noqa: E402,F401
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
