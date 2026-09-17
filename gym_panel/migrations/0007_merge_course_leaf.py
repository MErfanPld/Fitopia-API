# Merge:
# - 0006_merge_coach_and_business
# - 0005_course_financetransaction_gymoffering_and_more
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("gym_panel", "0006_merge_coach_and_business"),
        ("gym_panel", "0005_course_financetransaction_gymoffering_and_more"),
    ]

    operations = []
