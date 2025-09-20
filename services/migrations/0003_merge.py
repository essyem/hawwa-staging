"""Merge migration to resolve parallel 0002 migrations.

This migration depends on both 0002_add_vendor_to_service and 0002_add_cost_field
so Django's migration graph becomes linear for test and CI runs.
"""
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('services', '0002_add_vendor_to_service'),
        ('services', '0002_add_cost_field'),
    ]

    operations = []
