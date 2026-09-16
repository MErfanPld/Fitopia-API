from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("tokens", "0001_initial"),
        ("gym", "0006_gymcoach_sports"),
    ]

    operations = [
        migrations.AlterField(
            model_name="gymtoken",
            name="gym",
            field=models.ForeignKey(
                blank=True,
                help_text="اگر خالی باشد، بلیت سراسری برای همه باشگاه‌های پلن است.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="tokens",
                to="gym.gym",
                verbose_name="باشگاه",
            ),
        ),
    ]
