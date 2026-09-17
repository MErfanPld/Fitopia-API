# Local leaf that existed in parallel with 0005_business_expansion / 0005_coach_panel.
# Schema for offerings/courses/finance is already covered by 0005_business_expansion;
# this node is an empty leaf so the graph can merge cleanly.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("gym_panel", "0004_gymcustomer_added_by_gymcustomer_price_paid_and_more"),
    ]

    operations = []
