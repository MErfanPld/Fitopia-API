from django.db import models
from django.conf import settings

# Note: GymStaffAccess and GymCustomer are defined in gym_panel.models
# We use string references / same-app relations for FKs.

# =============================================================================
# Gym-specific sport offering (does not replace global Sport)
# =============================================================================

def upload_customer_photo(instance, filename):
    import os, uuid, time
    from django.utils.text import slugify
    base = slugify(instance.full_name or "customer", allow_unicode=True)[:40]
    ext = filename.rsplit(".", 1)[-1]
    name = f"{int(time.time())}_{uuid.uuid4().hex[:8]}_{base}.{ext}"
    return os.path.join("uploads/gym/customers", name)


class GymOffering(models.Model):
    """Gym-specific configuration for a global Sport."""
    LEVEL_CHOICES = [
        ("beginner", "مبتدی"),
        ("intermediate", "متوسط"),
        ("advanced", "پیشرفته"),
        ("all", "همه سطوح"),
    ]
    GENDER_CHOICES = [
        ("all", "همه"),
        ("male", "آقایان"),
        ("female", "بانوان"),
    ]

    gym = models.ForeignKey(
        "gym.Gym", on_delete=models.CASCADE, related_name="offerings"
    )
    sport = models.ForeignKey(
        "gym.Sport", on_delete=models.CASCADE, related_name="gym_offerings"
    )
    description = models.TextField(blank=True)
    coaches = models.ManyToManyField(
        "gym.GymCoach", blank=True, related_name="offerings"
    )
    capacity = models.PositiveIntegerField(null=True, blank=True)
    single_session_price = models.PositiveIntegerField(
        null=True, blank=True, help_text="تومان"
    )
    course_price = models.PositiveIntegerField(
        null=True, blank=True, help_text="تومان"
    )
    monthly_price = models.PositiveIntegerField(
        null=True, blank=True, help_text="تومان"
    )
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    skill_level = models.CharField(
        max_length=20, choices=LEVEL_CHOICES, default="all"
    )
    gender_restriction = models.CharField(
        max_length=10, choices=GENDER_CHOICES, default="all"
    )
    min_age = models.PositiveIntegerField(null=True, blank=True)
    max_age = models.PositiveIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ارائه رشته در باشگاه"
        verbose_name_plural = "ارائه‌های رشته در باشگاه"
        unique_together = ("gym", "sport")

    def __str__(self):
        return f"{self.gym.name} — {self.sport.name}"


class GymOfferingSchedule(models.Model):
    DAY_CHOICES = [
        (0, "شنبه"),
        (1, "یکشنبه"),
        (2, "دوشنبه"),
        (3, "سه‌شنبه"),
        (4, "چهارشنبه"),
        (5, "پنجشنبه"),
        (6, "جمعه"),
    ]
    offering = models.ForeignKey(
        GymOffering, on_delete=models.CASCADE, related_name="schedules"
    )
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["day_of_week", "start_time"]
        verbose_name = "برنامه زمانی رشته"
        verbose_name_plural = "برنامه‌های زمانی رشته"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            raise ValidationError("ساعت پایان باید بعد از ساعت شروع باشد.")


