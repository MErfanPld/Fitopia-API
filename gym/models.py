from django.db import models
import os
import uuid
import time
from django.utils.text import slugify


def upload_gym_cover_image(instance, filename):
    short_name = slugify(instance.name, allow_unicode=True)[:50]
    ext = filename.split('.')[-1]
    unique_name = f"{int(time.time())}_{uuid.uuid4().hex[:8]}_{short_name}.{ext}"
    return os.path.join('uploads/gym/cover', unique_name)


class SportCategory(models.Model):
    title = models.CharField(
        max_length=100,
        verbose_name="عنوان دسته‌بندی"
    )

    slug = models.SlugField(
        unique=True,
        verbose_name="اسلاگ"
    )

    class Meta:
        verbose_name = "دسته‌بندی ورزشی"
        verbose_name_plural = "دسته‌بندی‌های ورزشی"

    def __str__(self):
        return self.title


class Sport(models.Model):
    category = models.ForeignKey(
        SportCategory,
        on_delete=models.CASCADE,
        related_name="sports",
        verbose_name="دسته‌بندی"
    )

    name = models.CharField(
        max_length=100,
        verbose_name="نام رشته ورزشی"
    )

    class Meta:
        verbose_name = "رشته ورزشی"
        verbose_name_plural = "رشته‌های ورزشی"

    def __str__(self):
        return self.name


class GymFacility(models.Model):
    title = models.CharField(
        max_length=100,
        verbose_name="نام امکانات"
    )

    class Meta:
        verbose_name = "امکانات باشگاه"
        verbose_name_plural = "امکانات باشگاه"

    def __str__(self):
        return self.title


class Gym(models.Model):
    name = models.CharField(
        max_length=150,
        verbose_name="نام باشگاه"
    )

    description = models.TextField(
        blank=True,
        verbose_name="توضیحات"
    )

    address = models.TextField(
        verbose_name="آدرس"
    )

    phone = models.CharField(
        max_length=20,
        verbose_name="شماره تماس"
    )

    sports = models.ManyToManyField(
        Sport,
        related_name="gyms",
        verbose_name="رشته‌های ورزشی"
    )

    facilities = models.ManyToManyField(
        GymFacility,
        blank=True,
        related_name="gyms",
        verbose_name="امکانات"
    )

    latitude = models.FloatField(
        verbose_name="عرض جغرافیایی"
    )

    longitude = models.FloatField(
        verbose_name="طول جغرافیایی"
    )

    cover_image = models.ImageField(
        upload_to=upload_gym_cover_image,
        blank=True,
        null=True,
        verbose_name="تصویر اصلی باشگاه"
    )

    working_hours = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="ساعات کاری"
    )

    rules = models.TextField(
        blank=True,
        verbose_name="قوانین و مقررات"
    )

    instagram = models.URLField(
        blank=True,
        verbose_name="لینک اینستاگرام"
    )

    telegram = models.URLField(
        blank=True,
        verbose_name="لینک تلگرام"
    )

    website = models.URLField(
        blank=True,
        verbose_name="وب‌سایت"
    )

    whatsapp = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="شماره واتساپ"
    )

    popularity_score = models.PositiveIntegerField(
        default=0,
        verbose_name="امتیاز محبوبیت"
    )

    is_popular = models.BooleanField(
        default=False,
        verbose_name="باشگاه محبوب"
    )

    class Meta:
        verbose_name = "باشگاه"
        verbose_name_plural = "باشگاه‌ها"

    @property
    def average_rating(self):
        reviews = self.reviews.all()

        if not reviews.exists():
            return 0

        return round(
            sum(review.rating for review in reviews)
            / reviews.count(),
            1
        )

    @property
    def google_map_url(self):
        return f"https://maps.google.com/?q={self.latitude},{self.longitude}"

    def __str__(self):
        return self.name


class GymPrice(models.Model):
    gym = models.ForeignKey(
        Gym,
        on_delete=models.CASCADE,
        related_name="prices",
        verbose_name="باشگاه"
    )

    sport = models.ForeignKey(
        Sport,
        on_delete=models.CASCADE,
        verbose_name="رشته ورزشی"
    )

    session_price = models.PositiveIntegerField(
        default=0,
        verbose_name="قیمت تک جلسه"
    )

    monthly_price = models.PositiveIntegerField(
        verbose_name="قیمت ماهانه"
    )

    quarterly_price = models.PositiveIntegerField(
        default=0,
        verbose_name="قیمت سه ماهه"
    )

    yearly_price = models.PositiveIntegerField(
        verbose_name="قیمت سالانه"
    )

    class Meta:
        verbose_name = "تعرفه باشگاه"
        verbose_name_plural = "تعرفه‌های باشگاه"

    def __str__(self):
        return f"{self.gym.name} - {self.sport.name}"


class GymImage(models.Model):
    gym = models.ForeignKey(
        Gym,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="باشگاه"
    )

    image = models.ImageField(
        upload_to="gyms/gallery/",
        verbose_name="تصویر"
    )

    title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="عنوان تصویر"
    )

    class Meta:
        verbose_name = "تصویر باشگاه"
        verbose_name_plural = "گالری تصاویر"

    def __str__(self):
        return self.title or f"Image {self.id}"


class GymVideo(models.Model):
    gym = models.ForeignKey(
        Gym,
        on_delete=models.CASCADE,
        related_name="videos",
        verbose_name="باشگاه"
    )

    video_url = models.URLField(
        verbose_name="لینک ویدیو"
    )

    title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="عنوان ویدیو"
    )

    class Meta:
        verbose_name = "ویدیو باشگاه"
        verbose_name_plural = "ویدیوهای باشگاه"

    def __str__(self):
        return self.title or f"Video {self.id}"


class GymBanner(models.Model):
    gym = models.ForeignKey(
        Gym,
        on_delete=models.CASCADE,
        related_name="banners",
        verbose_name="باشگاه"
    )

    image = models.ImageField(
        upload_to="gyms/banners/",
        verbose_name="بنر"
    )

    class Meta:
        verbose_name = "بنر باشگاه"
        verbose_name_plural = "بنرهای باشگاه"

    def __str__(self):
        return self.gym.name


class GymCoach(models.Model):
    gym = models.ForeignKey(
        Gym,
        on_delete=models.CASCADE,
        related_name="coaches",
        verbose_name="باشگاه"
    )

    full_name = models.CharField(
        max_length=100,
        verbose_name="نام مربی"
    )

    image = models.ImageField(
        upload_to="gyms/coaches/",
        verbose_name="تصویر مربی"
    )

    specialty = models.CharField(
        max_length=100,
        verbose_name="تخصص"
    )

    class Meta:
        verbose_name = "مربی"
        verbose_name_plural = "مربیان"

    def __str__(self):
        return self.full_name


class GymReview(models.Model):
    gym = models.ForeignKey(
        Gym,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="باشگاه"
    )

    name = models.CharField(
        max_length=100,
        verbose_name="نام کاربر"
    )

    rating = models.PositiveSmallIntegerField(
        default=5,
        verbose_name="امتیاز"
    )

    comment = models.TextField(
        verbose_name="نظر"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ثبت"
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "نظر کاربران"
        verbose_name_plural = "نظرات کاربران"

    def __str__(self):
        return f"{self.gym.name} - {self.selfrating}"