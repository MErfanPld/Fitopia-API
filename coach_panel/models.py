"""پنل مربی — ثبت تمرین، PR، بانک حرکات، عکس پیشرفت، شبکه اجتماعی"""
import os
import time
import uuid

from django.conf import settings
from django.db import models


def upload_progress_photo(instance, filename):
    ext = filename.rsplit(".", 1)[-1]
    name = f"{int(time.time())}_{uuid.uuid4().hex[:8]}.{ext}"
    return os.path.join("uploads/coach/progress", name)


class Exercise(models.Model):
    MUSCLE_CHOICES = [
        ("chest", "سینه"), ("back", "پشت"), ("shoulders", "شانه"), ("arms", "بازو"),
        ("legs", "پا"), ("core", "میان‌تنه"), ("full_body", "کل بدن"),
        ("cardio", "هوازی"), ("other", "سایر"),
    ]
    gym = models.ForeignKey("gym.Gym", on_delete=models.CASCADE, related_name="exercises", null=True, blank=True)
    coach = models.ForeignKey("gym.GymCoach", on_delete=models.CASCADE, related_name="exercises", null=True, blank=True)
    name = models.CharField(max_length=150, verbose_name="نام حرکت")
    muscle_group = models.CharField(max_length=30, choices=MUSCLE_CHOICES, default="other")
    equipment = models.CharField(max_length=100, blank=True, verbose_name="تجهیزات")
    instructions = models.TextField(blank=True, verbose_name="توضیحات")
    video_url = models.URLField(blank=True, verbose_name="لینک ویدیو")
    is_public = models.BooleanField(default=True, verbose_name="عمومی در باشگاه")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "حرکت"
        verbose_name_plural = "بانک حرکات"
        ordering = ["name"]

    def __str__(self):
        return self.name


class WorkoutSession(models.Model):
    coach = models.ForeignKey("gym.GymCoach", on_delete=models.CASCADE, related_name="workout_sessions")
    student = models.ForeignKey("gym_panel.CoachStudent", on_delete=models.CASCADE, related_name="workout_sessions")
    gym = models.ForeignKey("gym.Gym", on_delete=models.CASCADE, related_name="workout_sessions")
    title = models.CharField(max_length=200, blank=True, default="", verbose_name="عنوان")
    performed_at = models.DateTimeField(verbose_name="زمان تمرین")
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    feeling = models.PositiveSmallIntegerField(null=True, blank=True, help_text="1-10 احساس کلی")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "جلسه تمرین"
        verbose_name_plural = "تاریخچه تمرینات"
        ordering = ["-performed_at"]


class WorkoutSet(models.Model):
    session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name="sets")
    exercise = models.ForeignKey(Exercise, on_delete=models.PROTECT, related_name="sets")
    set_number = models.PositiveIntegerField(default=1)
    reps = models.PositiveIntegerField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, verbose_name="وزن (کیلو)")
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    rpe = models.PositiveSmallIntegerField(null=True, blank=True, help_text="1-10")
    notes = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "set_number", "id"]


class PersonalRecord(models.Model):
    UNIT_CHOICES = [("kg", "کیلوگرم"), ("reps", "تکرار"), ("seconds", "ثانیه"), ("m", "متر")]
    coach = models.ForeignKey("gym.GymCoach", on_delete=models.CASCADE, related_name="personal_records")
    student = models.ForeignKey("gym_panel.CoachStudent", on_delete=models.CASCADE, related_name="personal_records")
    gym = models.ForeignKey("gym.Gym", on_delete=models.CASCADE, related_name="personal_records")
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="prs")
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="مقدار")
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default="kg")
    achieved_at = models.DateField(verbose_name="تاریخ ثبت")
    notes = models.TextField(blank=True)
    workout_set = models.ForeignKey(WorkoutSet, on_delete=models.SET_NULL, null=True, blank=True, related_name="prs")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "رکورد شخصی"
        verbose_name_plural = "رکوردهای شخصی"
        ordering = ["-achieved_at", "-created_at"]
        indexes = [
            models.Index(fields=["student", "exercise"]),
            models.Index(fields=["gym", "exercise", "-value"]),
        ]


class ProgressPhoto(models.Model):
    SIDE_CHOICES = [("front", "روبرو"), ("side", "نیم‌رخ"), ("back", "پشت"), ("other", "سایر")]
    coach = models.ForeignKey("gym.GymCoach", on_delete=models.CASCADE, related_name="progress_photos")
    student = models.ForeignKey("gym_panel.CoachStudent", on_delete=models.CASCADE, related_name="progress_photos")
    gym = models.ForeignKey("gym.Gym", on_delete=models.CASCADE, related_name="progress_photos")
    image = models.ImageField(upload_to=upload_progress_photo)
    caption = models.CharField(max_length=255, blank=True)
    side = models.CharField(max_length=20, choices=SIDE_CHOICES, default="front")
    taken_at = models.DateField(verbose_name="تاریخ عکس")
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "عکس پیشرفت"
        verbose_name_plural = "عکس‌های پیشرفت"
        ordering = ["-taken_at", "-created_at"]


class FeedLike(models.Model):
    post = models.ForeignKey("gym_panel.CoachPost", on_delete=models.CASCADE, related_name="likes")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="coach_feed_likes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("post", "user")
        ordering = ["-created_at"]


class FeedComment(models.Model):
    post = models.ForeignKey("gym_panel.CoachPost", on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="coach_feed_comments")
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