class Course(models.Model):
    STATUS_CHOICES = [
        ("draft", "پیش‌نویس"),
        ("open", "باز"),
        ("full", "تکمیل ظرفیت"),
        ("closed", "بسته"),
        ("cancelled", "لغو شده"),
    ]
    gym = models.ForeignKey(
        "gym.Gym", on_delete=models.CASCADE, related_name="courses"
    )
    sport = models.ForeignKey(
        "gym.Sport", on_delete=models.PROTECT, related_name="courses"
    )
    offering = models.ForeignKey(
        GymOffering, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="courses"
    )
    coach = models.ForeignKey(
        "gym.GymCoach", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="courses"
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    days_of_week = models.CharField(
        max_length=50, blank=True,
        help_text="مثلاً 0,2,4 برای شنبه/دوشنبه/چهارشنبه"
    )
    capacity = models.PositiveIntegerField(default=20)
    price = models.PositiveIntegerField(help_text="تومان")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date"]
        verbose_name = "دوره"
        verbose_name_plural = "دوره‌ها"

    def __str__(self):
        return self.title

    @property
    def enrollment_count(self):
        return self.enrollments.filter(status="active").count()

    @property
    def remaining_capacity(self):
        return max(0, self.capacity - self.enrollment_count)


class CourseEnrollment(models.Model):
    STATUS_CHOICES = [
        ("active", "فعال"),
        ("completed", "تمام‌شده"),
        ("cancelled", "لغو"),
    ]
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="enrollments"
    )
    customer = models.ForeignKey(
        "gym_panel.GymCustomer", on_delete=models.CASCADE, related_name="enrollments"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    enrolled_at = models.DateTimeField(auto_now_add=True)
    price_paid = models.PositiveIntegerField(default=0, help_text="تومان")

    class Meta:
        unique_together = ("course", "customer")
        verbose_name = "ثبت‌نام دوره"
        verbose_name_plural = "ثبت‌نام‌های دوره"


class SingleSessionPurchase(models.Model):
    STATUS_CHOICES = [
        ("unused", "استفاده‌نشده"),
        ("used", "استفاده‌شده"),
        ("expired", "منقضی"),
        ("cancelled", "لغو"),
    ]
    gym = models.ForeignKey(
        "gym.Gym", on_delete=models.CASCADE, related_name="single_sessions"
    )
    customer = models.ForeignKey(
        "gym_panel.GymCustomer", on_delete=models.CASCADE, related_name="single_sessions"
    )
    sport = models.ForeignKey(
        "gym.Sport", on_delete=models.SET_NULL, null=True, blank=True
    )
    price = models.PositiveIntegerField(help_text="تومان")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="unused")
    purchased_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    transaction = models.ForeignKey(
        "FinanceTransaction", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="single_sessions"
    )

    class Meta:
        ordering = ["-purchased_at"]
        verbose_name = "جلسه تکی"
        verbose_name_plural = "جلسات تکی"


class StaffPermission(models.Model):
    """Granular permission assigned to a GymStaffAccess row."""
    CODE_CHOICES = [
        ("customer.view", "مشاهده مشتری"),
        ("customer.create", "ایجاد مشتری"),
        ("customer.update", "ویرایش مشتری"),
        ("customer.delete", "حذف مشتری"),
        ("course.view", "مشاهده دوره"),
        ("course.create", "ایجاد دوره"),
        ("course.update", "ویرایش دوره"),
        ("course.enroll", "ثبت‌نام در دوره"),
        ("attendance.view", "مشاهده حضور"),
        ("attendance.create", "ثبت حضور"),
        ("finance.view", "مشاهده مالی"),
        ("finance.create", "ثبت مالی"),
        ("finance.update", "ویرایش مالی"),
        ("finance.report", "گزارش مالی"),
        ("finance.refund", "استرداد"),
        ("employee.view", "مشاهده کارمند"),
        ("employee.manage", "مدیریت کارمند"),
        ("offering.manage", "مدیریت رشته‌ها"),
    ]
    staff_access = models.ForeignKey(
        "GymStaffAccess", on_delete=models.CASCADE, related_name="permissions"
    )
    code = models.CharField(max_length=40, choices=CODE_CHOICES)

    class Meta:
        unique_together = ("staff_access", "code")
        verbose_name = "مجوز کارمند"
        verbose_name_plural = "مجوزهای کارمند"


