# Merge parallel tokens 0002 leaves:
# - 0002_alter_gymtoken_id
# - 0002_gymtoken_gym_nullable
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tokens", "0002_alter_gymtoken_id"),
        ("tokens", "0002_gymtoken_gym_nullable"),
    ]

    operations = []
