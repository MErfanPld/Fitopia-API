from django.conf import settings
from django.db import models


class SportCategory(models.Model):
    title = models.CharField(max_length=100, verbose_name="عنوان دسته‌بندی")
    slug = models.SlugField(unique=True, verbose_name="اسلاگ")

    class Meta:
        verbose_name = "دسته‌بندی ورزشی"
        verbose_name_plural = "دسته‌بندی‌های ورزشی"

    def __str__(self):
        return self.title


class Sport(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام رشته ورزشی")
    category = models.ForeignKey(
        SportCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sports",
        verbose_name="دسته‌بندی",
    )

    class Meta:
        verbose_name = "رشته ورزشی"
        verbose_name_plural = "رشته‌های ورزشی"

    def __str__(self):
        return self.name


class GymFacility(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام امکانات")

    class Meta:
        verbose_name = "امکانات"
        verbose_name_plural = "امکانات باشگاه"

    def __str__(self):
        return self.name


class Gym(models.Model):
    GENDER_CHOICES = [
        ("women", "بانوان"),
        ("men", "آقایان"),
        ("both", "آقایان و بانوان"),
    ]
    name = models.CharField(max_length=150, verbose_name="نام باشگاه")
    address = models.TextField(verbose_name="آدرس")
    phone = models.CharField(max_length=20, verbose_name="شماره تماس")
    latitude = models.FloatField(verbose_name="عرض جغرافیایی")
    longitude = models.FloatField(verbose_name="طول جغرافیایی")
    popularity_score = models.PositiveIntegerField(default=0, verbose_name="امتیاز محبوبیت")
    is_popular = models.BooleanField(default=False, verbose_name="باشگاه محبوب")
    cover_image = models.ImageField(
        upload_to="gyms/covers/", null=True, blank=True, verbose_name="تصویر کاور"
    )
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        default="both",
        verbose_name="جنسیت باشگاه",
        help_text="women | men | both",
    )
    is_open = models.BooleanField(
        default=True,
        verbose_name="باز است",
        help_text="وضعیت فعلی باز/بسته بودن باشگاه",
    )

    class Meta:
        verbose_name = "باشگاه"
        verbose_name_plural = "باشگاه‌ها"

    def __str__(self):
        return self.name

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if not reviews.exists():
            return 0
        return round(
            sum(review.rating for review in reviews) / reviews.count(),
            1,
        )


class GymPrice(models.Model):
    gym = models.ForeignKey(
        Gym, on_delete=models.CASCADE, related_name="prices", verbose_name="باشگاه"
    )
    sport = models.ForeignKey(
        Sport, on_delete=models.CASCADE, verbose_name="رشته ورزشی"
    )
    monthly_price = models.PositiveIntegerField(verbose_name="قیمت ماهانه")
    yearly_price = models.PositiveIntegerField(verbose_name="قیمت سالانه")

    class Meta:
        verbose_name = "قیمت باشگاه"
        verbose_name_plural = "قیمت‌های باشگاه"

    def __str__(self):
        return f"{self.gym} - {self.sport}"


class GymImage(models.Model):
    gym = models.ForeignKey(
        Gym, on_delete=models.CASCADE, related_name="images", verbose_name="باشگاه"
    )
    image = models.ImageField(upload_to="gyms/gallery/", verbose_name="تصویر")

    class Meta:
        verbose_name = "تصویر باشگاه"
        verbose_name_plural = "تصاویر باشگاه"


class GymVideo(models.Model):
    gym = models.ForeignKey(
        Gym, on_delete=models.CASCADE, related_name="videos", verbose_name="باشگاه"
    )
    video = models.FileField(upload_to="gyms/videos/", verbose_name="ویدیو")

    class Meta:
        verbose_name = "ویدیو باشگاه"
        verbose_name_plural = "ویدیوهای باشگاه"


class GymBanner(models.Model):
    gym = models.ForeignKey(
        Gym, on_delete=models.CASCADE, related_name="banners", verbose_name="باشگاه"
    )
    image = models.ImageField(upload_to="gyms/banners/", verbose_name="بنر")

    class Meta:
        verbose_name = "بنر باشگاه"
        verbose_name_plural = "بنرهای باشگاه"


class GymCoach(models.Model):
    gym = models.ForeignKey(
        Gym,
        on_delete=models.CASCADE,
        related_name="coaches",
        verbose_name="باشگاه",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coach_profiles",
        verbose_name="حساب کاربری مربی",
        help_text="برای ورود به پنل مربی به یک User با is_staff_user لینک می‌شود",
    )
    sports = models.ManyToManyField(
        Sport,
        related_name="coaches",
        blank=True,
    )
    full_name = models.CharField(max_length=100, verbose_name="نام مربی")
    image = models.ImageField(
        upload_to="gyms/coaches/",
        verbose_name="تصویر مربی",
        null=True,
        blank=True,
    )
    specialty = models.CharField(max_length=100, verbose_name="تخصص", blank=True, default="")
    bio = models.TextField(blank=True, default="", verbose_name="بیوگرافی مربی")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    class Meta:
        verbose_name = "مربی"
        verbose_name_plural = "مربیان"
        unique_together = ("gym", "user")

    def __str__(self):
        return self.full_name


class GymReview(models.Model):
    gym = models.ForeignKey(
        Gym, on_delete=models.CASCADE, related_name="reviews", verbose_name="باشگاه"
    )
    name = models.CharField(max_length=100, verbose_name="نام")
    rating = models.PositiveSmallIntegerField(verbose_name="امتیاز")
    comment = models.TextField(verbose_name="نظر")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ")

    class Meta:
        verbose_name = "نظر باشگاه"
        verbose_name_plural = "نظرات باشگاه"
