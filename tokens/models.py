import uuid
from django.db import models
from django.utils import timezone


def default_valid_until():
    return timezone.now() + timezone.timedelta(hours=24)


class GymToken(models.Model):
    STATUS_CHOICES = [
        ("active", "فعال"),
        ("used", "استفاده‌شده"),
        ("expired", "منقضی‌شده"),
    ]

    subscription = models.ForeignKey(
        "subscriptions.UserSubscription",
        on_delete=models.CASCADE,
        related_name="gym_tokens",
        verbose_name="اشتراک"
    )
    gym = models.ForeignKey(
        "gym.Gym",
        on_delete=models.CASCADE,
        related_name="tokens",
        verbose_name="باشگاه"
    )
    token_code = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name="کد توکن"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
        verbose_name="وضعیت"
    )
    issued_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان صدور"
    )
    valid_until = models.DateTimeField(
        default=default_valid_until,
        verbose_name="اعتبار تا"
    )
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان استفاده"
    )

    class Meta:
        verbose_name = "توکن باشگاه"
        verbose_name_plural = "توکن‌های باشگاه"
        ordering = ["-issued_at"]

    def __str__(self):
        return f"{self.subscription.user} - {self.gym.name} - {self.status}"

    @property
    def is_valid(self):
        return (
            self.status == "active"
            and self.valid_until > timezone.now()
        )

    def use(self):
        """مصرف توکن هنگام ورود به باشگاه — از هر مسیری (API/ادمین/شل) صدا زده بشه همین اتفاق می‌افته"""
        if not self.is_valid:
            return False

        self.status = "used"
        self.used_at = timezone.now()
        self.save(update_fields=["status", "used_at"])

        # import محلی برای جلوگیری از circular import بین tokens و gym_panel
        from gym_panel.models import GymVisit, GymCustomer

        GymVisit.objects.create(
            gym=self.gym,
            sport=None,   # فعلاً GymToken فیلد sport نداره
            price=0,      # فعلاً GymToken فیلد price نداره
            source="token",
            token=self,
        )

        fitopia_user = self.subscription.user
        customer, created = GymCustomer.objects.get_or_create(
            gym=self.gym,
            fitopia_user=fitopia_user,
            defaults={
                "full_name": fitopia_user.full_name or fitopia_user.username or "بدون نام",
                "phone": fitopia_user.phone_number or "",
                "sport": None,
                "join_date": timezone.now().date(),
                "source": "token",
            },
        )

        return True

    def expire(self):
        """انقضای توکن"""
        if self.status == "active":
            self.status = "expired"
            self.save(update_fields=["status"])

    def generate_qr_base64(self):
        """تولید QR Code به صورت base64"""
        import qrcode
        import base64
        from io import BytesIO

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(str(self.token_code))
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"