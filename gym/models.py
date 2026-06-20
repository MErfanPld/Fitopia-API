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