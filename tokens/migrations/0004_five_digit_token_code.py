import tokens.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tokens", "0003_merge_gymtoken_nullable"),
    ]

    operations = [
        # UUIDهای قبلی با طول ۵ سازگار نیستند؛ رکوردهای قدیمی پاک می‌شوند.
        migrations.RunPython(
            code=lambda apps, schema_editor: apps.get_model(
                "tokens", "GymToken"
            ).objects.all().delete(),
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="gymtoken",
            name="token_code",
            field=models.CharField(
                db_index=True,
                editable=False,
                help_text="کد ۵رقمی روزانه؛ بعد از نیمه‌شب قابل استفاده مجدد است",
                max_length=5,
                verbose_name="کد توکن",
            ),
        ),
        migrations.AlterField(
            model_name="gymtoken",
            name="valid_until",
            field=models.DateTimeField(
                default=tokens.models.default_valid_until,
                help_text="معمولاً نیمه‌شب همان روز",
                verbose_name="اعتبار تا",
            ),
        ),
        migrations.AddConstraint(
            model_name="gymtoken",
            constraint=models.UniqueConstraint(
                condition=models.Q(("status", "active")),
                fields=("token_code",),
                name="unique_active_gym_token_code",
            ),
        ),
    ]
