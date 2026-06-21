from django.db import models
import os
import uuid
from django.utils.text import slugify
import time


def upload_gym_cover_image(instance, filename):
    short_name = slugify(instance.name, allow_unicode=True)[:50]  
    ext = filename.split('.')[-1]
    unique_name = f"{int(time.time())}_{uuid.uuid4().hex[:8]}_{short_name}.{ext}"
    path = os.path.join('uploads/gym/cover', unique_name)
    return path

class SportCategory(models.Model):
    title = models.CharField(max_length=100, verbose_name="عنوان دسته‌بندی")
    slug = models.SlugField(unique=True, verbose_name="اسلاگ")

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
    name = models.CharField(max_length=100, verbose_name="نام رشته ورزشی")

    class Meta:
        verbose_name = "رشته ورزشی"
        verbose_name_plural = "رشته‌های ورزشی"

    def __str__(self):
        return self.name


class Gym(models.Model):
    name = models.CharField(max_length=150, verbose_name="نام باشگاه")
    address = models.TextField(verbose_name="آدرس")
    phone = models.CharField(max_length=20, verbose_name="شماره تماس")
    sports = models.ManyToManyField(Sport, related_name="gyms", verbose_name="رشته‌های ورزشی")

    latitude = models.FloatField(verbose_name="عرض جغرافیایی")
    longitude = models.FloatField(verbose_name="طول جغرافیایی")

    cover_image = models.ImageField(
        upload_to=upload_gym_cover_image,
        verbose_name="تصویر اصلی باشگاه",
        null=True,
        blank=True
    )

    popularity_score = models.PositiveIntegerField(default=0, verbose_name="امتیاز محبوبیت")
    is_popular = models.BooleanField(default=False, verbose_name="باشگاه محبوب")

    class Meta:
        verbose_name = "باشگاه"
        verbose_name_plural = "باشگاه‌ها"

    def __str__(self):
        return self.name


class GymPrice(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name="prices", verbose_name="باشگاه")
    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, verbose_name="رشته ورزشی")
    monthly_price = models.PositiveIntegerField(verbose_name="قیمت ماهانه")
    yearly_price = models.PositiveIntegerField(verbose_name="قیمت سالانه")

    class Meta:
        verbose_name = "قیمت باشگاه"
        verbose_name_plural = "قیمت‌های باشگاه"

    def __str__(self):
        return f"{self.gym.name} - {self.sport.name}"
    

class GymImage(models.Model):
    gym = models.ForeignKey(
        Gym,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="باشگاه"
    )
    image = models.ImageField(upload_to="gyms/gallery/", verbose_name="تصویر")
    title = models.CharField(max_length=100, blank=True, verbose_name="عنوان تصویر")

    class Meta:
        verbose_name = "تصویر باشگاه"
        verbose_name_plural = "تصاویر باشگاه"
        

class GymVideo(models.Model):
    gym = models.ForeignKey(
        Gym,
        on_delete=models.CASCADE,
        related_name="videos",
        verbose_name="باشگاه"
    )
    video_url = models.URLField(verbose_name="لینک ویدیو (YouTube/MP4)")
    title = models.CharField(max_length=100, blank=True, verbose_name="عنوان ویدیو")

    class Meta:
        verbose_name = "ویدیو باشگاه"
        verbose_name_plural = "ویدیوهای باشگاه"