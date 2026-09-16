from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gym", "0006_gymcoach_sports"),
    ]

    operations = [
        migrations.AddField(
            model_name="gym",
            name="gender",
            field=models.CharField(
                choices=[
                    ("women", "بانوان"),
                    ("men", "آقایان"),
                    ("both", "آقایان و بانوان"),
                ],
                default="both",
                help_text="women | men | both",
                max_length=10,
                verbose_name="جنسیت باشگاه",
            ),
        ),
        migrations.AddField(
            model_name="gym",
            name="is_open",
            field=models.BooleanField(
                default=True,
                help_text="وضعیت فعلی باز/بسته بودن باشگاه",
                verbose_name="باز است",
            ),
        ),
        migrations.AddField(
            model_name="gymcoach",
            name="bio",
            field=models.TextField(
                blank=True,
                default="",
                verbose_name="بیوگرافی مربی",
            ),
        ),
    ]
