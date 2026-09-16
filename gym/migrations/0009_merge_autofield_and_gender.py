# Merge parallel gym leaves:
# - 0006_alter_gym_id_alter_gymbanner_id_alter_gymcoach_id_and_more
# - 0008_merge_gender_is_open
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("gym", "0006_alter_gym_id_alter_gymbanner_id_alter_gymcoach_id_and_more"),
        ("gym", "0008_merge_gender_is_open"),
    ]

    operations = []