class FinanceTransaction(models.Model):
    TYPE_CHOICES = [
        ("income", "درآمد"),
        ("expense", "هزینه"),
    ]
    CATEGORY_CHOICES = [
        ("membership", "عضویت"),
        ("course", "دوره"),
        ("single_session", "جلسه تکی"),
        ("other_income", "سایر درآمد"),
        ("rent", "اجاره"),
        ("utilities", "قبوض"),
        ("equipment", "تجهیزات"),
        ("salary", "حقوق"),
        ("coach_payment", "پرداخت مربی"),
        ("maintenance", "نگهداری"),
        ("marketing", "بازاریابی"),
        ("other_expense", "سایر هزینه"),
    ]
    PAYMENT_METHOD_CHOICES = [
        ("cash", "نقد"),
        ("card", "کارت"),
        ("transfer", "کارت به کارت"),
        ("online", "آنلاین"),
        ("other", "سایر"),
    ]
    STATUS_CHOICES = [
        ("completed", "تکمیل"),
        ("pending", "در انتظار"),
        ("cancelled", "لغو"),
        ("refunded", "مسترد"),
    ]

    gym = models.ForeignKey(
        "gym.Gym", on_delete=models.CASCADE, related_name="transactions"
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    amount = models.PositiveIntegerField(help_text="مبلغ به تومان (صحیح)")
    date = models.DateField()
    description = models.TextField(blank=True)
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, default="cash"
    )
    reference_number = models.CharField(max_length=100, blank=True)
    customer = models.ForeignKey(
        "gym_panel.GymCustomer", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="transactions"
    )
    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="recorded_transactions"
    )
    course = models.ForeignKey(
        Course, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="transactions"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="created_transactions"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="completed")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        verbose_name = "تراکنش مالی"
        verbose_name_plural = "تراکنش‌های مالی"
        indexes = [
            models.Index(fields=["gym", "date"]),
            models.Index(fields=["gym", "type"]),
        ]


class CustomerPayment(models.Model):
    """Payment toward a customer's obligation (membership/course/session)."""
    gym = models.ForeignKey(
        "gym.Gym", on_delete=models.CASCADE, related_name="customer_payments"
    )
    customer = models.ForeignKey(
        "gym_panel.GymCustomer", on_delete=models.CASCADE, related_name="payments"
    )
    total_price = models.PositiveIntegerField(help_text="مبلغ کل تومان")
    amount_paid = models.PositiveIntegerField(default=0, help_text="پرداخت‌شده تومان")
    discount = models.PositiveIntegerField(default=0, help_text="تخفیف تومان")
    description = models.CharField(max_length=255, blank=True)
    payment_method = models.CharField(
        max_length=20, choices=FinanceTransaction.PAYMENT_METHOD_CHOICES, default="cash"
    )
    reference_number = models.CharField(max_length=100, blank=True)
    related_course = models.ForeignKey(
        Course, on_delete=models.SET_NULL, null=True, blank=True
    )
    related_transaction = models.ForeignKey(
        FinanceTransaction, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "پرداخت مشتری"
        verbose_name_plural = "پرداخت‌های مشتری"

    @property
    def remaining_balance(self):
        due = max(0, self.total_price - self.discount)
        return max(0, due - self.amount_paid)


class Refund(models.Model):
    STATUS_CHOICES = [
        ("pending", "در انتظار"),
        ("approved", "تایید"),
        ("rejected", "رد"),
        ("completed", "انجام‌شده"),
    ]
    gym = models.ForeignKey(
        "gym.Gym", on_delete=models.CASCADE, related_name="refunds"
    )
    original_transaction = models.ForeignKey(
        FinanceTransaction, on_delete=models.PROTECT, related_name="refunds"
    )
    amount = models.PositiveIntegerField(help_text="تومان")
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "استرداد"
        verbose_name_plural = "استردادها"


class AuditLog(models.Model):
    gym = models.ForeignKey(
        "gym.Gym", on_delete=models.CASCADE, related_name="audit_logs",
        null=True, blank=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=80, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "لاگ حسابرسی"
        verbose_name_plural = "لاگ‌های حسابرسی"
        indexes = [
            models.Index(fields=["gym", "-created_at"]),
        ]
