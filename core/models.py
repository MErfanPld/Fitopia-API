from django.db import models


class HomeSlider(models.Model):
    title = models.CharField(
        max_length=255,
        verbose_name="عنوان"
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="توضیحات"
    )

    image = models.ImageField(
        upload_to="uploads/sliders/",
        verbose_name="تصویر اسلایدر"
    )

    url = models.URLField(
        blank=True,
        null=True,
        verbose_name="لینک مقصد"
    )

    button_text = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="متن دکمه"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال"
    )

    order = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتیب نمایش"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["order", "-created_at"]
        verbose_name = "اسلایدر صفحه اصلی"
        verbose_name_plural = "اسلایدرهای صفحه اصلی"

    def __str__(self):
        return self.title