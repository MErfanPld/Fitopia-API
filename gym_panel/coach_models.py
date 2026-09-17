"""Coach Panel: feed, students, training/diet/supplement plans, monthly stats."""
import os
import time
import uuid

from django.conf import settings
from django.db import models
from django.utils.text import slugify


def upload_coach_post(instance, filename):
    ext = filename.rsplit(".", 1)[-1]
    name = f"{int(time.time())}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("uploads/coach/posts", name)


def upload_student_photo(instance, filename):
    base = slugify(instance.full_name or "student", allow_unicode=True)[:40]
    ext = filename.rsplit(".", 1)[-1]
    name = f"{int(time.time())}_{uuid.uuid4().hex[:8]}_{base}.{ext}"
    return os.path.join("uploads/coach/students", name)


class CoachStudent(models.Model):
    coach = models.ForeignKey("gym.GymCoach", on_delete=models.CASCADE, related_name="students", verbose_name="مربی")
    gym = models.ForeignKey("gym.Gym", on_delete=models.CASCADE, related_name="coach_students", verbose_name="باشگاه")
    gym_customer = models.ForeignKey("gym_panel.GymCustomer", on_delete=models.SET_NULL, null=True, blank=True, related_name="coach_links", verbose_name="مشتری باشگاه")
    fitopia_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="as_coach_student", verbose_name="کاربر فیتوپیا")
    full_name = models.CharField(max_length=150, verbose_name="نام کامل")
    phone = models.CharField(max_length=20, blank=True, verbose_name="موبایل")
    gender = models.CharField(max_length=10, blank=True, verbose_name="جنسیت")
    birth_date = models.DateField(null=True, blank=True, verbose_name="تاریخ تولد")
    photo = models.ImageField(upload_to=upload_student_photo, null=True, blank=True, verbose_name="عکس")
    notes = models.TextField(blank=True, verbose_name="یادداشت")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    joined_at = models.DateField(auto_now_add=True, verbose_name="تاریخ عضویت نزد مربی")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "شاگرد مربی"
        verbose_name_plural = "شاگردان مربی"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name} <- {self.coach}"


class CoachPost(models.Model):
    TYPE_CHOICES = [("coach", "عکس مربی"), ("student", "عکس شاگرد"), ("general", "عمومی")]
    coach = models.ForeignKey("gym.GymCoach", on_delete=models.CASCADE, related_name="posts", verbose_name="مربی")
    student = models.ForeignKey(CoachStudent, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts", verbose_name="شاگرد")
    image = models.ImageField(upload_to=upload_coach_post, verbose_name="تصویر")
    caption = models.TextField(blank=True, verbose_name="کپشن")
    post_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="general", verbose_name="نوع")
    is_public = models.BooleanField(default=True, verbose_name="عمومی")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "پست مربی"
        verbose_name_plural = "پست‌های مربی"
        ordering = ["-created_at"]


class TrainingProgram(models.Model):
    STATUS = [("draft", "پیش‌نویس"), ("active", "فعال"), ("completed", "تمام‌شده")]
    coach = models.ForeignKey("gym.GymCoach", on_delete=models.CASCADE, related_name="training_programs")
    student = models.ForeignKey(CoachStudent, on_delete=models.CASCADE, related_name="training_programs")
    title = models.CharField(max_length=200, verbose_name="عنوان")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    year = models.PositiveIntegerField(verbose_name="سال")
    month = models.PositiveIntegerField(verbose_name="ماه")
    status = models.CharField(max_length=20, choices=STATUS, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "برنامه تمرینی"
        verbose_name_plural = "برنامه‌های تمرینی"
        ordering = ["-year", "-month", "-created_at"]


class TrainingExercise(models.Model):
    program = models.ForeignKey(TrainingProgram, on_delete=models.CASCADE, related_name="exercises")
    day_of_week = models.PositiveSmallIntegerField(default=0, help_text="0=شنبه ... 6=جمعه", verbose_name="روز هفته")
    exercise_name = models.CharField(max_length=200, verbose_name="حرکت")
    sets = models.PositiveIntegerField(default=3, verbose_name="ست")
    reps = models.CharField(max_length=50, default="10", verbose_name="تکرار")
    rest_seconds = models.PositiveIntegerField(default=60, verbose_name="استراحت (ثانیه)")
    notes = models.TextField(blank=True, verbose_name="یادداشت")
    order = models.PositiveIntegerField(default=0, verbose_name="ترتیب")

    class Meta:
        ordering = ["day_of_week", "order", "id"]


class DietProgram(models.Model):
    STATUS = [("draft", "پیش‌نویس"), ("active", "فعال"), ("completed", "تمام‌شده")]
    coach = models.ForeignKey("gym.GymCoach", on_delete=models.CASCADE, related_name="diet_programs")
    student = models.ForeignKey(CoachStudent, on_delete=models.CASCADE, related_name="diet_programs")
    title = models.CharField(max_length=200, verbose_name="عنوان")
    description = models.TextField(blank=True)
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    daily_calories = models.PositiveIntegerField(null=True, blank=True, verbose_name="کالری روزانه")
    status = models.CharField(max_length=20, choices=STATUS, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "-month", "-created_at"]


class DietMeal(models.Model):
    MEAL_TYPES = [("breakfast", "صبحانه"), ("snack1", "میان‌وعده ۱"), ("lunch", "ناهار"), ("snack2", "میان‌وعده ۲"), ("dinner", "شام"), ("snack3", "میان‌وعده ۳")]
    program = models.ForeignKey(DietProgram, on_delete=models.CASCADE, related_name="meals")
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES, verbose_name="وعده")
    items = models.TextField(verbose_name="اقلام")
    calories = models.PositiveIntegerField(null=True, blank=True, verbose_name="کالری")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]


class SupplementProgram(models.Model):
    STATUS = [("draft", "پیش‌نویس"), ("active", "فعال"), ("completed", "تمام‌شده")]
    coach = models.ForeignKey("gym.GymCoach", on_delete=models.CASCADE, related_name="supplement_programs")
    student = models.ForeignKey(CoachStudent, on_delete=models.CASCADE, related_name="supplement_programs")
    title = models.CharField(max_length=200, verbose_name="عنوان")
    description = models.TextField(blank=True)
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-year", "-month", "-created_at"]


class SupplementItem(models.Model):
    program = models.ForeignKey(SupplementProgram, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=150, verbose_name="نام مکمل")
    dosage = models.CharField(max_length=100, blank=True, verbose_name="دوز")
    timing = models.CharField(max_length=100, blank=True, verbose_name="زمان مصرف")
    notes = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]


class StudentMonthlyStat(models.Model):
    coach = models.ForeignKey("gym.GymCoach", on_delete=models.CASCADE, related_name="student_stats")
    student = models.ForeignKey(CoachStudent, on_delete=models.CASCADE, related_name="monthly_stats")
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="وزن (کیلو)")
    body_fat_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, verbose_name="چربی بدن %")
    muscle_mass_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True, verbose_name="عضله (کیلو)")
    workouts_completed = models.PositiveIntegerField(default=0, verbose_name="تمرین انجام‌شده")
    adherence_percent = models.PositiveIntegerField(null=True, blank=True, verbose_name="درصد پایبندی")
    notes = models.TextField(blank=True, verbose_name="تحلیل مربی")
    measurements = models.JSONField(default=dict, blank=True, verbose_name="اندازه‌گیری‌ها")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "آمار ماهانه شاگرد"
        verbose_name_plural = "آمار ماهانه شاگردان"
        unique_together = ("student", "year", "month")
        ordering = ["-year", "-month"]
