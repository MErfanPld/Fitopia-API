# Local leaf that conflicted with the gender/is_open branch.
# Aligns primary keys to BigAutoField (no-op if already BigAutoField).
from django.db import migrations, models


def _big_auto():
    return models.BigAutoField(
        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("gym", "0005_alter_gym_options_alter_gymbanner_options_and_more"),
    ]

    operations = [
        migrations.AlterField(model_name="gym", name="id", field=_big_auto()),
        migrations.AlterField(model_name="gymbanner", name="id", field=_big_auto()),
        migrations.AlterField(model_name="gymcoach", name="id", field=_big_auto()),
        migrations.AlterField(model_name="gymfacility", name="id", field=_big_auto()),
        migrations.AlterField(model_name="gymimage", name="id", field=_big_auto()),
        migrations.AlterField(model_name="gymprice", name="id", field=_big_auto()),
        migrations.AlterField(model_name="gymreview", name="id", field=_big_auto()),
        migrations.AlterField(model_name="gymvideo", name="id", field=_big_auto()),
        migrations.AlterField(model_name="sport", name="id", field=_big_auto()),
        migrations.AlterField(model_name="sportcategory", name="id", field=_big_auto()),
    ]
