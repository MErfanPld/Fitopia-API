import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
import coach_panel.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("gym", "0010_gymcoach_user_is_active"),
        ("gym_panel", "0005_coach_panel"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Exercise",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=150, verbose_name="نام حرکت")),
                ("muscle_group", models.CharField(choices=[("chest", "سینه"), ("back", "پشت"), ("shoulders", "شانه"), ("arms", "بازو"), ("legs", "پا"), ("core", "میان‌تنه"), ("full_body", "کل بدن"), ("cardio", "هوازی"), ("other", "سایر")], default="other", max_length=30)),
                ("equipment", models.CharField(blank=True, max_length=100, verbose_name="تجهیزات")),
                ("instructions", models.TextField(blank=True, verbose_name="توضیحات")),
                ("video_url", models.URLField(blank=True, verbose_name="لینک ویدیو")),
                ("is_public", models.BooleanField(default=True, verbose_name="عمومی در باشگاه")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("coach", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="exercises", to="gym.gymcoach")),
                ("gym", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="exercises", to="gym.gym")),
            ],
            options={"verbose_name": "حرکت", "verbose_name_plural": "بانک حرکات", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="WorkoutSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(blank=True, default="", max_length=200, verbose_name="عنوان")),
                ("performed_at", models.DateTimeField(verbose_name="زمان تمرین")),
                ("duration_minutes", models.PositiveIntegerField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                ("feeling", models.PositiveSmallIntegerField(blank=True, help_text="1-10 احساس کلی", null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("coach", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="workout_sessions", to="gym.gymcoach")),
                ("gym", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="workout_sessions", to="gym.gym")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="workout_sessions", to="gym_panel.coachstudent")),
            ],
            options={"verbose_name": "جلسه تمرین", "verbose_name_plural": "تاریخچه تمرینات", "ordering": ["-performed_at"]},
        ),
        migrations.CreateModel(
            name="WorkoutSet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("set_number", models.PositiveIntegerField(default=1)),
                ("reps", models.PositiveIntegerField(blank=True, null=True)),
                ("weight_kg", models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True, verbose_name="وزن (کیلو)")),
                ("duration_seconds", models.PositiveIntegerField(blank=True, null=True)),
                ("rpe", models.PositiveSmallIntegerField(blank=True, help_text="1-10", null=True)),
                ("notes", models.CharField(blank=True, max_length=255)),
                ("order", models.PositiveIntegerField(default=0)),
                ("exercise", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sets", to="coach_panel.exercise")),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sets", to="coach_panel.workoutsession")),
            ],
            options={"ordering": ["order", "set_number", "id"]},
        ),
        migrations.CreateModel(
            name="PersonalRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("value", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="مقدار")),
                ("unit", models.CharField(choices=[("kg", "کیلوگرم"), ("reps", "تکرار"), ("seconds", "ثانیه"), ("m", "متر")], default="kg", max_length=20)),
                ("achieved_at", models.DateField(verbose_name="تاریخ ثبت")),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("coach", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="personal_records", to="gym.gymcoach")),
                ("exercise", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="prs", to="coach_panel.exercise")),
                ("gym", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="personal_records", to="gym.gym")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="personal_records", to="gym_panel.coachstudent")),
                ("workout_set", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="prs", to="coach_panel.workoutset")),
            ],
            options={"verbose_name": "رکورد شخصی", "verbose_name_plural": "رکوردهای شخصی", "ordering": ["-achieved_at", "-created_at"]},
        ),
        migrations.CreateModel(
            name="ProgressPhoto",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to=coach_panel.models.upload_progress_photo)),
                ("caption", models.CharField(blank=True, max_length=255)),
                ("side", models.CharField(choices=[("front", "روبرو"), ("side", "نیم‌رخ"), ("back", "پشت"), ("other", "سایر")], default="front", max_length=20)),
                ("taken_at", models.DateField(verbose_name="تاریخ عکس")),
                ("weight_kg", models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("coach", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="progress_photos", to="gym.gymcoach")),
                ("gym", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="progress_photos", to="gym.gym")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="progress_photos", to="gym_panel.coachstudent")),
            ],
            options={"verbose_name": "عکس پیشرفت", "verbose_name_plural": "عکس‌های پیشرفت", "ordering": ["-taken_at", "-created_at"]},
        ),
        migrations.CreateModel(
            name="FeedLike",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("post", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="likes", to="gym_panel.coachpost")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="coach_feed_likes", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at"], "unique_together": {("post", "user")}},
        ),
        migrations.CreateModel(
            name="FeedComment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("post", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="comments", to="gym_panel.coachpost")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="coach_feed_comments", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.AddIndex(
            model_name="personalrecord",
            index=models.Index(fields=["student", "exercise"], name="coach_panel_student_ex_idx"),
        ),
        migrations.AddIndex(
            model_name="personalrecord",
            index=models.Index(fields=["gym", "exercise", "-value"], name="coach_panel_gym_ex_val_idx"),
        ),
    ]
