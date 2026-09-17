# Merge parallel gym_panel 0005 leaves:
# - 0005_business_expansion
# - 0005_coach_panel
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("gym_panel", "0005_business_expansion"),
        ("gym_panel", "0005_coach_panel"),
    ]

    operations = []
