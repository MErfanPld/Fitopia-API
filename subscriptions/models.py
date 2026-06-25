from django.db import models
from django.utils import timezone
from django.conf import settings


class Plan(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name="نام پلن"
    )
    description = models.TextField(
        blank=True,
        verbose_name="توضیحات"
    )
    price = models.PositiveIntegerField(
        verbose_name="قیمت (تومان)"
    )
    duration_days = models.PositiveIntegerField(
        verbose_name="مدت اعتبار (روز)"
    )
    token_count = models.PositiveIntegerField(
        verbose_name="تعداد توکن"
    )
    gyms = models.ManyToManyField(
        "gym.Gym",
        related_name="plans",
        verbose_name="باشگاه‌های مجاز"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    class Meta:
        verbose_name = "پلن"
        verbose_name_plural = "پلن‌ها"
        ordering = ["order", "price"]

    def __str__(self):
        return f"{self.name} - {self.token_count} توکن - {self.duration_days} روز"


class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ("active", "فعال"),
        ("expired", "منقضی‌شده"),
        ("cancelled", "لغو‌شده"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscriptions",
        verbose_name="کاربر"
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name="subscriptions",
        verbose_name="پلن"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
        verbose_name="وضعیت"
    )
    start_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="تاریخ شروع"
    )
    end_date = models.DateTimeField(
        verbose_name="تاریخ پایان"
    )
    tokens_total = models.PositiveIntegerField(
        verbose_name="کل توکن‌ها"
    )
    tokens_used = models.PositiveIntegerField(
        default=0,
        verbose_name="توکن‌های استفاده‌شده"
    )
    # توکن‌های باقیمانده هنگام انقضا - برای محاسبه تخفیف
    leftover_tokens = models.PositiveIntegerField(
        default=0,
        verbose_name="توکن‌های باقیمانده هنگام انقضا"
    )
    paid_amount = models.PositiveIntegerField(
        verbose_name="مبلغ پرداختی (تومان)"
    )
    discount_applied = models.PositiveIntegerField(
        default=0,
        verbose_name="تخفیف اعمال‌شده (تومان)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ خرید"
    )

    class Meta:
        verbose_name = "اشتراک"
        verbose_name_plural = "اشتراک‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.plan.name} - {self.status}"

    @property
    def tokens_remaining(self):
        return self.tokens_total - self.tokens_used

    @property
    def is_active(self):
        return (
            self.status == "active"
            and self.end_date > timezone.now()
            and self.tokens_remaining > 0
        )

    def save(self, *args, **kwargs):
        if not self.pk:
            self.end_date = timezone.now() + timezone.timedelta(days=self.plan.duration_days)
            self.tokens_total = self.plan.token_count
        super().save(*args, **kwargs)

    def expire(self):
        """انقضای اشتراک و ذخیره توکن‌های باقیمانده"""
        if self.status == "active":
            self.leftover_tokens = self.tokens_remaining
            self.status = "expired"
            self.save(update_fields=["leftover_tokens", "status"])
            # آپدیت تخفیف روی پروفایل کاربر
            profile, _ = UserDiscountProfile.objects.get_or_create(user=self.user)
            profile.add_leftover_tokens(self.leftover_tokens)


class UserDiscountProfile(models.Model):
    """
    ذخیره توکن‌های باقیمانده کاربر برای تخفیف خرید بعدی
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="discount_profile",
        verbose_name="کاربر"
    )
    accumulated_leftover_tokens = models.PositiveIntegerField(
        default=0,
        verbose_name="مجموع توکن‌های باقیمانده"
    )
    discount_amount = models.PositiveIntegerField(
        default=0,
        verbose_name="مبلغ تخفیف (تومان)"
    )
    is_used = models.BooleanField(
        default=False,
        verbose_name="تخفیف استفاده شده"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین به‌روزرسانی"
    )

    class Meta:
        verbose_name = "پروفایل تخفیف"
        verbose_name_plural = "پروفایل‌های تخفیف"

    def __str__(self):
        return f"{self.user} - {self.discount_amount} تومان تخفیف"

    def add_leftover_tokens(self, count):
        """
        اضافه کردن توکن‌های باقیمانده و محاسبه تخفیف
        فرمول: هر توکن = X تومان تخفیف (قابل تنظیم)
        """
        DISCOUNT_PER_TOKEN = 5000  # هر توکن ۵۰۰۰ تومان تخفیف
        self.accumulated_leftover_tokens += count
        self.discount_amount += count * DISCOUNT_PER_TOKEN
        self.is_used = False
        self.save(update_fields=["accumulated_leftover_tokens", "discount_amount", "is_used", "updated_at"])

    def use_discount(self):
        """استفاده از تخفیف هنگام خرید"""
        amount = self.discount_amount
        self.discount_amount = 0
        self.accumulated_leftover_tokens = 0
        self.is_used = True
        self.save(update_fields=["discount_amount", "accumulated_leftover_tokens", "is_used", "updated_at"])
        return amount