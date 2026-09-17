import random

from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

from .redis_store import delete_token, next_midnight, store_token


def default_valid_until():
    """توکن‌ها تا نیمه‌شب همان روز معتبرند."""
    return next_midnight()


def generate_five_digit_code() -> str:
    """کد ۵رقمی یکتا بین توکن‌های فعال (۱۰۰۰۰–۹۹۹۹۹)."""
    for _ in range(80):
        code = f"{random.randint(10000, 99999)}"
        if not GymToken.objects.filter(token_code=code, status="active").exists():
            return code
    return f"{random.randint(10000, 99999)}"


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
        verbose_name="اشتراک",
    )
    gym = models.ForeignKey(
        "gym.Gym",
        on_delete=models.CASCADE,
        related_name="tokens",
        verbose_name="باشگاه",
        null=True,
        blank=True,
        help_text="اگر خالی باشد، بلیت سراسری برای همه باشگاه‌های پلن است.",
    )
    token_code = models.CharField(
        max_length=5,
        editable=False,
        db_index=True,
        verbose_name="کد توکن",
        help_text="کد ۵رقمی روزانه؛ بعد از نیمه‌شب قابل استفاده مجدد است",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
        verbose_name="وضعیت",
    )
    issued_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان صدور",
    )
    valid_until = models.DateTimeField(
        default=default_valid_until,
        verbose_name="اعتبار تا",
        help_text="معمولاً نیمه‌شب همان روز",
    )
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="زمان استفاده",
    )

    class Meta:
        verbose_name = "توکن باشگاه"
        verbose_name_plural = "توکن‌های باشگاه"
        ordering = ["-issued_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["token_code"],
                condition=Q(status="active"),
                name="unique_active_gym_token_code",
            ),
        ]

    def __str__(self):
        gym_label = self.gym.name if self.gym_id else "سراسری"
        return f"{self.subscription.user} - {gym_label} - {self.token_code} - {self.status}"

    @property
    def is_valid(self):
        return self.status == "active" and self.valid_until > timezone.now()

    def save(self, *args, **kwargs):
        creating = self.pk is None
        if not self.token_code:
            self.token_code = generate_five_digit_code()
        if not self.valid_until:
            self.valid_until = next_midnight()
        super().save(*args, **kwargs)
        if creating and self.status == "active":
            self.sync_to_redis()

    def sync_to_redis(self):
        """ثبت کد فعال در Redis با TTL تا نیمه‌شب."""
        if self.status != "active":
            return
        ttl = max(int((self.valid_until - timezone.now()).total_seconds()), 1)
        store_token(
            self.token_code,
            {
                "token_id": self.pk,
                "subscription_id": self.subscription_id,
                "gym_id": self.gym_id,
                "status": self.status,
                "valid_until": self.valid_until.isoformat(),
            },
            ttl_seconds=ttl,
        )

    def use(self):
        """Consume token safely under a row lock to prevent double-spend."""
        with transaction.atomic():
            try:
                locked = (
                    GymToken.objects.select_for_update()
                    .select_related("subscription__user", "gym")
                    .get(pk=self.pk)
                )
            except GymToken.DoesNotExist:
                return False

            if not (
                locked.status == "active"
                and locked.valid_until > timezone.now()
            ):
                return False

            if not locked.gym_id:
                return False

            locked.status = "used"
            locked.used_at = timezone.now()
            locked.save(update_fields=["status", "used_at"])

            self.status = locked.status
            self.used_at = locked.used_at

            delete_token(locked.token_code)

            from gym_panel.models import GymVisit, GymCustomer

            GymVisit.objects.create(
                gym=locked.gym,
                sport=None,
                price=0,
                source="token",
                token=locked,
            )

            fitopia_user = locked.subscription.user
            GymCustomer.objects.get_or_create(
                gym=locked.gym,
                fitopia_user=fitopia_user,
                defaults={
                    "full_name": (
                        fitopia_user.full_name
                        or fitopia_user.username
                        or "بدون نام"
                    ),
                    "phone": fitopia_user.phone_number or "",
                    "sport": None,
                    "join_date": timezone.now().date(),
                    "source": "token",
                },
            )
            return True

    def expire(self):
        if self.status == "active":
            self.status = "expired"
            self.save(update_fields=["status"])
            delete_token(self.token_code)

    def generate_qr_base64(self):
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
