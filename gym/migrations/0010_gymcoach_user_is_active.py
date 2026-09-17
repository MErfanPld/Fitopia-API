import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("gym", "0009_merge_autofield_and_gender"),
    ]

    operations = [
        migrations.AddField(
            model_name="gymcoach",
            name="user",
            field=models.ForeignKey(
                blank=True,
                help_text="لینک به User برای ورود به پنل مربی",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="coach_profiles",
                to=settings.AUTH_USER_MODEL,
                verbose_name="حساب کاربری مربی",
            ),
        ),
        migrations.AddField(
            model_name="gymcoach",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="فعال"),
        ),
        migrations.AlterField(
            model_name="gymcoach",
            name="image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="gyms/coaches/",
                verbose_name="تصویر مربی",
            ),
        ),
        migrations.AddConstraint(
            model_name="gymcoach",
            constraint=models.UniqueConstraint(
                condition=models.Q(("user__isnull", False)),
                fields=("gym", "user"),
                name="unique_gym_coach_user",
            ),
        ),
    ]
