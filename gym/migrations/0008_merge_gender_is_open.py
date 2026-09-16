# Merge parallel gym 0007 leaves:
# - 0007_gym_gender_is_open_coach_bio
# - 0007_merge_20260722_0956
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("gym", "0007_gym_gender_is_open_coach_bio"),
        ("gym", "0007_merge_20260722_0956"),
    ]

    operations = []
